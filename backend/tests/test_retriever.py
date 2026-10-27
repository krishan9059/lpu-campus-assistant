from pathlib import Path

from app.rag.embeddings import HashingEmbedder
from app.rag.ingest import Ingestor
from app.rag.retriever import HybridRetriever
from app.rag.vectorstore import InMemoryVectorStore


def _make_docs(tmp_path: Path) -> Path:
    docs = tmp_path / "docs" / "uni"
    docs.mkdir(parents=True)
    (docs / "attendance.md").write_text(
        "---\ntitle: Attendance Rules\neffective_date: 2025-07-01\n---\n"
        "# Attendance Rules\n\n## Minimum attendance\n"
        "Students must maintain at least 75 percent attendance to sit the term-end examination.\n"
    )
    (docs / "library.md").write_text(
        "# Library\n\n## Timings\nThe library is open from 8 AM to 10 PM on weekdays.\n"
    )
    return tmp_path / "docs"


def _build(tmp_path: Path):
    docs_dir = _make_docs(tmp_path)
    embedder = HashingEmbedder()
    store = InMemoryVectorStore()
    ingestor = Ingestor(
        docs_dir=docs_dir, store=store, embedder=embedder,
        chunk_size=900, chunk_overlap=120, manifest_path=None,
    )
    ingestor.sync()
    return HybridRetriever(store, embedder), ingestor, store


def test_relevant_query_scores_higher_than_irrelevant(tmp_path: Path):
    retriever, _, _ = _build(tmp_path)
    on_topic = retriever.search("what is the minimum attendance percentage?", "uni")
    off_topic = retriever.search("what is the weather like in Paris today?", "uni")
    assert on_topic.best_dense_score > off_topic.best_dense_score
    assert on_topic.chunks[0].chunk.section == "Minimum attendance"


def test_lexical_match_helps_rare_terms(tmp_path: Path):
    retriever, _, _ = _build(tmp_path)
    result = retriever.search("library timings", "uni")
    assert result.chunks
    assert result.chunks[0].chunk.section == "Timings"


def test_domain_isolation(tmp_path: Path):
    retriever, _, _ = _build(tmp_path)
    result = retriever.search("library timings", "placement")
    assert result.chunks == []
    assert result.best_dense_score == 0.0


def test_incremental_reingest_is_idempotent(tmp_path: Path):
    _, ingestor, store = _build(tmp_path)
    before = store.count()
    report = ingestor.sync()
    assert not report.changed
    assert store.count() == before


def test_document_update_replaces_old_chunks(tmp_path: Path):
    docs_dir = _make_docs(tmp_path)
    embedder = HashingEmbedder()
    store = InMemoryVectorStore()
    ingestor = Ingestor(docs_dir=docs_dir, store=store, embedder=embedder, chunk_size=900, chunk_overlap=120, manifest_path=None)
    ingestor.sync()
    (docs_dir / "uni" / "library.md").write_text("# Library\n\n## Timings\nOpen 24 hours during exams.\n")
    report = ingestor.sync()
    assert report.updated == ["uni/library.md"]
    chunks = store.all_chunks("uni")
    assert not any("8 AM to 10 PM" in c.text for c in chunks)
    assert any("24 hours" in c.text for c in chunks)


def test_document_removal_deletes_chunks(tmp_path: Path):
    docs_dir = _make_docs(tmp_path)
    embedder = HashingEmbedder()
    store = InMemoryVectorStore()
    ingestor = Ingestor(docs_dir=docs_dir, store=store, embedder=embedder, chunk_size=900, chunk_overlap=120, manifest_path=None)
    ingestor.sync()
    (docs_dir / "uni" / "library.md").unlink()
    report = ingestor.sync()
    assert report.removed == ["uni/library.md"]
    assert not any(c.doc_id == "uni/library.md" for c in store.all_chunks("uni"))


def test_manifest_persists_across_ingestor_instances(tmp_path: Path):
    docs_dir = _make_docs(tmp_path)
    embedder = HashingEmbedder()
    store = InMemoryVectorStore()
    manifest = tmp_path / "manifest.json"
    Ingestor(docs_dir=docs_dir, store=store, embedder=embedder, chunk_size=900, chunk_overlap=120, manifest_path=manifest).sync()
    second = Ingestor(docs_dir=docs_dir, store=store, embedder=embedder, chunk_size=900, chunk_overlap=120, manifest_path=manifest)
    report = second.sync()
    assert report.unchanged and not report.changed
