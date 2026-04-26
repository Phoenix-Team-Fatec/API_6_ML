"""
Scorers para avaliação da qualidade das respostas do agente.
 
Todos os scorers são DETERMINÍSTICOS e reaproveitam lógica já existente
no projeto (schema Pydantic + _validar_regras_negocio). Nenhum scorer aqui
usa LLM-as-judge, mantendo a avaliação rápida, reprodutível e sem custo extra.
 
Assinatura esperada pelo MLflow (keyword-only):
    @scorer
    def my_scorer(*, inputs, outputs, expectations, trace) -> int | float | bool:
        ...
 
Todos os kwargs são opcionais. Aqui usamos apenas outputs e expectations.
"""

from __future__ import annotations

from typing import Any

from mlflow.genai.scorers import scorer

from src.agent.graph.nodes import _validar_regras_negocio
from src.agent.models.outputs import RespostaAgente

def _get_validated(outputs: Any) -> RespostaAgente | None:
    """
    Extrai o RespostaAgente validado do output do grafo.
 
    O predict_fn retorna o state final do grafo, onde `validated_output`
    contém o RespostaAgente (ou None se o review falhou).
    """
    if not isinstance(outputs, dict):
        return None
    return outputs.get("validated_output")
 
 
@scorer
def schema_valid(*, outputs: Any) -> int:
    """1 se o output passou na validação do schema Pydantic; 0 caso contrário."""
    return 1 if _get_validated(outputs) is not None else 0
 
 
@scorer
def business_rules_valid(*, outputs: Any) -> int:
    """1 se o output passa em TODAS as validações de negócio; 0 caso contrário.
 
    Reusa `_validar_regras_negocio` do review_node — mesmo critério do runtime.
    """
    validated = _get_validated(outputs)
    if validated is None:
        return 0
    return 1 if not _validar_regras_negocio(validated) else 0
 
 
@scorer
def type_matches_expected(*, outputs: Any, expectations: dict[str, Any]) -> int:
    """1 se o tipo gerado bate com `expectations['expected_type']`."""
    validated = _get_validated(outputs)
    if validated is None:
        return 0
    return 1 if validated.tipo == expectations.get("expected_type") else 0
 
 
@scorer
def within_iteration_budget(*, outputs: Any, expectations: dict[str, Any]) -> int:
    """1 se o agente terminou sem estourar o orçamento de iterações."""
    if not isinstance(outputs, dict):
        return 0
    budget = expectations.get("max_iterations", 6)
    return 1 if outputs.get("iteration", 0) <= budget else 0
 
 
@scorer
def no_review_retry(*, outputs: Any) -> int:
    """1 se o code_editor acertou de primeira (sem retry no review)."""
    if not isinstance(outputs, dict):
        return 0
    return 1 if outputs.get("review_attempts", 0) == 0 else 0
 
 
ALL_SCORERS = [
    schema_valid,
    business_rules_valid,
    type_matches_expected,
    within_iteration_budget,
    no_review_retry,
]
