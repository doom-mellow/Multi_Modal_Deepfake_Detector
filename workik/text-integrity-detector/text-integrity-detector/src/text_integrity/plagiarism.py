"""Reference-corpus similarity search for finding possible copied passages.

This is a local corpus matcher, not internet search and not a legal plagiarism finding.
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

TOKEN_RE = re.compile(r"\b[\w]+(?:['’][\w]+)?\b", re.UNICODE)


def _word_shingles(text: str, n: int = 5) -> set[tuple[str, ...]]:
    tokens = [token.lower() for token in TOKEN_RE.findall(text)]
    if len(tokens) < n:
        return {tuple(tokens)} if tokens else set()
    return {tuple(tokens[index:index + n]) for index in range(len(tokens) - n + 1)}


def compare_corpus(query: str, documents: list[dict[str, str]], top_k: int = 5,
                   threshold: float = 0.15) -> dict[str, Any]:
    """Compare query against records shaped as {id, text} with TF-IDF and exact shingles."""
    if not query.strip():
        raise ValueError("Query text is empty")
    if not documents:
        return {"matches": [], "warning": _warning()}
    cleaned = []
    for index, item in enumerate(documents):
        text = item.get("text", "")
        if not text.strip():
            continue
        cleaned.append({"id": str(item.get("id", index + 1)), "text": text})
    if not cleaned:
        return {"matches": [], "warning": _warning()}
    corpus = [query] + [item["text"] for item in cleaned]
    try:
        matrix = TfidfVectorizer(analyzer="word", ngram_range=(1, 3),
                                 token_pattern=r"(?u)\b\w+\b", sublinear_tf=True).fit_transform(corpus)
        semantic_scores = cosine_similarity(matrix[0:1], matrix[1:]).ravel()
    except ValueError:
        semantic_scores = [0.0] * len(cleaned)

    query_shingles = _word_shingles(query)
    matches = []
    for document, semantic in zip(cleaned, semantic_scores):
        source_shingles = _word_shingles(document["text"])
        overlap = len(query_shingles & source_shingles)
        exact_overlap = overlap / max(1, len(query_shingles))
        # A transparent blended retrieval score; report component scores separately.
        similarity = max(float(semantic), exact_overlap)
        if similarity >= threshold:
            matches.append({
                "document_id": document["id"],
                "similarity": round(similarity, 4),
                "tfidf_similarity": round(float(semantic), 4),
                "query_shingle_coverage": round(exact_overlap, 4),
                "overlapping_shingles": overlap,
            })
    matches.sort(key=lambda item: item["similarity"], reverse=True)
    return {"matches": matches[:max(0, top_k)], "warning": _warning()}


def _warning() -> str:
    return "Only the supplied reference corpus is checked (not the internet or unpublished sources). Similarity flags are leads for human review, not proof of plagiarism; citations, common phrases, and quoted material can match."
