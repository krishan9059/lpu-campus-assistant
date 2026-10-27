"""Vector stores: Chroma for persistence, plus an in-memory store for tests."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from app.config import Settings
from app.rag.types import Chunk

logger = logging.getLogger(__name__)

_UPSERT_BATCH = 256


class VectorStore(Protocol):
    def upsert(self, chunks: Sequence[Chunk], embeddings: np.ndarray) -> None: ...

    def delete_document(self, doc_id: str) -> None: ...

    def query(self, embedding: np.ndarray, *, domain: str, k: int) -> list[tuple[Chunk, float]]:
        """Nearest chunks in a domain as ``(chunk, cosine similarity)``, best first."""

    def all_chunks(self, domain: str) -> list[Chunk]: ...

    def count(self, domain: str | None = None) -> int: ...

    def reset(self) -> None: ...


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._items: dict[str, tuple[Chunk, np.ndarray]] = {}

    def upsert(self, chunks: Sequence[Chunk], embeddings: np.ndarray) -> None:
        for chunk, vector in zip(chunks, embeddings, strict=True):
            self._items[chunk.chunk_id] = (chunk, np.asarray(vector, dtype=np.float32))

    def delete_document(self, doc_id: str) -> None:
        self._items = {k: v for k, v in self._items.items() if v[0].doc_id != doc_id}

    def query(self, embedding: np.ndarray, *, domain: str, k: int) -> list[tuple[Chunk, float]]:
        scored = [
            (chunk, float(np.dot(vector, embedding)))
            for chunk, vector in self._items.values()
            if chunk.domain == domain
        ]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:k]

    def all_chunks(self, domain: str) -> list[Chunk]:
        return [c for c, _ in self._items.values() if c.domain == domain]

    def count(self, domain: str | None = None) -> int:
        if domain is None:
            return len(self._items)
        return sum(1 for c, _ in self._items.values() if c.domain == domain)

    def reset(self) -> None:
        self._items.clear()


class ChromaVectorStore:
    _COLLECTION = "campus_chunks"

    def __init__(self, path: Path) -> None:
        import chromadb

        path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(path), settings=chromadb.Settings(anonymized_telemetry=False)
        )
        self._collection = self._open()

    def _open(self) -> Any:
        return self._client.get_or_create_collection(
            self._COLLECTION, metadata={"hnsw:space": "cosine"}
        )

    def upsert(self, chunks: Sequence[Chunk], embeddings: np.ndarray) -> None:
        for start in range(0, len(chunks), _UPSERT_BATCH):
            batch = chunks[start : start + _UPSERT_BATCH]
            self._collection.upsert(
                ids=[c.chunk_id for c in batch],
                embeddings=embeddings[start : start + _UPSERT_BATCH].tolist(),
                documents=[c.text for c in batch],
                metadatas=[c.to_metadata() for c in batch],
            )

    def delete_document(self, doc_id: str) -> None:
        self._collection.delete(where={"doc_id": doc_id})

    def query(self, embedding: np.ndarray, *, domain: str, k: int) -> list[tuple[Chunk, float]]:
        available = self._collection.count()
        if available == 0:
            return []
        result = self._collection.query(
            query_embeddings=[embedding.tolist()],
            n_results=min(k, available),
            where={"domain": domain},
            include=["documents", "metadatas", "distances"],
        )
        hits = zip(
            result["ids"][0],
            result["documents"][0],
            result["metadatas"][0],
            result["distances"][0],
            strict=True,
        )
        return [(Chunk.from_store(i, doc, meta), 1.0 - float(dist)) for i, doc, meta, dist in hits]

    def all_chunks(self, domain: str) -> list[Chunk]:
        result = self._collection.get(where={"domain": domain}, include=["documents", "metadatas"])
        return [
            Chunk.from_store(i, doc, meta)
            for i, doc, meta in zip(
                result["ids"], result["documents"], result["metadatas"], strict=True
            )
        ]

    def count(self, domain: str | None = None) -> int:
        if domain is None:
            return int(self._collection.count())
        return len(self._collection.get(where={"domain": domain}, include=[])["ids"])

    def reset(self) -> None:
        self._client.delete_collection(self._COLLECTION)
        self._collection = self._open()


def build_vector_store(settings: Settings) -> VectorStore:
    if settings.vector_store == "memory":
        return InMemoryVectorStore()
    return ChromaVectorStore(settings.vector_dir)
