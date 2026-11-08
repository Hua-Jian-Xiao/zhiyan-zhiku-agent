from __future__ import annotations

from django.db.models import Count
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
