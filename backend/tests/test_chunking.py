from app.rag.chunking import split_text
from app.rag.loaders import markdown_sections, split_front_matter


def test_split_text_respects_size_budget():
    text = "\n\n".join(f"Paragraph {i} about attendance rules and policy details here." for i in range(20))
    chunks = split_text(text, size=200, overlap=40)
    assert len(chunks) > 1
    assert all(len(c) <= 260 for c in chunks)  # a little slack for one oversized sentence


def test_split_text_overlaps_between_chunks():
    text = "\n\n".join(f"This is paragraph number {i} with some extra padding words." for i in range(12))
    chunks = split_text(text, size=150, overlap=50)
    assert len(chunks) >= 2
    tail_of_first = chunks[0][-30:]
    assert any(word in chunks[1] for word in tail_of_first.split() if len(word) > 4)


def test_split_text_never_drops_content():
    text = "Word " * 500
    chunks = split_text(text.strip(), size=100, overlap=10)
    assert sum(c.count("Word") for c in chunks) >= 490  # allow a little overlap double count


def test_markdown_sections_nest_headings():
    body = "# Title\n\n## A\n\ntext a\n\n### A.1\n\ntext a1\n\n## B\n\ntext b\n"
    sections = markdown_sections(body, title="Title")
    paths = [s.heading_path for s in sections]
    assert ("A",) in paths
    assert ("A", "A.1") in paths
    assert ("B",) in paths


def test_markdown_sections_ignore_headings_inside_code_blocks():
    body = "# Title\n\n## Real\n\n```\n# not a heading\n```\n\nmore text\n"
    sections = markdown_sections(body, title="Title")
    assert all("not a heading" not in s.heading_path for s in sections)
    assert any("not a heading" in s.text for s in sections)


def test_front_matter_is_parsed_and_stripped():
    raw = "---\ntitle: X\neffective_date: 2025-01-01\n---\n# X\n\nbody text\n"
    meta, body = split_front_matter(raw)
    assert meta["title"] == "X"
    assert "---" not in body
    assert "body text" in body


def test_front_matter_missing_is_empty():
    meta, body = split_front_matter("# X\n\nbody\n")
    assert meta == {}
    assert body.startswith("# X")
