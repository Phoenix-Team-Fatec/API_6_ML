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
        
    def _ingest(self, chunks: list[dict], table_name: str, overwrite: bool) -> None:
        if overwrite and table_name in self.db.table_names(): # Verifica dados duplic ados
            self.db.drop_table(table_name)
            
        documents = self._to_documents(chunks)
        
        # Log detalhado para debug
        logger.info(f"Starting ingestion of {len(documents)} documents into '{table_name}'")
        for i, doc in enumerate(documents[:3]):  # Log apenas os primeiros 3
            logger.debug(f"Doc {i}: {doc.page_content[:100]}... | Metadata: {doc.metadata}")
        
        try:
            if table_name in self.db.table_names():
                # Collection já existe, apenas adiciona os novos documentos
                store = self.get_store(table_name)
                store.add_documents(documents)
            else:
                # Collection não existe, cria e adiciona os documentos
                LanceDB.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    connection=self.db,
                    table_name=table_name
                )
        except Exception as e:
            logger.error(f"Error during ingestion to '{table_name}': {str(e)[:200]}")
            # Log o primeiro documento que está causando problema
            if documents:
                logger.error(f"First document: {documents[0].page_content[:200]}")
            raise
            
        logger.info(f"Successfully ingested {len(chunks)} chunks into table '{table_name}' (overwrite={overwrite})")
        
        
    
    def ingest_csv(self, chunks: list[dict], table_name: str,overwrite:bool =False) -> None:
        self._ingest(chunks, table_name, overwrite)
        logger.info(f"Ingested {len(chunks)} CSV chunks into '{table_name}' table (overwrite={overwrite})")
    
    
    def ingest_pdf(self, chunks: list[dict], overwrite:bool =False) -> None:
        self._ingest(chunks, "pdf_rules", overwrite)
        logger.info(f"Ingested {len(chunks)} PDF chunks into 'pdf_rules' table (overwrite={overwrite})")
        
    