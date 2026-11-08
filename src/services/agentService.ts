import type {
  AgentRunMeta,
  AgentStep,
  Citation,
  RetrievedChunk,
  RetrievalMode,
  ToolCall,
} from '@/types'
import { consumeSseStream } from '@/services/sse'
import { postStream } from '@/services/http'

export interface AgentStreamRequest {
  conversationId: string
  query: string
  topK: number
  threshold: number
  retrievalMode: RetrievalMode
  userMessageId: string
  assistantMessageId: string
  conversationTitle?: string
}

export type AgentStreamEvent =
  | { type: 'step'; step: AgentStep }
  | { type: 'tool'; tool: ToolCall }
  | { type: 'retrieval'; chunks: RetrievedChunk[] }
  | { type: 'citations'; citations: Citation[] }
  | { type: 'delta'; text: string }
  | { type: 'title'; title: string }
  | { type: 'done'; meta: AgentRunMeta }

export type AgentStreamHandler = (event: AgentStreamEvent) => void

export async function streamAgentReply(
  request: AgentStreamRequest,
  onEvent: AgentStreamHandler,
  signal?: AbortSignal,
): Promise<void> {
  const stream = await postStream(
    `/conversations/${encodeURIComponent(request.conversationId)}/stream/`,
    {
      query: request.query,
      topK: request.topK,
      threshold: request.threshold,
      retrievalMode: request.retrievalMode,
      userMessageId: request.userMessageId,
      assistantMessageId: request.assistantMessageId,
      conversationTitle: request.conversationTitle,
    },
    signal,
  )

  let doneReceived = false

  await consumeSseStream(stream, (message) => {
    let payload: unknown
    try {
      payload = JSON.parse(message.data)
    } catch {
      throw new Error('Agent 流式返回格式错误')
    }

    switch (message.event) {
      case 'step':
        onEvent({ type: 'step', step: payload as AgentStep })
        break
      case 'tool':
        onEvent({ type: 'tool', tool: payload as ToolCall })
        break
      case 'retrieval':
        onEvent({ type: 'retrieval', chunks: payload as RetrievedChunk[] })
        break
      case 'citations':
        onEvent({ type: 'citations', citations: payload as Citation[] })
        break
      case 'delta':
        onEvent({ type: 'delta', text: (payload as { text: string }).text })
        break
      case 'title':
        onEvent({ type: 'title', title: (payload as { title: string }).title })
        break
      case 'error': {
        const data = payload as { message?: string; code?: string }
        throw new Error(data.message || 'Agent 生成失败，请稍后重试')
      }
      case 'done': {
        doneReceived = true
        const data = payload as {
          citedCount: number
          latencyMs?: number
          messageId?: string
          runId?: string
          conversationId?: string
          title?: string
        }
        onEvent({
          type: 'done',
          meta: {
            latencyMs: Number(data.latencyMs ?? 0),
            citedCount: Number(data.citedCount ?? 0),
            messageId: data.messageId,
            runId: data.runId,
            conversationId: data.conversationId,
            title: data.title,
          },
        })
        break
      }
      default:
        break
    }
  })

  if (signal?.aborted) {
    throw new DOMException('The operation was aborted.', 'AbortError')
  }
  if (!doneReceived) {
    throw new Error('流式连接意外中断，请重试')
  }
}
