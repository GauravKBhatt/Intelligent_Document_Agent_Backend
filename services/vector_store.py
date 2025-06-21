# services/vector_store.py - Vector Store Service with Qdrant integration example


import numpy as np
from services.embedding_service import EmbeddingService
from config.settings import settings

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

class VectorStoreService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        if settings.VECTOR_DB == "qdrant" and QDRANT_AVAILABLE:
            self.qdrant = QdrantClient(host="localhost", port=6333)
        else:
            self.qdrant = None
            # In-memory fallback
            self.collections = {}

    def create_collection(self, collection_id):
        if self.qdrant:
            if collection_id not in [c.name for c in self.qdrant.get_collections().collections]:
                self.qdrant.recreate_collection(
                    collection_name=collection_id,
                    vectors_config={"size": 384, "distance": "Cosine"}
                )
        else:
            if collection_id not in self.collections:
                self.collections[collection_id] = []

    def add_vector(self, collection_id, vector, payload):
        self.create_collection(collection_id)
        if self.qdrant:
            point = PointStruct(
                id=payload.get("chunk_index", 0),
                vector=vector,
                payload=payload
            )
            self.qdrant.upsert(collection_name=collection_id, points=[point])
            return f"{collection_id}_vector_{payload.get('chunk_index', 0)}"
        else:
            self.collections[collection_id].append({
                "embedding": np.array(vector),
                **payload
            })
            print(f"[DEBUG] Added chunk to {collection_id}: {payload.get('content', '')[:100]}")
            return f"{collection_id}_vector_{len(self.collections[collection_id])}"

    def delete_collection(self, collection_id):
        if self.qdrant:
            self.qdrant.delete_collection(collection_id)
        else:
            if collection_id in self.collections:
                del self.collections[collection_id]

    def search(self, collection_id, query, top_k=3):
        query_emb = self.embedding_service.generate_embeddings([query])[0]
        if self.qdrant:
            search_result = self.qdrant.search(
                collection_name=collection_id,
                query_vector=query_emb,
                limit=top_k
            )
            return [point.payload for point in search_result]
        else:
            if collection_id not in self.collections or not self.collections[collection_id]:
                print(f"[DEBUG] No chunks found in collection {collection_id}.")
                return []
            print(f"[DEBUG] Searching in {collection_id}, {len(self.collections[collection_id])} chunks available.")
            def cosine_sim(a, b):
                a = np.array(a)
                b = np.array(b)
                return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)
            scored = []
            for chunk in self.collections[collection_id]:
                sim = cosine_sim(query_emb, chunk["embedding"])
                scored.append((sim, chunk))
            scored.sort(reverse=True, key=lambda x: x[0])
            print(f"[DEBUG] Top chunk similarity: {scored[0][0] if scored else 'N/A'}")
            return [chunk for _, chunk in scored[:top_k]]