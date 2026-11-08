import type { AgentStep, AgentTrace, Citation, RetrievedChunk, ToolCall } from '@/types'
import { delay, isAbortError } from '@/utils/async'
import { rankKnowledgeChunks } from '@/utils/retrieval'
import { truncate } from '@/utils/format'

export interface AgentStreamRequest {
  query: string
  topK: number
  threshold: number
}

type AgentIntent = 'roadmap' | 'prerequisite' | 'rag' | 'transformer' | 'general'

interface AgentSsePayloadMap {
  step: AgentStep
  tool: ToolCall
  retrieval: RetrievedChunk[]
  citations: Citation[]
  delta: { text: string }
  done: { citedCount: number }
}

const encoder = new TextEncoder()

export function createInitialTrace(): AgentTrace {
  return {
    steps: [
      {
        id: 'intent',
        title: '理解问题',
        detail: '等待识别问题意图与知识范围',
        status: 'pending',
      },
      {
        id: 'retrieve',
        title: '检索知识库',
        detail: '等待执行语义检索',
        status: 'pending',
      },
      {
        id: 'rerank',
        title: '证据重排',
        detail: '等待对候选片段进行相关性重排',
        status: 'pending',
      },
      {
        id: 'compose',
        title: '组织回答',
        detail: '等待基于证据生成可溯源回答',
        status: 'pending',
      },
    ],
    tools: [],
    chunks: [],
  }
}

export function toCitations(chunks: RetrievedChunk[]): Citation[] {
  return chunks.slice(0, 4).map((chunk, index) => ({
    id: chunk.id,
    index: index + 1,
    title: chunk.title,
    course: chunk.course,
    source: chunk.source,
    chapter: chunk.chapter,
    snippet: chunk.content,
    score: chunk.score,
  }))
}

function detectIntent(query: string): AgentIntent {
  if (/(学习路线|成长路线|路线图|AI\s*工程师|从零到|学习路径)/i.test(query)) return 'roadmap'
  if (/(前置|先修|依赖|先学什么|先掌握)/.test(query)) return 'prerequisite'
  if (/(rag|检索增强|向量检索)/i.test(query)) return 'rag'
  if (/(transformer|自注意力|self-attention|注意力机制)/i.test(query)) return 'transformer'
  return 'general'
}

function intentLabel(intent: AgentIntent): string {
  const labels: Record<AgentIntent, string> = {
    roadmap: '学习路线规划',
    prerequisite: '先修依赖查询',
    rag: 'RAG 概念解释',
    transformer: '模型机制解释',
    general: '学科知识问答',
  }
  return labels[intent]
}

function buildNoEvidenceAnswer(request: AgentStreamRequest): string {
  return [
    '## 暂时没有足够的检索证据',
    '',
    `我在当前知识库中以相似度阈值 **${request.threshold.toFixed(2)}** 检索了「${truncate(
      request.query,
      44,
    )}」，没有命中达到阈值的知识片段。`,
    '',
    '### 可以尝试',
    '1. 前往 **知识库管理**，将相似度阈值调整到 `0.70` 附近；',
    '2. 使用更具体的课程术语，例如「监督学习 泛化误差」而不是泛泛的提问；',
    '3. 打开 **RAG 检索调试**，观察不同阈值下的召回分布。',
    '',
    '> 为保证答案可追溯，我不会在缺少知识库证据时编造引用。你可以降低阈值后重新提问。',
  ].join('\n')
}

function buildAnswer(
  intent: AgentIntent,
  request: AgentStreamRequest,
  chunks: RetrievedChunk[],
  citations: Citation[],
): string {
  if (chunks.length === 0) return buildNoEvidenceAnswer(request)

  const citationFor = (chunkId: string): string => {
    const citation = citations.find((item) => item.id === chunkId)
    return citation ? ` [${citation.index}]` : ''
  }

  if (intent === 'roadmap') {
    return [
      '## AI 工程师成长路线',
      '',
      `基于知识库中 **${chunks.length}** 条高相关课程资料，我把从零到可独立完成 RAG 应用的路径拆成 4 个阶段。建议每周投入 8–12 小时，以「小项目驱动」推进。`,
      '',
      '### 路线总览',
      '',
      '| 阶段 | 建议周期 | 核心任务 | 阶段验收 |',
      '| --- | --- | --- | --- |',
      '| ① 数理与编程地基 | 4–6 周 | Python、NumPy、线性代数、概率统计 | 手写梯度下降并完成一次线性回归 |',
      '| ② 机器学习核心 | 6–8 周 | 监督学习、损失函数、模型评估 | 独立完成一个完整的表格数据项目 |',
      '| ③ 深度学习与 NLP | 8–10 周 | 反向传播、Transformer、预训练模型 | 读懂并微调一个小型 Transformer |',
      '| ④ RAG 工程实战 | 4–6 周 | 检索、重排、提示模板、评测与引用 | 构建带引用溯源的课程问答应用 |',
      '',
      '### 阶段一：先把地基打牢',
      '',
      `- **Python 与 NumPy**：掌握 ndarray、广播机制与向量化，能独立完成数据清洗和特征工程${citationFor(
        'chunk-python-numpy',
      )}。`,
      `- **线性代数**：重点理解矩阵乘法、特征值与 SVD，它们是降维和表示学习的共同语言${citationFor(
        'chunk-math-linear',
      )}。`,
      `- **概率统计**：条件概率、贝叶斯公式与常见分布，是理解模型不确定性的起点${citationFor(
        'chunk-prob-bayes',
      )}。`,
      '',
      '### 阶段二：建立机器学习直觉',
      '',
      `先从监督学习的问题形式化开始：输入空间、假设空间、损失函数与泛化误差${citationFor(
        'chunk-ml-supervised',
      )}。随后用梯度下降打通「模型—损失—优化」的闭环${citationFor(
        'chunk-ml-gradient',
      )}，并通过交叉验证建立可靠的模型评估习惯。`,
      '',
      '### 阶段三：进入深度学习与 NLP',
      '',
      '把反向传播、优化器和正则化吃透后，再学习序列建模与 Transformer。不要只停留在调用 API，至少手写一次缩放点积注意力，并画出 Q、K、V 的数据流。',
      '',
      '### 阶段四：完成一个可展示的 RAG 项目',
      '',
      '选择一个你熟悉的课程知识库，完成文档切分、向量召回、重排、上下文拼装和引用展示。最后用固定测试集评估召回率与答案忠实度，这比单纯展示 Demo 更有说服力。',
      '',
      '### 每周节奏建议',
      '',
      '1. **2 次概念学习**：每次 90 分钟，输出一页自己的图解笔记。',
      '2. **1 次编码练习**：优先复现核心算法，而不是照抄 Notebook。',
      '3. **1 次复盘**：记录失败案例，并回看知识图谱中的前置依赖。',
      '',
      '> 路线是参考而非约束。如果你已有编程基础，可以直接从阶段二的模型评估切入，再按缺口补齐数学知识。',
      '',
      '需要的话，我可以继续为你展开任意阶段的 **4 周学习清单**，或为「RAG 课程问答助手」拆解项目里程碑。',
    ].join('\n')
  }

  if (intent === 'prerequisite') {
    return [
      '## 机器学习的前置知识',
      '',
      '机器学习不是一个孤立的算法集合。为了能真正理解推导、调参与评估，建议先完成下面这条客观依赖链：',
      '',
      '```text',
      'Python / NumPy',
      '        ↓',
      '微积分 + 线性代数 + 概率论',
      '        ↓',
      '最优化方法',
      '        ↓',
      '机器学习',
      '```',
      '',
      '### 1. 编程与数据处理',
      '',
      `至少熟练掌握 Python 基础语法、函数、类，以及 NumPy 的数组形状、广播与向量化运算${citationFor(
        'chunk-python-numpy',
      )}。否则你会把大量时间耗在数据处理上，而不是理解模型。`,
      '',
      '### 2. 数学基础',
      '',
      `- **线性代数**：矩阵乘法、秩、特征值与 SVD。它们解释了特征表示、降维与神经网络层的本质${citationFor(
        'chunk-math-linear',
      )}。`,
      `- **概率统计**：随机变量、条件概率、贝叶斯公式和常见分布。它们是建模不确定性与评估泛化能力的语言${citationFor(
        'chunk-prob-bayes',
      )}。`,
      '- **微积分**：偏导、链式法则与泰勒展开。理解梯度如何传播，才能理解模型如何学习。',
      '',
      '### 3. 最优化基础',
      '',
      `理解目标函数、凸性与约束，再进入梯度下降、学习率和随机梯度的实践${citationFor(
        'chunk-ml-gradient',
      )}。重点不是背公式，而是知道学习率过大与过小分别会造成什么现象。`,
      '',
      '### 4. 算法思维',
      '',
      '复杂度分析和基础数据结构会直接影响你处理大规模特征、构建检索索引的效率。建议至少熟悉哈希表、堆、树与图遍历。',
      '',
      '### 推荐学习顺序',
      '',
      '| 顺序 | 内容 | 建议投入 | 达标信号 |',
      '| --- | --- | --- | --- |',
      '| 1 | Python + NumPy | 2–3 周 | 能向量化实现标准化、独热编码 |',
      '| 2 | 线性代数 + 概率 | 4–6 周 | 能手推 PCA 与贝叶斯分类的直觉 |',
      '| 3 | 微积分 + 优化 | 2–4 周 | 能解释学习率对收敛的影响 |',
      '| 4 | 机器学习 | 6–8 周 | 能独立完成端到端建模与评估 |',
      '',
      '> 如果你只有两周时间，建议优先补「Python + 线性代数」，然后在实践中边学概率与微积分。',
      '',
      '你可以继续问我某一个前置知识点的 **最小学习清单**，或让我对照你的已有基础做一次差距分析。',
    ].join('\n')
  }

  if (intent === 'rag') {
    return [
      '## RAG 的完整检索链路',
      '',
      `RAG（Retrieval-Augmented Generation）把外部知识检索与生成模型结合，目标是让回答具备事实依据与可追溯引用${citationFor(
        'chunk-rag-pipeline',
      )}。一个可评测的链路通常包含五个阶段：`,
      '',
      '### 1. 文档处理与切分',
      '',
      '先清理格式、保留章节结构，再按语义边界切块。块过大会降低召回精度，块过小会丢失上下文。实践中应保留 `标题 + 章节 + 正文` 的元数据，方便引用溯源。',
      '',
      '### 2. 向量化与索引',
      '',
      '将片段编码为向量并建立近似最近邻索引。中文学科语料建议同时保留关键词检索能力，用混合召回弥补纯向量的语义漂移。',
      '',
      '### 3. 多路召回',
      '',
      '按相似度阈值筛掉低置信候选，再取 Top-K 片段。阈值不是越低越好：过低的阈值会把噪声带进上下文，反而增加幻觉。',
      '',
      '### 4. 重排序与上下文组装',
      '',
      '使用交叉编码器或规则重排候选片段，并按相关性、章节完整性和冗余度组装上下文。给每个片段编号，要求模型在回答中显式引用。',
      '',
      '### 5. 生成与评估',
      '',
      '除了答案质量，还要评估 **召回率、引用覆盖率与忠实度**。针对没有足够证据的问题，系统应明确说「不知道」，而不是强行生成。',
      '',
      '### 设计时最容易被忽略的三件事',
      '',
      '1. **知识库更新策略**：课程文档更新后，旧索引需要重新构建。',
      '2. **引用一致性**：引用编号必须与最终上下文真实对应。',
      '3. **阈值与问题类型联动**：概念题和精确事实题不应共用同一套阈值。',
      '',
      '如果你在做课程知识库问答，我可以继续帮你设计一套 **可量化的 RAG 评测集**。',
    ].join('\n')
  }

  if (intent === 'transformer') {
    return [
      '## 用直觉理解 Transformer 自注意力',
      '',
      `自注意力的核心问题是：**序列中的每个词，应该从其他哪些词那里获取信息？** 它通过 Query、Key、Value 三组向量完成这件事${citationFor(
        'chunk-dl-transformer',
      )}。`,
      '',
      '### 一个图书馆类比',
      '',
      '| 角色 | 类比 | 在注意力中的含义 |',
      '| --- | --- | --- |',
      '| Query | 你的检索需求 | 当前词想寻找什么信息 |',
      '| Key | 每本书的标签 | 其他词提供什么线索 |',
      '| Value | 书的正文 | 真正被加权汇总的内容 |',
      '',
      '先用 Q 和每个 K 做点积，得到相关度分数；除以 `√d_k` 防止数值过大；经过 softmax 归一化为权重；最后对所有 V 加权求和。这样每个位置都得到一个新的上下文表示。',
      '',
      '### 为什么需要多头注意力',
      '',
      '单一注意力只能学习一种关联模式。多头注意力把表示投影到多个子空间，让不同头分别关注语法依赖、指代关系或长距离语义，再拼接融合。',
      '',
      '### 它解决了什么问题',
      '',
      '- 相比 RNN，注意力可以并行计算，训练效率更高；',
      '- 任意两个位置直接交互，长距离依赖的路径更短；',
      '- 注意力权重提供了一定程度的可解释性。',
      '',
      '### 常见误区',
      '',
      '注意力权重并不等于完整的解释，它只是模型内部计算的一部分。真正理解 Transformer，还需要结合位置编码、残差连接与层归一化一起看。',
      '',
      '如果你想继续，我可以带你手写一版 **缩放点积注意力**，或对比 BERT 与 GPT 在训练目标上的差异。',
    ].join('\n')
  }

  const firstCitation = citations[0] ? ` [${citations[0].index}]` : ''
  return [
    '## 核心回答',
    '',
    `关于「${truncate(request.query, 50)}」，我从课程知识库中召回了 **${chunks.length}** 条相关片段。综合这些证据，可以从「概念定位 → 关键机制 → 学习建议」三个层次来理解${firstCitation}。`,
    '',
    '### 概念定位',
    '',
    `这部分内容属于「${chunks[0]?.course ?? '计算机学科'}」的知识范围，核心材料来自《${chunks[0]?.source ?? '课程知识库'}》。建议先明确它解决的问题，再进入公式与实现细节。`,
    '',
    '### 关键机制',
    '',
    `1. **先建立问题模型**：明确输入、输出与优化目标，避免直接记忆术语。`,
    `2. **抓住核心变量**：关注模型中的关键假设，思考每个假设失效时会发生什么。`,
    `3. **用实验闭环验证**：通过小规模实验观察参数变化，并与理论预期对照${firstCitation}。`,
    '',
    '### 学习建议',
    '',
    '- 先阅读知识图谱中的前置节点，确认依赖链条完整；',
    '- 用一张图复述概念之间的因果关系；',
    '- 在一个真实的小项目中使用它，再回头补齐数学推导。',
    '',
    '> 当前回答已绑定知识库引用。你可以点击下方来源卡片查看原始片段，也可以在「RAG 检索调试」中检查召回质量。',
  ].join('\n')
}

function hashString(value: string): number {
  let hash = 0
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 31 + value.charCodeAt(index)) >>> 0
  }
  return hash
}

function createTool(
  id: string,
  name: string,
  label: string,
  input: string,
  status: ToolCall['status'],
  output: string,
  durationMs?: number,
): ToolCall {
  return { id, name, label, input, status, output, durationMs }
}

export function createMockAgentSseStream(
  request: AgentStreamRequest,
  streamSignal?: AbortSignal,
): ReadableStream<Uint8Array> {
  return new ReadableStream<Uint8Array>({
    async start(controller) {
      let closed = false
      const send = <K extends keyof AgentSsePayloadMap>(
        event: K,
        payload: AgentSsePayloadMap[K],
      ) => {
        if (closed) return
        controller.enqueue(
          encoder.encode(`event: ${event}\ndata: ${JSON.stringify(payload)}\n\n`),
        )
      }
      const sendStep = (step: AgentStep) => send('step', step)
      const sendTool = (tool: ToolCall) => send('tool', tool)

      try {
        if (streamSignal?.aborted) {
          closed = true
          controller.close()
          return
        }

        const intent = detectIntent(request.query)
        const hash = hashString(request.query)

        await delay(180, streamSignal)

        sendStep({
          id: 'intent',
          title: '理解问题',
          detail: `正在识别问题意图：${intentLabel(intent)}`,
          status: 'running',
        })
        await delay(360, streamSignal)
        sendStep({
          id: 'intent',
          title: '理解问题',
          detail: `识别为「${intentLabel(intent)}」，拆解为 2 个检索子问题`,
          status: 'done',
          durationMs: 360,
        })

        const searchToolId = 'tool-semantic-search'
        sendTool(
          createTool(
            searchToolId,
            'knowledge_base.semantic_search',
            '知识库语义检索',
            `query: "${truncate(request.query, 36)}" · top_k: ${request.topK} · threshold: ${request.threshold.toFixed(2)}`,
            'running',
            '正在计算查询向量并执行混合检索…',
          ),
        )
        sendStep({
          id: 'retrieve',
          title: '检索知识库',
          detail: `正在从 8 门课程、1,284 个知识片段中召回候选`,
          status: 'running',
        })

        const chunks = rankKnowledgeChunks(request.query, {
          topK: request.topK,
          threshold: request.threshold,
        })
        const citations = toCitations(chunks)

        await delay(680, streamSignal)
        sendTool(
          createTool(
            searchToolId,
            'knowledge_base.semantic_search',
            '知识库语义检索',
            `query: "${truncate(request.query, 36)}" · top_k: ${request.topK} · threshold: ${request.threshold.toFixed(2)}`,
            'done',
            chunks.length
              ? `召回 ${chunks.length} 条片段，最高相似度 ${(chunks[0]?.score ?? 0).toFixed(3)}`
              : '没有片段达到相似度阈值',
            682,
          ),
        )
        sendStep({
          id: 'retrieve',
          title: '检索知识库',
          detail: chunks.length
            ? `命中 ${chunks.length} 条候选片段，覆盖 ${new Set(chunks.map((chunk) => chunk.course)).size} 门课程`
            : '未命中达到阈值的片段',
          status: 'done',
          durationMs: 682,
        })
        send('retrieval', chunks)

        const rerankToolId = 'tool-rerank'
        sendTool(
          createTool(
            rerankToolId,
            'context.rerank',
            '上下文重排序',
            `candidates: ${chunks.length} · strategy: hybrid-cross-encoder`,
            'running',
            '正在对候选证据进行相关性重排…',
          ),
        )
        sendStep({
          id: 'rerank',
          title: '证据重排',
          detail: '结合课程结构与语义相关性重排候选证据',
          status: 'running',
        })
        await delay(420, streamSignal)
        sendStep({
          id: 'rerank',
          title: '证据重排',
          detail: chunks.length ? `保留 ${chunks.length} 条高置信证据，过滤冗余片段` : '没有候选证据可重排',
          status: 'done',
          durationMs: 420,
        })
        sendTool(
          createTool(
            rerankToolId,
            'context.rerank',
            '上下文重排序',
            `candidates: ${chunks.length} · strategy: hybrid-cross-encoder`,
            'done',
            chunks.length ? `完成重排，生成 ${citations.length} 条可引用来源` : '无候选片段，跳过重排',
            424,
          ),
        )
        send('citations', citations)

        sendStep({
          id: 'compose',
          title: '组织回答',
          detail: '正在基于证据生成带引用标记的回答',
          status: 'running',
        })
        await delay(240, streamSignal)

        const answer = buildAnswer(intent, request, chunks, citations)
        const characters = Array.from(answer)
        for (let cursor = 0; cursor < characters.length; cursor += 6) {
          if (streamSignal?.aborted) {
            throw new DOMException('The operation was aborted.', 'AbortError')
          }
          send('delta', { text: characters.slice(cursor, cursor + 6).join('') })
          await delay(15 + (hash % 11), streamSignal)
        }

        sendStep({
          id: 'compose',
          title: '组织回答',
          detail: `回答生成完成，已绑定 ${citations.length} 条知识库引用`,
          status: 'done',
          durationMs: Math.max(1200, 850 + characters.length * 3),
        })
        send('done', { citedCount: citations.length })
        closed = true
        controller.close()
      } catch (error) {
        if (isAbortError(error)) {
          closed = true
          try {
            controller.close()
          } catch {
            // The consumer may already have cancelled the stream.
          }
          return
        }
        closed = true
        controller.error(error)
      }
    },
  })
}

