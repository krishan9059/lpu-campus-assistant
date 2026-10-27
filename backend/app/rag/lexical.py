"""Small BM25 implementation for exact-term matching (codes, numbers, acronyms)."""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence

from app.rag.text import tokenize
from app.rag.types import Chunk


class BM25Index:
    def __init__(self, chunks: Sequence[Chunk], *, k1: float = 1.5, b: float = 0.75) -> None:
        self._chunks = list(chunks)
        self._k1, self._b = k1, b
        self._tf = [Counter(tokenize(c.contextual_text)) for c in self._chunks]
        self._lengths = [sum(tf.values()) for tf in self._tf]
        total = len(self._chunks)
        self._avg_length = sum(self._lengths) / total if total else 0.0
        document_frequency: Counter[str] = Counter()
        for tf in self._tf:
            document_frequency.update(tf.keys())
        self._idf = {
            term: math.log(1 + (total - df + 0.5) / (df + 0.5))
            for term, df in document_frequency.items()
        }

    def search(self, query: str, k: int) -> list[tuple[Chunk, float]]:
        terms = set(tokenize(query))
        if not terms or not self._chunks:
            return []
        scored: list[tuple[float, int]] = []
        for index, tf in enumerate(self._tf):
            length_norm = 1 - self._b + self._b * self._lengths[index] / (self._avg_length or 1.0)
            score = 0.0
            for term in terms:
                frequency = tf.get(term)
                if frequency:
                    score += (
                        self._idf[term]
                        * frequency
                        * (self._k1 + 1)
                        / (frequency + self._k1 * length_norm)
                    )
            if score > 0:
                scored.append((score, index))
        scored.sort(reverse=True)
        return [(self._chunks[i], s) for s, i in scored[:k]]
