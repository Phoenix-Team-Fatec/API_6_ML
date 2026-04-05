from src.agent.config.settings import settings
from src.agent.rag.vector_store import VectorStore

class CodeRetriever:
    def __init__(self, store: VectorStore):
        self.store = store
    
    def get_context(self, query: str) -> str:
        if settings.code_table_name not in self.store.db.table_names():
            return ""

        results = (
            self.store
            .get_store(settings.code_table_name)
            .similarity_search(query, k=settings.code_retriever_top_k)
        )

        if not results:
            return ""
        
        lines = ["Relevant code context:"]
        for doc in results:
            file_path = doc.metadata.get("file_path", "unknown")
            chunk_id = doc.metadata.get("chunk_id", "unknown")
            lines.append(f"FILE={file_path} CHUNK={chunk_id}\n{doc.page_content}")

        return "\n\n".join(lines)