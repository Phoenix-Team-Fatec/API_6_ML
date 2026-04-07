from typing import Annotated, Optional, TypedDict, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Input original do usuário
    user_request: str
    
    # Contextos coletados pelas tools
    rules_context: str
    code_context: str
    
    # Saída final do code editor
    generated_code: Optional[str]
    raw_output: str
    
    # Controle de iterações
    iteration: int
    
    # Erros encontrados pelo review_node
    review_errors: list[str]
    
    
    

