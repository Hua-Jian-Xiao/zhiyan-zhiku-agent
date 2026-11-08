export function delay(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException('The operation was aborted.', 'AbortError'))
      return
    }

    const timer = window.setTimeout(() => {
      signal?.removeEventListener('abort', handleAbort)
      resolve()
    }, ms)

    function handleAbort() {
      window.clearTimeout(timer)
      reject(new DOMException('The operation was aborted.', 'AbortError'))
    }

    signal?.addEventListener('abort', handleAbort, { once: true })
  })
}

export function isAbortError(error: unknown): boolean {
  return error instanceof DOMException
    ? error.name === 'AbortError'
    : Boolean(error && typeof error === 'object' && 'name' in error && error.name === 'AbortError')
}
