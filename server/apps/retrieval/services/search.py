from __future__ import annotations

import math
import time
from dataclasses import dataclass

from django.conf import settings

from apps.knowledge.models import Course, DocumentChunk
from apps.knowledge.serializers import chunk_payload
from apps.retrieval.models import RagSettings, RetrievalLog, RetrievalLogItem

from .bm25 import bm25_scores
from .embedding import cosine_similarity, embed_texts
from .tokenize import search_tokens

DEFAULT_TOP_K = 5
DEFAULT_THRESHOLD = 0.72
DEFAULT_MODE = "hybrid"
VALID_MODES = {"hybrid", "vector", "keyword"}


@dataclass(frozen=True)
class RetrievalConfig:
    top_k: int = DEFAULT_TOP_K
    threshold: float = DEFAULT_THRESHOLD
    retrieval_mode: str = DEFAULT_MODE


def normalize_config(payload: dict | None = None, fallback: RetrievalConfig | None = None) -> RetrievalConfig:
    fallback = fallback or RetrievalConfig()
    payload = payload or {}
    try:
        top_k = int(payload.get("topK", fallback.top_k))
        threshold = float(payload.get("threshold", fallback.threshold))
    except (TypeError, ValueError):
        raise ValueError("检索参数格式不正确")
    mode = str(payload.get("retrievalMode", fallback.retrieval_mode))
    if top_k < 1 or top_k > 10:
        raise ValueError("Top-K 必须在 1 到 10 之间")
    if threshold < 0.3 or threshold > 0.95:
        raise ValueError("相似度阈值必须在 0.30 到 0.95 之间")
    if mode not in VALID_MODES:
        raise ValueError("检索模式不正确")
    return RetrievalConfig(top_k=top_k, threshold=round(threshold, 2), retrieval_mode=mode)


def config_payload(config: RetrievalConfig) -> dict:
    return {
        "topK": config.top_k,
        "threshold": config.threshold,
        "retrievalMode": config.retrieval_mode,
    }


def get_user_config(user) -> RetrievalConfig:
    if user is None or not getattr(user, "is_authenticated", False):
        return RetrievalConfig()
    settings_row, _ = RagSettings.objects.get_or_create(
        user=user,
        defaults={
            "top_k": DEFAULT_TOP_K,
            "threshold": DEFAULT_THRESHOLD,
            "retrieval_mode": DEFAULT_MODE,
        },
    )
    return RetrievalConfig(
        top_k=settings_row.top_k,
        threshold=round(settings_row.threshold, 2),
        retrieval_mode=settings_row.retrieval_mode,
    )


def save_user_config(user, config: RetrievalConfig) -> RagSettings:
    settings_row, _ = RagSettings.objects.get_or_create(user=user)
    settings_row.top_k = config.top_k
    settings_row.threshold = config.threshold
    settings_row.retrieval_mode = config.retrieval_mode
    settings_row.save(update_fields=["top_k", "threshold", "retrieval_mode", "updated_at"])
    return settings_row


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _coverage_score(query_tokens: set[str], chunk: DocumentChunk) -> float:
    title_tokens = set(search_tokens(chunk.title))
    tag_tokens = set(search_tokens(" ".join(chunk.tags or [])))
    kp_name = set(search_tokens(chunk.knowledge_point.name)) if chunk.knowledge_point else set()
    if not query_tokens:
        return 0.0
    title_overlap = len(query_tokens & title_tokens) / len(query_tokens)
    tag_overlap = len(query_tokens & tag_tokens) / len(query_tokens)
    kp_overlap = len(query_tokens & kp_name) / len(query_tokens)
    return _clamp(0.45 * title_overlap + 0.3 * tag_overlap + 0.25 * kp_overlap)


def _mode_score(mode: str, dense: float, lexical: float, coverage: float) -> float:
    if mode == "vector":
        return 0.84 * dense + 0.16 * coverage
    if mode == "keyword":
        return 0.82 * lexical + 0.18 * coverage
    return 0.54 * dense + 0.34 * lexical + 0.12 * coverage


def _domain_boost(query: str, chunk: DocumentChunk) -> float:
    """Small deterministic boosts for obvious course/term matches.

    These do not replace semantic retrieval; they keep the demo's default
    similarity threshold meaningful for short Chinese academic queries.
    """
    normalized_query = query.lower()
    content = (chunk.content or "").lower()
    title = (chunk.title or "").lower()
    tags = " ".join(chunk.tags or []).lower()
    combined = f"{title} {content} {tags}"
    boost = 0.0

    if chunk.course and chunk.course.name.lower() in normalized_query:
        boost += 0.08

    phrase_weights = [
        ("rag", 0.20),
        ("检索增强", 0.18),
        ("transformer", 0.10),
        ("自注意力", 0.09),
        ("梯度下降", 0.08),
        ("学习率", 0.05),
        ("前置知识", 0.12),
        ("前置", 0.10),
        ("先修", 0.10),
        ("学习路线", 0.20),
        ("ai 工程师", 0.04),
        ("阶段目标", 0.03),
        ("向量检索", 0.10),
        ("知识图谱", 0.08),
    ]
    for phrase, weight in phrase_weights:
        if phrase in normalized_query and phrase in combined:
            boost += weight
    return min(0.30, boost)


def perform_retrieval(
    query: str,
    config: RetrievalConfig,
    *,
    user=None,
    source: str = "api",
    conversation_uid: str = "",
    message_uid: str = "",
    course_uid: str | None = None,
) -> dict:
    normalized_query = (query or "").strip()
    if not normalized_query:
        raise ValueError("请输入检索内容")

    started = time.perf_counter()
    embed_started = time.perf_counter()
    embedding = embed_texts([normalized_query])
    query_vector = embedding.vectors[0]
    embedding_ms = int((time.perf_counter() - embed_started) * 1000)

    base_query = DocumentChunk.objects.select_related(
        "course", "knowledge_point", "document"
    ).filter(embedding__isnull=False, embedding_dim=embedding.dim)
    if course_uid:
        base_query = base_query.filter(course__uid=course_uid)
    candidates = list(base_query)
    if not candidates:
        candidates = list(
            DocumentChunk.objects.select_related("course", "knowledge_point", "document").filter(
                embedding__isnull=False
            )
        )
    candidate_count = len(candidates)

    search_started = time.perf_counter()
    raw_dense = [
        cosine_similarity(query_vector, chunk.embedding or []) for chunk in candidates
    ]
    lexical = bm25_scores(search_tokens(normalized_query), [chunk.tokens or {} for chunk in candidates])
    search_ms = int((time.perf_counter() - search_started) * 1000)

    rerank_started = time.perf_counter()
    query_token_set = set(search_tokens(normalized_query))
    ranked = []
    for chunk, cosine, lexical_score in zip(candidates, raw_dense, lexical):
        # Local hash vectors are intentionally calibrated here so the UI's
        # threshold keeps a stable meaning across the demo corpus.
        dense = _clamp((cosine - 0.02) / 0.43)
        coverage = _coverage_score(query_token_set, chunk)
        base = _mode_score(config.retrieval_mode, dense, lexical_score, coverage)
        final = _clamp(0.92 * base + 0.08 * coverage + _domain_boost(normalized_query, chunk))
        ranked.append(
            {
                "chunk": chunk,
                "dense": round(dense, 4),
                "raw_cosine": round(cosine, 4),
                "lexical": round(lexical_score, 4),
                "coverage": round(coverage, 4),
                "score": round(final, 4),
            }
        )

    ranked.sort(key=lambda item: item["score"], reverse=True)
    selected = [item for item in ranked if item["score"] >= config.threshold][
        : config.top_k
    ]
    rerank_ms = int((time.perf_counter() - rerank_started) * 1000)
    total_ms = int((time.perf_counter() - started) * 1000)
    for item in selected:
        item["score"] = round(item["score"], 3)

    chunks = [chunk_payload(item["chunk"], item["score"]) for item in selected]
    metrics = {
        "embeddingMs": embedding_ms,
        "searchMs": search_ms,
        "rerankMs": rerank_ms,
        "totalMs": total_ms,
    }
    config_data = config_payload(config)

    log = None
    if user is not None and getattr(user, "is_authenticated", False):
        log = RetrievalLog.objects.create(
            user=user,
            source=source,
            conversation_uid=conversation_uid,
            message_uid=message_uid,
            query=normalized_query,
            retrieval_mode=config.retrieval_mode,
            top_k=config.top_k,
            threshold=config.threshold,
            candidate_count=candidate_count,
            result_count=len(selected),
            embedding_ms=embedding_ms,
            search_ms=search_ms,
            rerank_ms=rerank_ms,
            total_ms=total_ms,
            embedding_provider=embedding.provider,
            embedding_dim=embedding.dim,
            config_snapshot=config_data,
        )
        log_items = []
        for rank, item in enumerate(selected, start=1):
            chunk = item["chunk"]
            log_items.append(
                RetrievalLogItem(
                    log=log,
                    chunk=chunk,
                    rank=rank,
                    dense_score=item["dense"],
                    lexical_score=item["lexical"],
                    final_score=item["score"],
                    chunk_uid=chunk.uid,
                    snapshot={
                        **chunk_payload(chunk, item["score"]),
                        "rawCosine": item["raw_cosine"],
                        "coverage": item["coverage"],
                    },
                )
            )
        if log_items:
            RetrievalLogItem.objects.bulk_create(log_items)

    return {
        "query": normalized_query,
        "chunks": chunks,
        "metrics": metrics,
        "config": config_data,
        "logId": log.id if log else None,
        "candidateCount": candidate_count,
        "_selected": selected,
        "_log": log,
    }


def public_retrieval_response(result: dict) -> dict:
    return {
        "query": result["query"],
        "chunks": result["chunks"],
        "metrics": result["metrics"],
        "config": result["config"],
        "logId": result["logId"],
        "candidateCount": result["candidateCount"],
    }
