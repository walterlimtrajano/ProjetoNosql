# ProjetoNosql

## 📌 Escopo do Módulo (Pessoa 1)

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
```

---

## 🛠️ Tecnologias Utilizadas

- **[Python](https://www.python.org/)** — Linguagem principal
- **[Streamlit](https://streamlit.io/)** — Framework para interface web interativa
- **[PyMongo](https://pymongo.readthedocs.io/)** — Driver oficial de integração Python-MongoDB
- **[MongoDB](https://www.mongodb.com/)** — Banco de dados NoSQL orientado a documentos

---

## 👨‍💻 Autor

- **Walterlim Trajano** — *Pessoa 1: Modelação MongoDB & Ecrã do Catálogo*
- Repositório: [walterlimtrajano/ProjetoNosql](https://github.com/walterlimtrajano/ProjetoNosql)