"""
Script de Benchmark e Comparativo de Desempenho NoSQL:
MongoDB (Document / Disco) vs Redis (In-Memory Cache)

Este script pode ser executado a qualquer momento para gerar métricas reais de latência
e demonstrar matematicamente o benefício da camada de Cache-Aside na Defesa Oral Técnica.
"""
import os
import sys
import time
import statistics
from pymongo import MongoClient
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import redis_service as rs

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "ecommerce_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "produtos")

def executar_benchmark(num_amostras: int = 50):
    print("=" * 70)
    print("🚀 INICIANDO BENCHMARK DE LATÊNCIA: MongoDB vs Redis Cache")
    print("=" * 70)

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    query_filtro = {"categorias": "Eletrônicos", "ativo": True}
    hash_busca = rs.gerar_hash_busca("", "Eletrônicos", "Todas", 30000.0)

    tempos_mongo = []
    print(f"\n1. Executando {num_amostras} consultas diretas ao MongoDB...")
    for _ in range(num_amostras):
        t0 = time.perf_counter()
        prods = list(collection.find(query_filtro))
        t1 = time.perf_counter()
        tempos_mongo.append((t1 - t0) * 1000)

    produtos_cache = []
    for p in prods:
        d = dict(p)
        d["_id"] = str(d["_id"])
        produtos_cache.append(d)
    rs.cache_busca_set(hash_busca, produtos_cache, ttl=300)

    tempos_redis = []
    print(f"2. Executando {num_amostras} consultas em memória ao Redis (Cache Hit)...")
    for _ in range(num_amostras):
        t0 = time.perf_counter()
        res, ttl = rs.cache_busca_get(hash_busca)
        t1 = time.perf_counter()
        tempos_redis.append((t1 - t0) * 1000)

    media_mongo = statistics.mean(tempos_mongo)
    p95_mongo = sorted(tempos_mongo)[int(0.95 * len(tempos_mongo))]
    min_mongo = min(tempos_mongo)

    media_redis = statistics.mean(tempos_redis)
    p95_redis = sorted(tempos_redis)[int(0.95 * len(tempos_redis))]
    min_redis = min(tempos_redis)

    speedup = media_mongo / media_redis if media_redis > 0 else 1.0

    print("\n" + "=" * 70)
    print("📊 RESULTADOS COMPARATIVOS DE LATÊNCIA:")
    print("=" * 70)
    print(f"{'Métrica':<25} | {'MongoDB (Direto)':<18} | {'Redis (Cache)':<18}")
    print("-" * 70)
    print(f"{'Latência Média':<25} | {media_mongo:>14.3f} ms | {media_redis:>14.3f} ms")
    print(f"{'Latência Mínima':<25} | {min_mongo:>14.3f} ms | {min_redis:>14.3f} ms")
    print(f"{'Latência P95 (95%)':<25} | {p95_mongo:>14.3f} ms | {p95_redis:>14.3f} ms")
    print("-" * 70)
    print(f"\n⚡ Ganho de Desempenho (Speedup): O Redis foi ~{speedup:.1f}x MAIS RÁPIDO que o MongoDB!")
    print(f"📉 Redução de Latência: {((media_mongo - media_redis) / media_mongo) * 100:.1f}%")
    print("=" * 70)
    print("💡 Argumento para a Defesa Técnica:")
    print("   'O uso de Cache Invalidation (TTL) no Redis elimina o I/O de disco do MongoDB")
    print("    para as buscas mais frequentes, atendendo milhares de requisições por segundo")
    print("    em sub-milissegundos diretamente da memória RAM.'\n")

if __name__ == "__main__":
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    executar_benchmark(num_amostras=50)
