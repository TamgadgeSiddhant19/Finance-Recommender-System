from typing import List, Optional
from sentence_transformers import SentenceTransformer
from app.core.config import settings


class EmbeddingService:
    """
    Embedding service wrapping local Sentence Transformers model (all-MiniLM-L6-v2).
    Generates 384-dimensional dense semantic vectors.
    """
    _instance: Optional["EmbeddingService"] = None
    _model: Optional[SentenceTransformer] = None

    def __init__(self, model_name: str = settings.RAG_EMBEDDING_MODEL):
        self.model_name = model_name
        self.embedding_dim = settings.RAG_EMBEDDING_DIM

    @classmethod
    def get_instance(cls) -> "EmbeddingService":
        """Singleton accessor to reuse loaded model across requests."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def model(self) -> SentenceTransformer:
        """Lazy loader for the SentenceTransformer model."""
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for a single string."""
        embedding = self.model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate normalized embedding vectors for a batch of strings."""
        if not texts:
            return []
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return embeddings.tolist()
