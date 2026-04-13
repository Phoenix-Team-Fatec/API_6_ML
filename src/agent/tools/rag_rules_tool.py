from langchain_core.tools import tool
from src.agent.rag.code_retriever import CodeRetriever
from src.agent.rag.vector_store import VectorStore

_code_retriever = CodeRetriever(store=VectorStore())  

@tool
def buscar_trecho_codigo(consulta: str) -> str:
    """
    Busca trechos de código existentes relevantes para a alteração solicitada.
    Use para entender como o código atual implementa uma regra antes de editá-lo.
    """
    return _code_retriever.get_context(consulta)