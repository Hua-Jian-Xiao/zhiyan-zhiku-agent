"""Embedding providers for the RAG index.

The default provider is fully offline: Chinese character n-grams and Latin
terms are signed-hashed into a fixed-size vector. The interface is deliberately
small so a real embedding model or vector database can be introduced later.
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from dataclasses import dataclass

from django.conf import settings

CJK_RUN = re.compile(r"[㐀-鿿]+")
LATIN_WORD = re.compile(r"[a-zA-Z][a-zA-Z0-9_+#.-]{1,}|[0-9]{2,}")


@dataclass(frozen=True)
class EmbeddingResult:
    provider: str
    model: str
    dim: int
    vectors: list[list[float]]


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text).lower()


def _features(text: str) -> list[tuple[str, float]]:
    normalized = _normalize(text)
    features: list[tuple[str, float]] = []

    for run in CJK_RUN.findall(normalized):
        if len(run) == 1:
            features.append((run, 0.6))
            continue
        for index in range(len(run) - 1):
            features.append((run[index : index + 2], 1.0))
        for index in range(len(run) - 2):
            features.append((run[index : index + 3], 0.7))
    for word in LATIN_WORD.findall(normalized):
        features.append((word, 1.25))
    return features


def _hash_vector(text: str, dim: int) -> list[float]:
    vector = [0.0] * dim
    for token, weight in _features(text):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "little") % dim
        sign = 1.0 if digest[4] & 1 else -1.0
        vector[index] += sign * weight
    norm = math.sqrt(sum(value * value for value in vector))
    if norm <= 1e-12:
        return vector
    return [round(value / norm, 8) for value in vector]


def local_embed(texts: list[str]) -> EmbeddingResult:
    dim = int(settings.EMBEDDING_DIM)
    return EmbeddingResult(
        provider="local",
        model="blake2b-char-ngram-v1",
        dim=dim,
        vectors=[_hash_vector(text, dim) for text in texts],
    )


def openai_embed(texts: list[str]) -> EmbeddingResult:
    from openai import OpenAI

    client = OpenAI(
        api_key=settings.OPENAI_EMBEDDING_API_KEY,
        base_url=settings.OPENAI_EMBEDDING_BASE_URL,
        timeout=30,
        max_retries=1,
    )
    response = client.embeddings.create(
        model=settings.OPENAI_EMBEDDING_MODEL, input=texts
    )
    vectors = [list(item.embedding) for item in response.data]
    return EmbeddingResult(
        provider="openai",
        model=settings.OPENAI_EMBEDDING_MODEL,
        dim=len(vectors[0]) if vectors else 0,
        vectors=vectors,
    )


def embed_texts(texts: list[str], allow_external: bool = True) -> EmbeddingResult:
    if not texts:
        return local_embed([])

    provider = getattr(settings, "EMBEDDING_PROVIDER", "local")
    if allow_external and provider == "openai" and settings.OPENAI_EMBEDDING_API_KEY:
        try:
            return openai_embed(texts)
        except Exception:
            # Online embeddings are optional; deterministic local vectors keep
            # demos and tests working when the provider is unavailable.
            pass
    return local_embed(texts)


def embed_text(text: str, allow_external: bool = True) -> list[float]:
    return embed_texts([text], allow_external=allow_external).vectors[0]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return float(sum(a * b for a, b in zip(left, right)))
