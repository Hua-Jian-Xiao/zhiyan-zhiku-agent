from __future__ import annotations

import re
import time


def detect_intent(query: str) -> str:
    if re.search(r"(学习路线|成长路线|路线图|AI\s*工程师|从零到|学习路径)", query, re.I):
        return "roadmap"
    if re.search(r"(前置|先修|依赖|先学什么|先掌握)", query):
        return "prerequisite"
    if re.search(r"(rag|检索增强|向量检索)", query, re.I):
        return "rag"
    if re.search(r"(transformer|自注意力|self-attention|注意力机制)", query, re.I):
        return "transformer"
    return "general"


def _ref(citations: list[dict], index: int) -> str:
    return f" [{index}]" if len(citations) >= index else ""


def _evidence_lines(chunks: list[dict], limit: int = 3) -> list[str]:
    lines = []
    for index, chunk in enumerate(chunks[:limit], start=1):
        lines.append(
            f"- **{chunk.get('title', '知识片段')}**（{chunk.get('course', '课程')}，"
            f"{chunk.get('knowledgePointId', 'KP')}）：{chunk.get('content', '')[:140]}… [{index}]"
        )
    return lines


def build_fallback_answer(query: str, chunks: list[dict]) -> str:
    intent = detect_intent(query)
    refs = _evidence_lines(chunks)

    if not chunks:
        return (
            "## 当前知识库没有足够证据\n\n"
            "本次检索没有召回达到阈值的知识片段，因此我不会脱离课程资料编造答案。\n\n"
            "### 建议\n"
            "1. 在知识库管理中适当降低相似度阈值；\n"
            "2. 使用更具体的课程术语，例如「RAG 召回与重排序」；\n"
            "3. 在 RAG 检索调试中切换到混合检索观察候选片段。"
        )

    if intent == "roadmap":
        return "\n".join(
            [
                "## AI 工程师学习路线",
                "",
                "以下路线以本次检索到的课程证据为基础，建议按依赖顺序推进：",
                "",
                "### 阶段一：数理与编程地基",
                "掌握 Python、NumPy、线性代数、概率统计与微积分。重点不是刷题，而是能解释矩阵、梯度和概率分布如何进入模型。",
                "",
                "### 阶段二：机器学习与评估",
                f"从监督学习、损失函数与泛化评估开始，再进入梯度优化和集成学习。{_ref(chunks, 1)}",
                refs[0] if refs else "",
                "",
                "### 阶段三：深度学习与模型结构",
                "学习反向传播、卷积网络与序列建模，随后理解 Transformer 的自注意力机制。",
                "",
                "### 阶段四：RAG 工程实践",
                "围绕课程知识库完成文档入库、混合召回、重排序、引用约束与评测闭环，并记录检索耗时和引用覆盖率。",
                "",
                "### 学习建议",
                "- 每周保持一次完整的小项目复盘；",
                "- 先建立评估集，再调参数；",
                "- 每个结论都回到课程原文确认。",
                "",
                "> 该回答由本地检索兜底生成，引用编号与本次召回片段一致。",
            ]
        )

    if intent == "prerequisite":
        return "\n".join(
            [
                "## 机器学习的先修知识",
                "",
                "机器学习依赖一条相对稳定的知识链：",
                "",
                "```text",
                "Python / NumPy → 微积分 + 线性代数 + 概率论 → 最优化 → 机器学习",
                "```",
                "",
                "### 1. 编程与数据处理",
                "需要掌握 Python 语法、数组形状、广播与向量化运算，否则大部分时间会耗在数据搬运上。",
                "",
                "### 2. 数学基础",
                "线性代数用于理解特征空间和矩阵分解；概率统计用于建模不确定性；微积分提供梯度与链式法则。",
                "",
                "### 3. 最优化与模型评估",
                "理解梯度下降、学习率、过拟合与交叉验证，才能对训练结果做出可靠判断。",
                "",
                "### 证据摘录",
                *refs,
                "",
                f"建议先完成「线性代数 + 概率统计 + Python」，再进入机器学习。{_ref(chunks, 1)}",
            ]
        )

    if intent == "rag":
        return "\n".join(
            [
                "## RAG 检索增强生成",
                "",
                "RAG 把外部知识检索与生成模型结合，目标是让回答具备事实依据和可追溯引用。",
                "",
                "### 完整链路",
                "1. 文档解析与语义切分；",
                "2. 向量化与索引构建；",
                "3. 向量召回与关键词召回；",
                "4. 重排序与上下文组装；",
                "5. 带引用约束的流式生成。",
                "",
                "### 本次证据",
                *refs,
                "",
                "切换检索模式时，关键词检索更依赖术语命中，向量检索更依赖语义相似度；混合检索通常更稳定。",
            ]
        )

    if intent == "transformer":
        return "\n".join(
            [
                "## 用直觉理解自注意力",
                "",
                "自注意力回答的问题是：序列中的每个词，应该从其他词那里获取哪些信息？",
                "",
                "Query 是检索需求，Key 是其他位置的索引，Value 是真正被汇总的内容。Q 与 K 点积得到相关性，softmax 归一化后对 V 加权求和。",
                "",
                "### 证据摘录",
                *refs,
                "",
                "多头注意力在多个子空间并行建模关系；位置编码补足顺序信息；残差连接与层归一化保证深层训练稳定。",
            ]
        )

    return "\n".join(
        [
            "## 核心回答",
            "",
            f"关于「{query}」，本次从课程知识库召回了 {len(chunks)} 条相关证据。",
            "",
            "### 证据摘要",
            *refs,
            "",
            "### 学习建议",
            "- 先回到引用片段确认关键定义；",
            "- 用课程知识图谱补齐全前置关系；",
            "- 在小规模实验中验证你的理解，再扩展到大模型应用。",
            "",
            "> 当前回答由本地模板兜底生成，未调用外部大模型。",
        ]
    ).strip()


def stream_fallback(query: str, chunks: list[dict]):
    answer = build_fallback_answer(query, chunks)
    for start in range(0, len(answer), 6):
        yield answer[start : start + 6]
        time.sleep(0.008)
