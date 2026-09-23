"""Embeddings Service for EduAccess AI RAG System.

Generates dense semantic vector embeddings for lecture chunks (speech segments,
visual events, OCR code text, and concepts).
- Supports Hugging Face feature extraction endpoint
- Provides local deterministic vector fallback (sparse TF-IDF cosine matching)
- Handles caching of computed chunk embeddings
"""
from __future__ import annotations

import hashlib
import logging
import math
import re
from typing import Any

from backend import config
from backend.services.ai.hf_client import get_hf_client

logger = logging.getLogger("eduaccess.ai.embeddings")

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingsService:
    """Vector embeddings generator with offline fallback."""

    def __init__(self, model_id: str = DEFAULT_EMBEDDING_MODEL):
        self.model_id = model_id
        self.hf_client = get_hf_client()
        self._cache: dict[str, list[float]] = {}

    def is_cloud_ready(self) -> bool:
        return self.hf_client.is_configured

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding vector for a single string."""
        clean = text.strip()
        if not clean:
            return [0.0] * 64

        cache_key = hashlib.sha256(clean.encode("utf-8")).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]

        if self.is_cloud_ready():
            try:
                payload = {"inputs": clean, "options": {"wait_for_model": True}}
                res = self.hf_client.post_sync(self.model_id, payload=payload, timeout=3.0)
                if isinstance(res, list) and res and isinstance(res[0], (int, float)):
                    self._cache[cache_key] = res
                    return res
                if isinstance(res, list) and res and isinstance(res[0], list):
                    self._cache[cache_key] = res[0]
                    return res[0]
            except Exception as e:
                logger.debug(f"HF embedding call failed ({e}); using local deterministic vectorizer.")

        # Deterministic local embedding fallback (hash-based bag-of-words / n-grams)
        vec = self._local_embed(clean)
        self._cache[cache_key] = vec
        return vec

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        return [self.embed_text(t) for t in texts]

    def _local_embed(self, text: str, dim: int = 128) -> list[float]:
        """Compute a normalized pseudo-semantic vector using word hashes."""
        vec = [0.0] * dim
        words = re.findall(r"[\w\u0600-\u06ff]+", text.lower())
        if not words:
            return vec

        for word in words:
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            weight = 1.0 + (len(word) / 10.0)
            vec[idx] += weight

        # Normalize to unit length
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 1e-6:
            vec = [x / norm for x in vec]
        return vec

    @staticmethod
    def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
        """Compute cosine similarity between two float vectors."""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a < 1e-6 or norm_b < 1e-6:
            return 0.0
        return max(0.0, min(1.0, dot / (norm_a * norm_b)))


# Global shared embeddings instance
_embeddings_instance: EmbeddingsService | None = None

def get_embeddings_service() -> EmbeddingsService:
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = EmbeddingsService()
    return _embeddings_instance
