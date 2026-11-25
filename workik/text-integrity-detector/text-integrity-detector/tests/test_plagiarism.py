import pytest

from text_integrity.plagiarism import compare_corpus


def test_finds_copied_passage():
    query = "A careful researcher records every observation before drawing a conclusion from the available evidence."
    corpus = [{"id": "source-1", "text": query + " The notes are stored in a secure archive."},
              {"id": "source-2", "text": "Birds gathered in the garden as the sun disappeared behind distant hills."}]
    result = compare_corpus(query, corpus, threshold=0.1)
    assert result["matches"]
    assert result["matches"][0]["document_id"] == "source-1"
    assert result["matches"][0]["query_shingle_coverage"] > 0.8


def test_empty_corpus_and_query_validation():
    assert compare_corpus("some text", []) ["matches"] == []
    with pytest.raises(ValueError, match="empty"):
        compare_corpus(" ", [{"id": "x", "text": "source"}])
