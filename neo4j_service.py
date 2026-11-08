from neo4j import GraphDatabase
import os

class Neo4jECommerceService:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def popular_dados_iniciais(self):
        query = """
        MERGE (c1:Cliente {nome: "Cliente 01"})
        MERGE (cat:Categoria {nome: "Eletrônicos"})
        MERGE (p1:Produto {nome: "Smartphone Galaxy S24 Ultra", preco: 6999.00})
        MERGE (p2:Produto {nome: "iPad Pro 12.9 M2", preco: 9899.00})
        
        MERGE (c2:Cliente {nome: "Cliente 02"})
        
        // Criando as setas (relacionamentos)
        MERGE (p1)-[:PERTENCE_A]->(cat)
        MERGE (p2)-[:PERTENCE_A]->(cat)
        MERGE (c1)-[:COMPROU {data: "2026-11-08"}]->(p1)
        MERGE (c2)-[:COMPROU {data: "2026-11-08"}]->(p2)
        """
        with self.driver.session() as session:
            session.run(query)
            print("Dados de grafos (nós e relacionamentos) inseridos com sucesso!")

    def obter_recomendacoes(self, produto_nome):
        query = """
        MATCH (p1:Produto {nome: $produto_nome})<-[:COMPROU]-(c:Cliente)-[:COMPROU]->(p2:Produto)
        WHERE p1 <> p2
        RETURN p2.nome AS recomendacao, count(c) AS pontuacao
        """
        with self.driver.session() as session:
            result = session.run(query, produto_nome=produto_nome)
            return [record["recomendacao"] for record in result]

if __name__ == "__main__":
    URI = "neo4j://127.0.0.1:7687" 
    USER = "neo4j"
    PASSWORD = "admin123"

    service = Neo4jECommerceService(URI, USER, PASSWORD)
    try:
        service.popular_dados_iniciais()
    finally:
        service.close()