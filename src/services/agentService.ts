import type {
  AgentRunMeta,
  AgentStep,
  Citation,
  RetrievedChunk,
  ToolCall,
} from '@/types'
import { consumeSseStream } from '@/services/sse'
import {
  createMockAgentSseStream,
  type AgentStreamRequest,
} from '@/services/mockAgentServer'

export type AgentStreamEvent =
  | { type: 'step'; step: AgentStep }
  | { type: 'tool'; tool: ToolCall }
  | { type: 'retrieval'; chunks: RetrievedChunk[] }
  | { type: 'citations'; citations: Citation[] }
  | { type: 'delta'; text: string }
  | { type: 'done'; meta: AgentRunMeta }

export type AgentStreamHandler = (event: AgentStreamEvent) => void

/**
 * The UI only talks to this service. To connect a real backend later, replace
 * `createMockAgentSseStream` with a `fetch` call returning `response.body`.
 */
export async function streamAgentReply(
  request: AgentStreamRequest,
  onEvent: AgentStreamHandler,
  signal?: AbortSignal,
): Promise<void> {
  const startedAt = performance.now()
  const stream = createMockAgentSseStream(request, signal)
  let doneReceived = false
  let citedCount = 0

  await consumeSseStream(stream, (message) => {
    const payload = JSON.parse(message.data) as unknown

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
      case 'done': {
        doneReceived = true
        citedCount = (payload as { citedCount: number }).citedCount
        const meta: AgentRunMeta = {
          latencyMs: Math.round(performance.now() - startedAt),
          citedCount,
        }
        onEvent({ type: 'done', meta })
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
