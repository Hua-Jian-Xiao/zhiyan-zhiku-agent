import { mockKnowledgeChunks, type SeedChunk } from '@/mock'
import type { RagConfig, RetrievedChunk } from '@/types'

function hashString(value: string): number {
  let hash = 2166136261
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index)
    hash = Math.imul(hash, 16777619)
  }
  return hash >>> 0
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}

function relevanceBoost(query: string, chunk: SeedChunk): number {
  const normalized = query.toLowerCase()
  let boost = 0

  for (const tag of chunk.tags) {
    if (normalized.includes(tag.toLowerCase())) boost += 0.018
  }

  if (/(前置|先修|依赖|顺序)/.test(query)) {
    if (['chunk-math-linear', 'chunk-prob-bayes', 'chunk-python-numpy'].includes(chunk.id)) {
      boost += 0.06
    }
    if (chunk.id === 'chunk-ml-gradient') boost += 0.025
  }

  if (/(rag|检索增强|向量检索)/i.test(query)) {
    if (chunk.id === 'chunk-rag-pipeline') boost += 0.085
    if (chunk.id === 'chunk-kg-embedding') boost += 0.02
  }

  if (/(transformer|注意力|self-attention)/i.test(query)) {
    if (chunk.id === 'chunk-dl-transformer') boost += 0.1
  }

  if (/(梯度|学习率|优化器)/.test(query) && chunk.id === 'chunk-ml-gradient') {
    boost += 0.07
  }

  return boost
}

function modeScore(query: string, chunk: SeedChunk, config: RagConfig, jitter: number): number {
  const lexical = relevanceBoost(query, chunk)
  if (config.retrievalMode === 'vector') {
    // 向量模式只保留语义相似度与轻微随机扰动。
    return chunk.baseScore * 0.985 + jitter * 0.65
  }
  if (config.retrievalMode === 'keyword') {
    // 关键词模式放大课程术语命中带来的收益。
    return chunk.baseScore - 0.025 + lexical * 1.45 + jitter
  }
  return chunk.baseScore + lexical * 0.92 + jitter
}

export function rankKnowledgeChunks(query: string, config: RagConfig): RetrievedChunk[] {
  const normalizedQuery = query.trim()
  if (!normalizedQuery) return []

  const results = mockKnowledgeChunks
    .map((chunk) => {
      const hash = hashString(`${normalizedQuery}::${chunk.id}`)
      const jitter = ((hash % 1000) / 1000 - 0.5) * 0.016
      const score = clamp(modeScore(normalizedQuery, chunk, config, jitter), 0.5, 0.988)
      return {
        id: chunk.id,
        knowledgePointId: chunk.knowledgePointId,
        title: chunk.title,
        course: chunk.course,
        source: chunk.source,
        chapter: chunk.chapter,
        content: chunk.content,
        tags: [...chunk.tags],
        score: Math.round(score * 1000) / 1000,
      }
    })
    .filter((chunk) => chunk.score >= config.threshold)
    .sort((a, b) => b.score - a.score)

  return results.slice(0, config.topK)
}
