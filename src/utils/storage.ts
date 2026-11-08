export function readStorage<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') return fallback
  try {
    const raw = window.localStorage.getItem(key)
    if (!raw) return fallback
    return JSON.parse(raw) as T
  } catch {
    return fallback
  }
}

export function writeStorage(key: string, value: unknown): void {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // Storage can be unavailable in private mode or when the quota is exceeded.
  }
}

export function removeStorage(key: string): void {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.removeItem(key)
  } catch {
    // noop
  }
}
