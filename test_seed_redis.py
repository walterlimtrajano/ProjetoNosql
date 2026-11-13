import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

import redis_service as rs


PRODUCT_NAMES = (
    "Smartphone Galaxy S24 Ultra",
    "Teclado Mecânico Logitech G Pro X TKL",
)


def main():
    user_id = os.getenv("SEED_USER_ID", "ana@loja.com").strip().lower()
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))

    try:
        db = client[os.getenv("DB_NAME", "ecommerce_db")]
        products = list(
            db[os.getenv("COLLECTION_NAME", "produtos")].find(
                {"nome": {"$in": PRODUCT_NAMES}},
                {"nome": 1},
            )
        )
        products_by_name = {product["nome"]: product for product in products}
        missing_products = [
            name for name in PRODUCT_NAMES if name not in products_by_name
        ]
        if missing_products:
            raise RuntimeError(
                "Produtos não encontrados no catálogo: "
                + ", ".join(missing_products)
                + ". Abra a aplicação Streamlit uma vez para popular o catálogo."
            )

        rs.r.ping()
        if not rs.r.exists(rs.k_user(user_id)):
            raise RuntimeError(
                f"Usuário {user_id} não existe no Redis. "
                "Execute inicializacao_redis.py primeiro."
            )

        for name in PRODUCT_NAMES:
            product_id = str(products_by_name[name]["_id"])
            rs.adicionar_item(user_id, product_id, qtd=1, limite=1)

        print(f"Carrinho de teste criado para {user_id}:")
        for name in PRODUCT_NAMES:
            print(f"- {name}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
