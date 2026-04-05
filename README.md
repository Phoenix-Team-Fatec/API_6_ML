# 🤖 Agent Code Editor (Phoenis Team - FATEC)

Este projeto é um agente inteligente capaz de realizar manutenção automatizada em bases de código. Utilizando técnicas de **RAG (Retrieval-Augmented Generation)**, o agente consulta regras de negócio em PDFs e o contexto do código-fonte para propor alterações precisas via LLMs.

## 🚀 Tecnologias
* **FastAPI**: Interface de API de alta performance.
* **LangChain**: Orquestração da lógica de agentes e prompts.
* **Vector Store**: Armazenamento vetorial para busca semântica de código e regras.
* **Ollama/HuggingFace**: Integração com modelos de linguagem de última geração.

## 📂 Estrutura do Projeto
* `src/agent/ingestion`: Scripts para carregar e processar PDFs e arquivos de código.
* `src/agent/rag`: Motores de busca e recuperação de contexto.
* `src/agent/editing`: Lógica de geração de prompts e aplicação de patches de código.
* `main_api.py`: Ponto de entrada da aplicação FastAPI.

## 🛠️ Instalação e Configuração

1. **Clone o repositório:**
   ```bash
   git clone https://github.com
   cd API_6_ML
   ```

2. **Crie e ative seu ambiente virtual:**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure as variáveis de ambiente:**
Renomeie o arquivo .env_example para .env e preencha suas chaves e caminhos.

## 🚦 Como Rodar
Inicie o servidor Uvicorn:

    ```bash
    uvicorn main_api:app --reload
    ```

Acesse a documentação interativa (Swagger) em: [127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## 📌 Endpoints Principais

* `POST /change-request`: Solicita ao agente uma alteração no código baseado em uma regra.
* `POST /code`: Indexa uma pasta de código no banco vetorial.
* `POST /rules`: Indexa regras de negócio a partir de um PDF.
* `GET /health`: Verifica o status da API.

