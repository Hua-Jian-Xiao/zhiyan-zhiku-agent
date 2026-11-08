import {
  mockGraphNodes,
  mockKnowledgeBaseOverview,
  mockKnowledgeGraph,
  mockNcfItems,
  mockUsers,
} from '@/mock'
import type {
  AuthSession,
  KnowledgeBaseOverview,
  KnowledgeGraphData,
  NcfRecommendation,
  NcfResult,
  NcfUser,
  RagConfig,
  RetrievalMetrics,
  RetrievalResponse,
} from '@/types'
import { delay } from '@/utils/async'
import { rankKnowledgeChunks } from '@/utils/retrieval'

function hashString(value: string): number {
  let hash = 0
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 31 + value.charCodeAt(index)) >>> 0
  }
  return hash
}

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

export async function mockLogin(account: string, password: string): Promise<AuthSession> {
  await delay(720)
  const normalizedAccount = account.trim()

  if (!normalizedAccount || password.length < 6) {
    throw new Error('账号或密码格式不正确，请重新输入')
  }

  const isDemoAccount = normalizedAccount === 'admin'
  return {
    token: `mock_token_${Date.now()}`,
    signedAt: Date.now(),
    user: {
      id: isDemoAccount ? 'user-admin' : `user-${normalizedAccount}`,
      username: normalizedAccount,
      displayName: isDemoAccount ? '林晓' : normalizedAccount,
      role: '计算机科学 · 学习者',
      avatarText: isDemoAccount ? '林' : normalizedAccount.slice(0, 1).toUpperCase(),
    },
  }
}

export async function fetchKnowledgeBase(signal?: AbortSignal): Promise<KnowledgeBaseOverview> {
  await delay(820, signal)
  return clone(mockKnowledgeBaseOverview)
}

export async function fetchKnowledgeGraph(signal?: AbortSignal): Promise<KnowledgeGraphData> {
  await delay(760, signal)
  return clone(mockKnowledgeGraph)
}

function buildMetrics(query: string, chunks: number, config: RagConfig): RetrievalMetrics {
  const seed = hashString(query)
  const embeddingMs = 28 + (seed % 17)
  const modeCost = config.retrievalMode === 'hybrid' ? 12 : config.retrievalMode === 'keyword' ? 4 : 0
  const searchMs = 18 + ((seed >> 3) % 14) + chunks * 2 + modeCost
  const rerankMs = chunks > 0 ? 36 + ((seed >> 5) % 23) : 0
  return {
    embeddingMs,
    searchMs,
    rerankMs,
    totalMs: embeddingMs + searchMs + rerankMs,
  }
}

export async function retrieveKnowledge(
  query: string,
  config: RagConfig,
  signal?: AbortSignal,
): Promise<RetrievalResponse> {
  const normalized = query.trim()
  if (!normalized) throw new Error('请输入检索内容')

  const seed = hashString(normalized)
  await delay(560 + (seed % 420), signal)
  const chunks = rankKnowledgeChunks(normalized, config)

  return {
    query: normalized,
    chunks,
    metrics: buildMetrics(normalized, chunks.length, config),
    config: { ...config },
  }
}

export async function fetchNcfRecommendations(
  userId: string,
  topK: number,
  signal?: AbortSignal,
): Promise<NcfResult> {
  if (!userId) throw new Error('请选择一个用户')
  await delay(920, signal)

  const user = mockUsers.find((item) => item.id === userId)
  if (!user) throw new Error('用户不存在')

  const recommendations = mockNcfItems
    .map((item) => {
      const interestMatches = item.tags.filter((tag) => user.interests.includes(tag))
      const recentMatches = item.tags.filter((tag) =>
        user.recent.some((recent) => recent.includes(tag) || tag.includes(recent.split(' ')[0])),
      )
      const seed = hashString(`${userId}:${item.id}`)
      const jitter = (seed % 100) / 1000
      const base =
        0.54 + item.popularity / 420 + interestMatches.length * 0.075 + recentMatches.length * 0.032
      const score = Math.min(0.986, base + jitter)
      const matchTag = interestMatches[0] ?? recentMatches[0]
      const reason = matchTag
        ? `与你关注的「${matchTag}」方向高度相关，适合作为下一阶段学习内容。`
        : `来自「${item.category}」方向的高热度内容，与你当前阶段的学习路径互补。`

      return {
        item,
        score: Math.round(score * 1000) / 1000,
        reason,
        rank: 0,
      }
    })
    .sort((a, b) => b.score - a.score)
    .slice(0, topK)
    .map<NcfRecommendation>((recommendation, index) => ({
      ...recommendation,
      rank: index + 1,
    }))

  return {
    user: clone(user) as NcfUser,
    recommendations,
    latencyMs: 1180 + (hashString(userId) % 260),
    modelVersion: 'NeuMF · GMF + MLP',
  }
}

export function getGraphNode(nodeId: string) {
  return mockGraphNodes.find((node) => node.id === nodeId)
}
