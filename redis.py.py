"""
Backend Redis — Pessoa 2
Responsabilidades: sessão ativa / tokens de login, carrinho dinâmico e cache com TTL.

Modelagem das chaves (Redis = chave-valor / in-memory):
  user:{email}        HASH   nome, salt, senha_hash            (sem TTL)
  session:{token}     HASH   user_id, nome                     (TTL deslizante = SESSION_TTL)
  cart:{user_id}      HASH   {produto_id: quantidade}          (TTL = CART_TTL)
  cache:{nome}        STRING JSON                              (TTL = CACHE_TTL)
"""
import os
import json
import hmac
import hashlib
import secrets

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
