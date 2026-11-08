"""Local retrieval quality smoke script.

Run from server/: python scripts/smoke_retrieval.py
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from apps.accounts.models import User
from apps.retrieval.services.search import RetrievalConfig, perform_retrieval

QUERIES = [
    "机器学习需要哪些前置知识？",
    "RAG 的完整检索链路是什么？",
    "Transformer 自注意力如何计算？",
    "梯度下降的学习率如何选择？",
    "生成AI工程师学习路线",
    "查询机器学习前置知识点",
]


def main() -> None:
    user = User.objects.filter(username="student").first()
    if not user:
        raise SystemExit("Seed the database first: manage.py seed_all --reset")
    for query in QUERIES:
        result = perform_retrieval(
            query,
            RetrievalConfig(top_k=5, threshold=0.0, retrieval_mode="hybrid"),
            user=user,
            source="rag_debug",
        )
        print(f"\nQUERY: {query}")
        print(
            "COUNT:",
            len(result["chunks"]),
            "CANDIDATES:",
            result["candidateCount"],
            "METRICS:",
            result["metrics"],
        )
        for item in result["_selected"][:5]:
            chunk = item["chunk"]
            print(
                f"  final={item['score']:.3f} dense={item['dense']:.3f} "
                f"raw={item['raw_cosine']:.3f} lexical={item['lexical']:.3f} "
                f"coverage={item['coverage']:.3f} | {chunk.knowledge_point.uid} | "
                f"{chunk.course.name} | {chunk.title}"
            )


if __name__ == "__main__":
    main()
