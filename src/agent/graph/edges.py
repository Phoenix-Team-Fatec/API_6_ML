from langchain_core.messages import AIMessage
from src.agent.graph.state import State

MAX_ITERATIONS = 10

def route_agent(state: State) -> str:
    """
    Decide o próximo nó após o agente responder:
    - 'tools'       → agente quer chamar uma tool
    - 'code_editor' → agente coletou contexto suficiente
    - 'end'         → segurança contra loop infinito
    """
    last_message: AIMessage = state["messages"][-1]
    
    # Limite de iterações para evitar loops infinitos
    if state.get('iteration', 0) >= MAX_ITERATIONS:
        return 'code_editor_node'
    
    # Agente sinaliza que está pronto para editar o código
    if "PRONTO_PARA_EDITAR" in (last_message.content or ""):
        return 'code_editor_node'
    
    # Agente chama as tools quando precisa de mais contexto
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return 'tools'
    
    # Se não há tool calls, assumimos que o agente está pronto para editar
    return 'code_editor_node'


MAX_RETRIES = 2

def route_review(state: State) -> str:
    errors = state.get("review_errors", [])
    
    if not errors:
        return "end"
    
    if state.get("iteration", 0) < MAX_RETRIES:  # ✅ "iteration" sem 's'
        return "retry"
    
    return "end"