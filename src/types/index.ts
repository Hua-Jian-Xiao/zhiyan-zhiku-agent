export interface UserProfile {
  id: string
  username: string
  displayName: string
  role: string
  avatarText: string
  avatarUrl: string
  email: string
  major: string
  grade: string
  bio: string
  securityQuestion: string
  hasSecurityQuestion: boolean
}

export interface ProfileUpdatePayload {
  displayName?: string
  email?: string
  major?: string
  grade?: string
  bio?: string
  securityQuestion?: string
  securityAnswer?: string
  avatar?: File | null
}

export interface SecurityQuestionResponse {
  username: string
  securityQuestion: string
}

export interface AuthSession {
  token: string
  refresh?: string
  user: UserProfile
  signedAt: number
}

export type RetrievalMode = 'hybrid' | 'vector' | 'keyword'

export interface RagConfig {
  topK: number
  threshold: number
  retrievalMode: RetrievalMode
}

export interface Course {
  id: string
  code: string
  name: string
  shortName: string
  teacher: string
  school: string
  description: string
  category: string
  coverUrl: string
  sourceUrl: string
  popularity: number
  knowledgePointCount: number
  documentCount: number
  color: string
  legacyCourseId: number | null
  isLegacyImport: boolean
  updatedAt: string
}

export interface KnowledgePoint {
  id: string
  name: string
  course: string
  courseId: string
  courseSourceUrl: string
  courseCoverUrl: string
  chapter: string
  chapterNo: number
  difficulty: '入门' | '进阶' | '高阶'
  description: string
  tags: string[]
  chunkCount: number
  updatedAt: string
}

export interface KnowledgePointChunk {
  id: string
  title: string
  chapter: string
  source: string
  documentId: string
  documentTitle: string
  content: string
  ordinal: number
}

export interface KnowledgePointDetail extends KnowledgePoint {
  chunks: KnowledgePointChunk[]
}

export interface DocumentJumpRequest {
  courseId?: string
  documentId?: string
  documentTitle?: string
  nonce: number
}

export interface IndexHealth {
  status: 'healthy' | 'indexing' | 'degraded' | 'error'
  label: string
  issues: string[]
  database: string
  documentCount: number
  readyDocumentCount: number
  failedDocumentCount: number
  processingDocumentCount: number
  chunkCount: number
  emptyEmbeddingCount: number
  lastSyncedAt: string
}

export interface KnowledgeBaseOverview {
  courses: Course[]
  knowledgePoints: KnowledgePoint[]
  courseCount: number
  knowledgePointCount: number
  chunkCount: number
  documentCount: number
  lastSyncedAt: string
  indexHealth?: IndexHealth
}

export interface RetrievedChunk {
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

export interface Citation {
  id: string
  index: number
  knowledgePointId: string
  title: string
  course: string
  source: string
  chapter: string
  snippet: string
  score: number
}

export interface RetrievalMetrics {
  embeddingMs: number
  searchMs: number
  rerankMs: number
  totalMs: number
}

export interface RetrievalResponse {
  query: string
  chunks: RetrievedChunk[]
  metrics: RetrievalMetrics
  config: RagConfig
}

export type StepStatus = 'pending' | 'running' | 'done'
export type ToolStatus = 'running' | 'done' | 'error'

export interface AgentStep {
  id: string
  title: string
  detail: string
  status: StepStatus
  durationMs?: number
}

export interface ToolCall {
  id: string
  name: string
  label: string
  status: ToolStatus
  input: string
  output: string
  durationMs?: number
}

export interface AgentTrace {
  steps: AgentStep[]
  tools: ToolCall[]
  chunks: RetrievedChunk[]
}

export type MessageStatus = 'streaming' | 'done' | 'error'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt: number
  status: MessageStatus
  citations: Citation[]
  trace?: AgentTrace
  latencyMs?: number
  stopped?: boolean
  error?: string
}

export interface Conversation {
  id: string
  title: string
  createdAt: number
  updatedAt: number
  messages: ChatMessage[]
}

export type GraphCategory = 'foundation' | 'core' | 'advanced' | 'llm'

export interface KnowledgeGraphNode {
  id: string
  name: string
  category: GraphCategory
  description: string
  prerequisites: string[]
  relatedCourse: string
  difficulty: '基础' | '进阶' | '高阶'
}

export interface KnowledgeGraphEdge {
  source: string
  target: string
  reason: string
}

export interface KnowledgeGraphCategory {
  key: GraphCategory
  label: string
  color: string
}

export interface KnowledgeGraphData {
  nodes: KnowledgeGraphNode[]
  edges: KnowledgeGraphEdge[]
  categories: KnowledgeGraphCategory[]
}

export interface DocumentItem {
  id: string
  courseId: string
  courseName: string
  title: string
  sourceName: string
  sourceType: string
  status: 'pending' | 'processing' | 'ready' | 'failed'
  chunkCount: number
  byteSize: number
  createdAt: number
  updatedAt: number
  errorMessage: string | null
}

export interface DocumentListResponse {
  items: DocumentItem[]
  total: number
}

export interface KnowledgePointListResponse {
  items: KnowledgePoint[]
  total: number
}

export interface PublicStats {
  courseCount: number
  knowledgePointCount: number
  chunkCount: number
  documentCount: number
  graphNodeCount: number
  graphEdgeCount: number
  lastSyncedAt: string
}

export interface HealthStatus {
  status: string
  database: string
  llm: {
    configured: boolean
    provider: string
    model: string
  }
  embedding: {
    provider: string
    dim: number
  }
  version: string
}

export interface AgentRunMeta {
  latencyMs: number
  citedCount: number
  messageId?: string
  runId?: string
  conversationId?: string
  title?: string
}
