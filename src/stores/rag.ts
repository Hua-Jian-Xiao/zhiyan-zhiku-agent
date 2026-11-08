import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'
import type { RagConfig, RetrievalMode } from '@/types'
import { DEFAULT_RAG_CONFIG, MAX_THRESHOLD, MIN_THRESHOLD } from '@/constants/rag'
import { getRetrievalModeLabel } from '@/utils/rag'
import { readStorage, writeStorage } from '@/utils/storage'
import { fetchRagConfig, saveRagConfig } from '@/services/api'

export { MAX_THRESHOLD, MIN_THRESHOLD }

const STORAGE_KEY = 'zhiyan.rag.config'
const RETRIEVAL_MODES: RetrievalMode[] = ['hybrid', 'vector', 'keyword']

function normalizeConfig(value: RagConfig | null): RagConfig {
  if (!value) return { ...DEFAULT_RAG_CONFIG }
  const topK = Number.isFinite(value.topK) ? Math.round(value.topK) : DEFAULT_RAG_CONFIG.topK
  const threshold = Number.isFinite(value.threshold)
    ? value.threshold
    : DEFAULT_RAG_CONFIG.threshold
  const retrievalMode = RETRIEVAL_MODES.includes(value.retrievalMode)
    ? value.retrievalMode
    : DEFAULT_RAG_CONFIG.retrievalMode
  return {
    topK: Math.min(10, Math.max(1, topK)),
    threshold: Math.min(MAX_THRESHOLD, Math.max(MIN_THRESHOLD, threshold)),
    retrievalMode,
  }
}

export const useRagStore = defineStore('rag', () => {
  const config = ref<RagConfig>(
    normalizeConfig(readStorage<RagConfig | null>(STORAGE_KEY, null)),
  )

  const configLabel = computed(
    () =>
      `${getRetrievalModeLabel(config.value.retrievalMode)} · Top-K ${config.value.topK} · 阈值 ${config.value.threshold.toFixed(2)}`,
  )

  function updateConfig(patch: Partial<RagConfig>): void {
    config.value = normalizeConfig({ ...config.value, ...patch })
  }

  function resetConfig(): void {
    config.value = { ...DEFAULT_RAG_CONFIG }
  }

  async function loadFromServer(): Promise<void> {
    const remote = await fetchRagConfig()
    config.value = normalizeConfig(remote)
  }

  async function persistToServer(): Promise<RagConfig> {
    const saved = await saveRagConfig(config.value)
    config.value = normalizeConfig(saved)
    return config.value
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
    loadFromServer,
    persistToServer,
  }
})
