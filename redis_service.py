"""
Backend Redis — Pessoa 2
Responsabilidades: sessão ativa / tokens de login, carrinho dinâmico e cache com TTL.

Modelagem das chaves (Redis = chave-valor / in-memory):
  user:{email}        HASH   nome, salt, senha_hash            (sem TTL)
  session:{token}     HASH   user_id, nome                     (TTL deslizante = SESSION_TTL)
  cart:{user_id}      HASH   {produto_id: quantidade}          (TTL = CART_TTL)
  cache:{nome}        STRING JSON                              (TTL = CACHE_TTL)
"""
import json
import hmac
import hashlib
import secrets
import os

import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SESSION_TTL = int(os.getenv("SESSION_TTL", 1800))   # 30 min (renova a cada uso)
CART_TTL = int(os.getenv("CART_TTL", 86400))        # 24 h
CACHE_TTL = int(os.getenv("CACHE_TTL", 300))        # 5 min

# decode_responses=True -> retorna str em vez de bytes
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)


# ---------- nomes das chaves ----------
def k_user(email): return f"user:{email}"
def k_session(token): return f"session:{token}"
def k_cart(user_id): return f"cart:{user_id}"
def k_cache(nome): return f"cache:{nome}"
def k_cache_produto(pid): return f"cache:produto:{pid}"
def k_cache_busca(hash_query): return f"cache:busca:{hash_query}"
KEY_MAIS_ACESSADOS = "produtos:mais_acessados"


# ---------- usuários e login ----------
def _hash_senha(senha: str, salt_hex: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", senha.encode(), bytes.fromhex(salt_hex), 100_000
    ).hex()


def registrar_usuario(email: str, nome: str, senha: str) -> bool:
    """Cria o usuário. Retorna False se o e-mail já existe."""
    email = email.strip().lower()
    # HSETNX é atômico: só um dos concorrentes "ganha" o e-mail
    if not r.hsetnx(k_user(email), "email", email):
        return False
    salt = secrets.token_hex(16)
    r.hset(k_user(email), mapping={
        "nome": nome.strip(),
        "salt": salt,
        "senha_hash": _hash_senha(senha, salt),
    })
    return True


def autenticar(email: str, senha: str):
    """Valida credenciais e devolve um token de sessão (ou None)."""
    email = email.strip().lower()
    u = r.hgetall(k_user(email))
    if not u or "senha_hash" not in u:
        return None
    if not hmac.compare_digest(u["senha_hash"], _hash_senha(senha, u["salt"])):
        return None
    token = secrets.token_urlsafe(32)
    pipe = r.pipeline()
    pipe.hset(k_session(token), mapping={"user_id": email, "nome": u["nome"]})
    pipe.expire(k_session(token), SESSION_TTL)
    pipe.execute()
    return token


def validar_sessao(token):
    """Retorna {'user_id', 'nome'} se o token for válido e renova o TTL (sliding)."""
    if not token:
        return None
    dados = r.hgetall(k_session(token))
    if not dados:
        return None
    r.expire(k_session(token), SESSION_TTL)
    return dados


def ttl_sessao(token) -> int:
    return max(r.ttl(k_session(token)), 0)


def logout(token) -> None:
    r.delete(k_session(token))


# ---------- carrinho ----------
def obter_carrinho(user_id: str) -> dict:
    """{produto_id: quantidade}"""
    return {pid: int(q) for pid, q in r.hgetall(k_cart(user_id)).items()}


def adicionar_item(user_id: str, produto_id: str, qtd: int = 1, limite=None) -> int:
    """Soma qtd ao item (respeitando o estoque). Retorna a quantidade final."""
    key = k_cart(user_id)
    nova = int(r.hget(key, produto_id) or 0) + qtd
    if limite is not None:
        nova = min(nova, int(limite))
    if nova <= 0:
        remover_item(user_id, produto_id)
        return 0
    pipe = r.pipeline()
    pipe.hset(key, produto_id, nova)
    pipe.expire(key, CART_TTL)
    pipe.execute()
    return nova


def alterar_quantidade(user_id: str, produto_id: str, qtd: int) -> None:
    """Define a quantidade exata. qtd <= 0 remove o item."""
    key = k_cart(user_id)
    if qtd <= 0:
        r.hdel(key, produto_id)
    elif r.hexists(key, produto_id):
        pipe = r.pipeline()
        pipe.hset(key, produto_id, qtd)
        pipe.expire(key, CART_TTL)
        pipe.execute()


def remover_item(user_id: str, produto_id: str) -> None:
    r.hdel(k_cart(user_id), produto_id)


def limpar_carrinho(user_id: str) -> None:
    """Usado também pelo Checkout após salvar o pedido no MongoDB."""
    r.delete(k_cart(user_id))


def contar_itens(user_id: str) -> int:
    return sum(int(q) for q in r.hvals(k_cart(user_id)))


def ttl_carrinho(user_id: str) -> int:
    return r.ttl(k_cart(user_id))


# ---------- cache com TTL (cache invalidation) ----------
def cache_get(nome: str):
    valor = r.get(k_cache(nome))
    return json.loads(valor) if valor else None


def cache_set(nome: str, valor, ttl: int = CACHE_TTL) -> None:
    r.set(k_cache(nome), json.dumps(valor, default=str), ex=ttl)


def cache_invalidar(nome: str) -> None:
    r.delete(k_cache(nome))


# ---------- cache especializado para catálogo e busca (Cache-Aside + TTL) ----------
def gerar_hash_busca(termo: str, categoria: str, marca: str, preco_max: float) -> str:
    """Gera chave determinística MD5 para os parâmetros de busca."""
    normalizado = f"{termo.strip().lower()}|{categoria.strip().lower()}|{marca.strip().lower()}|{float(preco_max):.2f}"
    return hashlib.md5(normalizado.encode("utf-8")).hexdigest()


def cache_busca_get(hash_query: str):
    """
    Retorna tupla (produtos, ttl_restante) ou (None, 0).
    Aproveita resposta prévia no Redis com tempo de resposta em microssegundos.
    """
    key = k_cache_busca(hash_query)
    valor = r.get(key)
    if valor:
        ttl = max(r.ttl(key), 0)
        return json.loads(valor), ttl
    return None, 0


def cache_busca_set(hash_query: str, produtos: list, ttl: int = CACHE_TTL) -> None:
    """Armazena o resultado de uma busca no Redis com TTL configurável."""
    key = k_cache_busca(hash_query)
    r.set(key, json.dumps(produtos, default=str), ex=ttl)


# ---------- cache de produto individual ----------
def cache_produto_get(produto_id: str):
    """Retorna dados de um produto específico em cache ou None."""
    key = k_cache_produto(produto_id)
    valor = r.get(key)
    return json.loads(valor) if valor else None


def cache_produto_set(produto_id: str, produto: dict, ttl: int = CACHE_TTL) -> None:
    """Salva detalhes do produto em cache individual com TTL."""
    key = k_cache_produto(produto_id)
    r.set(key, json.dumps(produto, default=str), ex=ttl)


# ---------- produtos mais acessados (Sorted Set - ZSET) ----------
def registrar_acesso_produto(produto_id: str) -> int:
    """
    Incrementa o contador de acessos do produto no Redis (ZSET).
    Executa ZINCRBY O(log(N)) em memória para manter o ranking em tempo real.
    """
    if not produto_id:
        return 0
    return int(r.zincrby(KEY_MAIS_ACESSADOS, 1, str(produto_id)))


def obter_produtos_mais_acessados(limite: int = 5) -> list:
    """
    Retorna lista de tuplas [(produto_id, score_acessos), ...] dos mais populares.
    Usa ZREVRANGE para consulta de alto desempenho direto da RAM.
    """
    res = r.zrevrange(KEY_MAIS_ACESSADOS, 0, limite - 1, withscores=True)
    return [(pid, int(score)) for pid, score in res]


# ---------- lógicas de Cache Invalidation ----------
def invalidar_caches_busca() -> int:
    """
    Invalida todas as consultas de catálogo salvas em cache.
    Chamado após checkout, atualização de estoque ou modificação de produtos.
    """
    chaves = r.keys("cache:busca:*")
    if chaves:
        return r.delete(*chaves)
    return 0


def invalidar_cache_produto(produto_id: str) -> None:
    """Invalida o cache específico de um produto que sofreu alteração."""
    r.delete(k_cache_produto(produto_id))
    r.delete(k_cache(f"produto:{produto_id}"))


def invalidar_todo_cache() -> int:
    """
    Invalida todo o cache de busca e produtos (para testes e demonstração ao vivo).
    """
    chaves = r.keys("cache:*")
    if chaves:
        return r.delete(*chaves)
    return 0


def obter_estatisticas_cache() -> dict:
    """Retorna métricas operacionais do Redis para o painel de monitoramento."""
    chaves_busca = len(r.keys("cache:busca:*"))
    chaves_produtos = len(r.keys("cache:produto:*") + r.keys("cache:produto*"))
    total_mais_acessados = r.zcard(KEY_MAIS_ACESSADOS)
    info = r.info("memory")
    return {
        "chaves_busca": chaves_busca,
        "chaves_produtos": chaves_produtos,
        "total_ranqueados": total_mais_acessados,
        "memoria_usada_humana": info.get("used_memory_human", "N/A"),
        "memoria_pico_humana": info.get("used_memory_peak_human", "N/A"),
    }

