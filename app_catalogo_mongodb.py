import streamlit as st
import os
from pymongo import MongoClient, TEXT
from bson.objectid import ObjectId
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "ecommerce_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "produtos")

@st.cache_resource
def get_mongo_client():
    client = MongoClient(MONGO_URI)
    return client

client = get_mongo_client()
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

try:
    collection.create_index([("nome", TEXT), ("descricao", TEXT), ("marca", TEXT)])
except Exception:
    pass

def popular_banco_se_vazio():
  """Popula a coleção de produtos com um catálogo expandido (Esquema Flexível JSON)."""
  if collection.count_documents({}) == 0:
    produtos_exemplo = [
        {
            "nome": "Smartphone Galaxy S24 Ultra",
            "marca": "Samsung",
            "categorias": ["Eletrônicos", "Smartphones", "Tecnologia"],
            "preco": 6999.00,
            "estoque": 15,
            "imagens": [
                "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?auto=format&fit=crop&w=600&q=80"
            ],
            "descricao": (
                "Smartphone topo de linha com IA integrada, câmera de 200MP e"
                " caneta S-Pen."
            ),
            "especificacoes": {
                "tela": "6.8 polegadas Dynamic AMOLED 2X",
                "memoria_ram": "12GB",
                "armazenamento": "512GB",
                "processador": "Snapdragon 8 Gen 3",
                "bateria": "5000 mAh",
                "resistencia_agua": "IP68",
            },
            "ativo": True,
        },
        {
            "nome": "iPad Pro 12.9'' M2",
            "marca": "Apple",
            "categorias": ["Eletrônicos", "Tablets", "Tecnologia"],
            "preco": 9899.00,
            "estoque": 7,
            "imagens": [
                "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&w=600&q=80"
            ],
            "descricao": (
                "Performance absurda com o chip M2, ecrã Liquid Retina XDR e"
                " suporte à Apple Pencil 2."
            ),
            "especificacoes": {
                "processador": "Apple M2 (8-core CPU, 10-core GPU)",
                "tela": "12.9 polegadas Liquid Retina XDR",
                "memoria_ram": "8GB",
                "armazenamento": "256GB",
                "conexao": "Wi-Fi 6E + 5G",
            },
            "ativo": True,
        },
        {
            "nome": "Notebook MacBook Pro 16 M3 Max",
            "marca": "Apple",
            "categorias": ["Eletrônicos", "Computadores", "Notebooks"],
            "preco": 24999.00,
            "estoque": 8,
            "imagens": [
                "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=600&q=80"
            ],
            "descricao": (
                "Desempenho extremo para profissionais criativos com o chip M3"
                " Max."
            ),
            "especificacoes": {
                "processador": "Apple M3 Max (16-core CPU, 40-core GPU)",
                "memoria_ram": "36GB Unified",
                "armazenamento": "1TB SSD",
                "tela": "16.2 polegadas Liquid Retina XDR",
                "portas": ["3x Thunderbolt 4", "HDMI", "SDXC Card"],
            },
            "ativo": True,
        },
        {
            "nome": "Teclado Mecânico Logitech G Pro X TKL",
            "marca": "Logitech",
            "categorias": ["Periféricos", "Gaming", "Acessórios"],
            "preco": 1199.90,
            "estoque": 30,
            "imagens": [
                "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=600&q=80"
            ],
            "descricao": (
                "Teclado mecânico sem fios desenvolvido para atletas de eSports"
                " com iluminação RGB."
            ),
            "especificacoes": {
                "switches": "GX Red Linear",
                "conectividade": "LIGHTSPEED Wireless / Bluetooth / USB-C",
                "autonomia": "Até 50 horas",
                "formato": "Tenkeyless (TKL)",
            },
            "ativo": True,
        },
        {
            "nome": "Rato Sem Fio Logitech MX Master 3S",
            "marca": "Logitech",
            "categorias": ["Periféricos", "Produtividade", "Acessórios"],
            "preco": 649.90,
            "estoque": 22,
            "imagens": [
                "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?auto=format&fit=crop&w=600&q=80"
            ],
            "descricao": (
                "Rato ergonómico de alta precisão com clique silencioso e roda"
                " MagSpeed."
            ),
            "especificacoes": {
                "sensor": "Darkfield 8000 DPI",
                "bateria": "Recarregável USB-C (até 70 dias)",
                "conexoes_simultaneas": "Até 3 dispositivos",
            },
            "ativo": True,
        },
        {
            "nome": "Fone de Ouvido Sony WH-1000XM5",
            "marca": "Sony",
            "categorias": ["Eletrônicos", "Áudio", "Acessórios"],
            "preco": 2299.90,
            "estoque": 25,
            "imagens": [
                "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600&q=80"
            ],
            "descricao": (
                "Fone Wireless com o melhor cancelamento de ruído do mercado e"
                " som de alta fidelidade."
            ),
            "especificacoes": {
                "tipo": "Over-Ear Wireless",
                "autonomia_bateria": "30 horas",
                "cancelamento_ruido": "Ativo (Noise Cancelling)",
                "conexao": "Bluetooth 5.2 / P2",
                "peso": "250g",
            },
            "ativo": True,
        },
        {
            "nome": "Apple Watch Ultra 2",
            "marca": "Apple",
            "categorias": ["Wearables", "Smartwatches", "Esporte"],
            "preco": 7499.00,
            "estoque": 12,
            "imagens": [
                "https://images.unsplash.com/photo-1510017803434-a899398421b3?auto=format&fit=crop&w=600&q=80"
            ],
            "descricao": (
                "O relógio esportivo mais robusto e capaz da Apple, caixa de"
                " titânio e GPS de dupla frequência."
            ),
            "especificacoes": {
                "caixa": "49mm Titânio",
                "resistencia_agua": "100 metros (Mergulho)",
                "brilho_ecra": "3000 nits",
                "bateria": "Até 36 horas de uso normal",
            },
            "ativo": True,
        },
        {
            "nome": "Console PlayStation 5 Slim",
            "marca": "Sony",
            "categorias": ["Gaming", "Consoles", "Eletrônicos"],
            "preco": 3799.00,
            "estoque": 18,
            "imagens": [
                "https://images.unsplash.com/photo-1606813907291-d86efa9b94db?auto=format&fit=crop&w=600&q=80"
            ],
            "descricao": (
                "Design Slim com 1TB de armazenamento SSD ultra-rápido e leitor"
                " de discos."
            ),
            "especificacoes": {
                "armazenamento": "1TB SSD",
                "resolucao_maxima": "4K 120Hz / 8K",
                "tecnologia_audio": "Tempest 3D AudioTech",
                "comandos_incluidos": 1,
            },
            "ativo": True,
        },
        {
            "nome": "Monitor Gamer Curvo 34'' Odyssey G8",
            "marca": "Samsung",
            "categorias": ["Eletrônicos", "Monitores", "Gaming"],
            "preco": 5499.00,
            "estoque": 10,
            "imagens": [
                "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=600&q=80"
            ],
            "descricao": (
                "Monitor OLED Ultrawide curvo de 175Hz para máxima imersão em"
                " jogos."
            ),
            "especificacoes": {
                "tamanho_tela": "34 polegadas Ultrawide",
                "painel": "OLED Curvo 1750R",
                "taxa_atualizacao": "175Hz",
                "tempo_resposta": "0.03ms",
                "resolucao": "3440 x 1440 (UWQHD)",
            },
            "ativo": True,
        },
        {
            "nome": "Cadeira de Escritório Ergonômica Herman Miller Aeron",
            "marca": "Herman Miller",
            "categorias": ["Móveis", "Escritório", "Ergonomia"],
            "preco": 12500.00,
            "estoque": 5,
            "imagens": [
                "https://images.unsplash.com/photo-1580481072645-022f9a6d83d0?auto=format&fit=crop&w=600&q=80"
            ],
            "descricao": (
                "O padrão de referência em suporte ergonômico e design para"
                " trabalho contínuo."
            ),
            "especificacoes": {
                "material": "Malha Pellicle respirável",
                "ajustes": [
                    "PosturaFit SL",
                    "Braços 4D",
                    "Reclinação síncrona",
                ],
                "suporte_peso": "Até 159 kg",
                "garantia": "12 anos",
            },
            "ativo": True,
        },
        {
            "nome": "Mesa Digitalizadora Wacom Cintiq Pro 16",
            "marca": "Wacom",
            "categorias": ["Periféricos", "Design", "Acessórios"],
            "preco": 8999.00,
            "estoque": 4,
            "imagens": [
                "https://images.unsplash.com/photo-1561999908-561a38f32371?auto=format&fit=crop&w=600&q=80"
            ],
            "descricao": (
                "Ecrã de alta precisão com resolução 4K e 8192 níveis de"
                " pressão de caneta."
            ),
            "especificacoes": {
                "resolucao_ecra": "4K Ultra HD (3840 x 2160)",
                "caneta": "Pro Pen 2 sem bateria",
                "gama_cores": "98% Adobe RGB",
            },
            "ativo": True,
        },
    ]
    collection.insert_many(produtos_exemplo)
    
st.set_page_config(page_title="Catálogo de Produtos | NoSQL E-Commerce", page_icon="", layout="wide")

st.title("Catálogo & Busca de Produtos")
st.caption("Ecrã 1 — Leitura e Filtragem Direta no MongoDB (Esquemas JSON Flexíveis)")

st.sidebar.header("Filtros de Busca")

categorias_unicas = sorted(collection.distinct("categorias"))
marcas_unicas = sorted(collection.distinct("marca"))

busca_texto = st.sidebar.text_input("Buscar por nome ou descrição:", placeholder="Ex: Samsung, OLED, M3...")
categoria_selecionada = st.sidebar.selectbox("Filtrar por Categoria:", ["Todas"] + categorias_unicas)
marca_selecionada = st.sidebar.selectbox("Filtrar por Marca:", ["Todas"] + marcas_unicas)
faixa_preco = st.sidebar.slider("Preço Máximo (R$):", min_value=0.0, max_value=30000.0, value=30000.0, step=500.0)

query = {"ativo": True}

if busca_texto.strip():
    query["$text"] = {"$search": busca_texto}

if categoria_selecionada != "Todas":
    query["categorias"] = categoria_selecionada

if marca_selecionada != "Todas":
    query["marca"] = marca_selecionada

if faixa_preco < 30000.0:
    query["preco"] = {"$lte": faixa_preco}

produtos_cursor = collection.find(query)
produtos = list(produtos_cursor)

st.write(f"**Produtos Encontrados:** `{len(produtos)}`")

cols = st.columns(3)

for idx, prod in enumerate(produtos):
    col = cols[idx % 3]
    with col:
        with st.container(border=True):
            img_url = prod.get("imagens", ["https://via.placeholder.com/300"])[0]
            st.image(img_url, use_container_width=True)
            st.subheader(prod.get("nome", "Sem Nome"))
            st.write(f"**Marca:** `{prod.get('marca')}`")
            st.write(f"**Preço:** R$ {prod.get('preco', 0.0):,.2f}")
            st.write(f"**Estoque:** {prod.get('estoque', 0)} unid.")

            cats = " ".join([f"`{c}`" for c in prod.get("categorias", [])])
            st.markdown(f"**Categorias:** {cats}")

            with st.expander("Especificações Técnicas (JSON Flexível)"):
                st.write(prod.get("descricao", ""))
                specs = prod.get("especificacoes", {})
                if specs:
                    for k, v in specs.items():
                        st.markdown(f"- **{k.replace('_', ' ').capitalize()}:** {v}")

            st.button("Adicionar ao Carrinho", key=str(prod["_id"]))