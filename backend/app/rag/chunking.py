"""Split loaded documents into overlapping, citation-friendly chunks."""

from __future__ import annotations

import re

from app.rag.loaders import LoadedDocument
from app.rag.types import Chunk

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?\u0964])\s+")
_PARAGRAPH_BOUNDARY = re.compile(r"\n\s*\n")


def _hard_split(text: str, size: int) -> list[str]:
    pieces: list[str] = []
    while len(text) > size:
        cut = text.rfind(" ", 0, size)
        cut = cut if cut > size // 2 else size
        pieces.append(text[:cut].strip())
        text = text[cut:].strip()
    if text:
        pieces.append(text)
    return pieces


def _units(text: str, size: int) -> list[str]:
    units: list[str] = []
    for paragraph in _PARAGRAPH_BOUNDARY.split(text):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if len(paragraph) <= size:
            units.append(paragraph)
            continue
        for sentence in _SENTENCE_BOUNDARY.split(paragraph):
            units.extend(_hard_split(sentence.strip(), size))
    return units


def split_text(text: str, size: int, overlap: int) -> list[str]:
    """Pack paragraphs (then sentences) into chunks of at most ``size`` characters.

    Consecutive chunks share trailing units up to ``overlap`` characters so that an answer
    straddling a boundary is still retrievable from either side.
    """
    chunks: list[str] = []
    current: list[str] = []
    length = 0
    for unit in _units(text, size):
        added = len(unit) + (2 if current else 0)
        if current and length + added > size:
            chunks.append("\n\n".join(current))
            carry: list[str] = []
            carried = 0
            for previous in reversed(current):
                if carried + len(previous) > overlap:
                    break
                carry.insert(0, previous)
                carried += len(previous) + 2
            current = carry
            length = sum(len(u) for u in current) + 2 * max(len(current) - 1, 0)
            added = len(unit) + (2 if current else 0)
        current.append(unit)
        length += added
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def chunk_document(document: LoadedDocument, *, size: int, overlap: int) -> list[Chunk]:
    meta = document.meta
    effective = meta.effective_date.isoformat() if meta.effective_date else ""
    chunks: list[Chunk] = []
    for section in document.sections:
        for body in split_text(section.text, size, overlap):
            chunks.append(
                Chunk(
                    chunk_id=f"{meta.doc_id}#{len(chunks):04d}",
                    text=body,
                    doc_id=meta.doc_id,
                    domain=meta.domain,
                    title=meta.title,
                    section=" > ".join(section.heading_path),
                    page=section.page,
                    effective_date=effective,
                    department=meta.department,
                    source_url=meta.source_url,
                    sample=meta.sample,
                )
            )
    return chunks
