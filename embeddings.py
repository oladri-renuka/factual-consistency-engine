import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Union
from config import EMBEDDING_MODEL

class EmbeddingService:
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name

    def encode(self, texts: Union[str, List[str]]) -> Union[np.ndarray, List[np.ndarray]]:
        if isinstance(texts, str):
            embedding = self.model.encode([texts], convert_to_numpy=True)
            return embedding[0]
        else:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings

    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(embedding1, embedding2) / (norm1 * norm2))

    def batch_similarity(self, embedding: np.ndarray, embeddings: List[np.ndarray]) -> np.ndarray:
        similarities = []
        for emb in embeddings:
            similarities.append(self.similarity(embedding, emb))
        return np.array(similarities)

    def find_similar_claims(self, query_embedding: np.ndarray,
                           claim_embeddings: List[np.ndarray],
                           threshold: float = 0.7) -> List[int]:
        similarities = self.batch_similarity(query_embedding, claim_embeddings)
        similar_indices = np.where(similarities >= threshold)[0].tolist()
        return similar_indices
