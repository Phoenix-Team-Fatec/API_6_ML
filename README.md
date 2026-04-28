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

  *Caso esteja utilizando o gerenciador de pacotes **uv**, execute este comando*

   ```bash
   uv sync      
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


# MLflow
 
A observabilidade do agente é feita com MLflow. O que está integrado:
 
- **Tracing** de cada execução (nós do grafo, tool calls e chamadas de LLM
  com tokens e latência) via `mlflow.langchain.autolog`.
- **Spans manuais** nos pontos cegos do autolog: etapas do `review_node`
  (parse JSON, schema, regras de negócio), guardrail do `agent_node` e
  heurísticas do `_limpar_json`.
- **Tags por execução** (`provider`, `response_type`, `final_status`,
  `iteration_count`, `review_attempts`) para filtrar traces na UI.
- **Versionamento de prompts** via Prompt Registry, com fallback local.
- **Avaliação de qualidade** via `mlflow.genai.evaluate` usando scorers
  determinísticos baseados no schema Pydantic e nas regras de negócio.
---
 
## Como usar
 
### 1. Subir o servidor MLflow
 
Em um terminal separado:
 
```bash
mlflow server --host 127.0.0.1 --port 5000
```
 
A UI fica disponível em `http://localhost:5000`.
 
### 2. Registrar os prompts (apenas na primeira vez ou ao alterar)
 
```bash
python -m scripts.register_prompts
```
 
Cria/atualiza as versões de `agent-system-prompt` e `code-editor-prompt`
no Prompt Registry e move o alias `production` para a versão recém-criada.
 
### 3. Executar o agente
 
A execução normal já gera traces automaticamente, desde que
`setup_observability()` seja chamado no bootstrap.
 
### 4. Avaliar a qualidade
 
```bash
python -m scripts.evaluate
```
 
Roda o dataset de avaliação (`src/agent/evaluation/dataset.py`) contra o
grafo e aplica todos os scorers. Os resultados aparecem como um run de
avaliação na aba **Experiments** da UI.
 
---
 
## Onde olhar na UI
 
- **Experiments → Traces** — uma linha por execução. Filtre por tags
  (ex.: `tags.final_status = 'review_failed'`).
- **Experiments → Runs** — runs de avaliação com a tabela de scorers.
- **Prompts** — versões registradas, diff entre versões e alias atual.


