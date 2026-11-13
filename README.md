# ProjetoNosql

## 📌 Escopo do Módulo (Walterlim Trajano)

- **Modelagem NoSQL (MongoDB):** Estruturação flexível em JSON para persistência do catálogo de produtos, suportando subdocumentos/objetos aninhados (`especificacoes`) e listas (`categorias`, `imagens`).
- **Otimização de Consultas:** Criação de índices de texto (`TEXT index`) nos campos `nome`, `descricao` e `marca` para busca por palavra-chave em alta performance.
- **Gestão de Sessão e Carrinho (Redis):** Armazenamento de sessões de usuário, itens do carrinho e cache com TTL para reduzir latência e melhorar o comportamento da aplicação.
- **Recomendações em Grafo (Neo4j):** Conexões entre clientes e produtos para recomendar itens com base em compras semelhantes e comportamento de usuários.
- **Interface Gráfica (Streamlit):** Construção de uma interface interativa conectada em tempo real aos dados em MongoDB, Redis e Neo4j, com filtros dinâmicos, busca textual e navegação por páginas.

---

## 📁 Estrutura do Projeto

```text
ProjetoNosql/
├── app_catalogo_mongodb.py   # Aplicação principal em Streamlit com Cache-Aside e Ranking
├── neo4j_service.py          # Serviço Neo4j, consultas Cypher e registro de compras
├── redis_service.py          # Sessões, carrinho, Cache com TTL, Invalidation e ZSET
├── interface.py              # Autenticação compartilhada na barra lateral
├── benchmark_cache.py        # Benchmark de latência MongoDB vs Redis Cache
├── tests/
│   └── test_integracao_global.py # Suíte de testes automatizados Polyglot (pytest)
├── pages/
│   ├── 2_Carrinho.py        # Ecrã 2: carrinho ativo e Checkout Polyglot
│   └── 3_Recomendacoes.py   # Ecrã 3: recomendações Neo4j
├── docs/                    # Documentação complementar do projeto
├── docker-compose.yml        # Serviços locais de Redis, MongoDB e Neo4j
├── requirements.txt          # Dependências do projeto Python
├── .env                     # Variáveis de ambiente locais (não commitado)
├── .env.example             # Exemplo de configuração das variáveis de ambiente
├── .gitignore               # Arquivos ignorados pelo Git
├── README.md                # Documentação do projeto
├── inicializaçao redis.py   # Script auxiliar para inicialização do Redis
├── .venv                    # Ambiente virtual local (opcional)
└── __pycache__/             # Arquivos temporários do Python
```

---

## ⚙️ Pré-requisitos

Certifique-se de ter instalado em sua máquina:
- **Python 3.10+**
- **Docker Desktop** ou **Docker Compose**
- **MongoDB** (localmente ou em container)
- **Redis** (localmente ou em container)
- **Neo4j** (localmente ou em container)
- **Git**
- **MongoDB Compass** (opcional, para inspeção visual dos documentos e coleções)

---

## 🚀 Instalação e Execução

### 1. Clonar o Repositório
```bash
git clone https://github.com/walterlimtrajano/ProjetoNosql.git
cd ProjetoNosql
```

### 2. Criar e Ativar o Ambiente Virtual (`venv`)

- **No Windows (Git Bash):**
  ```bash
  python -m venv venv
  source venv/Scripts/activate
  ```

- **No Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```

- **No Linux/macOS:**
  ```bash
  python -m venv venv
  source venv/bin/activate
  ```

### 3. Instalar as Dependências
```bash
pip install -r requirements.txt
```

### 4. Configurar as Variáveis de Ambiente
Copie o arquivo `.env.example` para `.env`:
```bash
cp .env.example .env
```

No Windows PowerShell:
```powershell
Copy-Item .env.example .env
```

O arquivo `.env` deve conter, no mínimo, as seguintes variáveis:

```env
MONGO_URI=mongodb://localhost:27017/
DB_NAME=ecommerce_db
COLLECTION_NAME=produtos

NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=sua_senha
NEO4J_DATABASE=neo4j

STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
```

> Não compartilhe nem versionie o arquivo `.env`.

### 5. Subir os serviços com Docker (opcional, mas recomendado)
No diretório do projeto:

```bash
docker compose up -d
```

Isso inicia:
- **Redis** na porta `6379`
- **MongoDB** na porta `27017`
- **Neo4j** nas portas `7474` e `7687`

### 6. Inicializar o grafo e executar a aplicação
Com o Neo4j disponível e as variáveis configuradas, crie os dados de exemplo do grafo:

```bash
python neo4j_service.py
```

Em seguida, inicie o Streamlit:

```bash
streamlit run app_catalogo_mongodb.py
```

A aplicação abrirá automaticamente no navegador em:

```text
http://localhost:8501
```

Use o menu de páginas do Streamlit e abra **3 Recomendações**. A tela usa os produtos no carrinho Redis como contexto inicial; também permite selecionar outros produtos do catálogo.

---

## 🍃 Modelagem de Dados no MongoDB

A coleção `produtos` na base de dados `ecommerce_db` armazena documentos JSON com esquemas flexíveis:

```json
{
  "_id": { "$oid": "65c1a2b3c4d5e6f7a8b9c0d1" },
  "nome": "Smartphone Galaxy S24 Ultra",
  "marca": "Samsung",
  "categorias": ["Eletrônicos", "Smartphones", "Tecnologia"],
  "preco": 6999.00,
  "estoque": 15,
  "imagens": [
    "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf"
  ],
  "descricao": "Smartphone topo de linha com IA integrada e câmera de 200MP.",
  "especificacoes": {
    "tela": "6.8 polegadas Dynamic AMOLED 2X",
    "memoria_ram": "12GB",
    "armazenamento": "512GB",
    "processador": "Snapdragon 8 Gen 3",
    "bateria": "5000 mAh"
  },
  "ativo": true
}
{
  "_id": {
    "$oid": "6aee78c158d3af6683cfd9b9"
  },
  "nome": "iPad Pro 12.9'' M2",
  "marca": "Apple",
  "categorias": [
    "Eletrônicos",
    "Tablets",
    "Tecnologia"
  ],
  "preco": 9899,
  "estoque": 7,
  "imagens": [
    "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&w=600&q=80"
  ],
  "descricao": "Performance absurda com o chip M2, ecrã Liquid Retina XDR e suporte à Apple Pencil 2.",
  "especificacoes": {
    "processador": "Apple M2",
    "tela": "12.9 polegadas Liquid Retina XDR",
    "memoria_ram": "8GB",
    "armazenamento": "256GB"
  },
  "ativo": true
}
{
  "_id": {
    "$oid": "6aee78c158d3af6683cfd9ba"
  },
  "nome": "Notebook MacBook Pro 16 M3 Max",
  "marca": "Apple",
  "categorias": [
    "Eletrônicos",
    "Computadores",
    "Notebooks"
  ],
  "preco": 24999,
  "estoque": 8,
  "imagens": [
    "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=600&q=80"
  ],
  "descricao": "Desempenho extremo para profissionais criativos com o chip M3 Max.",
  "especificacoes": {
    "processador": "Apple M3 Max",
    "memoria_ram": "36GB Unified",
    "armazenamento": "1TB SSD",
    "tela": "16.2 polegadas Liquid Retina XDR"
  },
  "ativo": true
}
{
  "_id": {
    "$oid": "6aee78c158d3af6683cfd9bb"
  },
  "nome": "Teclado Mecânico Logitech G Pro X TKL",
  "marca": "Logitech",
  "categorias": [
    "Periféricos",
    "Gaming",
    "Acessórios"
  ],
  "preco": 1199.9,
  "estoque": 30,
  "imagens": [
    "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=600&q=80"
  ],
  "descricao": "Teclado mecânico sem fios desenvolvido para atletas de eSports com iluminação RGB.",
  "especificacoes": {
    "switches": "GX Red Linear",
    "conectividade": "LIGHTSPEED Wireless / Bluetooth",
    "autonomia": "Até 50 horas"
  },
  "ativo": true
}
{
  "_id": {
    "$oid": "6aee78c158d3af6683cfd9bc"
  },
  "nome": "Rato Sem Fio Logitech MX Master 3S",
  "marca": "Logitech",
  "categorias": [
    "Periféricos",
    "Produtividade",
    "Acessórios"
  ],
  "preco": 649.9,
  "estoque": 22,
  "imagens": [
    "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?auto=format&fit=crop&w=600&q=80"
  ],
  "descricao": "Rato ergonómico de alta precisão com clique silencioso e roda MagSpeed.",
  "especificacoes": {
    "sensor": "Darkfield 8000 DPI",
    "bateria": "Recarregável USB-C",
    "conexoes": "Até 3 dispositivos"
  },
  "ativo": true
}
{
  "_id": {
    "$oid": "6aee78c158d3af6683cfd9bd"
  },
  "nome": "Fone de Ouvido Sony WH-1000XM5",
  "marca": "Sony",
  "categorias": [
    "Eletrônicos",
    "Áudio",
    "Acessórios"
  ],
  "preco": 2299.9,
  "estoque": 25,
  "imagens": [
    "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600&q=80"
  ],
  "descricao": "Fone Wireless com o melhor cancelamento de ruído do mercado e som de alta fidelidade.",
  "especificacoes": {
    "tipo": "Over-Ear Wireless",
    "autonomia_bateria": "30 horas",
    "cancelamento_ruido": "Ativo"
  },
  "ativo": true
}
{
  "_id": {
    "$oid": "6aee78c158d3af6683cfd9be"
  },
  "nome": "Apple Watch Ultra 2",
  "marca": "Apple",
  "categorias": [
    "Wearables",
    "Smartwatches",
    "Esporte"
  ],
  "preco": 7499,
  "estoque": 12,
  "imagens": [
    "https://images.unsplash.com/photo-1510017803434-a899398421b3?auto=format&fit=crop&w=600&q=80"
  ],
  "descricao": "O relógio esportivo mais robusto e capaz da Apple, caixa de titânio e GPS de dupla frequência.",
  "especificacoes": {
    "caixa": "49mm Titânio",
    "resistencia_agua": "100 metros",
    "brilho": "3000 nits"
  },
  "ativo": true
}
{
  "_id": {
    "$oid": "6aee78c158d3af6683cfd9bf"
  },
  "nome": "Console PlayStation 5 Slim",
  "marca": "Sony",
  "categorias": [
    "Gaming",
    "Consoles",
    "Eletrônicos"
  ],
  "preco": 3799,
  "estoque": 18,
  "imagens": [
    "https://images.unsplash.com/photo-1606813907291-d86efa9b94db?auto=format&fit=crop&w=600&q=80"
  ],
  "descricao": "Design Slim com 1TB de armazenamento SSD ultra-rápido e leitor de discos.",
  "especificacoes": {
    "armazenamento": "1TB SSD",
    "resolucao": "4K 120Hz"
  },
  "ativo": true
}
{
  "_id": {
    "$oid": "6aee78c158d3af6683cfd9c0"
  },
  "nome": "Monitor Gamer Curvo 34'' Odyssey G8",
  "marca": "Samsung",
  "categorias": [
    "Eletrônicos",
    "Monitores",
    "Gaming"
  ],
  "preco": 5499,
  "estoque": 10,
  "imagens": [
    "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=600&q=80"
  ],
  "descricao": "Monitor OLED Ultrawide curvo de 175Hz para máxima imersão em jogos.",
  "especificacoes": {
    "tamanho_tela": "34 polegadas Ultrawide",
    "painel": "OLED Curvo",
    "taxa_atualizacao": "175Hz"
  },
  "ativo": true
}
{
  "_id": {
    "$oid": "6aee78c158d3af6683cfd9c1"
  },
  "nome": "Cadeira de Escritório Ergonômica Herman Miller Aeron",
  "marca": "Herman Miller",
  "categorias": [
    "Móveis",
    "Escritório",
    "Ergonomia"
  ],
  "preco": 12500,
  "estoque": 5,
  "imagens": [
    "https://images.unsplash.com/photo-1505797149-43b0069ec26b?auto=format&fit=crop&w=600&q=80"
  ],
  "descricao": "O padrão de referência em suporte ergonômico e design para trabalho contínuo.",
  "especificacoes": {
    "material": "Malha Pellicle respirável",
    "suporte_peso": "Até 159 kg",
    "garantia": "12 anos"
  },
  "ativo": true
}
```

A aplicação cria automaticamente um índice de texto para melhorar a busca por palavra-chave:

```python
collection.create_index([("nome", TEXT), ("descricao", TEXT), ("marca", TEXT)])
```

Esse índice é usado para pesquisas rápidas em campos relevantes do catálogo.

---

## 🧠 Modelagem de Dados no Redis & Camada de Cache

O Redis é usado para dados que exigem altíssima performance em memória, baixa latência e expiração automática:

- **Sessões de usuário**: token de autenticação com TTL deslizante (`SESSION_TTL = 1800s`).
- **Carrinho de compras dinâmico**: armazenamento em tempo real dos itens de cada usuário (`CART_TTL = 86400s`).
- **Cache-Aside para Catálogo**: consultas de busca filtrada salvas com hash determinístico e TTL configurável (`CACHE_TTL = 300s`).
- **Ranking de Mais Acessados**: contagem e ordenação em tempo real com Sorted Sets (ZSET).
- **Cache Invalidation Ativa**: expurgo automático de consultas e detalhes de produto quando ocorre checkout ou alteração de estoque.

Modelagem das chaves no Redis:

```text
user:{email}                HASH   nome, salt, senha_hash            (persistente)
session:{token}             HASH   user_id, nome                     (TTL deslizante = 30 min)
cart:{user_id}              HASH   produto_id -> quantidade          (TTL = 24h)
cache:busca:{hash_md5}      STRING JSON lista de produtos filtrados  (TTL = 5 min)
cache:produto:{produto_id}  STRING JSON detalhes do produto          (TTL = 5 min)
produtos:mais_acessados     ZSET   {produto_id: score_acessos}       (ZINCRBY / ZREVRANGE)
```

### ⚡ Estratégias de Cache Invalidation (Invalidação de Cache)
1. **Invalidação Temporal (TTL)**: Cada chave de busca e produto possui expiração automática, evitando consumo desnecessário de memória RAM.
2. **Invalidação Ativa Orientada a Eventos**: Durante o **Checkout** ou alteração de estoque, as chaves `cache:busca:*` e a chave específica do produto `cache:produto:{id}` são invalidadas imediatamente para garantir consistência e evitar exibição de estoque obsoleto (*stale data*).
3. **Invalidação Manual de Demonstração**: Disponível no painel interativo do Streamlit para testes ao vivo diante da banca examinadora.

---

## 🕸️ Modelagem de Dados no Neo4j

O Neo4j armazena relacionamentos entre clientes e produtos para gerar recomendações com base em compras semelhantes.

Estrutura de exemplo:

```text
(:Cliente)-[:COMPROU]->(:Produto)
(:Produto)-[:PERTENCE_A]->(:Categoria)
```

O algoritmo trabalha com a ideia de: "clientes que compraram os mesmos produtos também costumam comprar outros itens do mesmo catálogo".

---

## 🖥️ Funcionalidades da Interface

A aplicação principal em Streamlit oferece:

- filtro por categoria
- filtro por marca
- faixa de preço
- busca textual por nome, marca ou descrição
- visualização de imagens e detalhes do produto
- botão para adicionar ao carrinho
- acesso às páginas de carrinho e recomendações

---

## 🔍 Fluxo de Uso

### Catálogo MongoDB
- A página principal carrega produtos do MongoDB
- Aplica filtros e busca textual
- Exibe informações do produto e imagens

### Carrinho e sessão em Redis
- O login e a sessão são gerenciados no Redis
- O carrinho do usuário é persistido com TTL
- A aplicação usa cache para evitar processamento redundante

### Recomendações com Neo4j
- A página de recomendações considera os produtos selecionados e os itens do carrinho
- Compara clientes com histórico semelhante
- Retorna produtos mais relevantes, ordenados por afinidade

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.10+**
- **MongoDB** — banco de dados NoSQL orientado a documentos
- **Redis** — armazenamento em memória para sessão, carrinho e cache
- **Neo4j** — banco de dados orientado a grafos para recomendações
- **Streamlit** — construção da interface web interativa
- **PyMongo** — driver oficial para integração com MongoDB
- **redis-py** — cliente Python para Redis
- **Neo4j Python Driver** — conexão e consultas ao Neo4j
- **python-dotenv** — carregamento de variáveis de ambiente
- **Docker / Docker Compose** — orquestração de serviços locais

---

## 🛠️ Comandos Úteis

```bash
# Iniciar os serviços de infraestrutura (MongoDB, Redis e Neo4j)
docker compose up -d

# Popular dados iniciais no Neo4j
python neo4j_service.py

# Inicializar usuários de teste no Redis
python "inicializaçao redis.py"

# Executar a suíte de Testes Globais Polyglot (pytest)
python -m pytest -v tests/test_integracao_global.py

# Executar o Benchmark de Latência (MongoDB vs Redis Cache)
python benchmark_cache.py

# Rodar a aplicação Streamlit
streamlit run app_catalogo_mongodb.py
```

---

## 👥 Equipe / Autores

- **Walterlim Trajano** — *Modelação MongoDB & Ecrã do Catálogo*
- Repositório: [walterlimtrajano/ProjetoNosql](https://github.com/walterlimtrajano/ProjetoNosql)

- **Lucas Holanda** — *Modelação Neo4j, Scripts Cypher & Documentação em Grafo*
- Repositório: [Holandaz1/ProjetoNosql](https://github.com/walterlimtrajano/ProjetoNosql)

- **Daniel Leite** — *Motor de Recomendação, Consultas Cypher & Ecrã de Recomendações em Streamlit*
- Repositório: [TR014777/ProjetoNosql](https://github.com/walterlimtrajano/ProjetoNosql)

- **Lucas Henrique** — *Integração de Cache (Redis), Cache Invalidation (TTL), Ranking de Mais Acessados (ZSET) & Testes Globais Polyglot*
- Repositório: [lucashzz1/ProjetoNosql](https://github.com/walterlimtrajano/ProjetoNosql)
