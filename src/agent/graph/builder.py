from langgraph.graph import StateGraph

from src.agent.graph.state import State
from src.agent.graph.nodes import (build_agent_node, 
                                   build_code_editor_node, 
                                   build_review_node,
                                   tools_node
                                   )

from src.agent.graph.edges import route_agent, route_review
from src.agent.observability.tags import apply_trace_tags

import mlflow

def build_graph(provider: str = 'groq'):
    graph = StateGraph(State)
    
    # Nós 
    graph.add_node('agent_node', build_agent_node(provider=provider))
    graph.add_node('code_editor_node', build_code_editor_node())
    graph.add_node('review_node', build_review_node())
    graph.add_node('tools', tools_node)
    
    
    # Ponto de início
    graph.set_entry_point('agent_node')
    
    # Edges
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
    
    # Tools sempre retorna para o agente
    graph.add_edge('tools', 'agent_node')
    
    # Revisao do codigo gerado
    graph.add_edge('code_editor_node', 'review_node')
    
    graph.add_conditional_edges(
        "review_node", route_review,
        {
            "retry": "code_editor_node",   # erros recuperáveis → tenta de novo
            "end": '__end__',         # validado → encerra
        }
    )
    
    compiled = graph.compile()
    
    return _wrap_with_observability(compiled, provider)
    
    
def _wrap_with_observability(compiled_graph, provider: str):
    """
    Envolve o grafo compilado em uma função decorada com @mlflow.trace.
 
    Isso cria um ÚNICO trace raiz para cada execução, englobando:
    - os spans do autolog (um por nó),
    - os spans manuais (review, guardrail, limpar_json).
 
    Depois que a execução termina, aplicamos as tags no trace raiz
    a partir do state final (provider, response_type, final_status etc.).
    """
    @mlflow.trace(name="agent_run")
    def run(inputs: dict) -> dict:
        final_state = compiled_graph.invoke(inputs)
        apply_trace_tags(final_state, provider=provider)
        return final_state
 
    # Expõe atributos úteis do grafo compilado (ex.: get_graph para o mermaid).
    run.compiled = compiled_graph
    return run


    

if __name__ == "__main__":
    app = build_graph()
    print(app.get_graph().draw_mermaid())