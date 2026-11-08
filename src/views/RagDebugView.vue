<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Aim,
  ArrowRight,
  DataAnalysis,
  Document,
  Filter,
  Search,
  Timer,
  TrendCharts,
} from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import StatePanel from '@/components/feedback/StatePanel.vue'
import RetrievalResultCard from '@/components/rag/RetrievalResultCard.vue'
import { retrieveKnowledge } from '@/services/mockApi'
import { ragSampleQueries } from '@/data/mockData'
import { useRagStore, MIN_THRESHOLD, MAX_THRESHOLD } from '@/stores/rag'
import type { RetrievalResponse } from '@/types'
import { isAbortError } from '@/utils/async'

const ragStore = useRagStore()

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

const configDirty = computed(() => {
  if (!response.value) return false
  return (
    response.value.config.topK !== ragStore.config.topK ||
    Math.abs(response.value.config.threshold - ragStore.config.threshold) > 0.0001
  )
})

const metrics = computed(() => {
  if (!response.value) return []
  const result = response.value
  return [
    {
      label: '总耗时',
      value: `${result.metrics.totalMs} ms`,
      hint: '端到端检索',
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
      label: '向量召回',
      value: `${result.metrics.searchMs} ms`,
      hint: 'Hybrid ANN search',
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
        eyebrow="RAG Playground"
        title="RAG 检索调试"
        description="输入问题，观察知识库召回的每一个片段与相似度分数。所有参数与知识库管理页共享，适合演示检索链路与召回质量。"
      >
        <template #actions>
          <span
            class="hidden items-center gap-1.5 rounded-lg border border-emerald-100 bg-emerald-50 px-2.5 py-1.5 text-[9px] font-medium text-emerald-600 sm:inline-flex"
          >
            <span class="h-1.5 w-1.5 animate-soft-pulse rounded-full bg-emerald-400" />
            Vector Index Ready
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
                  <p class="text-[11px] font-semibold text-slate-700">输入检索问题</p>
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

            <div class="mt-2 rounded-lg border border-slate-100 bg-slate-50/70 px-2.5 py-2">
              <p class="font-mono text-[8px] leading-4 text-slate-500">
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

          <div class="rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50/80 to-cyan-50/50 p-3.5">
            <div class="flex items-start gap-2">
              <span class="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-md bg-white text-indigo-500 shadow-sm">
                <el-icon :size="10"><DataAnalysis /></el-icon>
              </span>
              <div>
                <p class="text-[9px] font-semibold text-indigo-700">竞赛展示提示</p>
                <p class="mt-1 text-[8px] leading-4 text-indigo-500/80">
                  展开片段可查看完整知识证据；调整阈值可直观观察召回集合的变化。分数由确定性 Mock 数据生成，可重复复现。
                </p>
              </div>
            </div>
          </div>
        </aside>

        <main class="min-w-0">
          <div
            v-if="isLoading"
            class="surface-card min-h-[560px] p-5"
          >
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
              正在执行混合检索与重排序…
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
              <div class="absolute left-1/2 top-1/3 h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full bg-indigo-100/40 blur-[80px]" />
              <div class="absolute bottom-[5%] right-[12%] h-44 w-44 rounded-full bg-cyan-100/45 blur-[60px]" />
              <div class="absolute inset-0 dot-grid opacity-[0.14]" />
            </div>

            <div class="relative">
              <div class="relative mx-auto h-24 w-24">
                <span class="absolute inset-0 rounded-full border border-indigo-100/80" />
                <span class="absolute inset-3 rounded-full border border-dashed border-indigo-200/80" />
                <span class="absolute inset-6 rounded-full border border-cyan-100 bg-white/70 shadow-sm" />
                <span class="absolute inset-0 grid place-items-center">
                  <span class="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-400 text-white shadow-[0_10px_26px_-12px_rgba(79,70,229,0.7)]">
                    <el-icon :size="18"><Search /></el-icon>
                  </span>
                </span>
                <span class="absolute right-1 top-4 h-1.5 w-1.5 rounded-full bg-cyan-400" />
                <span class="absolute bottom-4 left-0 h-1 w-1 rounded-full bg-indigo-400" />
              </div>

              <p class="mt-6 text-[8px] font-semibold uppercase tracking-[0.2em] text-indigo-400">
                Retrieval Observability
              </p>
              <h2 class="mt-2 text-[22px] font-bold tracking-tight text-ink-950">看见每一次召回</h2>
              <p class="mx-auto mt-2 max-w-[400px] text-[10px] leading-5 text-slate-500">
                输入问题后，系统会展示召回片段、相似度分数与检索各阶段耗时，
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
                <span class="empty-feature"><Document /> 证据片段</span>
                <span class="empty-feature"><TrendCharts /> 相似度分数</span>
                <span class="empty-feature"><Timer /> 阶段耗时</span>
              </div>
            </div>
          </div>

          <section v-else class="space-y-3.5">
            <div class="surface-card overflow-hidden">
              <div class="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 px-5 py-4">
                <div class="min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="grid h-6 w-6 place-items-center rounded-md bg-indigo-50 text-indigo-500">
                      <el-icon :size="11"><Search /></el-icon>
                    </span>
                    <p class="text-[8px] font-semibold uppercase tracking-[0.16em] text-slate-400">
                      Retrieval Response
                    </p>
                    <span class="h-1 w-1 rounded-full bg-emerald-400" />
                    <span class="font-mono text-[7.5px] text-emerald-500">SUCCESS</span>
                  </div>
                  <h2 class="mt-2 max-w-[620px] text-[13px] font-semibold leading-6 text-slate-700">
                    「{{ response.query }}」
                  </h2>
                  <div class="mt-1.5 flex flex-wrap items-center gap-2 text-[8px] text-slate-400">
                    <span>Top-K {{ response.config.topK }}</span>
                    <span class="text-slate-200">·</span>
                    <span>阈值 {{ response.config.threshold.toFixed(2) }}</span>
                    <span class="text-slate-200">·</span>
                    <span>混合检索 + 重排序</span>
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
                  <p class="mt-0.5 font-mono text-[7px] text-slate-300">{{ metric.hint }}</p>
                </div>
              </div>

              <div
                v-if="configDirty"
                class="flex flex-wrap items-center justify-between gap-2 border-t border-amber-100 bg-amber-50/70 px-5 py-2.5"
              >
                <p class="flex items-center gap-1.5 text-[9px] text-amber-600">
                  <span class="h-1.5 w-1.5 rounded-full bg-amber-400" />
                  参数已修改，当前结果仍基于上一次配置（Top-K {{ response.config.topK }} / 阈值 {{ response.config.threshold.toFixed(2) }}）
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
                  <h3 class="text-[12px] font-semibold text-slate-700">召回片段</h3>
                  <p class="mt-0.5 text-[8.5px] text-slate-400">
                    按重排序后的相关度降序展示，最高相似度
                    <span class="font-mono text-emerald-500">{{ highestScore.toFixed(3) }}</span>
                  </p>
                </div>
                <span class="font-mono text-[8px] text-slate-400">
                  MMR DIVERSITY · ON
                </span>
              </div>

              <RetrievalResultCard
                v-for="(chunk, index) in response.chunks"
                :key="chunk.id"
                :chunk="chunk"
                :rank="index + 1"
              />

              <p class="pt-1 text-center font-mono text-[7.5px] leading-4 text-slate-300">
                MOCK RETRIEVAL · EMBEDDING 768d · BM25 + VECTOR HYBRID · RESULTS ARE DETERMINISTIC
              </p>
            </div>

            <div v-else class="surface-card">
              <StatePanel
                type="empty"
                title="没有召回到符合条件的片段"
                :description="`当前相似度阈值为 ${response.config.threshold.toFixed(2)}，没有片段达到这个门槛。可以降低阈值，或换一个更具体的问题。`"
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
  padding: 3px 7px;
  color: #64748b;
  font-size: 8px;
  line-height: 1.5;
  text-align: left;
  background: #f8fafc;
  border: 1px solid #edf1f7;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.16s ease;
}

.rag-sample-chip:hover:not(:disabled) {
  color: #4f46e5;
  background: #f5f3ff;
  border-color: #ddd6fe;
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
  color: #64748b;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid #e8edf5;
  border-radius: 7px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 8px;
}

.pipeline-step b {
  color: #6366f1;
  font-size: 7px;
}

.empty-feature {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 7px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid #edf1f7;
  border-radius: 6px;
}

.empty-feature svg {
  width: 9px;
  height: 9px;
}
</style>
