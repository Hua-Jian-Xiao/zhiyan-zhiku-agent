from __future__ import annotations

import math
from collections import Counter


def bm25_scores(
    query_tokens: list[str],
    documents: list[dict[str, int]],
    k1: float = 1.5,
    b: float = 0.75,
) -> list[float]:
    if not documents:
        return []
    query_terms = set(query_tokens)
    if not query_terms:
        return [0.0 for _ in documents]

    lengths = [sum(document.values()) or 1 for document in documents]
    average_length = sum(lengths) / len(lengths)
    doc_frequency = Counter()
    for document in documents:
        for term in query_terms:
            if document.get(term, 0) > 0:
                doc_frequency[term] += 1

    scores: list[float] = []
    total_docs = len(documents)
    for document, length in zip(documents, lengths):
        score = 0.0
        for term in query_terms:
            frequency = document.get(term, 0)
            if not frequency:
                continue
            df = doc_frequency[term]
            idf = math.log(1 + (total_docs - df + 0.5) / (df + 0.5))
            denominator = frequency + k1 * (1 - b + b * length / average_length)
            score += idf * (frequency * (k1 + 1)) / denominator
        scores.append(score)

    maximum = max(scores) if scores else 0.0
    if maximum <= 0:
        return [0.0 for _ in scores]
    return [score / maximum for score in scores]
