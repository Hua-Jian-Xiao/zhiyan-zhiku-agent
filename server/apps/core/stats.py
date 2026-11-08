from django.db import connection
from django.utils import timezone

from apps.knowledge.models import Course, Document, DocumentChunk, GraphEdge, GraphNode, KnowledgePoint


def local_datetime_string(value) -> str:
    if not value:
        return "—"
    return timezone.localtime(value).strftime("%Y-%m-%d %H:%M")


def public_stats() -> dict:
    last_document = (
        Document.objects.filter(status="ready").order_by("-updated_at").first()
    )
    return {
        "courseCount": Course.objects.count(),
        "knowledgePointCount": KnowledgePoint.objects.count(),
        "chunkCount": DocumentChunk.objects.count(),
        "documentCount": Document.objects.count(),
        "graphNodeCount": GraphNode.objects.count(),
        "graphEdgeCount": GraphEdge.objects.count(),
        "lastSyncedAt": local_datetime_string(
            last_document.updated_at if last_document else timezone.now()
        ),
    }


def health_payload() -> dict:
    from django.conf import settings

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        database = "ok"
    except Exception:
        database = "error"

    has_key = bool(getattr(settings, "DEEPSEEK_API_KEY", ""))
    llm_enabled = getattr(settings, "LLM_PROVIDER", "deepseek").lower() != "local" and has_key
    return {
        "status": "ok" if database == "ok" else "degraded",
        "database": database,
        "llm": {
            "configured": llm_enabled,
            "provider": "deepseek" if llm_enabled else "local-fallback",
            "model": getattr(settings, "DEEPSEEK_MODEL", "deepseek-chat") if llm_enabled else "local-template",
        },
        "embedding": {
            "provider": getattr(settings, "EMBEDDING_PROVIDER", "local"),
            "dim": getattr(settings, "EMBEDDING_DIM", 384),
        },
        "version": "1.0.0",
    }
