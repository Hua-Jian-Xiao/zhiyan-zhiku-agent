from __future__ import annotations

import re
from dataclasses import dataclass

TARGET_SIZE = 420
MAX_SIZE = 620
OVERLAP = 60
MIN_SIZE = 80


@dataclass
class ChunkDraft:
    title: str
    chapter: str
    content: str


def _segments(text: str) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    result: list[str] = []
    for paragraph in paragraphs:
        if len(paragraph) <= MAX_SIZE:
            result.append(paragraph)
            continue
        sentences = re.split(r"(?<=[。！？；.!?\n])", paragraph)
        buffer = ""
        for sentence in sentences:
            if not sentence:
                continue
            if len(buffer) + len(sentence) <= MAX_SIZE:
                buffer += sentence
            else:
                if buffer.strip():
                    result.append(buffer.strip())
                buffer = sentence
        if buffer.strip():
            result.append(buffer.strip())
    return result


def split_plain_text(
    text: str,
    title: str,
    chapter: str = "",
    target_size: int = TARGET_SIZE,
) -> list[ChunkDraft]:
    segments = _segments(text)
    drafts: list[ChunkDraft] = []
    buffer = ""
    for segment in segments:
        if not buffer:
            buffer = segment
        elif len(buffer) + len(segment) + 2 <= target_size:
            buffer = f"{buffer}\n\n{segment}"
        else:
            if len(buffer) >= MIN_SIZE:
                drafts.append(ChunkDraft(title=title, chapter=chapter, content=buffer.strip()))
            tail = buffer[-OVERLAP:] if len(buffer) > OVERLAP else ""
            buffer = f"{tail}\n\n{segment}".strip()
    if buffer.strip():
        drafts.append(
            ChunkDraft(title=title, chapter=chapter, content=buffer.strip())
        )
    return drafts


def chunk_markdown(
    text: str,
    document_title: str,
    *,
    course_name: str = "",
) -> list[ChunkDraft]:
    """Heading-aware chunking for seed documents and uploaded markdown."""
    lines = text.splitlines()
    chapter = ""
    section = ""
    buffer: list[str] = []
    drafts: list[ChunkDraft] = []

    def flush() -> None:
        nonlocal buffer
        body = "\n".join(buffer).strip()
        if not body:
            buffer = []
            return
        title = section or chapter or document_title
        chapter_label = chapter or "课程讲义"
        for draft in split_plain_text(body, title, chapter_label):
            drafts.append(draft)
        buffer = []

    for line in lines:
        if line.startswith("## ") and not line.startswith("### "):
            flush()
            chapter = line[3:].strip()
            section = ""
            continue
        if line.startswith("### "):
            flush()
            section = line[4:].strip()
            continue
        if line.startswith("# "):
            continue
        buffer.append(line)
    flush()

    if not drafts and text.strip():
        drafts = split_plain_text(text.strip(), document_title, course_name)
    return drafts
