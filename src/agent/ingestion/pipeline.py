from pathlib import Path
from src.agent.ingestion.load_data import load_pdf
from src.agent.rag.code_indexer import load_codebase
from src.agent.rag.vector_store import VectorStore
from src.agent.config.settings import settings

def run_ingestion(pdf_path: str, overwrite: bool = False) -> None:
    store = VectorStore()
    pdf_chunks = load_pdf(pdf_path)
    store.ingest_documents(pdf_chunks, "pdf_rules", overwrite)

def run_code_ingestion(overwrite: bool = False):
    store = VectorStore()
    chunks = load_codebase(settings.code_root_path)
    store.ingest_documents(
        chunks=chunks,
        table_name=settings.code_table_name,
        overwrite=overwrite,
    )