import argparse

from src.agent.config.settings import settings
from src.agent.ingestion.load_data import load_pdf
from src.agent.rag.vector_store import VectorStore


def main():
    parser = argparse.ArgumentParser(description="Ingestão de PDF de regras")
    parser.add_argument("--pdf", required=True, help="Caminho para o PDF")
    parser.add_argument("--overwrite", action="store_true", help="Sobrescreve a tabela")
    args = parser.parse_args()

    store = VectorStore()
    chunks = load_pdf(args.pdf)

    store.ingest_documents(
        chunks=chunks,
        table_name=settings.rules_table_name,
        overwrite=args.overwrite,
    )

    print(f"Ingeridos {len(chunks)} chunks de regras em '{settings.rules_table_name}'.")


if __name__ == "__main__":
    main()