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
    pandas_context: str
    
    # Saída final do code editor
    generetad_code: Optional[str]
    
    # Controle de iterações
    iteration: int
    
    
    

