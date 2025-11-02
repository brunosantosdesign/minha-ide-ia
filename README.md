# 💡 IDE de IA com Django, Transformers e MongoDB

Este é o projeto prático da disciplina de **Processamento de Linguagem Natural**, desenvolvido pela equipe:

- **Bruno Santos** — *Frontend e UI/UX*  
- **Luccas Lohan** — *Backend e Banco de Dados*  
- **Artur Revollo** — *Lógica de IA e Integração*  

---

## 🎯 Objetivo

Desenvolver uma aplicação web em **Django** que utiliza um modelo de IA (**Qwen/Qwen2-0.5B-Instruct**) da **Hugging Face** para fornecer uma interface de chat.  
O sistema armazena todo o histórico de interações em uma base de dados **MongoDB** (via `pymongo`) e permite **visualizar, filtrar por texto e data, paginar e exportar** esse histórico.

---

## ✨ Funcionalidades

- **💬 Chat em Tempo Real:** Interface de chat reativa para interação com o modelo de IA.  
- **🤖 Modelo Local:** Carregamento e inferência local do modelo `Qwen/Qwen2-0.5B-Instruct` via `transformers`.  
- **💾 Persistência de Dados:** Cada pergunta e resposta é salva em uma base de dados MongoDB.  
- **📜 Histórico de Conversas:** Página dedicada (`/chat/historico/`) que lista todas as conversas passadas com paginação.  
- **🔍 Filtros Avançados:** O histórico pode ser filtrado por termos de busca (no título ou conteúdo) e por intervalo de datas.  
- **📤 Exportação de Dados:** Exportação do histórico (filtrado ou completo) em formatos **JSON** e **CSV**.  
- **🧪 Testes Unitários:** O projeto inclui testes para as principais views e serviços.

---

## 🛠️ Tecnologias Utilizadas

- **Backend:** Django  
- **Frontend:** Django Templates (HTML, CSS, JavaScript Vanilla)  
- **Banco de Dados:** MongoDB (via PyMongo)  
- **PLN:** Hugging Face Transformers  
- **Modelo de IA:** `Qwen/Qwen2-0.5B-Instruct`  
- **Gestão de Ambiente:** python-dotenv  
- **Testes:** mongomock (simulação do MongoDB) e Django Test Client  

---

## 🚀 Instruções de Execução Local

Siga estes passos para rodar o projeto no seu computador.

### 🔧 Pré-requisitos

- **Python 3.10+**  
- **Git**  
- **Servidor MongoDB** (local ou em nuvem via MongoDB Atlas)

---

### 1️⃣ Clonar o Repositório

```bash
git clone https://github.com/brunosantosdesign/minha-ide-ia.git
cd minha-ide-ia
````

---

### 2️⃣ Criar e Ativar o Ambiente Virtual

```bash
# Criar o ambiente virtual
python -m venv venv

# Ativar o ambiente
# No Windows (Git Bash)
source venv/Scripts/activate

# No macOS/Linux
# source venv/bin/activate
```

---

### 3️⃣ Instalar as Dependências

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Configurar Variáveis de Ambiente

Crie um arquivo chamado **`.env`** na raiz do projeto (`minha-ide-ia/.env`).

Copie o conteúdo do arquivo **`.env.example`** para dentro do `.env`.

#### 🔑 Gerar uma Chave Secreta do Django

No terminal (com o venv ativo), execute:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copie a chave gerada e cole-a na variável `DJANGO_SECRET_KEY` no seu `.env`.

#### ⚙️ Configurar o MongoDB

Edite a variável `MONGO_URI` no `.env` com a sua string de conexão:

* **MongoDB Local (padrão):**

  ```
  MONGO_URI=mongodb://localhost:27017
  ```

* **MongoDB Atlas (nuvem):**

  ```
  MONGO_URI=mongodb+srv://<seu_usuario>:<sua_senha>@<seu_cluster>.mongodb.net/
  ```

---

### 5️⃣ Executar a Aplicação

Execute as migrações para criar as tabelas internas do Django:

```bash
python manage.py migrate
```

Inicie o servidor:

```bash
python manage.py runserver
```

Aguarde o carregamento do modelo de IA — o terminal mostrará:
**“Modelo carregado com sucesso...”**

Abra o navegador e acesse:
👉 [http://localhost:8000](http://localhost:8000)

---

### 6️⃣ Executar os Testes

Para verificar a integridade da aplicação, execute:

```bash
python manage.py test
```

---

📘 **Licença:** Projeto acadêmico — uso educacional.
👨‍💻 **Autor:** Bruno Santos de Araujo

```

