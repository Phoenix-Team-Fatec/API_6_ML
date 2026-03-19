from pathlib import Path
from src.agent.ingestion.load_data import load_csv, load_pdf
from src.agent.rag.vector_store import VectorStore

def run_ingestion(csv_paths: list[str], pdf_path: str, overwrite: bool = False) -> None:
    store = VectorStore()
        
    if csv_paths:
        for csv_path in csv_paths:
            table_name = Path(csv_path).stem.lower()
            chunks = load_csv(csv_path)
            store.ingest_csv(chunks, table_name, overwrite)
    
    if pdf_path:
        pdf_chunks = load_pdf(pdf_path)
        store.ingest_pdf(pdf_chunks, overwrite)