import type {
  AuthSession,
  Conversation,
  Course,
  DocumentItem,
  DocumentListResponse,
  HealthStatus,
  KnowledgeBaseOverview,
  KnowledgeGraphData,
  KnowledgePoint,
  KnowledgePointDetail,
  KnowledgePointListResponse,
  PublicStats,
  RagConfig,
  RetrievalResponse,
  UserProfile,
} from '@/types'
import { request } from '@/services/http'

function queryString(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') search.set(key, String(value))
  })
  const result = search.toString()
  return result ? `?${result}` : ''
}

export async function login(username: string, password: string): Promise<AuthSession> {
  return request<AuthSession>('/auth/login/', {
    method: 'POST',
    body: { username, password },
    auth: false,
  })
}

export async function register(payload: {
  username: string
  password: string
  displayName?: string
}): Promise<AuthSession> {
  return request<AuthSession>('/auth/register/', {
    method: 'POST',
    body: payload,
    auth: false,
  })
}

export async function fetchMe(): Promise<{ user: UserProfile }> {
  return request<{ user: UserProfile }>('/auth/me/')
}

export async function logout(): Promise<void> {
  return request<void>('/auth/logout/', { method: 'POST', body: {} })
}

export async function fetchPublicStats(): Promise<PublicStats> {
  return request<PublicStats>('/public/stats/', { auth: false })
}

export async function fetchHealth(): Promise<HealthStatus> {
  return request<HealthStatus>('/health/', { auth: false })
}

export async function fetchKnowledgeOverview(signal?: AbortSignal): Promise<KnowledgeBaseOverview> {
  return request<KnowledgeBaseOverview>('/knowledge-base/overview/', { signal })
}

export async function fetchCourses(): Promise<Course[]> {
  return request<Course[]>('/courses/')
}

export async function fetchKnowledgePoints(params: {
  courseId?: string
  search?: string
} = {}): Promise<KnowledgePointListResponse> {
  return request<KnowledgePointListResponse>(
    `/knowledge-points/${queryString({
      courseId: params.courseId,
      search: params.search,
    })}`,
  )
}

export async function fetchGraph(signal?: AbortSignal): Promise<KnowledgeGraphData> {
  return request<KnowledgeGraphData>('/graph/', { signal })
}

export async function fetchKnowledgePointDetail(id: string): Promise<KnowledgePointDetail> {
  return request<KnowledgePointDetail>(`/knowledge-points/${encodeURIComponent(id)}/`)
}

export async function retrieveKnowledge(
  query: string,
  config: RagConfig,
  signal?: AbortSignal,
): Promise<RetrievalResponse> {
  return request<RetrievalResponse>('/retrieval/query/', {
    method: 'POST',
    signal,
    body: {
      query,
      topK: config.topK,
      threshold: config.threshold,
      retrievalMode: config.retrievalMode,
    },
  })
}

export async function fetchRagConfig(): Promise<RagConfig> {
  return request<RagConfig>('/rag/config/')
}

export async function saveRagConfig(config: RagConfig): Promise<RagConfig> {
  return request<RagConfig>('/rag/config/', {
    method: 'PUT',
    body: config,
  })
}

export async function fetchDocuments(params: {
  courseId?: string
  status?: string
  q?: string
} = {}): Promise<DocumentListResponse> {
  return request<DocumentListResponse>(
    `/documents/${queryString({
      courseId: params.courseId,
      status: params.status,
      q: params.q,
    })}`,
  )
}

export async function uploadDocument(payload: {
  file: File
  courseId: string
  knowledgePointId?: string
  title?: string
}): Promise<DocumentItem> {
  const form = new FormData()
  form.append('file', payload.file)
  form.append('courseId', payload.courseId)
  if (payload.knowledgePointId) form.append('knowledgePointId', payload.knowledgePointId)
  if (payload.title) form.append('title', payload.title)
  return request<DocumentItem>('/documents/', {
    method: 'POST',
    body: form,
  })
}

export async function reindexDocument(documentId: string): Promise<DocumentItem> {
  return request<DocumentItem>(`/documents/${documentId}/reindex/`, { method: 'POST', body: {} })
}

export async function deleteDocument(documentId: string): Promise<void> {
  return request<void>(`/documents/${documentId}/`, { method: 'DELETE' })
}

export async function fetchDocumentChunks(
  documentId: string,
): Promise<{ items: RetrievedChunkLike[]; total: number }> {
  return request(`/documents/${documentId}/chunks/`)
}

export interface RetrievedChunkLike {
  id: string
  knowledgePointId: string
  title: string
  course: string
  source: string
  chapter: string
  content: string
  tags: string[]
  score: number
}

export async function fetchConversations(): Promise<{ conversations: Conversation[] }> {
  return request<{ conversations: Conversation[] }>('/conversations/')
}

export async function createConversation(payload: {
  id?: string
  title?: string
}): Promise<Conversation> {
  return request<Conversation>('/conversations/', { method: 'POST', body: payload })
}

export async function deleteConversation(conversationId: string): Promise<void> {
  return request<void>(`/conversations/${conversationId}/`, { method: 'DELETE' })
}

export async function clearConversation(conversationId: string): Promise<void> {
  return request<void>(`/conversations/${conversationId}/messages/`, { method: 'DELETE' })
}

export async function deleteMessage(messageId: string): Promise<void> {
  return request<void>(`/messages/${messageId}/`, { method: 'DELETE' })
}

export async function renameConversation(
  conversationId: string,
  title: string,
): Promise<Conversation> {
  return request<Conversation>(`/conversations/${conversationId}/`, {
    method: 'PATCH',
    body: { title },
  })
}
