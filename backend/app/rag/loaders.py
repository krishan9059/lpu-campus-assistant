"""Read source documents (Markdown, plain text, PDF) into headed sections."""

from __future__ import annotations

import hashlib
import logging
import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from app.rag.types import DocumentMeta, Section

logger = logging.getLogger(__name__)

SUPPORTED_SUFFIXES = frozenset({".md", ".markdown", ".txt", ".pdf"})

_FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_MD_HEADING = re.compile(r"^(#{1,3})\s+(.+?)\s*#*\s*$")
_MD_TITLE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_NUMBERED_HEADING = re.compile(r"^(\d+(?:\.\d+)*)[.)]?\s+\S")
_PAGE_NUMBER = re.compile(r"^(page\s+)?\d+(\s*(of|/)\s*\d+)?$", re.IGNORECASE)


@dataclass(frozen=True)
class LoadedDocument:
    meta: DocumentMeta
    sections: list[Section]


def _sidecar(path: Path) -> Path:
    return path.with_name(path.name + ".yaml")


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _humanize(stem: str) -> str:
    return re.sub(r"[_\-]+", " ", stem).strip().title()


def _to_date(value: object) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            return None
    return None


def discover_documents(docs_dir: Path) -> list[Path]:
    """Files under ``docs_dir/<domain>/``. The first folder name is the document's domain."""
    found: list[Path] = []
    for path in sorted(docs_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        if path.name.lower() == "readme.md":
            continue
        if len(path.relative_to(docs_dir).parts) < 2:
            logger.warning("Skipping %s: place documents inside a domain folder", path)
            continue
        found.append(path)
    return found


def content_hash(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes())
    sidecar = _sidecar(path)
    if sidecar.exists():
        digest.update(sidecar.read_bytes())
    return digest.hexdigest()


def split_front_matter(raw: str) -> tuple[dict[str, Any], str]:
    match = _FRONT_MATTER.match(raw)
    if not match:
        return {}, raw
    data = yaml.safe_load(match.group(1)) or {}
    return (data if isinstance(data, dict) else {}), raw[match.end() :]


def markdown_sections(body: str, *, title: str = "") -> list[Section]:
    sections: list[Section] = []
    stack: list[tuple[int, str]] = []
    buffer: list[str] = []
    in_code = False

    def flush() -> None:
        text = "\n".join(buffer).strip()
        buffer.clear()
        if text:
            path = tuple(h for _, h in stack if h.casefold() != title.casefold())
            sections.append(Section(text=text, heading_path=path))

    for line in body.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
        match = None if in_code else _MD_HEADING.match(line)
        if match:
            flush()
            level, heading = len(match.group(1)), match.group(2).strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, heading))
        else:
            buffer.append(line)
    flush()
    return sections


def _heading_level(text: str) -> int | None:
    if len(text) > 70 or text.endswith((".", ",", ";")):
        return None
    match = _NUMBERED_HEADING.match(text)
    return match.group(1).count(".") + 1 if match else None


def _clean_pdf_block(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = re.sub(r"-\n(?=[a-z])", "", text)
    text = re.sub(r"\s*\n\s*", " ", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def _margin_key(text: str) -> str:
    return re.sub(r"\d+", "#", text.lower())


def _repeated_margins(pages: list[list[tuple[float, float, str, float]]]) -> set[str]:
    """Running headers and footers: margin text that recurs on at least half the pages."""
    if len(pages) < 2:
        return set()
    counts: Counter[str] = Counter()
    for blocks in pages:
        seen = {
            _margin_key(text)
            for y0, y1, text, height in blocks
            if y0 < 0.09 * height or y1 > 0.91 * height
        }
        counts.update(seen)
    threshold = max(2, math.ceil(len(pages) * 0.5))
    return {key for key, count in counts.items() if count >= threshold}


def pdf_sections(path: Path) -> tuple[list[Section], str]:
    """Extract text page by page, dropping running headers/footers and page numbers."""
    import pymupdf

    pages: list[list[tuple[float, float, str, float]]] = []
    with pymupdf.open(path) as pdf:
        title = (pdf.metadata or {}).get("title") or ""
        for page in pdf:
            height = page.rect.height
            blocks = []
            for _x0, y0, _x1, y1, text, _no, kind in page.get_text("blocks", sort=True):
                cleaned = _clean_pdf_block(text) if kind == 0 else ""
                if cleaned:
                    blocks.append((y0, y1, cleaned, height))
            pages.append(blocks)

    repeated = _repeated_margins(pages)
    sections: list[Section] = []
    stack: list[tuple[int, str]] = []
    for page_no, blocks in enumerate(pages, start=1):
        paragraphs: list[str] = []

        def flush(page_no: int = page_no, paragraphs: list[str] = paragraphs) -> None:
            if paragraphs:
                heading_path = tuple(h for _, h in stack)
                sections.append(Section("\n\n".join(paragraphs), heading_path, page_no))
                paragraphs.clear()

        for y0, y1, text, height in blocks:
            in_margin = y0 < 0.09 * height or y1 > 0.91 * height
            if _PAGE_NUMBER.match(text) or (in_margin and _margin_key(text) in repeated):
                continue
            level = _heading_level(text)
            if level is None:
                paragraphs.append(text)
                continue
            flush()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, text))
        flush()
    return sections, title


def load_document(path: Path, docs_dir: Path) -> LoadedDocument:
    relative = path.relative_to(docs_dir)
    doc_id, domain = relative.as_posix(), relative.parts[0]
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        sections, pdf_title = pdf_sections(path)
        raw_meta = {"title": pdf_title, **_read_yaml(_sidecar(path))}
        fallback_title = _humanize(path.stem)
        fallback_date = datetime.fromtimestamp(path.stat().st_mtime).date()
    else:
        text = path.read_text(encoding="utf-8")
        raw_meta, body = split_front_matter(text)
        heading = _MD_TITLE.search(body)
        fallback_title = heading.group(1) if heading else _humanize(path.stem)
        fallback_date = None
        title_for_paths = str(raw_meta.get("title") or fallback_title)
        if suffix == ".txt":
            sections = [Section(body.strip())] if body.strip() else []
        else:
            sections = markdown_sections(body, title=title_for_paths)

    meta = DocumentMeta(
        doc_id=doc_id,
        domain=domain,
        title=str(raw_meta.get("title") or fallback_title),
        effective_date=_to_date(raw_meta.get("effective_date")) or fallback_date,
        department=str(raw_meta.get("department") or ""),
        source_url=str(raw_meta.get("source_url") or ""),
        sample=bool(raw_meta.get("sample", False)),
    )
    return LoadedDocument(meta=meta, sections=sections)
