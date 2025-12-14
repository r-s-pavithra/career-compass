from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # API Keys - Both optional, but at least one must be provided
    groq_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # Model settings
    embedding_model: str = "all-MiniLM-L6-v2"
    llm_model: str = "llama-3.1-8b-instant"
    max_tokens: int = 1500
    temperature: float = 0.3
    
    # Vector store settings
    vector_dimension: int = 384
    upload_dir: str = "uploads"
    vector_store_path: str = "data/vector_store"
    
    class Config:
        env_file = ".env"
        extra = "ignore"
    
    def model_post_init(self, __context):
        """Validate that at least one API key is provided"""
        if not self.groq_api_key and not self.openai_api_key:
            raise ValueError(
                "Either GROQ_API_KEY or OPENAI_API_KEY must be set in .env file"
            )

@lru_cache()
def get_settings():
    return Settings()
