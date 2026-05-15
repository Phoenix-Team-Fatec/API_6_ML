import traceback
from contextlib import asynccontextmanager
from typing import Dict, List
 
from fastapi import FastAPI, HTTPException
from langchain_core.messages import HumanMessage
 
from src.agent.graph.builder import build_graph
from src.agent.observability.setup   import setup_observability
from src.agent.rules.base_algorithm import (
    ComissionamentoBase,
    Funcionario,
    Venda,
    calcular_comissionamento,
    carregar_intercorrencias_do_mes,
)
 
 
# -----------------------------------------------------------------------------
# Estado da aplicação: grafo compilado UMA vez no startup, reusado em todas
# as requisições. Evita re-compilar a cada chamada (carrega prompts do MLflow,
# instancia LLMs e tools).
# -----------------------------------------------------------------------------
state: dict = {}
 
 
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_observability()
    state["graph"] = build_graph(provider="groq")
    yield
    # Shutdown (nada a limpar por enquanto)
    state.clear()
 
 
app = FastAPI(
    title="🤖 Agent Code Editor API",
    description="""
    API para manutenção automatizada de código utilizando RAG e LLMs.
    *   **Ingestão**: Indexa códigos e regras de negócio em bancos vetoriais.
    *   **Agente**: Processa pedidos de mudança e sugere patches de código.
    """,
    version="1.0.0",
    contact={"name": "Phoenix Team - FATEC"},
    lifespan=lifespan,
)
 
 
@app.get("/health", tags=["Monitoramento"], summary="Verifica status da API")
async def health_check():
    return {"status": "ok"}
 
 
@app.post("/agent", tags=["Agente"], summary="Interação usuário com agente")
def ask(user_input: str):
    """
    Recebe uma solicitação em linguagem natural e devolve o objeto de regra
    gerado pelo agente junto com o consumo de tokens.
 
    Formato da resposta:
        {
            "rule_json":   {...},          # objeto OverridesMensais ou IntercorrenciaSazonal
            "token_usage": {"input": N, "output": N, "total": N}
        }
    """
    try:
        graph = state["graph"]
        inputs = {
            "messages": [HumanMessage(content=user_input)],
            "user_request": user_input,
            "iteration": 0,
            "review_attempts": 0,
            "agent_errors": [],
            "review_errors": [],
            "agent_blocked": False,
        }
        result = graph(inputs)
 
        api_response = result.get("api_response")
        if api_response is None:
            # Grafo terminou sem produzir um validated_output.
            raise HTTPException(
                status_code=422,
                detail={
                    "errors": result.get("review_errors", ["Sem output validado"]),
                },
            )
        return api_response
 
    except HTTPException:
        # Re-propaga HTTPException sem mascarar (ex.: 422 acima vira 500).
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    
@app.post("/commission-algorithm", tags=["Comissão"], summary="Calculo de comissão")
def calculate_commission(regras_mongo: List[Dict], funcionarios: List[Funcionario], vendas: List[Venda], tabela_comissao: List[ComissionamentoBase], ano: int, mes: int):
    try:
        # Calcula Intercorrencias
        intercorrencias = carregar_intercorrencias_do_mes(
            regras_mongo=regras_mongo,
            ano=ano,
            mes=mes,
        )

        # Calcula resultado da comissão
        resultados = calcular_comissionamento(
            funcionarios=funcionarios,
            vendas=vendas,
            tabela_comissao=tabela_comissao,
            intercorrencias=intercorrencias,
            ano=ano,
            mes=mes,
        )

        return resultados
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=404, detail=str(e))