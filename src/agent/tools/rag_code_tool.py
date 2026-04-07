from langchain_core.tools import tool
from src.agent.rag.retriever import Retriever
from src.agent.rag.vector_store import VectorStore

_retriever = Retriever(store=VectorStore())

@tool
def buscar_regras_negocio(consulta:str) -> str:
    """
    Busca regras de negócio relevantes no vector store.
    Use quando precisar entender como uma regra de comissionamento funciona
    antes de propor alterações no código.
    """
    return _retriever.get_context(consulta)