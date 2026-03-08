"""Vector store for embeddings-based RAG"""
import json
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
from uuid import UUID
import pickle

from uepi_api.config import get_settings
from uepi_api.storage_file import BASE_PATH

settings = get_settings()


class VectorStore:
    """Vector store for embeddings"""
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = Path(base_path or settings.vector_store_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.embeddings_cache = {}  # In-memory cache
    
    def _get_embedding_file(self, entity_type: str, entity_id: str) -> Path:
        """Get path for embedding file"""
        entity_dir = self.base_path / entity_type
        entity_dir.mkdir(parents=True, exist_ok=True)
        return entity_dir / f"{entity_id}.json"
    
    def store_embedding(
        self,
        entity_type: str,
        entity_id: str,
        text: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Store embedding for an entity"""
        embedding_file = self._get_embedding_file(entity_type, entity_id)
        
        data = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "text": text,
            "embedding": embedding,
            "metadata": metadata or {}
        }
        
        with open(embedding_file, 'w') as f:
            json.dump(data, f)
        
        # Cache in memory
        cache_key = f"{entity_type}:{entity_id}"
        self.embeddings_cache[cache_key] = {
            "embedding": np.array(embedding),
            "text": text,
            "metadata": metadata or {}
        }
    
    def get_embedding(self, entity_type: str, entity_id: str) -> Optional[np.ndarray]:
        """Get embedding for an entity"""
        cache_key = f"{entity_type}:{entity_id}"
        if cache_key in self.embeddings_cache:
            return self.embeddings_cache[cache_key]["embedding"]
        
        embedding_file = self._get_embedding_file(entity_type, entity_id)
        if not embedding_file.exists():
            return None
        
        with open(embedding_file, 'r') as f:
            data = json.load(f)
        
        embedding = np.array(data["embedding"])
        
        # Cache in memory
        self.embeddings_cache[cache_key] = {
            "embedding": embedding,
            "text": data["text"],
            "metadata": data.get("metadata", {})
        }
        
        return embedding
    
    def search_similar(
        self,
        query_embedding: np.ndarray,
        entity_type: str,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar entities using cosine similarity"""
        entity_dir = self.base_path / entity_type
        if not entity_dir.exists():
            return []
        
        results = []
        
        # Load all embeddings for this entity type
        for embedding_file in entity_dir.glob("*.json"):
            try:
                with open(embedding_file, 'r') as f:
                    data = json.load(f)
                
                entity_id = data["entity_id"]
                entity_embedding = np.array(data["embedding"])
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, entity_embedding)
                
                if similarity >= threshold:
                    results.append({
                        "entity_id": entity_id,
                        "entity_type": entity_type,
                        "similarity": float(similarity),
                        "text": data["text"],
                        "metadata": data.get("metadata", {})
                    })
            except Exception:
                continue
        
        # Sort by similarity and return top K
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
    
    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)


class EmbeddingService:
    """Service for generating embeddings"""
    
    def __init__(self):
        self.provider = settings.embedding_provider.lower()
        self.model = settings.embedding_model
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if self.provider == "openai":
            return await self._openai_embedding(text)
        else:
            # Local fallback - simple TF-IDF-like approach
            return self._local_embedding(text)
    
    async def _openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI"""
        try:
            import openai
            from uepi_api.config import get_settings
            
            settings = get_settings()
            client = openai.OpenAI(api_key=settings.openai_api_key or "")
            
            response = client.embeddings.create(
                model=self.model,
                input=text
            )
            
            return response.data[0].embedding
        except Exception as e:
            print(f"OpenAI embedding error: {e}")
            # Fallback to local
            return self._local_embedding(text)
    
    def _local_embedding(self, text: str) -> List[float]:
        """Simple local embedding (fallback)"""
        # Simple hash-based embedding for fallback
        # In production, use a proper local embedding model
        import hashlib
        
        # Create a simple embedding based on text hash
        hash_obj = hashlib.sha256(text.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Convert to float vector (128 dimensions)
        embedding = []
        for i in range(0, min(len(hash_hex), 128), 2):
            val = int(hash_hex[i:i+2], 16) / 255.0
            embedding.append(val)
        
        # Pad to 128 dimensions
        while len(embedding) < 128:
            embedding.append(0.0)
        
        return embedding[:128]

