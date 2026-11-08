from __future__ import annotations

import re
from pathlib import Path

from django.conf import settings


class ExtractionError(Exception):
    pass


def _clean(text: str) -> str:
    text = text.replace("﻿", "")
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    text = text.strip()
    if len(text) > settings.MAX_EXTRACTED_CHARS:
        raise ExtractionError("文档正文超过允许的最大长度")
    return text


def _decode_text(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ExtractionError("无法识别文本编码")


def extract_document(path: str | Path, source_type: str) -> str:
    file_path = Path(path)
    suffix = source_type.lower().lstrip(".")

    if suffix in {"txt", "md", "markdown"}:
        return _clean(_decode_text(file_path.read_bytes()))

    if suffix == "pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ExtractionError("服务器未安装 PDF 解析组件，请改用 TXT/Markdown") from exc
        reader = PdfReader(str(file_path))
        if len(reader.pages) > settings.MAX_PDF_PAGES:
            raise ExtractionError("PDF 页数超过允许上限")
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
        return _clean(text)

    if suffix == "docx":
        try:
            from docx import Document as DocxDocument
        except ImportError as exc:
            raise ExtractionError("服务器未安装 DOCX 解析组件，请改用 TXT/Markdown") from exc
        document = DocxDocument(str(file_path))
        parts = [paragraph.text for paragraph in document.paragraphs]
        for table in document.tables:
            for row in table.rows:
                parts.append(" | ".join(cell.text for cell in row.cells))
        return _clean("\n".join(parts))

    raise ExtractionError("仅支持 TXT、Markdown、PDF、DOCX 文档")
