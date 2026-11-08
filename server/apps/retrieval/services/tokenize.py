from __future__ import annotations

import re
import unicodedata
from collections import Counter

CJK_RUN = re.compile(r"[㐀-鿿]+")
LATIN_WORD = re.compile(r"[a-zA-Z][a-zA-Z0-9_+#.-]{1,}|[0-9]{2,}")
STOP_WORDS = {
    "的", "了", "和", "与", "是", "在", "有", "为", "被", "把", "中", "对",
    "及", "等", "并", "或", "一个", "一种", "可以", "需要", "通过", "进行",
    "the", "and", "for", "with", "from", "that", "this", "are", "is", "of",
}


def normalize_text(text: str) -> str:
    return unicodedata.normalize("NFKC", text).lower()


def search_tokens(text: str) -> list[str]:
    normalized = normalize_text(text)
    tokens: list[str] = []
    for run in CJK_RUN.findall(normalized):
        if len(run) == 1:
            if run not in STOP_WORDS:
                tokens.append(run)
            continue
        for index in range(len(run) - 1):
            token = run[index : index + 2]
            if token not in STOP_WORDS:
                tokens.append(token)
    for word in LATIN_WORD.findall(normalized):
        if word not in STOP_WORDS:
            tokens.append(word)
    return tokens


def token_counts(text: str) -> dict[str, int]:
    return dict(Counter(search_tokens(text)))
