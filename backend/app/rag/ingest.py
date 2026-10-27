"""Index documents from ``docs/<domain>/`` into the vector store, incrementally."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from app.rag.chunking import chunk_document
from app.rag.embeddings import Embedder
from app.rag.loaders import content_hash, discover_documents, load_document
from app.rag.vectorstore import VectorStore

logger = logging.getLogger(__name__)

_SCHEMA_VERSION = "1"


@dataclass
class IngestReport:
    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)
    chunks: int = 0
    rebuilt: bool = False

    @property
    def changed(self) -> bool:
        return bool(self.added or self.updated or self.removed or self.rebuilt)

    def summary(self) -> str:
        return (
            f"{len(self.added)} added, {len(self.updated)} updated, {len(self.removed)} removed, "
            f"{len(self.unchanged)} unchanged, {len(self.errors)} failed; "
            f"{self.chunks} chunks in index"
        )


class Ingestor:
    def __init__(
        self,
        *,
        docs_dir: Path,
        store: VectorStore,
        embedder: Embedder,
        chunk_size: int,
        chunk_overlap: int,
        manifest_path: Path | None,
    ) -> None:
        self._docs_dir = docs_dir
        self._store = store
        self._embedder = embedder
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._manifest_path = manifest_path
        # Cached in the instance so that a store with no manifest file (in-memory vector
        # store, tests) still gets incremental syncs across repeated calls on this object.
        self._known_cache: dict[str, dict] | None = None

    def _fingerprint(self) -> str:
        parts = [
            _SCHEMA_VERSION,
            self._embedder.name,
            str(self._chunk_size),
            str(self._chunk_overlap),
        ]
        return hashlib.sha256("|".join(parts).encode()).hexdigest()

    def _read_manifest(self) -> dict:
        if self._manifest_path and self._manifest_path.exists():
            try:
                return json.loads(self._manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                logger.warning("Ignoring unreadable index manifest")
        return {}

    def _write_manifest(self, documents: dict[str, dict]) -> None:
        if not self._manifest_path:
            return
        self._manifest_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"fingerprint": self._fingerprint(), "documents": documents}
        temporary = self._manifest_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temporary.replace(self._manifest_path)

    def sync(self, *, rebuild: bool = False) -> IngestReport:
        report = IngestReport()
        if self._known_cache is None:
            manifest = self._read_manifest()
            self._known_cache = manifest.get("documents", {})
            fingerprint_matches = manifest.get("fingerprint") == self._fingerprint()
        else:
            fingerprint_matches = True  # already validated when the cache was loaded
        known = self._known_cache

        stale = not fingerprint_matches or (bool(known) and self._store.count() == 0)
        if rebuild or stale:
            self._store.reset()
            known = {}
            report.rebuilt = True

        files = {
            p.relative_to(self._docs_dir).as_posix(): p for p in discover_documents(self._docs_dir)
        }

        for doc_id in sorted(set(known) - set(files)):
            self._store.delete_document(doc_id)
            known.pop(doc_id)
            report.removed.append(doc_id)

        for doc_id, path in files.items():
            digest = content_hash(path)
            previous = known.get(doc_id)
            if previous and previous.get("hash") == digest:
                report.unchanged.append(doc_id)
                continue
            try:
                document = load_document(path, self._docs_dir)
                chunks = chunk_document(
                    document, size=self._chunk_size, overlap=self._chunk_overlap
                )
                if previous:
                    self._store.delete_document(doc_id)
                if chunks:
                    vectors = self._embedder.embed_documents([c.contextual_text for c in chunks])
                    self._store.upsert(chunks, vectors)
            except Exception as exc:
                logger.exception("Failed to index %s", doc_id)
                report.errors[doc_id] = str(exc)
                known.pop(doc_id, None)
                continue
            known[doc_id] = {"hash": digest, "chunks": len(chunks), "domain": document.meta.domain}
            (report.updated if previous else report.added).append(doc_id)

        self._known_cache = known
        self._write_manifest(known)
        report.chunks = self._store.count()
        logger.info("Index sync: %s", report.summary())
        return report
