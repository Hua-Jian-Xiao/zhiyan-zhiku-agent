"""Small retrieval smoke check using the exact UI quick prompts."""
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
    "请为我生成一份从零到 AI 工程师的系统学习路线，包含阶段目标与推荐资料。",
    "查询机器学习的前置知识点，并按依赖顺序告诉我应该先学什么。",
    "请用直观的例子解释 Transformer 的自注意力机制，并说明它解决了什么问题。",
    "请设计一套面向课程知识库的 RAG 方案，说明切分、召回、重排与评估策略。",
    "RAG 的完整检索链路是什么？",
]


def main() -> None:
    user = User.objects.get(username="student")
    for query in QUERIES:
        result = perform_retrieval(
            query,
            RetrievalConfig(top_k=5, threshold=0.0, retrieval_mode="hybrid"),
            user=user,
            source="rag_debug",
        )
        print("\nQUERY:", query)
        for item in result["_selected"][:5]:
            print(
                f"  final={item['score']:.3f} dense={item['dense']:.3f} "
                f"lex={item['lexical']:.3f} cov={item['coverage']:.3f} "
                f"{item['chunk'].knowledge_point.uid} {item['chunk'].title}"
            )


if __name__ == "__main__":
    main()
