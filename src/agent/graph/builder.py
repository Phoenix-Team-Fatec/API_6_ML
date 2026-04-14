from langgraph.graph import StateGraph, END

from src.agent.graph.state import State
from src.agent.graph.nodes import (build_agent_node, 
                                   build_code_editor_node, 
                                   build_review_node,
                                   tools_node
                                   )

from src.agent.graph.edges import route_agent, route_review

def build_graph():
    graph = StateGraph(State)
    
    # Nós 
    graph.add_node('agent_node', build_agent_node(provider='groq'))
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
    
    return graph.compile()
    
if __name__ == "__main__":
    app = build_graph()
    print(app.get_graph().draw_mermaid())