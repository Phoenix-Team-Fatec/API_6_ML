from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    
    # LLM
    # hugging_face_model: str
    
    # Ollama
    embed_model: str = "nomic-embed-text:latest"
    embed_dim: int = 768
    
    # LanceDB
    vector_db_path: str = 'vector_db' 
    
    # Retriever
    retrievr_top_k: int = 4
    
settings = Settings()