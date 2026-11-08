import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { HealthStatus, PublicStats } from '@/types'
import { fetchHealth, fetchPublicStats } from '@/services/api'

export const useSystemStore = defineStore('system', () => {
  const stats = ref<PublicStats | null>(null)
  const health = ref<HealthStatus | null>(null)
  const isLoading = ref(false)
  const error = ref('')

  const llmLabel = computed(() => {
    if (!health.value) return '服务检查中'
    return health.value.llm.configured ? 'DeepSeek 在线' : '本地生成兜底'
  })

  const lastSyncedAt = computed(() => stats.value?.lastSyncedAt || '—')

  async function loadStats(): Promise<void> {
    isLoading.value = true
    error.value = ''
    try {
      const [nextStats, nextHealth] = await Promise.all([fetchPublicStats(), fetchHealth()])
      stats.value = nextStats
      health.value = nextHealth
    } catch (err) {
      error.value = err instanceof Error ? err.message : '无法读取系统状态'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  return {
    stats,
    health,
    isLoading,
    error,
    llmLabel,
    lastSyncedAt,
    loadStats,
  }
})
