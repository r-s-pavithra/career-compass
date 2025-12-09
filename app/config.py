from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    openai_api_key: str
    embedding_model: str = "all-MiniLM-L6-v2"
    llm_model: str = "llama-3.1-70b-versatile"
    max_tokens: int = 1500
    temperature: float = 0.3
    vector_dimension: int = 384  # Changed from 1536
    upload_dir: str = "uploads"
    vector_store_path: str = "data/vector_store"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
