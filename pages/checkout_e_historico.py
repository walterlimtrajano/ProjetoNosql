import os
from datetime import datetime

import streamlit as st
from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from redis.exceptions import RedisError

import redis_service as rs
from interface import render_sidebar_auth

load_dotenv()
st.set_page_config(page_title="Checkout | NoSQL E-Commerce", layout="wide")


@st.cache_resource
def get_mongo_db():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
    return client[os.getenv("DB_NAME", "ecommerce_db")]


def get_products_collection():
    return get_mongo_db()[os.getenv("COLLECTION_NAME", "produtos")]


def get_orders_collection():
    return get_mongo_db()["pedidos"]


def format_order_date(order):
    value = order.get("data") or order.get("data_pedido")
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y às %H:%M")
    if not value:
        return "Data desconhecida"
    try:
        return datetime.fromisoformat(value).strftime("%d/%m/%Y às %H:%M")
    except (TypeError, ValueError):
        return str(value)


st.title("🛒 E-Commerce NoSQL — Checkout e Histórico de Pedidos")

sessao = render_sidebar_auth()
if not sessao:
    st.info("Faça login na barra lateral para finalizar pedidos e consultar seu histórico.")
    st.stop()

user_id = sessao["user_id"]
tab_checkout, tab_history = st.tabs(
    ["🛍️ Finalizar Checkout", "📜 Histórico de Pedidos"]
)

with tab_checkout:
    st.subheader("Carrinho de compras ativo (Redis)")
    redis_disponivel = True
    try:
        carrinho = rs.obter_carrinho(user_id)
    except (RedisError, ValueError) as erro:
        st.error(f"Não foi possível consultar o carrinho no Redis: {erro}")
        carrinho = {}
        redis_disponivel = False

    if redis_disponivel and not carrinho:
        st.info("O seu carrinho está vazio no momento.")
    elif redis_disponivel:
        produtos_ids = [
            ObjectId(produto_id)
            for produto_id in carrinho
            if ObjectId.is_valid(produto_id)
        ]
        ids_invalidos = [
            produto_id
            for produto_id in carrinho
            if not ObjectId.is_valid(produto_id)
        ]

        catalogo_disponivel = True
        try:
            produtos = (
                get_products_collection().find({"_id": {"$in": produtos_ids}})
                if produtos_ids
                else []
            )
            produtos_por_id = {str(produto["_id"]): produto for produto in produtos}
        except PyMongoError as erro:
            st.error(f"Não foi possível carregar os produtos do MongoDB: {erro}")
            produtos_por_id = {}
            catalogo_disponivel = False

        itens_pedido = []
        itens_indisponiveis = list(ids_invalidos)
        total_pedido = 0.0
        total_itens = 0

        for produto_id, quantidade in carrinho.items():
            if not catalogo_disponivel:
                itens_indisponiveis.append(produto_id)
                continue

            produto = produtos_por_id.get(produto_id)
            if produto is None:
                itens_indisponiveis.append(produto_id)
                continue

            try:
                preco = float(produto["preco"])
                quantidade = int(quantidade)
                if quantidade <= 0 or preco < 0:
                    raise ValueError("Quantidade ou preço inválido.")
            except (KeyError, TypeError, ValueError) as erro:
                st.error(f"Dados inválidos para o produto {produto_id}: {erro}")
                itens_indisponiveis.append(produto_id)
                continue

            subtotal = preco * quantidade
            total_pedido += subtotal
            total_itens += quantidade
            st.write(
                f"- **{produto.get('nome', 'Produto sem nome')}** | "
                f"Qtd: {quantidade} | Subtotal: R$ {subtotal:.2f}"
            )
            itens_pedido.append(
                {
                    "produto_id": produto_id,
                    "nome": produto.get("nome", "Produto sem nome"),
                    "marca": produto.get("marca", ""),
                    "quantidade": quantidade,
                    "preco": preco,
                    "subtotal": subtotal,
                }
            )

        if not catalogo_disponivel:
            st.info("O checkout ficará disponível quando o MongoDB voltar a responder.")
        elif itens_indisponiveis:
            st.warning(
                "Há itens inválidos ou removidos do catálogo no carrinho. "
                "Remova-os na página Carrinho antes de finalizar."
            )

        if itens_pedido:
            st.markdown(f"### **Total do Pedido: R$ {total_pedido:.2f}**")

        if st.button(
            "✅ Confirmar e Processar Pedido",
            type="primary",
            disabled=not itens_pedido or bool(itens_indisponiveis),
        ):
            novo_pedido = {
                "comprador_email": user_id,
                "comprador_nome": sessao.get("nome", "Cliente"),
                "data": datetime.now().isoformat(),
                "status": "FINALIZADO",
                "total": total_pedido,
                "total_itens": total_itens,
                "itens": itens_pedido,
            }

            try:
                resultado = get_orders_collection().insert_one(novo_pedido)
            except PyMongoError as erro:
                st.error(f"Não foi possível gravar o pedido no MongoDB: {erro}")
            else:
                try:
                    rs.limpar_carrinho(user_id)
                except RedisError as erro:
                    st.error(
                        f"O pedido {resultado.inserted_id} foi gravado, mas não foi "
                        f"possível limpar o carrinho no Redis: {erro}"
                    )
                else:
                    st.success(
                        f"🎉 Pedido #{str(resultado.inserted_id)[-6:]} finalizado "
                        "e gravado no MongoDB. O carrinho foi limpo."
                    )
                    st.rerun()

with tab_history:
    st.subheader("Seus pedidos finalizados (MongoDB)")
    try:
        pedidos = list(
            get_orders_collection()
            .find(
                {
                    "$or": [
                        {"comprador_email": user_id},
                        {"cliente_id": user_id},
                    ]
                }
            )
            .sort([("data", -1), ("data_pedido", -1)])
        )
    except PyMongoError as erro:
        st.error(f"Não foi possível consultar o histórico no MongoDB: {erro}")
        st.stop()

    if not pedidos:
        st.warning("Nenhum pedido finalizado encontrado no MongoDB.")
    else:
        for pedido in pedidos:
            data_formatada = format_order_date(pedido)
            total = pedido.get("total", pedido.get("valor_total", 0.0))
            pedido_id = str(pedido.get("_id", ""))
            with st.expander(
                f"📦 Pedido #{pedido_id[-6:]} — {data_formatada} — "
                f"Total: R$ {float(total):.2f}"
            ):
                st.write(f"**Status:** {pedido.get('status', 'Finalizado')}")
                st.write("**Itens do Pedido:**")
                for item in pedido.get("itens", []):
                    quantidade = int(item.get("quantidade", 0))
                    subtotal = item.get("subtotal")
                    if subtotal is None:
                        preco = item.get("preco", item.get("preco_unitario", 0.0))
                        subtotal = float(preco) * quantidade
                    st.write(
                        f"- {item.get('nome', 'Produto')} (x{quantidade}) — "
                        f"R$ {float(subtotal):.2f}"
                    )
