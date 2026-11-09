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
    description: '语义向量 + BM25 关键词 + 覆盖率综合排序，兼顾语义与术语',
  },
  {
    value: 'vector',
    label: '向量检索',
    shortLabel: 'Vector',
    description: '以语义向量为主，叠加标题/标签覆盖率，适合自然语言描述',
  },
  {
    value: 'keyword',
    label: '关键词检索',
    shortLabel: 'Keyword',
    description: '以 BM25 词法匹配为主，叠加覆盖率，适合精确术语与缩写',
  },
]

export function getRetrievalModeOption(mode: RetrievalMode): RetrievalModeOption {
  return retrievalModeOptions.find((option) => option.value === mode) ?? retrievalModeOptions[0]
}

export function getRetrievalModeLabel(mode: RetrievalMode): string {
  return getRetrievalModeOption(mode).label
}
