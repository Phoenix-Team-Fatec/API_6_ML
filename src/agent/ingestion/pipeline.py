from pathlib import Path
from src.agent.ingestion.load_data import load_pdf
from src.agent.rag.vector_store import VectorStore

def run_ingestion(pdf_path: str, overwrite: bool = False) -> None:
    store = VectorStore()
    pdf_chunks = load_pdf(pdf_path)
    store.ingest_pdf(pdf_chunks, overwrite)