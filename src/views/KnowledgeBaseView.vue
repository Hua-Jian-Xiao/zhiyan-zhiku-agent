<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import type { Component } from 'vue'
import {
  Collection,
  DataAnalysis,
  Document,
  Refresh,
  Search,
  Setting,
  Timer,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/PageHeader.vue'
import StatePanel from '@/components/feedback/StatePanel.vue'
import { fetchKnowledgeBase } from '@/services/mockApi'
import { useRagStore, MIN_THRESHOLD, MAX_THRESHOLD } from '@/stores/rag'
import { defaultRagConfig } from '@/mock'
import type {
  KnowledgeBaseOverview,
  KnowledgePoint,
  RetrievalMode,
} from '@/types'
import { isAbortError } from '@/utils/async'
import { retrievalModeOptions } from '@/utils/rag'

const ragStore = useRagStore()

const overview = ref<KnowledgeBaseOverview | null>(null)
const isLoading = ref(true)
const errorMessage = ref('')
const isSaving = ref(false)
const activeTab = ref<'courses' | 'points'>('courses')
const keyword = ref('')
const draftTopK = ref(ragStore.config.topK)
const draftThreshold = ref(ragStore.config.threshold)
const draftMode = ref<RetrievalMode>(ragStore.config.retrievalMode)
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
    label: '课程数量',
    value: String(overview.value?.courseCount ?? 0),
    suffix: '门',
    hint: '全部课程已建立检索索引',
    icon: Collection,
    iconClass: 'bg-indigo-50 text-indigo-500 border-indigo-100',
    barClass: 'bg-indigo-400',
  },
  {
    label: '知识点数量',
    value: String(overview.value?.knowledgePointCount ?? 0),
    suffix: '个',
    hint: '覆盖 8 个计算机学科方向',
    icon: DataAnalysis,
    iconClass: 'bg-cyan-50 text-cyan-500 border-cyan-100',
    barClass: 'bg-cyan-400',
  },
  {
    label: '向量片段数量',
    value: (overview.value?.chunkCount ?? 0).toLocaleString('en-US'),
    suffix: '条',
    hint: '平均每个知识点 4 个片段',
    icon: Document,
    iconClass: 'bg-emerald-50 text-emerald-500 border-emerald-100',
    barClass: 'bg-emerald-400',
  },
  {
    label: '最后更新时间',
    value: overview.value?.lastSyncedAt ?? '—',
    suffix: '',
    hint: '知识索引健康，可正常检索',
    icon: Timer,
    iconClass: 'bg-amber-50 text-amber-500 border-amber-100',
    barClass: 'bg-amber-400',
  },
])

const configDirty = computed(
  () =>
    draftTopK.value !== ragStore.config.topK ||
    Math.abs(draftThreshold.value - ragStore.config.threshold) > 0.0001 ||
    draftMode.value !== ragStore.config.retrievalMode,
)

const normalizedKeyword = computed(() => keyword.value.trim().toLowerCase())

const filteredCourses = computed(() => {
  const courses = overview.value?.courses ?? []
  if (!normalizedKeyword.value) return courses
  return courses.filter((course) =>
    [course.name, course.code, course.teacher, course.shortName]
      .join(' ')
      .toLowerCase()
      .includes(normalizedKeyword.value),
  )
})

const filteredKnowledgePoints = computed(() => {
  const points = overview.value?.knowledgePoints ?? []
  if (!normalizedKeyword.value) return points
  return points.filter((point) =>
    [point.name, point.course, point.chapter, point.id]
      .join(' ')
      .toLowerCase()
      .includes(normalizedKeyword.value),
  )
})

const activeCount = computed(() =>
  activeTab.value === 'courses'
    ? filteredCourses.value.length
    : filteredKnowledgePoints.value.length,
)

const searchPlaceholder = computed(() =>
  activeTab.value === 'courses'
    ? '搜索课程名称、课程号或教师'
    : '搜索知识点名称、课程、章节或 ID',
)

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

function switchTab(tab: 'courses' | 'points'): void {
  activeTab.value = tab
  keyword.value = ''
}

function formatTopK(value: number): string {
  return `Top-${value}`
}

function formatThreshold(value: number): string {
  return value.toFixed(2)
}

async function saveConfig(): Promise<void> {
  if (isSaving.value || !configDirty.value) return
  isSaving.value = true
  await new Promise((resolve) => window.setTimeout(resolve, 320))
  ragStore.updateConfig({
    topK: draftTopK.value,
    threshold: draftThreshold.value,
    retrievalMode: draftMode.value,
  })
  isSaving.value = false
  ElMessage.success('RAG 检索参数已同步到 Agent 与检索调试页')
}

function resetConfig(): void {
  draftTopK.value = defaultRagConfig.topK
  draftThreshold.value = defaultRagConfig.threshold
  draftMode.value = defaultRagConfig.retrievalMode
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
        description="管理计算机学科课程索引，调整 RAG 的召回范围、相似度门槛与检索模式。参数会实时同步到 Agent 工作台和检索调试页。"
      >
        <template #actions>
          <span class="hidden items-center gap-1.5 rounded-lg border border-emerald-100 bg-emerald-50 px-2.5 py-1.5 text-[9px] font-medium text-emerald-600 sm:inline-flex">
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
              <div class="skeleton h-2 w-14" />
            </div>
            <div class="skeleton mt-4 h-7 w-20" />
            <div class="skeleton mt-2.5 h-2 w-32" />
          </div>
        </div>
        <div class="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_356px]">
          <div class="surface-card p-5">
            <div class="flex items-center justify-between">
              <div class="skeleton h-4 w-32" />
              <div class="skeleton h-8 w-48 rounded-lg" />
            </div>
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
          <div class="surface-card h-[450px] p-5">
            <div class="skeleton h-4 w-28" />
            <div class="mt-6 skeleton h-2 w-20" />
            <div class="skeleton mt-2 h-9 w-full" />
            <div class="mt-5 skeleton h-2 w-24" />
            <div class="skeleton mt-2 h-9 w-full" />
            <div class="mt-5 skeleton h-20 w-full rounded-xl" />
            <div class="mt-5 skeleton h-10 w-full rounded-xl" />
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
              <div class="grid h-8 w-8 place-items-center rounded-lg border" :class="stat.iconClass">
                <el-icon :size="15"><component :is="stat.icon" /></el-icon>
              </div>
              <span class="font-mono text-[8px] uppercase tracking-wider text-slate-300">
                {{ stat.label }}
              </span>
            </div>
            <div class="mt-4 flex items-end gap-1.5">
              <span
                class="font-serif text-[30px] font-medium leading-none tracking-[-0.025em] text-ink-950"
                :class="stat.label === '最后更新时间' ? '!text-[16px]' : ''"
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
          <section class="surface-card min-w-0 overflow-hidden">
            <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-4">
              <div class="flex flex-wrap items-center gap-3">
                <div class="app-tab-bar">
                  <button
                    type="button"
                    class="app-tab"
                    :class="{ 'is-active': activeTab === 'courses' }"
                    @click="switchTab('courses')"
                  >
                    <el-icon :size="10"><Collection /></el-icon>
                    课程列表
                    <span class="app-tab-count">{{ overview.courseCount }}</span>
                  </button>
                  <button
                    type="button"
                    class="app-tab"
                    :class="{ 'is-active': activeTab === 'points' }"
                    @click="switchTab('points')"
                  >
                    <el-icon :size="10"><Document /></el-icon>
                    知识点列表
                    <span class="app-tab-count">{{ overview.knowledgePoints.length }}</span>
                  </button>
                </div>
                <span class="hidden text-[8px] text-slate-400 sm:inline">
                  {{ activeTab === 'courses' ? `${overview.documentCount} 份课程文档` : '知识点索引抽样' }}
                </span>
              </div>

              <div class="app-search w-full sm:w-[236px]">
                <el-icon :size="11" class="shrink-0 text-slate-400"><Search /></el-icon>
                <input
                  v-model="keyword"
                  type="search"
                  :placeholder="searchPlaceholder"
                  aria-label="搜索知识库"
                />
              </div>
            </div>

            <div v-if="activeTab === 'courses'" class="p-4">
              <div v-if="filteredCourses.length" class="grid gap-3 md:grid-cols-2">
                <article
                  v-for="course in filteredCourses"
                  :key="course.id"
                  class="group border border-[#ded4c4] border-t-2 border-t-[#bfb29e] bg-[#fffdf8] p-3.5 transition-all duration-200 hover:border-[#b9ab97] hover:border-t-[#7d302f]"
                >
                  <div class="flex items-start gap-3">
                    <span
                      class="grid h-9 w-9 shrink-0 place-items-center font-serif text-[11px] font-semibold"
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
                        <h3 class="truncate font-serif text-[12px] font-semibold text-slate-700">
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
              <StatePanel
                v-else
                compact
                type="empty"
                title="没有匹配的课程"
                description="尝试调整关键词，或清空搜索条件查看全部课程。"
                action-text="清空搜索"
                @action="keyword = ''"
              />
            </div>

            <div v-else>
              <div
                v-if="filteredKnowledgePoints.length"
                class="divide-y divide-slate-50"
              >
                <div
                  v-for="point in filteredKnowledgePoints"
                  :key="point.id"
                  class="grid grid-cols-[minmax(0,1fr)_82px_56px] items-center gap-3 px-5 py-3 transition hover:bg-slate-50/60 sm:grid-cols-[minmax(0,1fr)_150px_70px_60px]"
                >
                  <div class="flex min-w-0 items-center gap-2.5">
                    <span class="grid h-7 w-7 shrink-0 place-items-center rounded-md bg-slate-50 text-slate-400">
                      <el-icon :size="11"><Document /></el-icon>
                    </span>
                    <div class="min-w-0">
                      <p class="truncate text-[10px] font-medium text-slate-700">{{ point.name }}</p>
                      <p class="mt-0.5 flex items-center gap-1.5 truncate text-[8px] text-slate-400">
                        <span class="font-mono text-indigo-400">{{ point.id.toUpperCase() }}</span>
                        <span class="text-slate-200">·</span>
                        {{ point.chapter }}
                      </p>
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
              <StatePanel
                v-else
                type="empty"
                title="没有匹配的知识点"
                description="尝试搜索课程名称、章节或知识点 ID，例如 KP-001。"
                action-text="清空搜索"
                @action="keyword = ''"
              />
            </div>

            <div class="flex items-center justify-between border-t border-slate-100 px-5 py-2.5">
              <span class="text-[8px] text-slate-400">
                当前显示 {{ activeCount }} 条{{ activeTab === 'courses' ? '课程' : '知识点' }}
              </span>
              <span class="font-mono text-[7.5px] text-slate-300">
                MOCK KNOWLEDGE INDEX · 1,284 VECTORS
              </span>
            </div>
          </section>

          <aside class="surface-card sticky top-5 overflow-hidden">
            <div class="relative overflow-hidden border-b border-[#3d3328] bg-[#1a1510] px-5 py-5 text-[#f4ead9]">
              <div class="pointer-events-none absolute inset-0 dot-grid opacity-[0.04]" />
              <span class="absolute -right-1 -top-6 font-serif text-[90px] leading-none text-[#9a463c]/20">§</span>
              <div class="relative flex items-start gap-3">
                <span class="grid h-9 w-9 shrink-0 place-items-center border border-[#5a4b3a] bg-[#241e18] text-[#c39e40]">
                  <el-icon :size="16"><Setting /></el-icon>
                </span>
                <div>
                  <p class="font-mono text-[7px] uppercase tracking-[0.16em] text-[#a49179]">Lab settings / 参数</p>
                  <h3 class="mt-1 font-serif text-[14px] font-medium text-[#f4ead9]">RAG 参数设置</h3>
                  <p class="mt-1.5 text-[8.5px] leading-4 text-[#9d8f7c]">
                    调整召回范围、相似度门槛与检索模式，影响 Agent 使用的知识证据。
                  </p>
                </div>
              </div>
            </div>

            <div class="p-5">
              <div>
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-[10px] font-semibold text-slate-700">Top-K 召回数量</p>
                    <p class="mt-0.5 text-[8px] text-slate-400">单次检索最多返回的片段数</p>
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

              <div class="mt-5">
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

              <div class="mt-5">
                <p class="text-[10px] font-semibold text-slate-700">检索模式</p>
                <div class="mt-2 space-y-1.5">
                  <button
                    v-for="mode in retrievalModeOptions"
                    :key="mode.value"
                    type="button"
                    class="w-full rounded-lg border px-2.5 py-2 text-left transition"
                    :class="
                      draftMode === mode.value
                        ? 'border-indigo-200 bg-indigo-50/60'
                        : 'border-slate-100 bg-white hover:border-slate-200'
                    "
                    @click="draftMode = mode.value"
                  >
                    <span class="flex items-center gap-2">
                      <span
                        class="h-1.5 w-1.5 rounded-full"
                        :class="draftMode === mode.value ? 'bg-indigo-500' : 'bg-slate-300'"
                      />
                      <span
                        class="text-[9px] font-semibold"
                        :class="draftMode === mode.value ? 'text-indigo-600' : 'text-slate-600'"
                      >
                        {{ mode.label }}
                      </span>
                      <span class="ml-auto font-mono text-[7px] text-slate-300">
                        {{ mode.shortLabel }}
                      </span>
                    </span>
                    <span class="mt-1 block pl-3.5 text-[7.5px] leading-4 text-slate-400">
                      {{ mode.description }}
                    </span>
                  </button>
                </div>
              </div>

              <div class="mt-4 rounded-xl border border-slate-100 bg-slate-50/70 p-3">
                <div class="flex items-center gap-1.5">
                  <span class="h-1.5 w-1.5 rounded-full bg-indigo-400" />
                  <p class="text-[8px] font-semibold text-slate-500">当前检索策略</p>
                </div>
                <p class="mt-1.5 font-mono text-[9px] leading-4 text-slate-500">
                  {{ draftMode }}<br />
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
