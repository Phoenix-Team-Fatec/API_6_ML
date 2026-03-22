from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    
    # LLM
    llm_model: str = "qwen3-coder:latest"
    llm_temperature: float = 0.0
    
    # Ollama
    embed_model: str = "nomic-embed-text:latest"
    embed_dim: int = 768
    
    # LanceDB
    vector_db_path: str = 'vector_db' 
    
    # Retriever
    retriever_top_k: int = 4
    code_retriever_top_k: int = 4

    # Tables
    rules_table_name: str = "pdf_rules"
    code_table_name: str = "codebase"

    # Codebase root
    code_root_path: str = "src"

    class Config:
        env_file = ".env"
    
settings = Settings()