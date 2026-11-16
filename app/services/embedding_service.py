import math
import hashlib
from typing import List, Optional
from app.config import get_settings

class EmbeddingService:
    """Service for generating dense vector embeddings using Sentence Transformers."""

    def __init__(self, model_name: Optional[str] = None):
        settings = get_settings()
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.dimension = 384  # Standard dimension for all-MiniLM-L6-v2
        self._model = None

    def _load_model(self):
        """Lazy load SentenceTransformer model."""
        if self._model is None:
            try:
                import os
                # Disable huggingface online calls if cached locally
                os.environ["HF_HUB_OFFLINE"] = "1"
                os.environ["TRANSFORMERS_OFFLINE"] = "1"
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name, local_files_only=True)
            except Exception:
                try:
                    import os
                    os.environ.pop("HF_HUB_OFFLINE", None)
                    os.environ.pop("TRANSFORMERS_OFFLINE", None)
                    from sentence_transformers import SentenceTransformer
                    self._model = SentenceTransformer(self.model_name)
                except Exception as e:
                    print(f"[Warning] Could not load SentenceTransformer ('{self.model_name}'): {e}")
                    self._model = "fallback"

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding vector for a single query text."""
        self._load_model()
        if self._model != "fallback":
            vector = self._model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
            return vector.tolist()
        return self._generate_fallback_embedding(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate batch embeddings for a list of document texts."""
        if not texts:
            return []
        self._load_model()
        if self._model != "fallback":
            vectors = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True, batch_size=32)
            return [v.tolist() for v in vectors]
        return [self._generate_fallback_embedding(t) for t in texts]

    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """
        Deterministic, normalized 384-dimensional fallback embedding.
        Used when SentenceTransformer model is unavailable or in offline test environments.
        """
        vec = [0.0] * self.dimension
        if not text:
            return vec

        words = text.lower().split()
        for idx, word in enumerate(words):
            h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
            pos = h % self.dimension
            weight = 1.0 / (math.log(idx + 2) + 1.0)
            vec[pos] += weight

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec
