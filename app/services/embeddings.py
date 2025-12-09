from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
from app.config import get_settings

class EmbeddingService:
    def __init__(self):
        self.settings = get_settings()
        # Load local embedding model (runs on your computer, no API calls)
        self.model = SentenceTransformer(self.settings.embedding_model)
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        embedding = self.model.encode(text)
        return embedding.tolist()
    
    def generate_embeddings_batch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts"""
        embeddings = self.model.encode(texts)
        return embeddings.astype('float32')
