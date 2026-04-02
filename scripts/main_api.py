from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from src.agent.service.change_request_service import ChangeRequestService
from src.agent.config import settings
from src.agent.rag.vector_store import VectorStore
from src.agent.rag.code_indexer import load_codebase
from src.agent.ingestion.load_data import load_pdf

app = FastAPI(
    title="🤖 Agent Code Editor API",
    description="""
    API para manutenção automatizada de código utilizando RAG e LLMs.
    
    *   **Ingestão**: Indexa códigos e regras de negócio em bancos vetoriais.
    *   **Agente**: Processa pedidos de mudança e sugere patches de código.
    """,
    version="1.0.0",
    contact={
        "name": "Phoenix Team - FATEC",
    }
)

service = ChangeRequestService()

class ChangeRequestPayload(BaseModel):
    request: str = Field(
        ..., 
        description="Descrição da alteração desejada no código",
        examples=["Somente este mês, a % de comissão de vendas deve ser 5%."]
    )
    apply: bool = Field(
        False, 
        description="Se True, aplica a mudança no arquivo. Se False (default), apenas simula (dry-run)."
    )

class IngestCodePayload(BaseModel):
    root: Optional[str] = Field(None, description="Caminho da pasta raiz do código")
    overwrite: bool = Field(False, description="Limpar banco vetorial antes de indexar")

    class Config:
        json_schema_extra = {"example": {"root": "C:/Projetos/MeuApp", "overwrite": False}}

class IngestRulesPayload(BaseModel):
    pdf_path: str = Field(..., alias="pdf", description="Caminho do arquivo PDF com as regras")
    overwrite: bool = False

@app.get("/health", tags=["Monitoramento"], summary="Verifica status da API")
async def health_check():
    return {"status": "ok"}

@app.post("/change-request", tags=["Agente"], summary="Solicitar alteração de código")
async def change_request(change_request: ChangeRequestPayload):
    try:
        result = service.process_change_request(
            user_request=change_request.request,
            dry_run=not change_request.apply,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/ingestion/code", tags=["Ingestão de Dados"], summary="Indexar Base de Código")
def ingest_code(payload: IngestCodePayload):
    root = payload.root or settings.code_root_path
    store = VectorStore()
    chunks = load_codebase(root)
    store.ingest_documents(
       chunks=chunks,
       table_name=settings.code_table_name,
       overwrite=payload.overwrite,
   )
    return {"message": f"Código ingerido com sucesso a partir de {root}"}

@app.post("/ingestion/rules", tags=["Ingestão de Dados"], summary="Indexar Regras de Negócio (PDF)")
def ingest_rules(payload: IngestRulesPayload):
    store = VectorStore()
    chunks = load_pdf(payload.pdf)
    store.ingest_documents(
       chunks=chunks,
       table_name=settings.rules_table_name,
       overwrite=payload.overwrite,
   )
    return {"message": f"Regras ingeridas com sucesso a partir de {payload.pdf}"}


@app.post("/generate-code", tags=["Agente"], summary="Gerar código a partir de descrição")
def generate_code(query: str):
    try:
        response_json = service.generate_code(query)
        return response_json
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))