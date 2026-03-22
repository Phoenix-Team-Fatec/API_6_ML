import argparse

from src.agent.config.settings import settings
from src.agent.rag.code_indexer import load_codebase
from src.agent.rag.vector_store import VectorStore


def main():
    parser = argparse.ArgumentParser(description="Ingestão do código-fonte")
    parser.add_argument("--root", default=settings.code_root_path, help="Raiz do código")
    parser.add_argument("--overwrite", action="store_true", help="Sobrescreve a tabela")
    args = parser.parse_args()

    store = VectorStore()
    chunks = load_codebase(args.root)

    store.ingest_documents(
        chunks=chunks,
        table_name=settings.code_table_name,
        overwrite=args.overwrite,
    )

    print(f"Ingeridos {len(chunks)} chunks de código em '{settings.code_table_name}'.")


if __name__ == "__main__":
    main()