import mlflow
from langgraph.graph import StateGraph

from src.agent.graph.state import State
from src.agent.graph.nodes import (
    build_agent_node,
    build_code_editor_node,
    build_review_node,
    tools_node,
)
from src.agent.graph.edges import route_agent, route_review
from src.agent.observability.tags import apply_trace_tags


def build_graph(provider: str = 'groq'):
    graph = StateGraph(State)

    graph.add_node('agent_node', build_agent_node(provider=provider))
    graph.add_node('code_editor_node', build_code_editor_node())
    graph.add_node('review_node', build_review_node())
    graph.add_node('tools', tools_node)

    graph.set_entry_point('agent_node')

    graph.add_conditional_edges(
        'agent_node',
        route_agent,
        {
            'tools': 'tools',
            'code_editor_node': 'code_editor_node',
            'agent_node': 'agent_node',
            'end': '__end__',
        }
    )
    graph.add_edge('tools', 'agent_node')
    graph.add_edge('code_editor_node', 'review_node')
    graph.add_conditional_edges(
        "review_node", route_review,
        {
            "retry": "code_editor_node",
            "end": '__end__',
        }
    )

    compiled = graph.compile()
    return _wrap_with_observability(compiled, provider)


def _build_token_usage(final_state: dict) -> dict:
    """Consolida tokens acumulados no state em um dict pronto para a API."""
    input_tokens = int(final_state.get("tokens_input", 0) or 0)
    output_tokens = int(final_state.get("tokens_output", 0) or 0)
    return {
        "input": input_tokens,
        "output": output_tokens,
        "total": input_tokens + output_tokens,
    }


def _build_api_response(final_state: dict) -> dict | None:
    """
    Monta o payload pronto para a API no formato:
        {
            "rule_json": {...},      # validated_output serializado
            "token_usage": {...}     # input, output, total
        }
    Retorna None se não houver validated_output (o endpoint trata como erro).
    """
    validated = final_state.get("validated_output")
    if validated is None:
        return None
    return {
        "rule_json": validated.model_dump(mode="json"),
        "token_usage": _build_token_usage(final_state),
    }


def _wrap_with_observability(compiled_graph, provider: str):
    """
    Envolve o grafo compilado em uma função decorada com @mlflow.trace.

    No final da execução:
    - Aplica tags no trace raiz (provider, response_type, final_status etc.).
    - Anexa `api_response` ao resultado, pronto para devolver na API.
    O state interno (validated_output, tokens_input, etc.) permanece intacto
    e pode ser inspecionado por quem chama, se precisar.
    """
    @mlflow.trace(name="agent_run")
    def run(inputs: dict) -> dict:
        final_state = compiled_graph.invoke(inputs)
        apply_trace_tags(final_state, provider=provider)
        final_state["api_response"] = _build_api_response(final_state)
        return final_state

    run.compiled = compiled_graph
    return run