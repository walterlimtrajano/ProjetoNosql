"""Ecrã 3 — recomendações cruzadas com base no grafo Neo4j."""
import os

import streamlit as st
from bson.objectid import ObjectId
from dotenv import load_dotenv
from neo4j.exceptions import Neo4jError
from pymongo import MongoClient
from pymongo.errors import PyMongoError

import redis_service as rs
from interface import render_sidebar_auth
from neo4j_service import Neo4jECommerceService

load_dotenv()
st.set_page_config(page_title="Recomendações | NoSQL E-Commerce", layout="wide")


@st.cache_resource
def get_collection():
    # conectando coleção de produtos ao mongodb
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
    db = client[os.getenv("DB_NAME", "ecommerce_db")]
    return db[os.getenv("COLLECTION_NAME", "produtos")]


@st.cache_resource
def get_neo4j_service():
    # mantendo a conexão neo4j aberta
    return Neo4jECommerceService()


def carregar_carrinho(user_id):
    """Busca no MongoDB os nomes dos produtos que estão no carrinho Redis."""
    # pegando os produtos guardados no carrinho do usuário
    itens = rs.obter_carrinho(user_id)
    if not itens:
        return []
    # convertendo os IDs para o formato usado no mongodb
    ids_validos = []
    for product_id in itens:
        if ObjectId.is_valid(product_id):
            ids_validos.append(ObjectId(product_id))
    if not ids_validos:
        return []
    # buscando os nomes dos produtos para consulta do neo4j
    produtos = get_collection().find(
        {"_id": {"$in": ids_validos}, "ativo": True},
        {"nome": 1},
    )
    return [produto["nome"] for produto in produtos if produto.get("nome")]


st.title("Motor de Recomendação")
st.caption(
    "Ecrã 3 — produtos comprados por clientes com interesses semelhantes, "
    "consultados no grafo Neo4j."
)

sessao = render_sidebar_auth()
if not sessao:
    st.info("Faça login na barra lateral para ver recomendações.")
    st.stop()

# carregando os produtos disponíveis no catálogo
try:
    produtos_catalogo = list(
        get_collection().find({"ativo": True}, {"nome": 1}).sort("nome", 1)
    )
except PyMongoError as erro:
    st.error(f"Não foi possível carregar o catálogo do MongoDB: {erro}")
    st.stop()

nomes_disponiveis = [
    produto["nome"] for produto in produtos_catalogo if produto.get("nome")
]
# usando os produtos do carrinho como seleção inicial
try:
    produtos_carrinho = carregar_carrinho(sessao["user_id"])
except PyMongoError as erro:
    st.error(f"Não foi possível consultar os produtos do carrinho: {erro}")
    st.stop()

selecionados = [nome for nome in produtos_carrinho if nome in nomes_disponiveis]
# deixando o usuário escolher os produtos para buscar recomendações
st.write(
    "As recomendações são calculadas a partir dos produtos selecionados "
    "(por padrão, os itens do seu carrinho)."
)
produtos_base = st.multiselect(
    "Produtos de interesse",
    options=nomes_disponiveis,
    default=selecionados,
    help="Escolha pelo menos um produto para encontrar clientes com compras semelhantes.",
)

if not produtos_base:
    st.info("Adicione produtos ao carrinho ou selecione um produto de interesse.")
    st.stop()

# consultando o neo4j para encontrar produtos recomendados
try:
    recomendacoes = get_neo4j_service().recomendar_produtos(produtos_base)
except ValueError as erro:
    st.error(str(erro))
    st.stop()
except Neo4jError as erro:
    st.error(f"Não foi possível consultar as recomendações no Neo4j: {erro}")
    st.stop()

if not recomendacoes:
    st.info(
        "Ainda não há compras relacionadas a esses produtos no grafo. "
        "Verifique se o Neo4j foi inicializado e contém dados de compras."
    )
else:
    # exibindo as recomendações e os clientes que compraram os produtos
    st.subheader("Clientes com perfil similar também compraram")
    colunas = st.columns(2)
    for indice, recomendacao in enumerate(recomendacoes):
        with colunas[indice % 2]:
            with st.container(border=True):
                st.subheader(recomendacao["produto"])
                st.metric(
                    "Clientes semelhantes",
                    recomendacao["clientes_similares"],
                )
                st.caption(
                    f"Produtos em comum: {recomendacao['produtos_em_comum']}"
                )
                if recomendacao["origens"]:
                    st.caption(
                        "Comprado por clientes como: "
                        + ", ".join(recomendacao["origens"])
                    )

with st.expander("Como a recomendação é calculada"):
    # consulta cypher usada para gerar as recomendações
    st.code(
        "MATCH (cliente_similar:Cliente)-[:COMPROU]->(produto_base:Produto)\n"
        "MATCH (cliente_similar)-[:COMPROU]->(recomendado:Produto)\n"
        "WHERE produto_base.nome IN $produtos_base\n"
        "  AND NOT recomendado.nome IN $produtos_base\n"
        "RETURN recomendado, count(DISTINCT cliente_similar) AS pontuacao\n"
        "ORDER BY pontuacao DESC",
        language="cypher",
    )
