import argparse 
from src.agent.ingestion.pipeline import run_ingestion

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingestão de dados para o agente de regras de negócio."
    )
        
    parser.add_argument("--pdf", 
                        default=None, 
                        help="Caminho para o arquivo .pdf")
    
    parser.add_argument("--overwrite", 
                        action="store_true",
                        help="Recria a collection do zero antes de indexar")
    
    args = parser.parse_args()

    if not args.pdf:
        parser.error("Informe ao menos um arquivo -pdf")

    run_ingestion(
        pdf_path=args.pdf,
        overwrite=args.overwrite
    )