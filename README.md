# ProjetoNosql

## 📌 Escopo do Módulo (Walterlim Trajano)

- **Modelagem NoSQL (MongoDB):** Estruturação flexível em JSON para persistência do catálogo de produtos, suportando subdocumentos/objetos aninhados (`especificacoes`) e listas (`categorias`, `imagens`).
- **Otimização de Consultas:** Criação de índices de texto (`TEXT index`) nos campos `nome`, `descricao` e `marca` para busca por palavra-chave de alta performance.
- **Interface Gráfica (Streamlit):** Construção da interface visual interativa conectada em tempo real à leitura dos dados no MongoDB, com suporte a filtros dinâmicos (categorias, marcas, faixa de preço e busca textual).

---

## 📁 Estrutura do Projeto

```text
ProjetoNosql/
├── app_catalogo_mongodb.py   # Aplicação Streamlit e script de seed do MongoDB
├── requirements.txt          # Dependências do projeto Python
├── .env                      # Variáveis de ambiente (não commitado)
├── .env.example              # Exemplo de configuração das variáveis de ambiente
├── .gitignore                # Arquivos ignorados pelo Git
└── README.md                 # Documentação do projeto
```

---

## ⚙️ Pré-requisitos

Certifique-se de ter instalado em sua máquina:
- **Python 3.10+**
- **MongoDB Server** (rodando localmente na porta `27017` ou via Docker / MongoDB Atlas)
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
  . env\Scripts\Activate.ps1
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

### 5. Executar a Aplicação Streamlit
```bash
streamlit run app_catalogo_mongodb.py
```
A aplicação abrirá automaticamente no seu navegador padrão no endereço: `http://localhost:8501`.

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

---

## 🛠️ Tecnologias Utilizadas

- **[Python](https://www.python.org/)** — Linguagem principal
- **[Streamlit](https://streamlit.io/)** — Framework para interface web interativa
- **[PyMongo](https://pymongo.readthedocs.io/)** — Driver oficial de integração Python-MongoDB
- **[MongoDB](https://www.mongodb.com/)** — Banco de dados NoSQL orientado a documentos

---

## 👨‍💻 Autor

- **Walterlim Trajano** — *Modelação MongoDB & Ecrã do Catálogo*
- Repositório: [walterlimtrajano/ProjetoNosql](https://github.com/walterlimtrajano/ProjetoNosql)