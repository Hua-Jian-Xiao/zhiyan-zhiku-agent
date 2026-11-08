export function formatRelativeTime(timestamp: number): string {
  const diff = Date.now() - timestamp
  if (diff < 60_000) return '刚刚'
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)} 分钟前`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)} 小时前`
  if (diff < 7 * 86_400_000) return `${Math.floor(diff / 86_400_000)} 天前`

  const date = new Date(timestamp)
  return `${date.getMonth() + 1} 月 ${date.getDate()} 日`
}

export function formatDateTime(timestamp: number): string {
  const date = new Date(timestamp)
  const pad = (value: number) => value.toString().padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(
    date.getHours(),
  )}:${pad(date.getMinutes())}`
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${Math.max(1, Math.round(ms))} ms`
  return `${(ms / 1000).toFixed(1)} s`
}

export function formatScore(score: number): string {
  return `${(score * 100).toFixed(1)}%`
}

export function truncate(text: string, max = 40): string {
  const normalized = text.replace(/\s+/g, ' ').trim()
  return normalized.length > max ? `${normalized.slice(0, max)}…` : normalized
}

export function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}
