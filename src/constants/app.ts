export const quickPrompts = [
  {
    label: '生成AI工程师学习路线',
    description: '从数学基础到 RAG 应用的四阶段路线',
    prompt: '请为我生成一份从零到 AI 工程师的系统学习路线，包含阶段目标与参考资料。',
    accent: 'indigo',
  },
  {
    label: '查询机器学习前置知识点',
    description: '按客观依赖关系梳理先修内容',
    prompt: '查询机器学习的前置知识点，并按依赖顺序告诉我应该先学什么。',
    accent: 'cyan',
  },
] as const

export const starterPrompts = [
  {
    title: '规划学习路线',
    description: '从数学基础到 RAG 工程的阶段化路径',
    prompt: '请为我生成一份从零到 AI 工程师的系统学习路线，包含阶段目标与参考资料。',
    icon: 'route',
  },
  {
    title: '拆解前置依赖',
    description: '机器学习需要先掌握哪些知识？',
    prompt: '查询机器学习的前置知识点，并按依赖顺序告诉我应该先学什么。',
    icon: 'graph',
  },
  {
    title: '理解核心机制',
    description: '用直观方式解释 Transformer 自注意力',
    prompt: '请用直观的例子解释 Transformer 的自注意力机制，并说明它解决了什么问题。',
    icon: 'spark',
  },
  {
    title: '设计 RAG 方案',
    description: '梳理可落地的检索增强生成链路',
    prompt: '请设计一套面向课程知识库的 RAG 方案，说明切分、召回、重排与评估策略。',
    icon: 'layers',
  },
]

export const ragSampleQueries = [
  '机器学习需要哪些前置知识？',
  'RAG 的完整检索链路是什么？',
  'Transformer 自注意力如何计算？',
  '梯度下降的学习率如何选择？',
]
