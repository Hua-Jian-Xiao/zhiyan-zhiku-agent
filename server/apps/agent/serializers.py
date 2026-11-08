from __future__ import annotations

from apps.knowledge.serializers import chunk_payload, to_epoch_ms

from .models import AgentRun, Citation, Message


def citation_payload(citation: Citation) -> dict:
    return {
        "id": citation.chunk.uid if citation.chunk else f"citation-{citation.id}",
        "index": citation.index_no,
        "knowledgePointId": citation.knowledge_point_uid,
        "title": citation.title,
        "course": citation.course_name,
        "source": citation.source_name,
        "chapter": citation.chapter,
        "snippet": citation.snippet,
        "score": round(citation.score, 3),
    }


def run_trace(run: AgentRun | None) -> dict | None:
    if run is None:
        return None
    return {
        "steps": [
            {
                "id": step.step_key,
                "title": step.title,
                "detail": step.detail,
                "status": step.status,
                "durationMs": step.duration_ms,
            }
            for step in run.steps.all()
        ],
        "tools": [
            {
                "id": tool.call_key,
                "name": tool.name,
                "label": tool.label,
                "status": tool.status,
                "input": tool.input_text,
                "output": tool.output_text,
                "durationMs": tool.duration_ms,
            }
            for tool in run.tools.all()
        ],
        "chunks": run.retrieval_snapshot or [],
    }


def message_payload(message: Message, run: AgentRun | None = None) -> dict:
    citations = []
    if run is not None:
        citations = [citation_payload(item) for item in run.citations.all()]
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "createdAt": to_epoch_ms(message.created_at),
        "status": message.status,
        "citations": citations,
        "trace": run_trace(run),
        "latencyMs": message.latency_ms,
        "stopped": message.stopped,
        "error": message.error or None,
    }


def conversation_payload(conversation) -> dict:
    messages = list(conversation.messages.all())
    runs = {
        run.message_id: run
        for run in AgentRun.objects.filter(message_id__in=[message.id for message in messages])
        .prefetch_related("steps", "tools", "citations")
        .order_by("started_at")
    }
    return {
        "id": conversation.id,
        "title": conversation.title,
        "createdAt": to_epoch_ms(conversation.created_at),
        "updatedAt": to_epoch_ms(conversation.updated_at),
        "messages": [message_payload(message, runs.get(message.id)) for message in messages],
    }


def stream_chunk(chunk: dict) -> dict:
    return chunk_payload_dict(chunk)


def chunk_payload_dict(chunk: dict) -> dict:
    """Pass through the already-serialized retrieval payload."""
    return chunk
