"""
Script de avaliação da qualidade das respostas do agente.

Executa:
    python -m scripts.evaluate

Passos:
1. Carrega o dataset de avaliação (src/agent/evaluation/dataset.py).
2. Constrói o grafo uma única vez (com o provider escolhido).
3. Usa mlflow.genai.evaluate() para rodar cada caso do dataset e aplicar
   todos os scorers determinísticos.
4. Resultados ficam visíveis na UI do MLflow, dentro do experimento atual,
   na aba 'Runs' (como um run de avaliação).

Para comparar providers, rode duas vezes alterando o parâmetro `provider`
e compare os runs lado a lado na UI.
"""
from __future__ import annotations

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
import mlflow

from src.agent.evaluation.eval_dataset import EVAL_DATASET
from src.agent.evaluation.scorers import ALL_SCORERS
from src.agent.graph.builder import build_graph
from src.agent.observability.setup import setup_observability


PROVIDER = "groq"


def build_predict_fn(graph):
    """
    Cria a função que o MLflow chama para cada item do dataset.

    A assinatura precisa bater com as CHAVES do dicionário `inputs`
    no dataset. Como usamos `{"user_request": ...}`, a função recebe
    `user_request` como kwarg.
    """
    def predict_fn(user_request: str) -> dict:
        initial_state = {
            "messages": [HumanMessage(content=user_request)],
            "user_request": user_request,
            "rules_context": "",
            "code_context": "",
            "raw_output": "",
            "validated_output": None,
            "review_errors": [],
            "iteration": 0,
        }
        return graph(initial_state)

    return predict_fn


def main() -> None:
    load_dotenv()
    setup_observability()

    graph = build_graph(provider=PROVIDER)
    predict_fn = build_predict_fn(graph)

    results = mlflow.genai.evaluate(
        data=EVAL_DATASET,
        predict_fn=predict_fn,
        scorers=ALL_SCORERS,
    )

    print("Avaliação concluída. Veja os resultados na UI do MLflow.")
    print(f"Provider avaliado: {PROVIDER}")
    print(f"Total de casos:    {len(EVAL_DATASET)}")
    return results


if __name__ == "__main__":
    main()