"""Hybrid retrieval: dense vectors plus BM25, merged with reciprocal rank fusion."""

from __future__ import annotations

import threading

from app.rag.embeddings import Embedder
from app.rag.lexical import BM25Index
from app.rag.types import Chunk, RetrievedChunk, SearchResult
from app.rag.vectorstore import VectorStore


class HybridRetriever:
    def __init__(
        self,
        store: VectorStore,
        embedder: Embedder,
        *,
        top_k: int = 5,
        candidates: int = 20,
        rrf_k: int = 60,
    ) -> None:
        self._store = store
        self._embedder = embedder
        self._top_k = top_k
        self._candidates = candidates
        self._rrf_k = rrf_k
        self._bm25: dict[str, BM25Index] = {}
        self._lock = threading.Lock()

    def refresh(self) -> None:
        """Drop cached keyword indexes. Call after the document index changes."""
        with self._lock:
            self._bm25.clear()

    def _lexical_index(self, domain: str) -> BM25Index:
        with self._lock:
            if domain not in self._bm25:
                self._bm25[domain] = BM25Index(self._store.all_chunks(domain))
            return self._bm25[domain]

    def search(self, query: str, domain: str) -> SearchResult:
        dense = self._store.query(
            self._embedder.embed_query(query), domain=domain, k=self._candidates
        )
        lexical = self._lexical_index(domain).search(query, self._candidates)

        merged: dict[str, dict[str, object]] = {}

        def add(rank: int, chunk: Chunk, score: float, kind: str) -> None:
            entry = merged.setdefault(
                chunk.chunk_id, {"chunk": chunk, "dense": None, "lexical": None, "rrf": 0.0}
            )
            entry[kind] = score
            entry["rrf"] = float(entry["rrf"]) + 1.0 / (self._rrf_k + rank)  # type: ignore[arg-type]

        for rank, (chunk, score) in enumerate(dense, start=1):
            add(rank, chunk, score, "dense")
        for rank, (chunk, score) in enumerate(lexical, start=1):
            add(rank, chunk, score, "lexical")

        ordered = sorted(merged.values(), key=lambda e: float(e["rrf"]), reverse=True)  # type: ignore[arg-type]
        chunks = [
            RetrievedChunk(
                chunk=e["chunk"],  # type: ignore[arg-type]
                dense_score=e["dense"],  # type: ignore[arg-type]
                lexical_score=e["lexical"],  # type: ignore[arg-type]
                fused_score=float(e["rrf"]),  # type: ignore[arg-type]
            )
            for e in ordered[: self._top_k]
        ]
        best_dense = dense[0][1] if dense else 0.0
        return SearchResult(chunks=chunks, best_dense_score=best_dense)
