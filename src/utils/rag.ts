import type { RetrievalMode } from '@/types'

export interface RetrievalModeOption {
  value: RetrievalMode
  label: string
  shortLabel: string
  description: string
}

export const retrievalModeOptions: RetrievalModeOption[] = [
  {
    value: 'hybrid',
    label: '混合检索',
    shortLabel: 'Hybrid',
    description: '向量语义召回 + 关键词加权，兼顾语义与术语精确性',
  },
  {
    value: 'vector',
    label: '向量检索',
    shortLabel: 'Vector',
    description: '仅依赖语义向量相似度，适合自然语言描述型问题',
  },
  {
    value: 'keyword',
    label: '关键词检索',
    shortLabel: 'Keyword',
    description: '强化课程术语与标签匹配，适合精确概念查询',
  },
]

export function getRetrievalModeOption(mode: RetrievalMode): RetrievalModeOption {
  return retrievalModeOptions.find((option) => option.value === mode) ?? retrievalModeOptions[0]
}

export function getRetrievalModeLabel(mode: RetrievalMode): string {
  return getRetrievalModeOption(mode).label
}
