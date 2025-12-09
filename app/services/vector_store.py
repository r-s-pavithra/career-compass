import faiss
import numpy as np
import pickle
import os
from typing import List, Tuple
from app.config import get_settings

class VectorStore:
    def __init__(self):
        self.settings = get_settings()
        self.dimension = self.settings.vector_dimension
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []
        self.metadata = []
        
        os.makedirs(self.settings.vector_store_path, exist_ok=True)
        self.index_path = f"{self.settings.vector_store_path}/faiss.index"
        self.metadata_path = f"{self.settings.vector_store_path}/metadata.pkl"
    
    def add_documents(self, embeddings: np.ndarray, documents: List[str], metadata: List[dict]):
        """Add documents with embeddings to FAISS index"""
        self.index.add(embeddings)
        self.documents.extend(documents)
        self.metadata.extend(metadata)
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[str, dict, float]]:
        """Search for similar documents"""
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        distances, indices = self.index.search(query_embedding, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents):
                results.append((
                    self.documents[idx],
                    self.metadata[idx],
                    float(distances[0][i])
                ))
        return results
    
    def save(self):
        """Save index and metadata to disk"""
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, 'wb') as f:
            pickle.dump({
                'documents': self.documents,
                'metadata': self.metadata
            }, f)
    
    def load(self):
        """Load index and metadata from disk"""
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, 'rb') as f:
                data = pickle.load(f)
                self.documents = data['documents']
                self.metadata = data['metadata']
            return True
        return False
