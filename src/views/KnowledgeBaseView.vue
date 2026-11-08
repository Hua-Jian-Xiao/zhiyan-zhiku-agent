<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import type { Component } from 'vue'
import {
  Collection,
  DataAnalysis,
  Document,
  Refresh,
  Setting,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/PageHeader.vue'
import StatePanel from '@/components/feedback/StatePanel.vue'
import { fetchKnowledgeBase } from '@/services/mockApi'
import { useRagStore, MIN_THRESHOLD, MAX_THRESHOLD } from '@/stores/rag'
import { defaultRagConfig } from '@/data/mockData'
import type { KnowledgeBaseOverview, KnowledgePoint } from '@/types'
import { isAbortError } from '@/utils/async'

const ragStore = useRagStore()

const overview = ref<KnowledgeBaseOverview | null>(null)
const isLoading = ref(true)
const errorMessage = ref('')
const isSaving = ref(false)
const draftTopK = ref(ragStore.config.topK)
const draftThreshold = ref(ragStore.config.threshold)
let controller: AbortController | null = null

interface StatItem {
  label: string
  value: string
  suffix: string
  hint: string
  icon: Component
  iconClass: string
  barClass: string
}

const stats = computed<StatItem[]>(() => [
  {
    label: '课程总数',
    value: String(overview.value?.courseCount ?? 0),
    suffix: '门',
    hint: '全部课程已建立检索索引',
    icon: Collection,
    iconClass: 'bg-indigo-50 text-indigo-500 border-indigo-100',
    barClass: 'bg-indigo-400',
  },
  {
    label: '知识点总数',
    value: String(overview.value?.knowledgePointCount ?? 0),
    suffix: '个',
    hint: '覆盖 8 个计算机学科方向',
    icon: DataAnalysis,
    iconClass: 'bg-cyan-50 text-cyan-500 border-cyan-100',
    barClass: 'bg-cyan-400',
  },
  {
    label: '知识片段',
    value: (overview.value?.chunkCount ?? 0).toLocaleString('en-US'),
    suffix: '条',
    hint: '平均每个知识点 4 个片段',
    icon: Document,
    iconClass: 'bg-emerald-50 text-emerald-500 border-emerald-100',
    barClass: 'bg-emerald-400',
  },
  {
    label: '最近同步',
    value: overview.value?.lastSyncedAt ?? '—',
    suffix: '',
    hint: '知识索引健康，可正常检索',
    icon: Refresh,
    iconClass: 'bg-amber-50 text-amber-500 border-amber-100',
    barClass: 'bg-amber-400',
  },
])

const configDirty = computed(
  () =>
    draftTopK.value !== ragStore.config.topK ||
    Math.abs(draftThreshold.value - ragStore.config.threshold) > 0.0001,
)

const recentKnowledgePoints = computed(() => overview.value?.knowledgePoints.slice(0, 6) ?? [])

async function loadKnowledgeBase(showToast = false): Promise<void> {
  controller?.abort()
  const currentController = new AbortController()
  controller = currentController
  isLoading.value = true
  errorMessage.value = ''

  try {
    const data = await fetchKnowledgeBase(currentController.signal)
    if (currentController.signal.aborted) return
    overview.value = data
    if (showToast) ElMessage.success('知识库索引已刷新')
  } catch (error) {
    if (!isAbortError(error)) {
      errorMessage.value = error instanceof Error ? error.message : '知识库加载失败，请重试'
    }
  } finally {
    if (controller === currentController) isLoading.value = false
  }
}

function formatTopK(value: number): string {
  return `Top-${value}`
}

function formatThreshold(value: number): string {
  return value.toFixed(2)
}

async function saveConfig(): Promise<void> {
  if (isSaving.value) return
  isSaving.value = true
  await new Promise((resolve) => window.setTimeout(resolve, 360))
  ragStore.updateConfig({
    topK: draftTopK.value,
    threshold: draftThreshold.value,
  })
  isSaving.value = false
  ElMessage.success('RAG 检索参数已同步到 Agent 与检索调试页')
}

function resetConfig(): void {
  draftTopK.value = defaultRagConfig.topK
  draftThreshold.value = defaultRagConfig.threshold
  ragStore.updateConfig({ ...defaultRagConfig })
  ElMessage.success('已恢复默认检索参数')
}

function difficultyClass(difficulty: KnowledgePoint['difficulty']): string {
  if (difficulty === '入门') return 'border-emerald-100 bg-emerald-50 text-emerald-600'
  if (difficulty === '进阶') return 'border-indigo-100 bg-indigo-50 text-indigo-600'
  return 'border-amber-100 bg-amber-50 text-amber-600'
}

onMounted(() => {
  void loadKnowledgeBase()
})

onBeforeUnmount(() => {
  controller?.abort()
})
</script>

<template>
  <div class="page-scroll">
    <div class="page-container">
      <PageHeader
        eyebrow="Knowledge Operations"
        title="知识库管理"
        description="管理计算机学科课程索引，并调整 RAG 检索的召回范围与相似度门槛。配置会实时同步到 Agent 工作台和检索调试页。"
      >
        <template #actions>
          <span
            class="hidden items-center gap-1.5 rounded-lg border border-emerald-100 bg-emerald-50 px-2.5 py-1.5 text-[9px] font-medium text-emerald-600 sm:inline-flex"
          >
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            索引健康
          </span>
          <el-button :loading="isLoading" @click="loadKnowledgeBase(true)">
            <el-icon v-if="!isLoading" class="mr-1"><Refresh /></el-icon>
            刷新索引
          </el-button>
        </template>
      </PageHeader>

      <div v-if="isLoading && !overview" class="mt-7">
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div v-for="index in 4" :key="index" class="surface-card p-4">
            <div class="flex items-center justify-between">
              <div class="skeleton h-8 w-8 rounded-lg" />
              <div class="skeleton h-2 w-12" />
            </div>
            <div class="skeleton mt-4 h-7 w-20" />
            <div class="skeleton mt-2.5 h-2 w-32" />
          </div>
        </div>
        <div class="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
          <div class="surface-card p-5">
            <div class="skeleton h-4 w-32" />
            <div class="mt-5 grid gap-3 sm:grid-cols-2">
              <div v-for="index in 4" :key="index" class="rounded-2xl border border-slate-100 p-4">
                <div class="flex gap-3">
                  <div class="skeleton h-10 w-10 rounded-xl" />
                  <div class="flex-1">
                    <div class="skeleton h-3 w-24" />
                    <div class="skeleton mt-2 h-2 w-16" />
                  </div>
                </div>
                <div class="skeleton mt-4 h-2 w-full" />
                <div class="skeleton mt-2 h-2 w-3/4" />
                <div class="mt-4 flex gap-2">
                  <div class="skeleton h-5 w-14 rounded-md" />
                  <div class="skeleton h-5 w-14 rounded-md" />
                </div>
              </div>
            </div>
          </div>
          <div class="surface-card h-[390px] p-5">
            <div class="skeleton h-4 w-28" />
            <div class="mt-6 skeleton h-2 w-20" />
            <div class="skeleton mt-2 h-9 w-full" />
            <div class="mt-6 skeleton h-2 w-24" />
            <div class="skeleton mt-2 h-9 w-full" />
            <div class="mt-7 skeleton h-10 w-full rounded-xl" />
          </div>
        </div>
      </div>

      <div v-else-if="errorMessage" class="surface-card mt-7">
        <StatePanel
          type="error"
          title="知识库加载失败"
          :description="errorMessage"
          action-text="重新加载"
          @action="loadKnowledgeBase()"
        />
      </div>

      <template v-else-if="overview">
        <div class="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div
            v-for="stat in stats"
            :key="stat.label"
            class="surface-card group relative overflow-hidden p-4 transition duration-200 hover:-translate-y-0.5 hover:shadow-soft"
          >
            <div class="flex items-start justify-between">
              <div
                class="grid h-8 w-8 place-items-center rounded-lg border"
                :class="stat.iconClass"
              >
                <el-icon :size="15"><component :is="stat.icon" /></el-icon>
              </div>
              <span class="font-mono text-[8px] uppercase tracking-wider text-slate-300">
                {{ stat.label }}
              </span>
            </div>
            <div class="mt-4 flex items-end gap-1.5">
              <span
                class="font-mono text-[24px] font-semibold leading-none tracking-tight text-ink-950"
                :class="stat.label === '最近同步' ? '!text-[15px]' : ''"
              >
                {{ stat.value }}
              </span>
              <span v-if="stat.suffix" class="mb-0.5 text-[9px] text-slate-400">{{ stat.suffix }}</span>
            </div>
            <p class="mt-2 flex items-center gap-1.5 text-[8.5px] text-slate-400">
              <span class="h-1 w-1 rounded-full" :class="stat.barClass" />
              {{ stat.hint }}
            </p>
          </div>
        </div>

        <div class="mt-5 grid items-start gap-5 xl:grid-cols-[minmax(0,1fr)_356px]">
          <div class="min-w-0 space-y-5">
            <section class="surface-card p-5">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-[12px] font-semibold text-slate-700">课程索引</p>
                  <p class="mt-1 text-[9px] text-slate-400">
                    {{ overview.courseCount }} 门课程 · {{ overview.documentCount }} 份课程文档
                  </p>
                </div>
                <span
                  class="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-2 py-1 text-[8px] text-slate-500"
                >
                  <span class="h-1 w-1 rounded-full bg-emerald-400" />
                  全部可检索
                </span>
              </div>

              <div class="mt-4 grid gap-3 md:grid-cols-2">
                <article
                  v-for="course in overview.courses"
                  :key="course.id"
                  class="group rounded-2xl border border-slate-100 bg-white p-3.5 transition-all duration-200 hover:border-indigo-100 hover:bg-indigo-50/[0.16] hover:shadow-[0_14px_36px_-30px_rgba(79,70,229,0.4)]"
                >
                  <div class="flex items-start gap-3">
                    <span
                      class="grid h-9 w-9 shrink-0 place-items-center rounded-xl text-[10px] font-bold"
                      :style="{
                        color: course.color,
                        backgroundColor: `${course.color}12`,
                        border: `1px solid ${course.color}1f`,
                      }"
                    >
                      {{ course.shortName }}
                    </span>
                    <div class="min-w-0 flex-1">
                      <div class="flex items-center justify-between gap-2">
                        <h3 class="truncate text-[11px] font-semibold text-slate-700">
                          {{ course.name }}
                        </h3>
                        <span class="shrink-0 font-mono text-[7.5px] text-slate-300">
                          {{ course.code }}
                        </span>
                      </div>
                      <p class="mt-0.5 truncate text-[8px] text-slate-400">
                        {{ course.teacher }} · 更新于 {{ course.updatedAt }}
                      </p>
                    </div>
                  </div>
                  <p class="mt-2.5 line-clamp-2 text-[9px] leading-4 text-slate-500">
                    {{ course.description }}
                  </p>
                  <div class="mt-3 flex items-center gap-1.5">
                    <span class="rounded-md border border-slate-100 bg-slate-50 px-1.5 py-0.5 text-[8px] text-slate-500">
                      {{ course.knowledgePointCount }} 知识点
                    </span>
                    <span class="rounded-md border border-slate-100 bg-slate-50 px-1.5 py-0.5 text-[8px] text-slate-500">
                      {{ course.documentCount }} 文档
                    </span>
                    <span class="ml-auto flex items-center gap-1 text-[7.5px] text-emerald-500">
                      <span class="h-1 w-1 rounded-full bg-emerald-400" />
                      已索引
                    </span>
                  </div>
                </article>
              </div>
            </section>

            <section class="surface-card overflow-hidden">
              <div class="flex items-center justify-between border-b border-slate-100 px-5 py-4">
                <div>
                  <p class="text-[12px] font-semibold text-slate-700">最近更新的知识点</p>
                  <p class="mt-1 text-[9px] text-slate-400">展示当前知识库中最近入库的内容抽样</p>
                </div>
                <span class="font-mono text-[8px] text-slate-400">
                  {{ recentKnowledgePoints.length }} / {{ overview.knowledgePointCount }}
                </span>
              </div>
              <div class="divide-y divide-slate-50">
                <div
                  v-for="point in recentKnowledgePoints"
                  :key="point.id"
                  class="grid grid-cols-[minmax(0,1fr)_82px_56px] items-center gap-3 px-5 py-3 transition hover:bg-slate-50/60 sm:grid-cols-[minmax(0,1fr)_150px_70px_60px]"
                >
                  <div class="flex min-w-0 items-center gap-2.5">
                    <span class="grid h-6 w-6 shrink-0 place-items-center rounded-md bg-slate-50 text-slate-400">
                      <el-icon :size="10"><Document /></el-icon>
                    </span>
                    <div class="min-w-0">
                      <p class="truncate text-[10px] font-medium text-slate-700">{{ point.name }}</p>
                      <p class="mt-0.5 truncate text-[8px] text-slate-400">{{ point.chapter }}</p>
                    </div>
                  </div>
                  <span class="hidden truncate text-[8.5px] text-slate-400 sm:block">{{ point.course }}</span>
                  <span
                    class="justify-self-start rounded border px-1.5 py-0.5 text-[7.5px]"
                    :class="difficultyClass(point.difficulty)"
                  >
                    {{ point.difficulty }}
                  </span>
                  <span class="justify-self-end font-mono text-[7.5px] text-slate-400">
                    {{ point.updatedAt.slice(5) }}
                  </span>
                </div>
              </div>
            </section>
          </div>

          <aside class="surface-card sticky top-5 overflow-hidden">
            <div class="relative overflow-hidden border-b border-slate-100 bg-[#0b1326] px-5 py-5 text-white">
              <div class="pointer-events-none absolute -right-8 -top-10 h-32 w-32 rounded-full bg-indigo-500/22 blur-3xl" />
              <div class="pointer-events-none absolute inset-0 dot-grid opacity-[0.06]" />
              <div class="relative flex items-start gap-3">
                <span class="grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-white/10 bg-white/[0.06] text-cyan-300">
                  <el-icon :size="17"><Setting /></el-icon>
                </span>
                <div>
                  <h3 class="text-[13px] font-semibold text-white">RAG 检索配置</h3>
                  <p class="mt-1 text-[9px] leading-4 text-slate-400">
                    调整召回范围与相似度门槛，影响 Agent 回答所依赖的知识证据。
                  </p>
                </div>
              </div>
            </div>

            <div class="p-5">
              <div>
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-[10px] font-semibold text-slate-700">Top-K 召回数量</p>
                    <p class="mt-0.5 text-[8px] text-slate-400">单次检索最多返回的知识片段数</p>
                  </div>
                  <span class="rounded-lg border border-indigo-100 bg-indigo-50 px-2 py-1 font-mono text-[10px] font-semibold text-indigo-600">
                    {{ draftTopK }}
                  </span>
                </div>
                <el-slider
                  v-model="draftTopK"
                  :min="1"
                  :max="10"
                  :step="1"
                  show-stops
                  :format-tooltip="formatTopK"
                  class="!mt-3"
                />
                <div class="flex justify-between font-mono text-[7.5px] text-slate-300">
                  <span>1</span>
                  <span>10</span>
                </div>
              </div>

              <div class="mt-6">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-[10px] font-semibold text-slate-700">相似度阈值</p>
                    <p class="mt-0.5 text-[8px] text-slate-400">低于此分数的片段会被过滤</p>
                  </div>
                  <span class="rounded-lg border border-cyan-100 bg-cyan-50 px-2 py-1 font-mono text-[10px] font-semibold text-cyan-600">
                    {{ draftThreshold.toFixed(2) }}
                  </span>
                </div>
                <el-slider
                  v-model="draftThreshold"
                  :min="MIN_THRESHOLD"
                  :max="MAX_THRESHOLD"
                  :step="0.01"
                  :format-tooltip="formatThreshold"
                  class="!mt-3"
                />
                <div class="flex justify-between font-mono text-[7.5px] text-slate-300">
                  <span>{{ MIN_THRESHOLD.toFixed(1) }}</span>
                  <span>{{ MAX_THRESHOLD.toFixed(2) }}</span>
                </div>
              </div>

              <div class="mt-5 rounded-xl border border-slate-100 bg-slate-50/70 p-3">
                <div class="flex items-center gap-1.5">
                  <span class="h-1.5 w-1.5 rounded-full bg-indigo-400" />
                  <p class="text-[8px] font-semibold text-slate-500">当前策略</p>
                </div>
                <p class="mt-1.5 font-mono text-[9px] leading-4 text-slate-500">
                  recall(top_k={{ draftTopK }})<br />
                  → filter(score ≥ {{ draftThreshold.toFixed(2) }})<br />
                  → rerank → context
                </p>
                <p class="mt-2 border-t border-slate-200/60 pt-2 text-[8px] leading-4 text-slate-400">
                  阈值越高，回答越保守；阈值过低可能引入不相关证据。
                </p>
              </div>

              <div class="mt-4 flex gap-2">
                <el-button
                  type="primary"
                  class="!flex-1"
                  :loading="isSaving"
                  :disabled="!configDirty"
                  @click="saveConfig"
                >
                  {{ configDirty ? '保存并同步' : '已是最新配置' }}
                </el-button>
                <el-button :disabled="isSaving" @click="resetConfig">默认值</el-button>
              </div>
              <router-link
                :to="{ name: 'rag-debug' }"
                class="mt-3 flex items-center justify-center gap-1 text-[9px] font-medium text-indigo-500 transition hover:text-indigo-600"
              >
                去 RAG 检索调试验证效果
                <span>→</span>
              </router-link>
            </div>
          </aside>
        </div>
      </template>
    </div>
  </div>
</template>
