"""Ecrã 2 — Carrinho Ativo (Redis em tempo real + detalhes do produto via MongoDB/cache) & Checkout."""
import os
import datetime

import streamlit as st
from bson.objectid import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient

import redis_service as rs
from interface import render_sidebar_auth
from neo4j_service import Neo4jECommerceService

load_dotenv()
st.set_page_config(page_title="Carrinho | NoSQL E-Commerce", layout="wide")


@st.cache_resource
def get_mongo_db():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
    return client[os.getenv("DB_NAME", "ecommerce_db")]


def get_collection():
    return get_mongo_db()[os.getenv("COLLECTION_NAME", "produtos")]


def get_pedidos_collection():
    return get_mongo_db()["pedidos"]


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
    itens_comprados = []
    total, total_itens = 0.0, 0
    for pid, qtd in carrinho.items():
        prod, origem = carregar_produto(pid)
        if prod is None:
            rs.remover_item(user_id, pid)
            continue

        qtd = min(qtd, max(prod["estoque"], 1))
        subtotal = prod["preco"] * qtd
        total += subtotal
        total_itens += qtd
        itens_comprados.append({
            "produto_id": pid,
            "nome": prod["nome"],
            "marca": prod["marca"],
            "preco": prod["preco"],
            "quantidade": qtd,
            "subtotal": subtotal,
        })

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

    c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
    c1.metric("Itens", total_itens)
    c2.metric("Total", f"R$ {total:,.2f}")
    with c3:
        st.write("")
        st.button("Esvaziar carrinho", on_click=rs.limpar_carrinho, args=(user_id,))
    
    with c4:
        st.write("")
        if st.button("🛍️ Finalizar Pedido (Checkout)", type="primary", use_container_width=True):
            novo_pedido = {
                "comprador_email": user_id,
                "comprador_nome": sessao.get("nome", "Cliente"),
                "data": datetime.datetime.now().isoformat(),
                "itens": itens_comprados,
                "total": total,
                "total_itens": total_itens,
                "status": "FINALIZADO",
            }
            res = get_pedidos_collection().insert_one(novo_pedido)
            pedido_id = str(res.inserted_id)

            produtos_col = get_collection()
            nomes_para_grafo = []
            for item in itens_comprados:
                nomes_para_grafo.append(item["nome"])
                pid = item["produto_id"]
                qtd = item["quantidade"]
                try:
                    produtos_col.update_one(
                        {"_id": ObjectId(pid)},
                        {"$inc": {"estoque": -qtd}}
                    )
                except Exception:
                    pass
                rs.invalidar_cache_produto(pid)

            invalidados = rs.invalidar_caches_busca()

            rs.limpar_carrinho(user_id)

            try:
                neo_svc = Neo4jECommerceService()
                neo_svc.registrar_compra(sessao.get("nome", "Cliente"), nomes_para_grafo)
                neo_svc.close()
                grafo_msg = "✅ Relacionamentos [:COMPROU] criados no Neo4j."
            except Exception as e:
                grafo_msg = f"⚠️ Neo4j: {e}"

            st.balloons()
            st.success(f"🎉 Pedido #{pedido_id[:8]}... finalizado com sucesso!")
            st.markdown(f"""
            **Fluxo Polyglot Persistence concluído:**
            - **MongoDB:** Pedido persistido na coleção `pedidos` e estoque atualizado.
            - **Redis:** Carrinho esvaziado e `{invalidados}` chave(s) de cache de catálogo invalidadas para refletir o novo estoque.
            - **Neo4j:** {grafo_msg}
            """)
            st.rerun()

pedidos_usuario = list(get_pedidos_collection().find({"comprador_email": user_id}).sort("data", -1))
if pedidos_usuario:
    with st.expander(f"📦 Histórico de Pedidos Finalizados no MongoDB ({len(pedidos_usuario)} pedidos)"):
        for p in pedidos_usuario:
            st.markdown(f"**Pedido ID:** `{str(p.get('_id'))}` — Data: `{p.get('data')[:19]}` — **Total: R$ {p.get('total', 0.0):,.2f}**")
            for it in p.get("itens", []):
                st.caption(f"- {it.get('quantidade')}x {it.get('nome')} (R$ {it.get('subtotal', 0.0):,.2f})")
            st.divider()

with st.expander("Ver dados brutos no Redis (para a demonstração)"):
    st.json({
        "chave_sessao": f"session:{st.session_state['token'][:8]}...",
        "ttl_sessao_s": rs.ttl_sessao(st.session_state["token"]),
        "chave_carrinho": rs.k_cart(user_id),
        "ttl_carrinho_s": rs.ttl_carrinho(user_id),
        "HGETALL": rs.obter_carrinho(user_id),
    })
