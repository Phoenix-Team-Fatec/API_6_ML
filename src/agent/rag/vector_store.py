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
              
    def ingest_documents(self, chunks: list[dict], table_name: str, overwrite:bool =False) -> None:
        if not chunks:
            raise ValueError("No valid chunks to ingest.")
        
        if overwrite and table_name in self.db.table_names(): 
            self.db.drop_table(table_name)
            logger.info(f"Existing {table_name} table dropped for overwrite.")
            
        documents = self._to_documents(chunks)
        
        if table_name in self.db.table_names():
            store = self.get_store(table_name)
            store.add_documents(documents)
            logger.info(f"Added {len(documents)} documents to existing {table_name} table.")
        else:
            LanceDB.from_documents(
                documents=documents,
                connection=self.db,
                embedding=self.embeddings,
                table_name=table_name
            )
            logger.info(f"Created {table_name} table and ingested {len(documents)} documents.")
    