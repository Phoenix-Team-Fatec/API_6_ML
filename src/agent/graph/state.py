from typing import Annotated, Optional, TypedDict, Sequence
from operator import add 

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from src.agent.models.outputs import RespostaAgente

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

    # Guardrail de resposta do agente
    agent_blocked: bool
    agent_errors: list[str]

    # Tentativas de revisao do JSON
    review_attempts: int
    
    # Erros encontrados pelo review_node
    review_errors: list[str]
    
    #Output final em JSON
    validated_output: Optional[RespostaAgente]
    
    # Contangem de tokens usados
    tokens_input: Annotated[int, add] 
    tokens_output: Annotated[int, add] 
    
    

