import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'
import { defaultRagConfig } from '@/data/mockData'
import type { RagConfig } from '@/types'
import { readStorage, writeStorage } from '@/utils/storage'

const STORAGE_KEY = 'zhiyan.rag.config'
export const MIN_THRESHOLD = 0.3
export const MAX_THRESHOLD = 0.95

function normalizeConfig(value: RagConfig | null): RagConfig {
  if (!value) return { ...defaultRagConfig }
  const topK = Number.isFinite(value.topK) ? Math.round(value.topK) : defaultRagConfig.topK
  const threshold = Number.isFinite(value.threshold)
    ? value.threshold
    : defaultRagConfig.threshold
  return {
    topK: Math.min(10, Math.max(1, topK)),
    threshold: Math.min(MAX_THRESHOLD, Math.max(MIN_THRESHOLD, threshold)),
  }
}

export const useRagStore = defineStore('rag', () => {
  const config = ref<RagConfig>(
    normalizeConfig(readStorage<RagConfig | null>(STORAGE_KEY, null)),
  )

  const configLabel = computed(
    () => `Top-K ${config.value.topK} · 阈值 ${config.value.threshold.toFixed(2)}`,
  )

  function updateConfig(patch: Partial<RagConfig>): void {
    config.value = normalizeConfig({ ...config.value, ...patch })
  }

  function resetConfig(): void {
    config.value = { ...defaultRagConfig }
  }

  watch(
    config,
    (value) => {
      writeStorage(STORAGE_KEY, value)
    },
    { deep: true },
  )

  return {
    config,
    configLabel,
    updateConfig,
    resetConfig,
  }
})
