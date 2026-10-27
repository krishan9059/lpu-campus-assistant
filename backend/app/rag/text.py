"""Tokenisation shared by the lexical index and the offline hashing embedder."""

from __future__ import annotations

import re

# \w does not cover Devanagari and Gurmukhi vowel signs, so those blocks are added explicitly.
_TOKEN = re.compile(r"[\w\u0900-\u097f\u0a00-\u0a7f]+")

STOPWORDS = frozenset(
    [
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "of",
        "to",
        "in",
        "on",
        "for",
        "and",
        "or",
        "at",
        "by",
        "with",
        "from",
        "as",
        "it",
        "this",
        "that",
        "these",
        "those",
        "what",
        "which",
        "who",
        "whom",
        "how",
        "when",
        "where",
        "why",
        "do",
        "does",
        "did",
        "can",
        "could",
        "should",
        "would",
        "will",
        "shall",
        "may",
        "might",
        "i",
        "me",
        "my",
        "we",
        "our",
        "you",
        "your",
        "he",
        "she",
        "they",
        "their",
        "them",
        "its",
        "if",
        "then",
        "than",
        "so",
        "about",
        "into",
        "any",
        "there",
        "have",
        "has",
        "had",
        "not",
        "no",
    ]
)


def _stem(token: str) -> str:
    if not token.isascii() or len(token) <= 3:
        return token
    if token.endswith("ies"):
        return token[:-3] + "y"
    if token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def tokenize(text: str) -> list[str]:
    tokens = (_stem(t) for t in _TOKEN.findall(text.lower()))
    return [t for t in tokens if t not in STOPWORDS]
