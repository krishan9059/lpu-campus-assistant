"""Embedding models behind one small interface."""

from __future__ import annotations

import logging
import math
import threading
import zlib
from collections import Counter
from collections.abc import Sequence
from itertools import pairwise
from typing import Any, Protocol

import numpy as np

from app.config import Settings
from app.rag.text import tokenize

logger = logging.getLogger(__name__)


class Embedder(Protocol):
    @property
    def name(self) -> str: ...

    def embed_documents(self, texts: Sequence[str]) -> np.ndarray:
        """Return an ``(n, dim)`` float32 array of L2-normalised vectors."""

    def embed_query(self, text: str) -> np.ndarray:
        """Return a single L2-normalised vector."""


class HashingEmbedder:
    """Deterministic bag-of-words embedder that needs no model download.

    It has no semantic understanding, so it exists for tests, CI and offline development.
    Production runs use :class:`SentenceTransformerEmbedder`.
    """

    def __init__(self, dim: int = 1024) -> None:
        self._dim = dim

    @property
    def name(self) -> str:
        return f"hash-{self._dim}"

    def _vectorise(self, text: str) -> np.ndarray:
        tokens = tokenize(text)
        features: Counter[str] = Counter(tokens)
        features.update(f"{a}_{b}" for a, b in pairwise(tokens))
        vector = np.zeros(self._dim, dtype=np.float32)
        for feature, count in features.items():
            weight = 1.0 + math.log(count)
            vector[zlib.crc32(feature.encode("utf-8")) % self._dim] += weight * (
                0.5 if "_" in feature else 1.0
            )
        norm = float(np.linalg.norm(vector))
        return vector / norm if norm else vector

    def embed_documents(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self._dim), dtype=np.float32)
        return np.stack([self._vectorise(t) for t in texts])

    def embed_query(self, text: str) -> np.ndarray:
        return self._vectorise(text)


class SentenceTransformerEmbedder:
    """Multilingual dense embeddings via sentence-transformers.

    E5 models expect ``query:`` and ``passage:`` prefixes; other models are used as-is.
    """

    def __init__(
        self,
        model_name: str,
        *,
        device: str | None = None,
        batch_size: int = 32,
        model: Any | None = None,
    ) -> None:
        self._model_name = model_name
        self._device = device
        self._batch_size = batch_size
        self._model = model
        self._lock = threading.Lock()
        is_e5 = "e5" in model_name.lower()
        self._query_prefix = "query: " if is_e5 else ""
        self._passage_prefix = "passage: " if is_e5 else ""

    @property
    def name(self) -> str:
        return self._model_name

    def _load(self) -> Any:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:  # pragma: no cover - depends on optional extra
                raise RuntimeError(
                    "sentence-transformers is not installed. Run `pip install -e '.[ml]'`, "
                    "or set EMBEDDING_PROVIDER=hash for an offline development embedder."
                ) from exc
            logger.info("Loading embedding model %s", self._model_name)
            self._model = SentenceTransformer(self._model_name, device=self._device)
        return self._model

    def _encode(self, texts: list[str]) -> np.ndarray:
        with self._lock:
            model = self._load()
            vectors = model.encode(
                texts,
                batch_size=self._batch_size,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        return np.asarray(vectors, dtype=np.float32)

    def embed_documents(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 0), dtype=np.float32)
        return self._encode([self._passage_prefix + t for t in texts])

    def embed_query(self, text: str) -> np.ndarray:
        return self._encode([self._query_prefix + text])[0]


def build_embedder(settings: Settings) -> Embedder:
    if settings.embedding_provider == "hash":
        return HashingEmbedder()
    return SentenceTransformerEmbedder(settings.embedding_model, device=settings.embedding_device)
