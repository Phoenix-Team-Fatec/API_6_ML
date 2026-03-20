import lancedb
from langchain_community.vectorstores import LanceDB
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document

from src.agent.config.settings import settings

import logging 

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.db = lancedb.connect(settings.vector_db_path)
        self.embeddings = OllamaEmbeddings(
            model=settings.embed_model,
            keep_alive=300,  # Keep model alive for 5 minutes (300 seconds)
        )
        
        
    def _to_documents(self, chunks: list[dict]) -> list[Document]:
        return [
            Document(
                page_content=chunk["text"],
                metadata={k: v for k, v in chunk.items() if k != "text"}
            )
            for chunk in chunks
        ]
        
    def get_store(self, table_name: str) -> LanceDB:
        """ Retorna a vector store de uma collection existente """
        return LanceDB(
            connection=self.db,
            embedding=self.embeddings,
            table_name=table_name
        )
              
    def ingest_pdf(self, chunks: list[dict], overwrite:bool =False) -> None:
        if not chunks:
            raise ValueError("No valid chunks to ingest.")
        
        if overwrite and 'pdf_rules' in self.db.table_names(): 
            self.db.drop_table('pdf_rules')
            logger.info("Existing 'pdf_rules' table dropped for overwrite.")
            
        documents = self._to_documents(chunks)
        
        if "pdf_rules" in self.db.table_names():
            store = self.get_store("pdf_rules")
            store.add_documents(documents)
            logger.info(f"Added {len(documents)} documents to existing 'pdf_rules' table.")
        else:
            LanceDB.from_documents(
                documents=documents,
                connection=self.db,
                embedding=self.embeddings,
                table_name="pdf_rules"
            )
            logger.info(f"Created 'pdf_rules' table and ingested {len(documents)} documents.")
    