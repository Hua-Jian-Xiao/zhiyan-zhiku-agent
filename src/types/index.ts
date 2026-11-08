export interface UserProfile {
  id: string
  username: string
  displayName: string
  role: string
  avatarText: string
}

export interface AuthSession {
  token: string
  user: UserProfile
  signedAt: number
}

export interface RagConfig {
  topK: number
  threshold: number
}

export interface Course {
  id: string
  code: string
  name: string
  shortName: string
  teacher: string
  description: string
  knowledgePointCount: number
  documentCount: number
  color: string
  updatedAt: string
}

export interface KnowledgePoint {
  id: string
  name: string
  course: string
  chapter: string
  difficulty: '入门' | '进阶' | '高阶'
  updatedAt: string
}

export interface KnowledgeBaseOverview {
  courses: Course[]
  knowledgePoints: KnowledgePoint[]
  courseCount: number
  knowledgePointCount: number
  chunkCount: number
  documentCount: number
  lastSyncedAt: string
}

export interface RetrievedChunk {
  id: string
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

export interface NcfUser {
  id: string
  name: string
  avatar: string
  color: string
  stage: string
  interests: string[]
  recent: string[]
}

export interface NcfItem {
  id: string
  title: string
  type: '课程' | '知识点' | '专题'
  category: string
  tags: string[]
  description: string
  popularity: number
}

export interface NcfRecommendation {
  rank: number
  item: NcfItem
  score: number
  reason: string
}

export interface NcfResult {
  user: NcfUser
  recommendations: NcfRecommendation[]
  latencyMs: number
  modelVersion: string
}

export interface AgentRunMeta {
  latencyMs: number
  citedCount: number
}
