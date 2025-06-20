# services/embedding_service.py - Embedding Service Stub
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    """Service for generating text embeddings using various models"""
    
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def generate_embeddings(self, chunks, model=None):
        # For now, use the default model
        return self.model.encode(chunks)