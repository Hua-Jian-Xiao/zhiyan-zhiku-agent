from __future__ import annotations

import json
import logging
import time

from django.conf import settings
from django.utils import timezone

from apps.agent.models import (
    AgentRun,
    AgentStep,
    Citation,
    Conversation,
    Message,
    ToolCall,
)
from apps.retrieval.services.search import (
    config_payload,
    perform_retrieval,
)

from .fallback import detect_intent, stream_fallback
from .llm import llm_configured, stream_llm_answer

logger = logging.getLogger(__name__)


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def _citation_payloads(selected: list[dict]) -> list[dict]:
    citations = []
    for index, item in enumerate(selected[:4], start=1):
        chunk = item["chunk"]
        point = chunk.knowledge_point
        citations.append(
            {
                "id": chunk.uid,
                "index": index,
                "knowledgePointId": point.uid if point else "",
                "title": chunk.title,
                "course": chunk.course.name,
                "source": chunk.source_name,
                "chapter": chunk.chapter,
                "snippet": chunk.content,
                "score": round(item["score"], 3),
            }
        )
    return citations


def _step(run: AgentRun, key: str, title: str, detail: str, status: str, duration_ms=None, order=0):
    AgentStep.objects.update_or_create(
        run=run,
        step_key=key,
        defaults={
            "title": title,
            "detail": detail,
            "status": status,
            "duration_ms": duration_ms,
            "sort_order": order,
        },
    )


def _tool(
    run: AgentRun,
    key: str,
    name: str,
    label: str,
    input_text: str,
    output_text: str,
    status: str,
    duration_ms=None,
    order=0,
):
    ToolCall.objects.update_or_create(
        run=run,
        call_key=key,
        defaults={
            "name": name,
            "label": label,
            "input_text": input_text,
            "output_text": output_text,
            "status": status,
            "duration_ms": duration_ms,
            "sort_order": order,
        },
    )


def _persist_final(
    *,
    conversation: Conversation,
    message: Message,
    run: AgentRun,
    content: str,
    retrieval_chunks: list[dict],
    selected: list[dict],
    cited_count: int,
    latency_ms: int,
    status: str = "done",
    error: str = "",
    stopped: bool = False,
):
    message.content = content
    message.status = "error" if status == "error" else "done"
    message.latency_ms = latency_ms
    message.stopped = stopped
    message.error = error
    message.save(
        update_fields=["content", "status", "latency_ms", "stopped", "error"]
    )

    run.status = status
    run.finished_at = timezone.now()
    run.latency_ms = latency_ms
    run.cited_count = cited_count
    run.retrieval_snapshot = retrieval_chunks
    run.error = error
    run.save(
        update_fields=[
            "status",
            "finished_at",
            "latency_ms",
            "cited_count",
            "retrieval_snapshot",
            "error",
        ]
    )

    Citation.objects.filter(message=message).delete()
    citation_rows = []
    chunk_map = {item["chunk"].uid: item["chunk"] for item in selected}
    for citation in _citation_payloads(selected):
        citation_rows.append(
            Citation(
                message=message,
                run=run,
                chunk=chunk_map.get(citation["id"]),
                index_no=citation["index"],
                knowledge_point_uid=citation["knowledgePointId"],
                title=citation["title"],
                course_name=citation["course"],
                source_name=citation["source"],
                chapter=citation["chapter"],
                snippet=citation["snippet"],
                score=citation["score"],
            )
        )
    if citation_rows:
        Citation.objects.bulk_create(citation_rows)

    conversation.updated_at = timezone.now()
    conversation.save(update_fields=["updated_at"])


def run_agent_stream(
    *,
    user,
    conversation: Conversation,
    user_message: Message,
    assistant_message: Message,
    query: str,
    config,
    request_id: str = "",
    history: list[dict] | None = None,
):
    started = time.perf_counter()
    run = AgentRun.objects.create(
        id=f"run_{request_id or int(time.time() * 1000)}",
        conversation=conversation,
        message=assistant_message,
        user=user,
        query=query,
        top_k=config.top_k,
        threshold=config.threshold,
        retrieval_mode=config.retrieval_mode,
        status="running",
        provider="deepseek" if llm_configured() else "local-template",
        model=settings.DEEPSEEK_MODEL if llm_configured() else "retrieval-template",
        config_snapshot=config_payload(config),
    )

    content_parts: list[str] = []
    retrieval_chunks: list[dict] = []
    selected: list[dict] = []
    citation_data: list[dict] = []
    completed = False
    had_error = False
    first_token_emitted = False

    def persist(status: str, error: str = "", stopped: bool = False):
        content = "".join(content_parts)
        _persist_final(
            conversation=conversation,
            message=assistant_message,
            run=run,
            content=content,
            retrieval_chunks=retrieval_chunks,
            selected=selected,
            cited_count=len(citation_data),
            latency_ms=_elapsed_ms(started),
            status=status,
            error=error,
            stopped=stopped,
        )

    try:
        intent = detect_intent(query)
        intent_label = {
            "roadmap": "学习路线规划",
            "prerequisite": "先修依赖查询",
            "rag": "RAG 概念解释",
            "transformer": "模型机制解释",
            "general": "学科知识问答",
        }.get(intent, "学科知识问答")

        _step(run, "intent", "理解问题", f"正在识别问题意图：{intent_label}", "running", order=1)
        yield sse(
            "step",
            {
                "id": "intent",
                "title": "理解问题",
                "detail": f"正在识别问题意图：{intent_label}",
                "status": "running",
            },
        )
        time.sleep(0.12)
        _step(run, "intent", "理解问题", f"识别为「{intent_label}」", "done", 120, order=1)
        yield sse(
            "step",
            {
                "id": "intent",
                "title": "理解问题",
                "detail": f"识别为「{intent_label}」，拆解为检索子问题",
                "status": "done",
                "durationMs": 120,
            },
        )

        search_input = (
            f'query: "{query[:60]}" · mode: {config.retrieval_mode} · '
            f"top_k: {config.top_k} · threshold: {config.threshold:.2f}"
        )
        _tool(run, "tool-semantic-search", "knowledge_base.hybrid_search", "知识库混合检索", search_input, "正在召回课程知识片段…", "running", order=1)
        yield sse(
            "tool",
            {
                "id": "tool-semantic-search",
                "name": "knowledge_base.hybrid_search",
                "label": "知识库混合检索",
                "status": "running",
                "input": search_input,
                "output": "正在召回课程知识片段…",
            },
        )
        _step(run, "retrieve", "检索知识库", "正在执行混合检索", "running", order=2)
        yield sse(
            "step",
            {
                "id": "retrieve",
                "title": "检索知识库",
                "detail": "正在以向量与关键词混合方式检索课程知识库",
                "status": "running",
            },
        )

        retrieval = perform_retrieval(
            query,
            config,
            user=user,
            source="agent",
            conversation_uid=conversation.id,
            message_uid=assistant_message.id,
        )
        retrieval_chunks = retrieval["chunks"]
        selected = retrieval["_selected"]
        citation_data = _citation_payloads(selected)
        retrieval["_selected"] = selected
        retrieval_metrics = retrieval["metrics"]

        search_output = (
            f"召回 {len(retrieval_chunks)} 条片段，候选 {retrieval['candidateCount']} 条，"
            f"最高相似度 {retrieval_chunks[0]['score'] if retrieval_chunks else 0:.3f}"
        )
        _tool(
            run,
            "tool-semantic-search",
            "knowledge_base.hybrid_search",
            "知识库混合检索",
            search_input,
            search_output,
            "done",
            retrieval_metrics["embeddingMs"] + retrieval_metrics["searchMs"],
            order=1,
        )
        yield sse(
            "tool",
            {
                "id": "tool-semantic-search",
                "name": "knowledge_base.hybrid_search",
                "label": "知识库混合检索",
                "status": "done",
                "input": search_input,
                "output": search_output,
                "durationMs": retrieval_metrics["embeddingMs"] + retrieval_metrics["searchMs"],
            },
        )
        _step(
            run,
            "retrieve",
            "检索知识库",
            f"命中 {len(retrieval_chunks)} 条候选片段",
            "done",
            retrieval_metrics["embeddingMs"] + retrieval_metrics["searchMs"],
            order=2,
        )
        yield sse(
            "step",
            {
                "id": "retrieve",
                "title": "检索知识库",
                "detail": f"命中 {len(retrieval_chunks)} 条候选片段，覆盖 {len({chunk['course'] for chunk in retrieval_chunks})} 门课程",
                "status": "done",
                "durationMs": retrieval_metrics["embeddingMs"] + retrieval_metrics["searchMs"],
            },
        )
        yield sse("retrieval", retrieval_chunks)

        rerank_input = f"candidates: {len(retrieval_chunks)} · strategy: hybrid-rerank"
        _tool(run, "tool-rerank", "context.rerank", "证据重排", rerank_input, "正在按标题、标签与语义覆盖率重排…", "running", order=2)
        yield sse(
            "tool",
            {
                "id": "tool-rerank",
                "name": "context.rerank",
                "label": "证据重排",
                "status": "running",
                "input": rerank_input,
                "output": "正在按标题、标签与语义覆盖率重排…",
            },
        )
        _step(run, "rerank", "证据重排", "按知识结构与语义相关性筛选证据", "running", order=3)
        yield sse(
            "step",
            {
                "id": "rerank",
                "title": "证据重排",
                "detail": "按知识结构与语义相关性筛选证据",
                "status": "running",
            },
        )
        time.sleep(0.1)
        _step(
            run,
            "rerank",
            "证据重排",
            f"保留 {len(retrieval_chunks)} 条高置信证据",
            "done",
            retrieval_metrics["rerankMs"],
            order=3,
        )
        yield sse(
            "step",
            {
                "id": "rerank",
                "title": "证据重排",
                "detail": f"保留 {len(retrieval_chunks)} 条高置信证据，生成 {len(citation_data)} 条引用",
                "status": "done",
                "durationMs": retrieval_metrics["rerankMs"],
            },
        )
        _tool(
            run,
            "tool-rerank",
            "context.rerank",
            "证据重排",
            rerank_input,
            f"完成重排，生成 {len(citation_data)} 条可引用来源",
            "done",
            retrieval_metrics["rerankMs"],
            order=2,
        )
        yield sse(
            "tool",
            {
                "id": "tool-rerank",
                "name": "context.rerank",
                "label": "证据重排",
                "status": "done",
                "input": rerank_input,
                "output": f"完成重排，生成 {len(citation_data)} 条可引用来源",
                "durationMs": retrieval_metrics["rerankMs"],
            },
        )
        yield sse("citations", citation_data)

        _step(run, "compose", "组织回答", "正在基于证据生成带引用标记的回答", "running", order=4)
        yield sse(
            "step",
            {
                "id": "compose",
                "title": "组织回答",
                "detail": "正在基于证据生成带引用标记的回答",
                "status": "running",
            },
        )

        provider = "deepseek" if llm_configured() else "local-template"
        model = settings.DEEPSEEK_MODEL if llm_configured() else "retrieval-template"
        token_stream = None
        if llm_configured():
            try:
                token_stream = stream_llm_answer(query, retrieval_chunks, history or [])
                first = next(token_stream)
                first_token_emitted = True
                content_parts.append(first)
                yield sse("delta", {"text": first})
                for token in token_stream:
                    content_parts.append(token)
                    yield sse("delta", {"text": token})
            except Exception as exc:
                logger.warning("DeepSeek streaming unavailable: %s", type(exc).__name__)
                if first_token_emitted:
                    raise
                provider = "local-template"
                model = "retrieval-template"
                for token in stream_fallback(query, retrieval_chunks):
                    content_parts.append(token)
                    yield sse("delta", {"text": token})
        else:
            for token in stream_fallback(query, retrieval_chunks):
                content_parts.append(token)
                yield sse("delta", {"text": token})

        run.provider = provider
        run.model = model
        run.retrieval_log = retrieval["_log"]
        run.save(update_fields=["provider", "model", "retrieval_log"])
        _step(
            run,
            "compose",
            "组织回答",
            f"回答生成完成，已绑定 {len(citation_data)} 条知识库引用",
            "done",
            _elapsed_ms(started),
            order=4,
        )
        yield sse(
            "step",
            {
                "id": "compose",
                "title": "组织回答",
                "detail": f"回答生成完成，已绑定 {len(citation_data)} 条知识库引用",
                "status": "done",
                "durationMs": _elapsed_ms(started),
            },
        )
        completed = True
        persist("done")
        latency_ms = _elapsed_ms(started)
        yield sse(
            "done",
            {
                "citedCount": len(citation_data),
                "latencyMs": latency_ms,
                "messageId": assistant_message.id,
                "runId": run.id,
                "conversationId": conversation.id,
                "title": conversation.title,
            },
        )
    except GeneratorExit:
        if not completed:
            persist("stopped", stopped=True)
        raise
    except Exception as exc:
        had_error = True
        logger.exception("Agent stream failed: %s", exc)
        error_message = "回答生成失败，请检查检索配置或稍后重试"
        persist("error", error=error_message)
        yield sse("error", {"message": error_message, "code": "AGENT_STREAM_ERROR", "retryable": True})
    finally:
        if not completed and not had_error:
            try:
                persist("stopped", stopped=True)
            except Exception:
                logger.exception("Failed to persist stopped agent message")
