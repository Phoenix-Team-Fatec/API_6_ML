from src.agent.config.settings import settings
from src.agent.rag.vector_store import VectorStore

import logging

logger = logging.getLogger(__name__)

class Retriever:
    def __init__(self, store: VectorStore):
        self.store = store
        
    def get_context(self, query: str) -> str:
        results = (
            self.store
                .get_store("pdf_rules")
                .similarity_search(query, k=settings.retrievr_top_k)
        )
        
        if not results: 
            logger.warning("No relevant context found for the query.")
            return ""
        
        lines = ['Context retrieved from PDF:']
        for doc in results:
            page = doc.metadata.get("page", "unknown")
            lines.append(f"Page {page}: {doc.page_content}")
            
        return "\n".join(lines)
        