from src.agent.config.settings import settings
from src.agent.rag.vector_store import VectorStore

import logging

logger = logging.getLogger(__name__)

class FederatedRetriever:
    def __init__(self, store: VectorStore):
        self.store = store
        
    def _search(self, table_name: str, query: str) -> list:
        ''' Busca em uma collection '''
        try:
            results = (
                self.store
                    .get_store(table_name)
                    .similarity_search(query, k=settings.retrievr_top_k)
            )
            
            logger.info(f"Retrieved {len(results)} results from table '{table_name}' for query: '{query}'")            
            
            return results
        except Exception as e:
            logger.error(f"Error occurred while searching table '{table_name}' for query: '{query}'")            
            return []
        
        
    def get_context(self, query: str) -> str:
        pdf_results = self._search("pdf_rules" + query)
        csv_results = self._search("csv_data" + query) 
        
        parts = []
        
        if pdf_results:
            parts.append("### Regras de negócio (PDFs)")
            logger.info(f"Adding {len(pdf_results)} PDF results to context for query: '{query}'")
            for doc in pdf_results:
                page = doc.metadata.get("page", "?")
                parts.append(f"- (Page {page}) {doc.page_content}")
        
        if csv_results:
            parts.append("\n### Dados estruturados (CSV)")
            logger.info(f"Adding {len(csv_results)} CSV results to context for query: '{query}'")
            for doc in csv_results:
                parts.append(f"- {doc.page_content}")

        return "\n".join(parts)