"""Plain data types passed between the retrieval components."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

MetadataValue = str | int | float | bool


@dataclass(frozen=True, slots=True)
class DocumentMeta:
    doc_id: str
    domain: str
    title: str
    effective_date: date | None = None
    department: str = ""
    source_url: str = ""
    sample: bool = False


@dataclass(frozen=True, slots=True)
class Section:
    """A run of text that shares one heading path (and, for PDFs, one page)."""

    text: str
    heading_path: tuple[str, ...] = ()
    page: int | None = None


@dataclass(frozen=True, slots=True)
class Chunk:
    chunk_id: str
    text: str
    doc_id: str
    domain: str
    title: str
    section: str = ""
    page: int | None = None
    effective_date: str = ""
    department: str = ""
    source_url: str = ""
    sample: bool = False

    @property
    def contextual_text(self) -> str:
        """Text used for embedding and keyword search: the passage prefixed by where it lives."""
        header = f"{self.title} - {self.section}" if self.section else self.title
        return f"{header}\n{self.text}"

    def to_metadata(self) -> dict[str, MetadataValue]:
        # Chroma metadata values must be scalars, so None becomes an empty value.
        return {
            "doc_id": self.doc_id,
            "domain": self.domain,
            "title": self.title,
            "section": self.section,
            "page": self.page or 0,
            "effective_date": self.effective_date,
            "department": self.department,
            "source_url": self.source_url,
            "sample": self.sample,
        }

    @classmethod
    def from_store(cls, chunk_id: str, text: str, metadata: dict[str, MetadataValue]) -> Chunk:
        page = int(metadata.get("page") or 0)
        return cls(
            chunk_id=chunk_id,
            text=text,
            doc_id=str(metadata.get("doc_id", "")),
            domain=str(metadata.get("domain", "")),
            title=str(metadata.get("title", "")),
            section=str(metadata.get("section", "")),
            page=page or None,
            effective_date=str(metadata.get("effective_date", "")),
            department=str(metadata.get("department", "")),
            source_url=str(metadata.get("source_url", "")),
            sample=bool(metadata.get("sample", False)),
        )


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    chunk: Chunk
    dense_score: float | None
    lexical_score: float | None
    fused_score: float


@dataclass(frozen=True, slots=True)
class SearchResult:
    chunks: list[RetrievedChunk]
    best_dense_score: float
