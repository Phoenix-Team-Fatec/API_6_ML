from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    
    # LLMs
    hugging_face_model: str = 'Qwen/Qwen3-Coder-30B-A3B-Instruct:featherless-ai'
    huggingfacehub_api_token: str = os.getenv("HUGGINGFACEHUB_API_TOKEN") 
    
    google_model: str = "gemini-3-flash-preview"
    google_api_key: str = os.getenv("GOOGLE_API_KEY")
    
    groq_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    groq_api_key: str = os.getenv("GROQ_API_KEY")
    
    llm_temperature: float = 0.1


    
    # Ollama
    llm_model: str = "qwen3-coder:latest"
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