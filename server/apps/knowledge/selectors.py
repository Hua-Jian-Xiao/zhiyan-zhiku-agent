from __future__ import annotations

from django.db import connection
from django.db.models import Count, Q
from django.utils import timezone

from apps.retrieval.services.embedding import local_embed

from .models import Course, Document, DocumentChunk, GraphCategory, GraphEdge, GraphNode, KnowledgePoint
from .serializers import (
    course_payload,
    graph_payload,
    knowledge_point_payload,
)


def courses_with_counts():
    return Course.objects.annotate(
        kp_count=Count("knowledge_points", distinct=True),
        doc_count=Count("documents", distinct=True),
    ).order_by("sort_order", "id")


def knowledge_points_with_course():
    return (
        KnowledgePoint.objects.select_related("course")
        .annotate(chunk_count=Count("chunks", distinct=True))
        .order_by("course__sort_order", "chapter_no", "sort_order", "id")
    )


def latest_sync_string() -> str:
    latest = Document.objects.filter(status="ready").order_by("-updated_at").first()
    value = latest.updated_at if latest else timezone.now()
    return timezone.localtime(value).strftime("%Y-%m-%d %H:%M")


def index_health_payload() -> dict:
    """Return a real, query-backed health snapshot for the knowledge index."""
    database = "ok"
    document_count = ready_count = failed_count = processing_count = 0
    chunk_count = empty_embedding_count = 0
    last_synced_at = "—"

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        document_count = Document.objects.count()
        ready_count = Document.objects.filter(status="ready").count()
        failed_count = Document.objects.filter(status="failed").count()
        processing_count = Document.objects.filter(
            status__in=["pending", "processing"]
        ).count()
        chunk_count = DocumentChunk.objects.count()
        empty_embedding_count = DocumentChunk.objects.filter(
            Q(embedding__isnull=True) | Q(embedding_dim__lte=0)
        ).count()
        latest = Document.objects.filter(status="ready").order_by("-updated_at").first()
        last_synced_at = (
            timezone.localtime(latest.updated_at).strftime("%Y-%m-%d %H:%M")
            if latest
            else "—"
        )
    except Exception:
        database = "error"

    issues: list[str] = []
    if database != "ok":
        issues.append("数据库连接异常")
    else:
        if document_count == 0:
            issues.append("知识库暂无文档")
        if chunk_count == 0:
            issues.append("知识库暂无向量片段")
        if empty_embedding_count:
            issues.append(f"{empty_embedding_count} 个片段缺少向量")
        if failed_count:
            issues.append(f"{failed_count} 份文档解析失败")
        if processing_count:
            issues.append(f"{processing_count} 份文档正在索引")

    if database == "error":
        status = "error"
    elif processing_count:
        status = "indexing"
    elif issues:
        status = "degraded"
    else:
        status = "healthy"

    labels = {
        "healthy": "索引健康",
        "indexing": "索引更新中",
        "degraded": "索引待修复",
        "error": "索引异常",
    }
    return {
        "status": status,
        "label": labels[status],
        "issues": issues,
        "database": database,
        "documentCount": document_count,
        "readyDocumentCount": ready_count,
        "failedDocumentCount": failed_count,
        "processingDocumentCount": processing_count,
        "chunkCount": chunk_count,
        "emptyEmbeddingCount": empty_embedding_count,
        "lastSyncedAt": last_synced_at,
    }


def overview_payload() -> dict:
    courses = list(courses_with_counts())
    points = list(knowledge_points_with_course())
    return {
        "courses": [course_payload(course) for course in courses],
        "knowledgePoints": [knowledge_point_payload(point) for point in points],
        "courseCount": len(courses),
        "knowledgePointCount": KnowledgePoint.objects.count(),
        "chunkCount": DocumentChunk.objects.count(),
        "documentCount": Document.objects.count(),
        "lastSyncedAt": latest_sync_string(),
        "indexHealth": index_health_payload(),
    }


def graph_data() -> dict:
    categories = list(GraphCategory.objects.order_by("sort_order", "id"))
    nodes = list(
        GraphNode.objects.select_related("category", "related_course")
        .order_by("sort_order", "id")
    )
    edges = list(
        GraphEdge.objects.select_related("source", "target").order_by("id")
    )
    return graph_payload(categories, nodes, edges)


def embed_missing_chunks() -> int:
    """Backfill local embeddings for imported/corrupt rows."""
    missing = list(DocumentChunk.objects.filter(embedding__isnull=True))
    if not missing:
        return 0
    result = local_embed([chunk.content for chunk in missing])
    for chunk, vector in zip(missing, result.vectors):
        chunk.embedding = vector
        chunk.embedding_provider = result.provider
        chunk.embedding_model = result.model
        chunk.embedding_dim = result.dim
        chunk.save(
            update_fields=[
                "embedding",
                "embedding_provider",
                "embedding_model",
                "embedding_dim",
            ]
        )
    return len(missing)
