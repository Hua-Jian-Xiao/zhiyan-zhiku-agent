<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Aim,
  ArrowRight,
  DataAnalysis,
  Filter,
  Search,
  Timer,
  TrendCharts,
} from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import StatePanel from '@/components/feedback/StatePanel.vue'
import RetrievalResultCard from '@/components/rag/RetrievalResultCard.vue'
import { retrieveKnowledge } from '@/services/api'
import { ragSampleQueries } from '@/constants/app'
import { useRagStore, MIN_THRESHOLD, MAX_THRESHOLD } from '@/stores/rag'
import { useSystemStore } from '@/stores/system'
import type { RetrievalMode, RetrievalResponse } from '@/types'
import { isAbortError } from '@/utils/async'
import {
  getRetrievalModeLabel,
  retrievalModeOptions,
} from '@/utils/rag'

const ragStore = useRagStore()
const systemStore = useSystemStore()

const query = ref('机器学习需要哪些前置知识？')
const isLoading = ref(false)
const errorMessage = ref('')
const response = ref<RetrievalResponse | null>(null)
let controller: AbortController | null = null

const topK = computed({
  get: () => ragStore.config.topK,
  set: (value: number) => ragStore.updateConfig({ topK: value }),
})

const threshold = computed({
  get: () => ragStore.config.threshold,
  set: (value: number) => ragStore.updateConfig({ threshold: value }),
})

const retrievalMode = computed({
  get: () => ragStore.config.retrievalMode,
  set: (value: RetrievalMode) => ragStore.updateConfig({ retrievalMode: value }),
})

const configDirty = computed(() => {
  if (!response.value) return false
  return (
    response.value.config.topK !== ragStore.config.topK ||
    Math.abs(response.value.config.threshold - ragStore.config.threshold) > 0.0001 ||
    response.value.config.retrievalMode !== ragStore.config.retrievalMode
  )
})

const metrics = computed(() => {
  if (!response.value) return []
  const result = response.value
  return [
    {
      label: '总耗时',
      value: `${result.metrics.totalMs} ms`,
      hint: 'End-to-end',
      icon: Timer,
      tone: 'text-indigo-500 bg-indigo-50 border-indigo-100',
    },
    {
      label: '向量化',
      value: `${result.metrics.embeddingMs} ms`,
      hint: 'Query embedding',
      icon: Aim,
      tone: 'text-cyan-500 bg-cyan-50 border-cyan-100',
    },
    {
      label: '召回检索',
      value: `${result.metrics.searchMs} ms`,
      hint: getRetrievalModeLabel(result.config.retrievalMode),
      icon: Search,
      tone: 'text-emerald-500 bg-emerald-50 border-emerald-100',
    },
    {
      label: '重排序',
      value: `${result.metrics.rerankMs} ms`,
      hint: 'Cross encoder',
      icon: Filter,
      tone: 'text-amber-500 bg-amber-50 border-amber-100',
    },
  ]
})

const highestScore = computed(() => response.value?.chunks[0]?.score ?? 0)
const currentModeLabel = computed(() => getRetrievalModeLabel(ragStore.config.retrievalMode))

async function handleSearch(): Promise<void> {
  const normalized = query.value.trim()
  if (!normalized) {
    ElMessage.warning('请先输入检索问题')
    return
  }

  controller?.abort()
  const currentController = new AbortController()
  controller = currentController
  isLoading.value = true
  errorMessage.value = ''
  response.value = null

  try {
    const result = await retrieveKnowledge(
      normalized,
      { ...ragStore.config },
      currentController.signal,
    )
    if (currentController.signal.aborted) return
    response.value = result
    void ragStore.persistToServer().catch(() => null)
  } catch (error) {
    if (!isAbortError(error)) {
      errorMessage.value = error instanceof Error ? error.message : '检索失败，请稍后重试'
    }
  } finally {
    if (controller === currentController) isLoading.value = false
  }
}

function handleSampleQuery(sample: string): void {
  query.value = sample
  void handleSearch()
}

function clearResults(): void {
  controller?.abort()
  response.value = null
  errorMessage.value = ''
  isLoading.value = false
}

function lowerThresholdAndRetry(): void {
  ragStore.updateConfig({
    threshold: Math.max(MIN_THRESHOLD, Number((ragStore.config.threshold - 0.08).toFixed(2))),
  })
  void handleSearch()
}

function formatTooltip(value: number): string {
  return value.toFixed(2)
}

onBeforeUnmount(() => {
  controller?.abort()
})
</script>

<template>
  <div class="page-scroll">
    <div class="page-container">
      <PageHeader
        title="RAG 检索调试"
        description="输入问题，查看召回片段的原文、相似度分数、来源课程与知识点 ID。所有参数与知识库管理页共享，便于评审理解 RAG 的内部机制。"
      >
        <template #actions>
          <span class="hidden items-center gap-1.5 rounded-lg border border-emerald-100 bg-emerald-50 px-2.5 py-1.5 text-[9px] font-medium text-emerald-600 sm:inline-flex">
            <span class="h-1.5 w-1.5 animate-soft-pulse rounded-full bg-emerald-400" />
            {{ systemStore.stats ? 'Live Index Ready' : 'Checking Index' }}
          </span>
          <el-button :disabled="!response" @click="clearResults">清空结果</el-button>
        </template>
      </PageHeader>

      <div class="mt-6 grid items-start gap-5 xl:grid-cols-[372px_minmax(0,1fr)]">
        <aside class="space-y-4 xl:sticky xl:top-5">
          <section class="surface-card overflow-hidden">
            <div class="border-b border-slate-100 px-4 py-3.5">
              <div class="flex items-center gap-2">
                <span class="grid h-6 w-6 place-items-center rounded-md bg-indigo-50 font-mono text-[8px] font-semibold text-indigo-500">
                  01
                </span>
                <div>
                  <p class="text-[11px] font-semibold text-slate-700">输入测试问题</p>
                  <p class="mt-0.5 text-[8px] text-slate-400">自然语言 query 将生成检索向量</p>
                </div>
              </div>
            </div>
            <div class="p-4">
              <el-input
                v-model="query"
                type="textarea"
                :autosize="{ minRows: 4, maxRows: 7 }"
                resize="none"
                maxlength="200"
                show-word-limit
                placeholder="例如：RAG 的完整检索链路是什么？"
                @keydown.ctrl.enter.prevent="handleSearch"
              />

              <div class="mt-3">
                <p class="text-[8px] font-medium uppercase tracking-[0.12em] text-slate-400">
                  示例问题
                </p>
                <div class="mt-2 flex flex-wrap gap-1.5">
                  <button
                    v-for="sample in ragSampleQueries"
                    :key="sample"
                    type="button"
                    class="rag-sample-chip"
                    :disabled="isLoading"
                    @click="handleSampleQuery(sample)"
                  >
                    {{ sample }}
                  </button>
                </div>
              </div>

              <el-button
                type="primary"
                class="!mt-4 !h-10 !w-full"
                :loading="isLoading"
                @click="handleSearch"
              >
                <template v-if="!isLoading">
                  <el-icon class="mr-1"><Search /></el-icon>
                  开始检索
                </template>
                <template v-else>正在召回知识片段…</template>
              </el-button>
              <p class="mt-2 text-center font-mono text-[7.5px] text-slate-300">
                CTRL + ENTER TO RUN
              </p>
            </div>
          </section>

          <section class="surface-card p-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="grid h-6 w-6 place-items-center rounded-md bg-cyan-50 font-mono text-[8px] font-semibold text-cyan-500">
                  02
                </span>
                <div>
                  <p class="text-[11px] font-semibold text-slate-700">检索参数</p>
                  <p class="mt-0.5 text-[8px] text-slate-400">与工作台、知识库实时共享</p>
                </div>
              </div>
              <span class="rounded-full border border-slate-200 bg-slate-50 px-1.5 py-0.5 text-[7px] text-slate-400">
                GLOBAL
              </span>
            </div>

            <div class="mt-4">
              <div class="flex items-center justify-between">
                <span class="text-[9px] font-medium text-slate-600">Top-K</span>
                <span class="font-mono text-[10px] font-semibold text-indigo-500">{{ topK }}</span>
              </div>
              <el-slider
                v-model="topK"
                :min="1"
                :max="10"
                :step="1"
                :disabled="isLoading"
                show-stops
              />
            </div>

            <div class="mt-3">
              <div class="flex items-center justify-between">
                <span class="text-[9px] font-medium text-slate-600">相似度阈值</span>
                <span class="font-mono text-[10px] font-semibold text-cyan-600">
                  {{ threshold.toFixed(2) }}
                </span>
              </div>
              <el-slider
                v-model="threshold"
                :min="MIN_THRESHOLD"
                :max="MAX_THRESHOLD"
                :step="0.01"
                :disabled="isLoading"
                :format-tooltip="formatTooltip"
              />
            </div>

            <div class="mt-3">
              <p class="mb-1.5 text-[9px] font-medium text-slate-600">检索模式</p>
              <div class="app-tab-bar w-full">
                <button
                  v-for="mode in retrievalModeOptions"
                  :key="mode.value"
                  type="button"
                  class="app-tab flex-1 justify-center"
                  :class="{ 'is-active': retrievalMode === mode.value }"
                  :disabled="isLoading"
                  @click="retrievalMode = mode.value"
                >
                  {{ mode.label }}
                </button>
              </div>
            </div>

            <div class="mt-3 rounded-lg border border-slate-100 bg-slate-50/70 px-2.5 py-2">
              <p class="font-mono text-[8px] leading-4 text-slate-500">
                mode={{ retrievalMode }}<br />
                recall(k={{ topK }}) → filter(score ≥ {{ threshold.toFixed(2) }}) → rerank
              </p>
            </div>
            <router-link
              :to="{ name: 'knowledge' }"
              class="mt-2.5 flex items-center justify-center gap-1 text-[8px] text-slate-400 transition hover:text-indigo-500"
            >
              在知识库管理中调整并保存
              <span>→</span>
            </router-link>
          </section>

          <div class="border-y border-[#c9bdab] bg-[#fbf7ee] p-3.5">
            <div class="flex items-start gap-2.5">
              <span class="mt-0.5 grid h-6 w-6 shrink-0 place-items-center border border-[#c99f98] text-[#7d302f]">
                <el-icon :size="10"><DataAnalysis /></el-icon>
              </span>
              <div>
                <p class="font-mono text-[7.5px] font-medium uppercase tracking-[0.1em] text-[#7d302f]">Exhibition note / 展示提示</p>
                <p class="mt-1.5 text-[8.5px] leading-4 text-[#766b5b]">
                  当前使用「{{ currentModeLabel }}」。调整参数后重新检索，可直观对比召回集合、排序与相似度分布的变化。
                </p>
              </div>
            </div>
          </div>
        </aside>

        <main class="min-w-0">
          <div v-if="isLoading" class="surface-card min-h-[560px] p-5">
            <div class="flex items-center gap-3">
              <div class="skeleton h-9 w-9 rounded-xl" />
              <div class="flex-1">
                <div class="skeleton h-2.5 w-40" />
                <div class="skeleton mt-2 h-2 w-24" />
              </div>
              <div class="skeleton h-6 w-20 rounded-lg" />
            </div>
            <div class="mt-5 grid grid-cols-2 gap-2 sm:grid-cols-4">
              <div v-for="index in 4" :key="index" class="rounded-xl border border-slate-100 p-3">
                <div class="skeleton h-2 w-12" />
                <div class="skeleton mt-2 h-4 w-16" />
              </div>
            </div>
            <div class="mt-5 space-y-3">
              <div v-for="index in 3" :key="index" class="rounded-2xl border border-slate-100 p-4">
                <div class="flex gap-3">
                  <div class="skeleton h-8 w-8 rounded-lg" />
                  <div class="flex-1">
                    <div class="skeleton h-3 w-2/5" />
                    <div class="skeleton mt-2 h-2 w-3/5" />
                    <div class="skeleton mt-3 h-12 w-full rounded-xl" />
                  </div>
                </div>
              </div>
            </div>
            <div class="mt-4 flex items-center justify-center gap-2 text-[9px] text-indigo-400">
              <span class="h-1.5 w-1.5 animate-ping rounded-full bg-indigo-400" />
              正在执行向量化、召回与重排序…
            </div>
          </div>

          <div v-else-if="errorMessage" class="surface-card min-h-[480px]">
            <StatePanel
              type="error"
              title="检索请求失败"
              :description="errorMessage"
              action-text="重新检索"
              @action="handleSearch"
            />
          </div>

          <div
            v-else-if="!response"
            class="surface-card relative flex min-h-[560px] flex-col items-center justify-center overflow-hidden px-6 py-14 text-center"
          >
            <div class="pointer-events-none absolute inset-0" aria-hidden="true">
              <div class="absolute inset-0 dot-grid opacity-[0.12]" />
              <div class="absolute inset-y-8 left-1/2 w-px bg-[#e2d9ca]" />
              <span class="absolute left-1/2 top-10 -translate-x-1/2 font-serif text-[180px] leading-none text-[#7d302f]/[0.035]">§</span>
              <div class="absolute inset-x-8 top-8 h-px bg-[#e2d9ca]" />
            </div>

            <div class="relative">
              <div class="relative mx-auto h-24 w-24">
                <span class="absolute inset-0 border border-[#d8cebd]" />
                <span class="absolute inset-3 border border-dashed border-[#c9bdab]" />
                <span class="absolute inset-6 bg-[#fbf5e9]" />
                <span class="absolute inset-0 grid place-items-center">
                  <span class="grid h-10 w-10 place-items-center border border-[#7d302f]/40 bg-[#fbf5e9] text-[#682728]">
                    <el-icon :size="18"><Search /></el-icon>
                  </span>
                </span>
                <span class="absolute right-1 top-4 h-1.5 w-1.5 bg-[#a37b2b]" />
                <span class="absolute bottom-4 left-0 h-1 w-1 bg-[#7d302f]" />
              </div>

              <p class="mt-6 text-[8px] font-semibold uppercase tracking-[0.2em] text-indigo-400">
                Retrieval Observability
              </p>
              <h2 class="mt-2 font-serif text-[26px] font-medium tracking-[-0.02em] text-ink-950">看见每一次召回</h2>
              <p class="mx-auto mt-2 max-w-[400px] text-[10px] leading-5 text-slate-500">
                输入问题后，系统会展示召回片段的原文、相似度分数、来源课程与知识点 ID，
                让 RAG 不再是一个黑盒。
              </p>

              <div class="mx-auto mt-7 flex max-w-[520px] flex-wrap items-center justify-center gap-1.5">
                <span class="pipeline-step"><b>01</b> Query</span>
                <el-icon :size="10" class="text-slate-300"><ArrowRight /></el-icon>
                <span class="pipeline-step"><b>02</b> Embedding</span>
                <el-icon :size="10" class="text-slate-300"><ArrowRight /></el-icon>
                <span class="pipeline-step"><b>03</b> Top-K</span>
                <el-icon :size="10" class="text-slate-300"><ArrowRight /></el-icon>
                <span class="pipeline-step"><b>04</b> Rerank</span>
              </div>

              <div class="mt-7 flex flex-wrap justify-center gap-2 text-[8px] text-slate-400">
                <span class="empty-feature"><Search /> 证据片段</span>
                <span class="empty-feature"><TrendCharts /> 相似度分数</span>
                <span class="empty-feature"><Timer /> 阶段耗时</span>
              </div>
            </div>
          </div>

          <section v-else class="space-y-3.5">
            <div class="surface-card overflow-hidden">
              <div class="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 px-5 py-4">
                <div class="min-w-0">
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="grid h-6 w-6 place-items-center rounded-md bg-indigo-50 text-indigo-500">
                      <el-icon :size="11"><Search /></el-icon>
                    </span>
                    <p class="text-[8px] font-semibold uppercase tracking-[0.16em] text-slate-400">
                      Retrieval Debugger
                    </p>
                    <span class="h-1 w-1 rounded-full bg-emerald-400" />
                    <span class="font-mono text-[7.5px] text-emerald-500">SUCCESS</span>
                  </div>
                  <h2 class="mt-2 max-w-[620px] font-serif text-[15px] font-semibold leading-6 text-slate-700">
                    「{{ response.query }}」
                  </h2>
                  <div class="mt-1.5 flex flex-wrap items-center gap-2 text-[8px] text-slate-400">
                    <span class="rounded border border-indigo-100 bg-indigo-50 px-1.5 py-0.5 text-indigo-500">
                      {{ getRetrievalModeLabel(response.config.retrievalMode) }}
                    </span>
                    <span>Top-K {{ response.config.topK }}</span>
                    <span class="text-slate-200">·</span>
                    <span>阈值 {{ response.config.threshold.toFixed(2) }}</span>
                    <span class="text-slate-200">·</span>
                    <span>MMR Diversity On</span>
                  </div>
                </div>
                <div class="shrink-0 text-right">
                  <p class="font-mono text-[25px] font-semibold leading-none text-indigo-600">
                    {{ response.chunks.length }}
                    <span class="text-[10px] text-slate-400">/ {{ response.config.topK }}</span>
                  </p>
                  <p class="mt-1 text-[8px] text-slate-400">召回片段</p>
                </div>
              </div>

              <div class="grid grid-cols-2 divide-x divide-slate-100 sm:grid-cols-4">
                <div
                  v-for="metric in metrics"
                  :key="metric.label"
                  class="border-b border-slate-100 px-4 py-3 sm:border-b-0"
                >
                  <div class="flex items-center gap-1.5">
                    <span class="grid h-4 w-4 place-items-center rounded border" :class="metric.tone">
                      <el-icon :size="8"><component :is="metric.icon" /></el-icon>
                    </span>
                    <span class="text-[8px] text-slate-400">{{ metric.label }}</span>
                  </div>
                  <p class="mt-1.5 font-mono text-[13px] font-semibold text-slate-700">
                    {{ metric.value }}
                  </p>
                  <p class="mt-0.5 truncate font-mono text-[7px] text-slate-300">{{ metric.hint }}</p>
                </div>
              </div>

              <div
                v-if="configDirty"
                class="flex flex-wrap items-center justify-between gap-2 border-t border-amber-100 bg-amber-50/70 px-5 py-2.5"
              >
                <p class="flex items-center gap-1.5 text-[9px] text-amber-600">
                  <span class="h-1.5 w-1.5 rounded-full bg-amber-400" />
                  参数已修改，当前结果仍基于上一次配置
                </p>
                <button
                  type="button"
                  class="rounded-md border border-amber-200 bg-white px-2 py-1 text-[8px] font-medium text-amber-600 transition hover:bg-amber-100"
                  @click="handleSearch"
                >
                  使用新参数重新检索
                </button>
              </div>
            </div>

            <div v-if="response.chunks.length" class="space-y-3">
              <div class="flex items-end justify-between px-1">
                <div>
                  <h3 class="font-serif text-[14px] font-semibold text-slate-700">召回片段</h3>
                  <p class="mt-0.5 text-[8.5px] text-slate-400">
                    按重排序后的相关度降序展示，最高相似度
                    <span class="font-mono text-emerald-500">{{ highestScore.toFixed(3) }}</span>
                  </p>
                </div>
                <span class="font-mono text-[8px] text-slate-400">SIMILARITY DESC</span>
              </div>

              <RetrievalResultCard
                v-for="(chunk, index) in response.chunks"
                :key="chunk.id"
                :chunk="chunk"
                :rank="index + 1"
              />

              <p class="pt-1 text-center font-mono text-[7.5px] leading-4 text-slate-300">
                LIVE RETRIEVAL · {{ systemStore.health?.embedding.provider ?? 'local' }}
                {{ systemStore.health?.embedding.dim ?? '—' }}d · HYBRID / VECTOR / KEYWORD
              </p>
            </div>

            <div v-else class="surface-card">
              <StatePanel
                type="empty"
                title="没有召回到符合条件的片段"
                :description="`当前为「${getRetrievalModeLabel(response.config.retrievalMode)}」，相似度阈值为 ${response.config.threshold.toFixed(2)}。没有片段达到这个门槛，可以降低阈值或更换检索问题。`"
                action-text="降低阈值并重新检索"
                @action="lowerThresholdAndRetry"
              />
            </div>
          </section>
        </main>
      </div>
    </div>
  </div>
</template>

<style scoped>
.rag-sample-chip {
  padding: 2px 1px;
  color: #6f6456;
  font-size: 10px;
  line-height: 1.6;
  text-align: left;
  background: transparent;
  border: 0;
  border-bottom: 1px solid #d8cebd;
  border-radius: 0;
  cursor: pointer;
  transition: all 0.16s ease;
}

.rag-sample-chip:hover:not(:disabled) {
  color: #7d302f;
  border-bottom-color: #7d302f;
}

.rag-sample-chip:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.pipeline-step {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 8px;
  color: #6f6456;
  background: #fffdf8;
  border: 1px solid #d8cebd;
  border-radius: 0;
  font-family: var(--app-mono);
  font-size: 10px;
}

.pipeline-step b {
  color: #7d302f;
  font-size: 10px;
}

.empty-feature {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 7px;
  background: #fffdf8;
  border: 1px solid #e2d9ca;
  border-radius: 0;
}

.empty-feature svg {
  width: 9px;
  height: 9px;
}
</style>
