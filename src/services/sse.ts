export interface SseMessage {
  event: string
  data: string
  id?: string
}

type SseMessageHandler = (message: SseMessage) => void

function parseEventBlock(block: string): SseMessage | null {
  const lines = block.split('\n')
  let event = 'message'
  let id: string | undefined
  const dataLines: string[] = []

  for (const line of lines) {
    if (!line || line.startsWith(':')) continue
    const separatorIndex = line.indexOf(':')
    const field = separatorIndex === -1 ? line : line.slice(0, separatorIndex)
    let value = separatorIndex === -1 ? '' : line.slice(separatorIndex + 1)
    if (value.startsWith(' ')) value = value.slice(1)

    if (field === 'event') event = value
    if (field === 'data') dataLines.push(value)
    if (field === 'id') id = value
  }

  if (dataLines.length === 0) return null
  return { event, data: dataLines.join('\n'), id }
}

/**
 * A small SSE parser for ReadableStream. It mirrors the browser EventSource
 * framing rules closely enough for this mock stream and can be reused against
 * a real text/event-stream response later.
 */
export async function consumeSseStream(
  stream: ReadableStream<Uint8Array>,
  onMessage: SseMessageHandler,
): Promise<void> {
  const reader = stream.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  const normalize = (value: string) => value.replace(/\r\n/g, '\n').replace(/\r/g, '\n')

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer = normalize(buffer + decoder.decode(value, { stream: true }))

      let boundary = buffer.indexOf('\n\n')
      while (boundary !== -1) {
        const block = buffer.slice(0, boundary)
        buffer = buffer.slice(boundary + 2)
        const message = parseEventBlock(block)
        if (message) onMessage(message)
        boundary = buffer.indexOf('\n\n')
      }
    }

    buffer = normalize(buffer + decoder.decode())
    if (buffer.trim()) {
      const message = parseEventBlock(buffer.trim())
      if (message) onMessage(message)
    }
  } finally {
    reader.releaseLock()
  }
}
