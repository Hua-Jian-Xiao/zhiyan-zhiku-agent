from __future__ import annotations

import hashlib
import re
from pathlib import Path

from django.db import transaction

from apps.knowledge.models import Document, DocumentChunk, KnowledgePoint
from apps.retrieval.services.embedding import embed_texts
from apps.retrieval.services.tokenize import search_tokens, token_counts

from .chunking import ChunkDraft, chunk_markdown, split_plain_text
from .extract import extract_document


class IngestionError(Exception):
    pass


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _clean_heading(value: str) -> str:
    return re.sub(r"^[\d.\s、]+", "", value or "").strip()


def _match_knowledge_point(
    document: Document, draft: ChunkDraft, points: list[KnowledgePoint]
) -> KnowledgePoint | None:
    if document.knowledge_point_id:
        return document.knowledge_point
    title = f"{_clean_heading(draft.title)} {_clean_heading(draft.chapter)}"
    candidates = [
        point
        for point in points
        if point.name
        and (
            point.name in title
            or _clean_heading(draft.title) == point.name
            or _clean_heading(draft.title) in point.name
        )
    ]
    if candidates:
        return max(candidates, key=lambda point: len(point.name))
    return None


def _build_tags(document: Document, draft: ChunkDraft, point: KnowledgePoint | None) -> list[str]:
    tags = [document.course.short_name, document.course.name]
    if point:
        tags.extend(point.tags or [])
    tokens = search_tokens(draft.title)
    tags.extend(tokens[:4])
    seen: list[str] = []
    for tag in tags:
        if tag and tag not in seen:
            seen.append(tag)
    return seen[:8]


def ingest_document(document: Document, *, raise_errors: bool = True) -> Document:
    document.status = "processing"
    document.error_message = ""
    document.save(update_fields=["status", "error_message", "updated_at"])
    try:
        path = Path(document.storage_path)
        if not path.exists():
            raise IngestionError("找不到源文件，无法解析")
        text = extract_document(path, document.source_type)
        if document.source_type in {"md", "markdown"}:
            drafts = chunk_markdown(text, document.title, course_name=document.course.name)
        else:
            drafts = split_plain_text(text, document.title, document.course.name)
        drafts = [draft for draft in drafts if len(draft.content.strip()) >= 40]
        if not drafts:
            raise IngestionError("文档中没有可入库的正文内容")

        points = list(document.course.knowledge_points.all())
        embedding_result = embed_texts([draft.content for draft in drafts])

        with transaction.atomic():
            DocumentChunk.objects.filter(document=document).delete()
            lookup: dict[str, KnowledgePoint] = {point.name: point for point in points}
            chunk_rows = []
            for index, draft in enumerate(drafts, start=1):
                point = _match_knowledge_point(document, draft, points)
                uid = f"CH-{document.uid}-{index:03d}"
                if len(uid) > 80:
                    uid = f"CH-{document.uid[-30:]}-{index:03d}"
                chunk_rows.append(
                    DocumentChunk(
                        uid=uid,
                        document=document,
                        course=document.course,
                        knowledge_point=point,
                        ordinal=index,
                        title=draft.title[:200],
                        content=draft.content,
                        content_hash=_hash(draft.content),
                        char_count=len(draft.content),
                        tokens=token_counts(
                            " ".join([draft.title, draft.chapter, draft.content])
                        ),
                        tags=_build_tags(document, draft, point),
                        source_name=document.source_name,
                        chapter=draft.chapter[:160],
                        embedding=embedding_result.vectors[index - 1],
                        embedding_provider=embedding_result.provider,
                        embedding_model=embedding_result.model,
                        embedding_dim=embedding_result.dim,
                        embedding_norm=1.0,
                    )
                )
            DocumentChunk.objects.bulk_create(chunk_rows)
            document.status = "ready"
            document.chunk_count = len(chunk_rows)
            document.error_message = ""
            document.save(
                update_fields=["status", "chunk_count", "error_message", "updated_at"]
            )
        return document
    except Exception as exc:
        document.status = "failed"
        document.error_message = str(exc)[:1000]
        document.save(update_fields=["status", "error_message", "updated_at"])
        if raise_errors:
            raise
        return document
