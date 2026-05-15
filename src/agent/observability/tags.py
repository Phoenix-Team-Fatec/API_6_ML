"""
Tags aplicadas ao trace raiz, permitindo filtrar execuções na UI do MLflow.
 
Exemplos de consultas habilitadas por estas tags:
- "todas execuções com provider=groq que falharam no review"
- "todas execuções cujo final_status=max_iterations"
- "tempo médio por tipo de resposta (override vs intercorrencia)"
"""

from typing import Any

import mlflow

def _final_status(state: dict) -> str:
    """Resume o desfecho da execução em uma string."""
    if state.get("agent_blocked"):
        return "agent_blocked"
    if state.get("validated_output") is not None:
        return "success"
    if state.get("review_errors"):
        return "review_failed"
    if state.get("iteration", 0) >= 6:
        return "max_iterations"
    return "unknown"

def _response_type(state: dict) -> str:
    """Retorna o tipo da resposta validada, ou 'unknown' se não houver."""
    validated = state.get("validated_output")
    if validated is None:
        return "unknown"
    return getattr(validated, "tipo", "unknown")

def apply_trace_tags(state: dict, provider: str) -> None:
    """
    Aplica tags no trace atualmente ativo a partir do state final do grafo.
 
    Deve ser chamada DEPOIS do app.invoke(), ainda dentro do span raiz
    (ou seja, dentro do wrapper decorado com @mlflow.trace).
    """
    
    tokens_input = int(state.get("tokens_input", 0) or 0)
    tokens_output = int(state.get("tokens_output", 0) or 0)

    tags: dict[str, Any] = {
        "provider": provider,
        "response_type": _response_type(state),
        "final_status": _final_status(state),
        "iteration_count": str(state.get("iteration", 0)),
        "review_attempts": str(state.get("review_attempts", 0)),
        "tokens_input": str(tokens_input),
        "tokens_output": str(tokens_output),
        "tokens_total": str(tokens_input + tokens_output),
    }
    mlflow.update_current_trace(tags=tags)
