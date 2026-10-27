from app.services.chat import build_retrieval_query, normalise_citations
from app.schemas.chat import Turn


def test_normalise_splits_comma_group():
    text, cited = normalise_citations("Attendance must be 75% [1, 2].", max_id=3)
    assert text == "Attendance must be 75% [1][2]."
    assert cited == {1, 2}


def test_normalise_drops_out_of_range_ids():
    text, cited = normalise_citations("See [1] and [9].", max_id=2)
    assert text == "See [1] and ."
    assert cited == {1}


def test_normalise_leaves_already_split_citations():
    text, cited = normalise_citations("A[1] and B[2].", max_id=2)
    assert text == "A[1] and B[2]."
    assert cited == {1, 2}


def test_normalise_handles_no_citations():
    text, cited = normalise_citations("No citations here.", max_id=3)
    assert text == "No citations here."
    assert cited == set()


def test_retrieval_query_uses_history_for_short_followup():
    history = [Turn(role="user", content="What is the minimum CGPA for placements?")]
    query = build_retrieval_query("and for Dream companies?", history)
    assert "minimum CGPA" in query
    assert "Dream companies" in query


def test_retrieval_query_ignores_history_for_full_question():
    history = [Turn(role="user", content="What is the minimum CGPA for placements?")]
    query = build_retrieval_query("What is the attendance requirement for the term-end exam?", history)
    assert query == "What is the attendance requirement for the term-end exam?"
