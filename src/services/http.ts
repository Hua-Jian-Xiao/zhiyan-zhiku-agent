import type { AuthSession } from '@/types'

export const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '')
export const AUTH_STORAGE_KEY = 'zhiyan.auth.session'

export class ApiError extends Error {
  status: number
  code?: string

  constructor(message: string, status = 0, code?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

export function readSession(): AuthSession | null {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY)
    return raw ? (JSON.parse(raw) as AuthSession) : null
  } catch {
    return null
  }
}

export function writeSession(session: AuthSession): void {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session))
  window.dispatchEvent(new CustomEvent('zhiyan:session-updated', { detail: session }))
}

export function clearSession(): void {
  localStorage.removeItem(AUTH_STORAGE_KEY)
  window.dispatchEvent(new Event('zhiyan:session-cleared'))
}

function notifyUnauthorized(): void {
  clearSession()
  window.dispatchEvent(new Event('zhiyan:unauthorized'))
}

function authHeaders(session: AuthSession | null): Record<string, string> {
  return session?.token ? { Authorization: `Bearer ${session.token}` } : {}
}

async function parseError(response: Response): Promise<ApiError> {
  let message = `请求失败（${response.status}）`
  let code: string | undefined
  try {
    const payload = (await response.json()) as { detail?: string; message?: string; code?: string }
    message = payload.detail || payload.message || message
    code = payload.code
  } catch {
    // Keep the generic HTTP error when the body is not JSON.
  }
  return new ApiError(message, response.status, code)
}

async function refreshAccessToken(): Promise<AuthSession | null> {
  const session = readSession()
  if (!session?.refresh) return null
  try {
    const response = await fetch(`${API_BASE}/auth/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: session.refresh }),
    })
    if (!response.ok) return null
    const data = (await response.json()) as { token: string; refresh?: string }
    const next: AuthSession = {
      ...session,
      token: data.token,
      refresh: data.refresh || session.refresh,
    }
    writeSession(next)
    return next
  } catch {
    return null
  }
}

export interface RequestOptions extends Omit<RequestInit, 'body' | 'headers'> {
  body?: unknown
  headers?: Record<string, string>
  auth?: boolean
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, headers: customHeaders, auth = true, ...rest } = options
  const session = readSession()
  const buildHeaders = (activeSession: AuthSession | null): Record<string, string> => {
    const headers: Record<string, string> = {
      Accept: 'application/json',
      ...authHeaders(activeSession),
      ...customHeaders,
    }
    if (body !== undefined && !(body instanceof FormData)) {
      headers['Content-Type'] = 'application/json'
    }
    return headers
  }

  const perform = (activeSession: AuthSession | null): Promise<Response> =>
    fetch(`${API_BASE}${path}`, {
      ...rest,
      headers: buildHeaders(activeSession),
      body:
        body === undefined
          ? undefined
          : body instanceof FormData
            ? body
            : JSON.stringify(body),
    })

  let response: Response
  try {
    response = await perform(auth ? session : null)
  } catch (error) {
    if ((error as Error)?.name === 'AbortError') throw error
    throw new ApiError('无法连接服务，请确认后端已启动', 0, 'NETWORK_ERROR')
  }

  if (response.status === 401 && auth && session) {
    const refreshed = await refreshAccessToken()
    if (refreshed) {
      response = await perform(refreshed)
    } else {
      notifyUnauthorized()
      throw await parseError(response)
    }
  }

  if (!response.ok) {
    const error = await parseError(response)
    if (response.status === 401 && auth) notifyUnauthorized()
    throw error
  }
  if (response.status === 204) return undefined as T
  const text = await response.text()
  return text ? (JSON.parse(text) as T) : (undefined as T)
}

export async function postStream(
  path: string,
  body: unknown,
  signal?: AbortSignal,
): Promise<ReadableStream<Uint8Array>> {
  const perform = (session: AuthSession | null): Promise<Response> =>
    fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: {
        Accept: 'text/event-stream',
        'Content-Type': 'application/json',
        ...authHeaders(session),
      },
      body: JSON.stringify(body),
      signal,
    })

  let session = readSession()
  let response: Response
  try {
    response = await perform(session)
  } catch (error) {
    if ((error as Error)?.name === 'AbortError') throw error
    throw new ApiError('无法连接 Agent 服务，请确认后端已启动', 0, 'NETWORK_ERROR')
  }

  if (response.status === 401) {
    const refreshed = await refreshAccessToken()
    if (refreshed) {
      response = await perform(refreshed)
    } else {
      notifyUnauthorized()
      throw await parseError(response)
    }
  }
  if (!response.ok) {
    throw await parseError(response)
  }
  if (!response.body) {
    throw new ApiError('Agent 流式连接为空', 0, 'EMPTY_STREAM')
  }
  session = readSession()
  if (!session) notifyUnauthorized()
  return response.body
}
