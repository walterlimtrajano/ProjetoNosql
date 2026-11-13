import math
import os
from datetime import date

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()


class Neo4jECommerceService:
    def __init__(self, uri=None, user=None, password=None, database=None):
        self.uri = uri or os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
        self.user = user or os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD")
        self.database = database or os.getenv("NEO4J_DATABASE", "neo4j")
        if not self.password:
            raise ValueError("Configure NEO4J_PASSWORD nas variáveis de ambiente.")
        self.driver = GraphDatabase.driver(
            self.uri, auth=(self.user, self.password)
        )

    def close(self):
        self.driver.close()

    def popular_dados_iniciais(self):
        query = """
        MERGE (c1:Cliente {nome: "Cliente 01"})
        MERGE (c2:Cliente {nome: "Cliente 02"})
        MERGE (c3:Cliente {nome: "Cliente 03"})
        MERGE (cat:Categoria {nome: "Eletrônicos"})
        MERGE (p1:Produto {nome: "Smartphone Galaxy S24 Ultra", preco: 6999.00})
        MERGE (p2:Produto {nome: "iPad Pro 12.9'' M2", preco: 9899.00})
        MERGE (p3:Produto {nome: "Notebook MacBook Pro 16 M3 Max", preco: 24999.00})
        
        MERGE (p1)-[:PERTENCE_A]->(cat)
        MERGE (p2)-[:PERTENCE_A]->(cat)
        MERGE (p3)-[:PERTENCE_A]->(cat)
        MERGE (c1)-[:COMPROU {data: "2026-11-08"}]->(p1)
        MERGE (c2)-[:COMPROU {data: "2026-11-08"}]->(p2)
        MERGE (c3)-[:COMPROU {data: "2026-11-08"}]->(p1)
        MERGE (c3)-[:COMPROU {data: "2026-11-08"}]->(p2)
        MERGE (c3)-[:COMPROU {data: "2026-11-08"}]->(p3)
        MERGE (c1)-[a1:AVALIOU]->(p1)
        SET a1.nota = 5, a1.data = "2026-11-08"
        MERGE (c2)-[a2:AVALIOU]->(p2)
        SET a2.nota = 4, a2.data = "2026-11-08"
        MERGE (c3)-[a3:AVALIOU]->(p1)
        SET a3.nota = 5, a3.data = "2026-11-08"
        MERGE (c3)-[a4:AVALIOU]->(p2)
        SET a4.nota = 4, a4.data = "2026-11-08"
        MERGE (c3)-[a5:AVALIOU]->(p3)
        SET a5.nota = 5, a5.data = "2026-11-08"
        """
        with self.driver.session(database=self.database) as session:
            session.run(query)
            print("Dados de grafos (nós e relacionamentos) inseridos com sucesso!")

    def registrar_compra(self, cliente_nome: str, produtos_nomes: list, data: str = None):
        """
        Registra no grafo Neo4j que o cliente finalizou a compra de determinados produtos.
        Cria/atualiza o nó (:Cliente) e o relacionamento [:COMPROU {data: ...}] para cada (:Produto).
        """
        if not cliente_nome or not produtos_nomes:
            return
        data_compra = data or date.today().isoformat()
        query = """
        MERGE (c:Cliente {nome: $cliente_nome})
        WITH c
        UNWIND $produtos_nomes AS prod_nome
        MERGE (p:Produto {nome: prod_nome})
        MERGE (c)-[r:COMPROU]->(p)
        SET r.data = $data_compra
        """
        with self.driver.session(database=self.database) as session:
            session.run(
                query,
                cliente_nome=cliente_nome,
                produtos_nomes=produtos_nomes,
                data_compra=data_compra,
            )

    def registrar_avaliacao(
        self, cliente_nome: str, produto_nome: str, nota: float, data: str | None = None
    ) -> None:
        if not cliente_nome or not cliente_nome.strip():
            raise ValueError("O nome do cliente é obrigatório.")
        if not produto_nome or not produto_nome.strip():
            raise ValueError("O nome do produto é obrigatório.")
        try:
            nota = float(nota)
        except (OverflowError, TypeError, ValueError) as erro:
            raise ValueError("A nota deve ser um número entre 1 e 5.") from erro
        if not math.isfinite(nota) or not 1 <= nota <= 5:
            raise ValueError("A nota deve estar entre 1 e 5.")

        data_avaliacao = data or date.today().isoformat()
        query = """
        MERGE (c:Cliente {nome: $cliente_nome})
        MERGE (p:Produto {nome: $produto_nome})
        MERGE (c)-[r:AVALIOU]->(p)
        SET r.nota = $nota, r.data = $data_avaliacao
        """
        with self.driver.session(database=self.database) as session:
            session.run(
                query,
                cliente_nome=cliente_nome.strip(),
                produto_nome=produto_nome.strip(),
                nota=nota,
                data_avaliacao=data_avaliacao,
            )

    def recomendar_produtos(self, produtos_base, limite=10):
        """Retorna itens comprados por clientes que também compraram os itens base."""
        if isinstance(produtos_base, str):
            produtos_base = [produtos_base]
        produtos_base = list(dict.fromkeys(produtos_base))
        if not produtos_base:
            return []

        query = """
        UNWIND $produtos_base AS produto_base
        MATCH (cliente_similar:Cliente)-[:COMPROU]->(base:Produto)
        WHERE base.nome = produto_base
        MATCH (cliente_similar)-[:COMPROU]->(recomendado:Produto)
        WHERE NOT recomendado.nome IN $produtos_base
        WITH recomendado,
             count(DISTINCT cliente_similar) AS clientes_similares,
             count(DISTINCT base) AS produtos_em_comum,
             collect(DISTINCT cliente_similar.nome)[..3] AS origens
        RETURN recomendado.nome AS produto,
               clientes_similares,
               produtos_em_comum,
               origens
        ORDER BY clientes_similares DESC, produtos_em_comum DESC, produto
        LIMIT $limite
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(
                query, produtos_base=produtos_base, limite=max(1, min(int(limite), 50))
            )
            return [dict(record) for record in result]

    def obter_recomendacoes(self, produto_nome):
        """Mantém compatibilidade com chamadas antigas que esperam nomes simples."""
        return [
            item["produto"]
            for item in self.recomendar_produtos(produto_nome)
        ]

if __name__ == "__main__":
    service = Neo4jECommerceService()
    try:
        service.popular_dados_iniciais()
    finally:
        service.close()