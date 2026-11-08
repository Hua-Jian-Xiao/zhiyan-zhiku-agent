from __future__ import annotations

import logging

from django.conf import settings

from .prompts import build_messages

logger = logging.getLogger(__name__)


class LLMUnavailable(Exception):
    pass


def llm_configured() -> bool:
    provider = getattr(settings, "LLM_PROVIDER", "deepseek").lower()
    return provider != "local" and bool(getattr(settings, "DEEPSEEK_API_KEY", ""))


def stream_llm_answer(query: str, chunks: list[dict], history: list[dict]):
    if not llm_configured():
        raise LLMUnavailable("DeepSeek API key is not configured")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LLMUnavailable("openai package is not installed") from exc

    client = OpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        timeout=settings.LLM_TIMEOUT_SECONDS,
        max_retries=1,
    )
    stream = client.chat.completions.create(
        model=settings.DEEPSEEK_MODEL,
        messages=build_messages(query, chunks, history),
        temperature=0.3,
        max_tokens=settings.LLM_MAX_TOKENS,
        stream=True,
    )
    emitted = False
    for event in stream:
        if not event.choices:
            continue
        delta = event.choices[0].delta
        text = getattr(delta, "content", None)
        if text:
            emitted = True
            yield text
    if not emitted:
        raise LLMUnavailable("The model returned an empty response")
