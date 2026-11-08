"""Ecrã 2 — Carrinho Ativo (Redis em tempo real + detalhes do produto via MongoDB/cache)."""
import os

import streamlit as st
from bson.objectid import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient

import redis_service as rs
from interface import render_sidebar_auth

load_dotenv()
st.set_page_config(page_title="Carrinho | NoSQL E-Commerce", layout="wide")


@st.cache_resource
def get_collection():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
    db = client[os.getenv("DB_NAME", "ecommerce_db")]
    return db[os.getenv("COLLECTION_NAME", "produtos")]


def carregar_produto(pid: str):
    """Cache-aside: tenta o Redis (TTL) e, se não houver, busca no MongoDB."""
    cached = rs.cache_get(f"produto:{pid}")
    if cached:
        return cached, "Redis (cache)"
    try:
        doc = get_collection().find_one({"_id": ObjectId(pid)})
    except Exception:
        doc = None
    if not doc:
        return None, None
    prod = {
        "nome": doc.get("nome", "Sem nome"),
        "marca": doc.get("marca", ""),
        "preco": float(doc.get("preco", 0.0)),
        "estoque": int(doc.get("estoque", 0)),
        "imagem": (doc.get("imagens") or [None])[0],
    }
    rs.cache_set(f"produto:{pid}", prod)
    return prod, "MongoDB"


def _atualizar_qtd(user_id, pid):
    rs.alterar_quantidade(user_id, pid, st.session_state[f"qtd_{pid}"])


st.title("Carrinho Ativo")
st.caption("Ecrã 2 — Itens mantidos em tempo real no Redis (HASH por usuário)")

sessao = render_sidebar_auth()
if not sessao:
    st.info("Faça login na barra lateral para ver seu carrinho.")
    st.stop()

user_id = sessao["user_id"]
carrinho = rs.obter_carrinho(user_id)

if not carrinho:
    st.info("Seu carrinho está vazio. Adicione produtos pelo Catálogo.")
else:
    total, total_itens = 0.0, 0
    for pid, qtd in carrinho.items():
        prod, origem = carregar_produto(pid)
        if prod is None:  # produto removido do catálogo
            rs.remover_item(user_id, pid)
            continue

        qtd = min(qtd, max(prod["estoque"], 1))
        subtotal = prod["preco"] * qtd
        total += subtotal
        total_itens += qtd

        with st.container(border=True):
            c_img, c_info, c_qtd, c_sub, c_del = st.columns([1, 3, 2, 2, 1])
            with c_img:
                if prod["imagem"]:
                    st.image(prod["imagem"], use_container_width=True)
            with c_info:
                st.subheader(prod["nome"])
                st.caption(f"{prod['marca']} · R$ {prod['preco']:,.2f} un. · Estoque: {prod['estoque']} · dados via {origem}")
            with c_qtd:
                st.number_input(
                    "Quantidade", min_value=1, max_value=max(prod["estoque"], 1),
                    value=qtd, step=1, key=f"qtd_{pid}",
                    on_change=_atualizar_qtd, args=(user_id, pid),
                )
            with c_sub:
                st.metric("Subtotal", f"R$ {subtotal:,.2f}")
            with c_del:
                st.write("")
                st.button("Remover", key=f"rm_{pid}", on_click=rs.remover_item, args=(user_id, pid))

    c1, c2, c3 = st.columns(3)
    c1.metric("Itens", total_itens)
    c2.metric("Total", f"R$ {total:,.2f}")
    with c3:
        st.button("Esvaziar carrinho", on_click=rs.limpar_carrinho, args=(user_id,))

with st.expander("Ver dados brutos no Redis (para a demonstração)"):
    st.json({
        "chave_sessao": f"session:{st.session_state['token'][:8]}...",
        "ttl_sessao_s": rs.ttl_sessao(st.session_state["token"]),
        "chave_carrinho": rs.k_cart(user_id),
        "ttl_carrinho_s": rs.ttl_carrinho(user_id),
        "HGETALL": rs.obter_carrinho(user_id),
    })
