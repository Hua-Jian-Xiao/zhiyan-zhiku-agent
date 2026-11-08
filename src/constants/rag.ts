import type { RagConfig } from '@/types'

export const DEFAULT_RAG_CONFIG: RagConfig = {
  topK: 5,
  threshold: 0.72,
  retrievalMode: 'hybrid',
}

export const MIN_THRESHOLD = 0.3
export const MAX_THRESHOLD = 0.95
