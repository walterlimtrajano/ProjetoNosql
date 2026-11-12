import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()


class Neo4jECommerceService:
    def __init__(self, uri=None, user=None, password=None, database=None):
        # Lendo os dados de conexão do arquivo .env
        self.uri = uri or os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
        self.user = user or os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD")
        self.database = database or os.getenv("NEO4J_DATABASE", "neo4j")
        if not self.password:
            raise ValueError("Configure NEO4J_PASSWORD nas variáveis de ambiente.")
        # Criando a conexão com o Neo4j
        self.driver = GraphDatabase.driver(
            self.uri, auth=(self.user, self.password)
        )

    def close(self):
        self.driver.close()

    def popular_dados_iniciais(self):
        query = """
        // Criando clientes, produtos e categoria de exemplo
        MERGE (c1:Cliente {nome: "Cliente 01"})
        MERGE (c2:Cliente {nome: "Cliente 02"})
        MERGE (c3:Cliente {nome: "Cliente 03"})
        MERGE (cat:Categoria {nome: "Eletrônicos"})
        MERGE (p1:Produto {nome: "Smartphone Galaxy S24 Ultra", preco: 6999.00})
        MERGE (p2:Produto {nome: "iPad Pro 12.9'' M2", preco: 9899.00})
        MERGE (p3:Produto {nome: "Notebook MacBook Pro 16 M3 Max", preco: 24999.00})
        
        // Criando as setas (relacionamentos)
        MERGE (p1)-[:PERTENCE_A]->(cat)
        MERGE (p2)-[:PERTENCE_A]->(cat)
        MERGE (p3)-[:PERTENCE_A]->(cat)
        MERGE (c1)-[:COMPROU {data: "2026-11-08"}]->(p1)
        MERGE (c2)-[:COMPROU {data: "2026-11-08"}]->(p2)
        MERGE (c3)-[:COMPROU {data: "2026-11-08"}]->(p1)
        MERGE (c3)-[:COMPROU {data: "2026-11-08"}]->(p2)
        MERGE (c3)-[:COMPROU {data: "2026-11-08"}]->(p3)
        """
        with self.driver.session(database=self.database) as session:
            session.run(query)
            print("Dados de grafos (nós e relacionamentos) inseridos com sucesso!")

    def registrar_compra(self, cliente_nome: str, produtos_nomes: list, data: str = None):
        """
        Registra no grafo Neo4j que o cliente finalizou a compra de determinados produtos.
        Cria/atualiza o nó (:Cliente) e o relacionamento [:COMPROU {data: ...}] para cada (:Produto).
        """
        import datetime
        if not cliente_nome or not produtos_nomes:
            return
        data_compra = data or datetime.date.today().isoformat()
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

    def recomendar_produtos(self, produtos_base, limite=10):
        """Retorna itens comprados por clientes que também compraram os itens base."""
        # Aceitando um produto ou uma lista de produtos
        if isinstance(produtos_base, str):
            produtos_base = [produtos_base]
        # Removendo produtos repetidos
        produtos_base = list(dict.fromkeys(produtos_base))
        if not produtos_base:
            return []

        query = """
        // Procurando clientes que compraram os produtos escolhidos
        UNWIND $produtos_base AS produto_base
        MATCH (cliente_similar:Cliente)-[:COMPROU]->(base:Produto)
        WHERE base.nome = produto_base
        // Procurando outros produtos comprados pelos mesmos clientes
        MATCH (cliente_similar)-[:COMPROU]->(recomendado:Produto)
        WHERE NOT recomendado.nome IN $produtos_base
        // Contando clientes parecidos e produtos em comum
        WITH recomendado,
             count(DISTINCT cliente_similar) AS clientes_similares,
             count(DISTINCT base) AS produtos_em_comum,
             collect(DISTINCT cliente_similar.nome)[..3] AS origens
        // Mostrando primeiro os produtos com mais clientes em comum
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
        # Devolvendo apenas os nomes das recomendações
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