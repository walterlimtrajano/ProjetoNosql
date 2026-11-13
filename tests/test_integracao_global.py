"""
Testes Globais e de Integração — Estudo de Caso 01: E-Commerce NoSQL
Valida a integração entre MongoDB, Redis e Neo4j (Polyglot Persistence),
focando especialmente na Camada de Cache (Cache-Aside, TTL, Invalidation, Ranking ZSET)
e no fluxo transacional completo de ponta a ponta (Checkout).
"""
import os
import sys
import pytest
from bson.objectid import ObjectId
from pymongo import MongoClient
from dotenv import load_dotenv

# Garante que a raiz do projeto está no sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import redis_service as rs
from neo4j_service import Neo4jECommerceService

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "ecommerce_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "produtos")


@pytest.fixture(scope="session")
def mongo_db():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db


@pytest.fixture(scope="session")
def neo4j_svc():
    svc = Neo4jECommerceService()
    yield svc
    svc.close()


# ==============================================================================
# TESTE 1: CONECTIVIDADE E SAÚDE DOS 3 BANCOS NOSQL
# ==============================================================================
def test_conectividade_polyglot(mongo_db, neo4j_svc):
    """Garante que MongoDB, Redis e Neo4j estão acessíveis e respondendo."""
    # 1. Redis
    assert rs.r.ping() is True, "Falha na conexão com o Redis!"

    # 2. MongoDB
    mongo_ping = mongo_db.command("ping")
    assert mongo_ping.get("ok") == 1.0, "Falha na conexão com o MongoDB!"

    # 3. Neo4j
    with neo4j_svc.driver.session(database=neo4j_svc.database) as session:
        res = session.run("RETURN 1 AS val").single()
        assert res["val"] == 1, "Falha na conexão com o Neo4j!"


# ==============================================================================
# TESTE 2: AUTENTICAÇÃO E SESSÃO ATIVA COM TTL NO REDIS
# ==============================================================================
def test_autenticacao_e_sessao_ttl():
    """Valida cadastro, login, integridade do token e renovação deslizante de TTL."""
    email_teste = "aluno_teste@loja.com"
    nome_teste = "Aluno Teste"
    senha_teste = "senhaSegura123"

    # Garante usuário cadastrado
    rs.registrar_usuario(email_teste, nome_teste, senha_teste)

    # Autenticação
    token = rs.autenticar(email_teste, senha_teste)
    assert token is not None, "Autenticação com credenciais corretas deve retornar um token."

    # Validação da sessão ativa
    sessao = rs.validar_sessao(token)
    assert sessao is not None
    assert sessao["user_id"] == email_teste
    assert sessao["nome"] == nome_teste

    # TTL deve estar ativo
    ttl = rs.ttl_sessao(token)
    assert 0 < ttl <= rs.SESSION_TTL

    # Logout
    rs.logout(token)
    assert rs.validar_sessao(token) is None


# ==============================================================================
# TESTE 3: CAMADA DE CACHE (CACHE-ASIDE + TTL + INVALIDAÇÃO)
# ==============================================================================
def test_cache_aside_ttl_e_invalidacao():
    """Valida o ciclo completo do Cache: Miss -> Hit -> TTL -> Invalidação."""
    termo = "samsung_test_query"
    hash_busca = rs.gerar_hash_busca(termo, "Todas", "Todas", 30000.0)

    # 1. Garante que inicialmente não está em cache (Cache Miss)
    rs.r.delete(rs.k_cache_busca(hash_busca))
    res, ttl = rs.cache_busca_get(hash_busca)
    assert res is None
    assert ttl == 0

    # 2. Grava no cache simulando Cache Miss resolvido
    mock_produtos = [
        {"nome": "Produto Teste 1", "preco": 100.0},
        {"nome": "Produto Teste 2", "preco": 200.0},
    ]
    rs.cache_busca_set(hash_busca, mock_produtos, ttl=60)

    # 3. Consulta subsequente deve ser Cache Hit
    res_hit, ttl_hit = rs.cache_busca_get(hash_busca)
    assert res_hit is not None
    assert len(res_hit) == 2
    assert res_hit[0]["nome"] == "Produto Teste 1"
    assert 0 < ttl_hit <= 60

    # 4. Invalidação Ativa das buscas
    invalidados = rs.invalidar_caches_busca()
    assert invalidados >= 1

    # 5. Após invalidação, deve ser Cache Miss novamente
    res_pos_inv, _ = rs.cache_busca_get(hash_busca)
    assert res_pos_inv is None


# ==============================================================================
# TESTE 4: RANKING DE PRODUTOS MAIS ACESSADOS (REDIS ZSET)
# ==============================================================================
def test_produtos_mais_acessados_zset():
    """Valida a contabilização em memória de acessos via Sorted Set (ZSET)."""
    p_a = "prod_teste_alpha"
    p_b = "prod_teste_beta"

    # Remove pontuações anteriores desses IDs de teste
    rs.r.zrem(rs.KEY_MAIS_ACESSADOS, p_a, p_b)

    # Simula acessos
    rs.registrar_acesso_produto(p_a)
    rs.registrar_acesso_produto(p_a)
    rs.registrar_acesso_produto(p_a)  # 3 acessos
    rs.registrar_acesso_produto(p_b)  # 1 acesso

    # Consulta ranking
    top = rs.obter_produtos_mais_acessados(limite=10)
    top_dict = dict(top)

    assert top_dict.get(p_a) == 3
    assert top_dict.get(p_b) == 1

    # Ordem decrescente (o mais acessado deve vir na frente)
    indices = [pid for pid, _ in top]
    assert indices.index(p_a) < indices.index(p_b)

    # Limpeza do teste
    rs.r.zrem(rs.KEY_MAIS_ACESSADOS, p_a, p_b)


# ==============================================================================
# TESTE 5: GESTÃO DO CARRINHO DINÂMICO NO REDIS (HASH)
# ==============================================================================
def test_carrinho_dinamico_redis():
    """Valida operações de adição, limite de estoque, alteração e esvaziamento."""
    user = "carrinho_test@loja.com"
    pid = "prod_999"

    rs.limpar_carrinho(user)
    assert rs.obter_carrinho(user) == {}

    # Adição respeitando limite
    qtd1 = rs.adicionar_item(user, pid, qtd=2, limite=5)
    assert qtd1 == 2
    assert rs.contar_itens(user) == 2

    # Tentar ultrapassar limite
    qtd2 = rs.adicionar_item(user, pid, qtd=10, limite=5)
    assert qtd2 == 5

    # Alteração direta
    rs.alterar_quantidade(user, pid, 3)
    assert rs.obter_carrinho(user).get(pid) == 3

    # Remoção
    rs.remover_item(user, pid)
    assert rs.obter_carrinho(user).get(pid) is None

    # Limpeza
    rs.adicionar_item(user, "outro_prod", 1)
    rs.limpar_carrinho(user)
    assert rs.contar_itens(user) == 0


# ==============================================================================
# TESTE 6: RECOMENDAÇÕES CRUZADAS NO NEO4J (CYPHER)
# ==============================================================================
def test_recomendacoes_neo4j(neo4j_svc):
    """Valida o algoritmo Cypher de recomendação baseada em compras semelhantes."""
    # Garante que os dados iniciais do grafo existem
    neo4j_svc.popular_dados_iniciais()

    # Baseado nas compras prévias:
    # Cliente 03 comprou Galaxy S24, iPad Pro e MacBook Pro
    # Cliente 01 comprou Galaxy S24
    # Quem tem Galaxy S24 no carrinho deve receber recomendações com iPad Pro ou MacBook Pro
    recs = neo4j_svc.recomendar_produtos(["Smartphone Galaxy S24 Ultra"])
    assert isinstance(recs, list)
    assert len(recs) > 0

    nomes_recomendados = [r["produto"] for r in recs]
    assert "iPad Pro 12.9'' M2" in nomes_recomendados or "Notebook MacBook Pro 16 M3 Max" in nomes_recomendados


# ==============================================================================
# TESTE 7: FLUXO COMPLETO DE CHECKOUT (INTEGRAÇÃO DOS 3 BANCOS)
# ==============================================================================
def test_fluxo_checkout_polyglot(mongo_db, neo4j_svc):
    """
    Testa o ciclo transacional completo exigido pelo estudo de caso:
    1. Produto existe no MongoDB.
    2. Usuário adiciona ao carrinho no Redis.
    3. Finaliza compra (Checkout):
       - Cria pedido na coleção 'pedidos' do MongoDB.
       - Decrementa estoque do produto no MongoDB.
       - Invalida cache no Redis (busca e produto).
       - Limpa carrinho no Redis.
       - Registra relacionamento [:COMPROU] no Neo4j.
    """
    user_teste = "checkout_polyglot@loja.com"
    cliente_nome = "Cliente Polyglot"
    produtos_col = mongo_db[COLLECTION_NAME]
    pedidos_col = mongo_db["pedidos"]

    # 1. Garante um produto com estoque conhecido no MongoDB
    doc_prod = produtos_col.find_one({"ativo": True, "estoque": {"$gt": 2}})
    assert doc_prod is not None, "É necessário pelo menos um produto com estoque > 2 no catálogo."
    pid = str(doc_prod["_id"])
    nome_prod = doc_prod["nome"]
    estoque_inicial = doc_prod["estoque"]
    preco = doc_prod["preco"]

    # 2. Adiciona ao carrinho no Redis
    rs.limpar_carrinho(user_teste)
    rs.adicionar_item(user_teste, pid, qtd=2, limite=estoque_inicial)
    assert rs.contar_itens(user_teste) == 2

    # Pré-condição: popula o cache de busca para testar a invalidação
    h_busca = rs.gerar_hash_busca("teste_check", "Todas", "Todas", 30000.0)
    rs.cache_busca_set(h_busca, [{"nome": nome_prod}], ttl=300)
    rs.cache_produto_set(pid, {"nome": nome_prod, "estoque": estoque_inicial})
    assert rs.cache_busca_get(h_busca)[0] is not None
    assert rs.cache_produto_get(pid) is not None

    # 3. Execução do Checkout
    # A. Salvar pedido no MongoDB
    res_pedido = pedidos_col.insert_one({
        "comprador_email": user_teste,
        "comprador_nome": cliente_nome,
        "total": preco * 2,
        "itens": [{"produto_id": pid, "nome": nome_prod, "quantidade": 2, "preco": preco}],
        "status": "FINALIZADO"
    })
    assert res_pedido.inserted_id is not None

    # B. Atualizar estoque no MongoDB
    produtos_col.update_one({"_id": ObjectId(pid)}, {"$inc": {"estoque": -2}})
    prod_atualizado = produtos_col.find_one({"_id": ObjectId(pid)})
    assert prod_atualizado["estoque"] == estoque_inicial - 2

    # C. Invalidação de Cache no Redis
    rs.invalidar_cache_produto(pid)
    rs.invalidar_caches_busca()
    assert rs.cache_produto_get(pid) is None, "Cache do produto deve ter sido invalidado!"
    assert rs.cache_busca_get(h_busca)[0] is None, "Caches de busca devem ter sido invalidados!"

    # D. Limpeza do carrinho no Redis
    rs.limpar_carrinho(user_teste)
    assert rs.contar_itens(user_teste) == 0

    # E. Atualização do grafo no Neo4j
    neo4j_svc.registrar_compra(cliente_nome, [nome_prod])
    with neo4j_svc.driver.session(database=neo4j_svc.database) as session:
        check_compra = session.run("""
            MATCH (c:Cliente {nome: $cliente})-[:COMPROU]->(p:Produto {nome: $prod})
            RETURN count(*) AS qtd
        """, cliente=cliente_nome, prod=nome_prod).single()
        assert check_compra["qtd"] >= 1, "Relacionamento de compra deve existir no Neo4j!"

    # Restaura estoque para não prejudicar futuros testes
    produtos_col.update_one({"_id": ObjectId(pid)}, {"$inc": {"estoque": 2}})
