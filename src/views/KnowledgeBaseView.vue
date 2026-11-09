<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import type { Component } from 'vue'
import {
  ArrowRight,
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
import CourseCard from '@/components/knowledge/CourseCard.vue'
import DocumentManager from '@/components/knowledge/DocumentManager.vue'
import KnowledgePointDrawer from '@/components/knowledge/KnowledgePointDrawer.vue'
import { fetchKnowledgeOverview } from '@/services/api'
import { useRagStore, MIN_THRESHOLD, MAX_THRESHOLD } from '@/stores/rag'
import { useSystemStore } from '@/stores/system'
import { DEFAULT_RAG_CONFIG } from '@/constants/rag'
import type {
  DocumentJumpRequest,
  IndexHealth,
  KnowledgeBaseOverview,
  KnowledgePoint,
  RetrievalMode,
} from '@/types'
import { isAbortError } from '@/utils/async'
import { getRetrievalModeOption, retrievalModeOptions } from '@/utils/rag'

const ragStore = useRagStore()
const systemStore = useSystemStore()

const overview = ref<KnowledgeBaseOverview | null>(null)
const isLoading = ref(true)
const errorMessage = ref('')
const isSaving = ref(false)
const activeTab = ref<'courses' | 'points' | 'documents'>('courses')
const keyword = ref('')
const draftTopK = ref(ragStore.config.topK)
const draftThreshold = ref(ragStore.config.threshold)
const draftMode = ref<RetrievalMode>(ragStore.config.retrievalMode)
const listSection = ref<HTMLElement | null>(null)
const pointDrawerOpen = ref(false)
const selectedPoint = ref<KnowledgePoint | null>(null)
const documentJump = ref<DocumentJumpRequest | null>(null)
let documentJumpNonce = 0
let controller: AbortController | null = null

interface StatItem {
  label: string
  value: string
  suffix: string
  hint: string
  icon: Component
  iconClass: string
  barClass: string
  target: 'courses' | 'points' | 'documents'
  targetLabel: string
}

const stats = computed<StatItem[]>(() => [
  {
    label: '课程数量',
    value: String(overview.value?.courseCount ?? 0),
    suffix: '门',
    hint: '全部课程均已建立检索索引',
    icon: Collection,
    iconClass: 'bg-indigo-50 text-indigo-500 border-indigo-100',
    barClass: 'bg-indigo-400',
    target: 'courses',
    targetLabel: '课程列表',
  },
  {
    label: '知识点数量',
    value: String(overview.value?.knowledgePointCount ?? 0),
    suffix: '个',
    hint: `覆盖 ${overview.value?.courseCount ?? 0} 门课程的知识索引`,
    icon: DataAnalysis,
    iconClass: 'bg-cyan-50 text-cyan-500 border-cyan-100',
    barClass: 'bg-cyan-400',
    target: 'points',
    targetLabel: '知识点列表',
  },
  {
    label: '向量片段数量',
    value: (overview.value?.chunkCount ?? 0).toLocaleString('en-US'),
    suffix: '条',
    hint: `${overview.value?.documentCount ?? 0} 份课程文档已建立向量索引`,
    icon: Document,
    iconClass: 'bg-emerald-50 text-emerald-500 border-emerald-100',
    barClass: 'bg-emerald-400',
    target: 'documents',
    targetLabel: '文档库',
  },
  {
    label: '最后更新时间',
    value: overview.value?.lastSyncedAt ?? '—',
    suffix: '',
    hint: '知识索引健康，可正常检索',
    icon: Timer,
    iconClass: 'bg-amber-50 text-amber-500 border-amber-100',
    barClass: 'bg-amber-400',
    target: 'documents',
    targetLabel: '文档库',
  },
])

interface IndexBadge {
  label: string
  dotClass: string
  wrapperClass: string
  details: string
  issues: string[]
}

const indexBadge = computed<IndexBadge>(() => {
  if (errorMessage.value) {
    return {
      label: '索引异常',
      dotClass: 'bg-rose-400',
      wrapperClass: 'border-rose-100 bg-rose-50 text-rose-600',
      details: errorMessage.value,
      issues: [],
    }
  }

  const health = overview.value?.indexHealth
  if (!health) {
    return isLoading.value
      ? {
          label: '索引检查中',
          dotClass: 'bg-slate-300 animate-pulse',
          wrapperClass: 'border-slate-200 bg-slate-50 text-slate-500',
          details: '正在读取知识库索引状态…',
          issues: [],
        }
      : {
          label: '索引状态未知',
          dotClass: 'bg-slate-300',
          wrapperClass: 'border-slate-200 bg-slate-50 text-slate-500',
          details: '暂未获取到索引健康信息。',
          issues: [],
        }
  }

  const tones: Record<IndexHealth['status'], Pick<IndexBadge, 'dotClass' | 'wrapperClass'>> = {
    healthy: {
      dotClass: 'bg-emerald-400',
      wrapperClass: 'border-emerald-100 bg-emerald-50 text-emerald-600',
    },
    indexing: {
      dotClass: 'bg-amber-400 animate-pulse',
      wrapperClass: 'border-amber-100 bg-amber-50 text-amber-600',
    },
    degraded: {
      dotClass: 'bg-amber-400',
      wrapperClass: 'border-amber-100 bg-amber-50 text-amber-600',
    },
    error: {
      dotClass: 'bg-rose-400',
      wrapperClass: 'border-rose-100 bg-rose-50 text-rose-600',
    },
  }
  const tone = tones[health.status] ?? tones.degraded

  return {
    label: health.label,
    ...tone,
    details: `${health.documentCount} 份文档 · ${health.chunkCount} 个片段 · 空向量 ${health.emptyEmbeddingCount} · 最后更新 ${health.lastSyncedAt}`,
    issues: health.issues,
  }
})

const configDirty = computed(
  () =>
    draftTopK.value !== ragStore.config.topK ||
    Math.abs(draftThreshold.value - ragStore.config.threshold) > 0.0001 ||
    draftMode.value !== ragStore.config.retrievalMode,
)

const strategyMode = computed(() => getRetrievalModeOption(draftMode.value))

const strategyFormula = computed(() => {
  if (draftMode.value === 'vector') {
    return '0.84 × 语义分 + 0.16 × 覆盖率'
  }
  if (draftMode.value === 'keyword') {
    return '0.82 × BM25 + 0.18 × 覆盖率'
  }
  return '0.54 × 语义分 + 0.34 × BM25 + 0.12 × 覆盖率'
})

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

const activeCount = computed(() => {
  if (activeTab.value === 'courses') return filteredCourses.value.length
  if (activeTab.value === 'points') return filteredKnowledgePoints.value.length
  return overview.value?.documentCount ?? 0
})

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
    const data = await fetchKnowledgeOverview(currentController.signal)
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

function switchTab(tab: 'courses' | 'points' | 'documents'): void {
  activeTab.value = tab
  keyword.value = ''
}

function handleStatClick(stat: StatItem): void {
  switchTab(stat.target)
  requestAnimationFrame(() => {
    listSection.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

function openPoint(point: KnowledgePoint): void {
  selectedPoint.value = point
  pointDrawerOpen.value = true
}

function jumpToDocuments(request: Omit<DocumentJumpRequest, 'nonce'>): void {
  pointDrawerOpen.value = false
  switchTab('documents')
  documentJumpNonce += 1
  documentJump.value = { ...request, nonce: documentJumpNonce }
  requestAnimationFrame(() => {
    listSection.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

function handleOpenDocument(payload: {
  documentId: string
  courseId: string
  documentTitle: string
}): void {
  jumpToDocuments({
    courseId: payload.courseId,
    documentId: payload.documentId,
    documentTitle: payload.documentTitle,
  })
}

function handleOpenDocuments(payload: { courseId: string }): void {
  jumpToDocuments({ courseId: payload.courseId })
}

function handleDocumentJumpConsumed(): void {
  documentJump.value = null
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
  ragStore.updateConfig({
    topK: draftTopK.value,
    threshold: draftThreshold.value,
    retrievalMode: draftMode.value,
  })
  try {
    await ragStore.persistToServer()
    ElMessage.success('RAG 检索参数已同步到 Agent 与检索调试页')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '保存检索配置失败')
  } finally {
    isSaving.value = false
  }
}

async function resetConfig(): Promise<void> {
  ragStore.resetConfig()
  draftTopK.value = ragStore.config.topK
  draftThreshold.value = ragStore.config.threshold
  draftMode.value = ragStore.config.retrievalMode
  try {
    await ragStore.persistToServer()
    ElMessage.success('已恢复默认检索参数')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '恢复默认参数失败')
  }
}

async function handleDocumentsChanged(): Promise<void> {
  await loadKnowledgeBase()
  await systemStore.loadStats().catch(() => null)
}

function difficultyClass(difficulty: KnowledgePoint['difficulty']): string {
  if (difficulty === '入门') return 'border-emerald-100 bg-emerald-50 text-emerald-600'
  if (difficulty === '进阶') return 'border-indigo-100 bg-indigo-50 text-indigo-600'
  return 'border-amber-100 bg-amber-50 text-amber-600'
}

onMounted(async () => {
  await loadKnowledgeBase()
  try {
    await ragStore.loadFromServer()
    draftTopK.value = ragStore.config.topK
    draftThreshold.value = ragStore.config.threshold
    draftMode.value = ragStore.config.retrievalMode
  } catch {
    // Keep the local cached values when the backend is unreachable.
  }
})

onBeforeUnmount(() => {
  controller?.abort()
})
</script>

<template>
  <div class="page-scroll">
    <div class="page-container">
      <PageHeader
        title="知识库管理"
        description="管理计算机学科课程索引，调整 RAG 的召回范围、相似度门槛与检索模式。参数会实时同步到 Agent 工作台和检索调试页。"
      >
        <template #actions>
          <el-tooltip placement="bottom" :show-after="300">
            <template #content>
              <div class="max-w-[280px] space-y-1 text-[11px] leading-5">
                <p class="font-medium">{{ indexBadge.label }}</p>
                <p class="opacity-80">{{ indexBadge.details }}</p>
                <ul v-if="indexBadge.issues.length" class="list-disc pl-4 opacity-90">
                  <li v-for="issue in indexBadge.issues" :key="issue">{{ issue }}</li>
                </ul>
                <p class="opacity-60">点击徽标刷新索引状态</p>
              </div>
            </template>
            <button
              type="button"
              class="hidden cursor-pointer items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-[9px] font-medium transition hover:brightness-[0.98] sm:inline-flex"
              :class="indexBadge.wrapperClass"
              :aria-label="indexBadge.label"
              @click="loadKnowledgeBase(true)"
            >
              <span class="h-1.5 w-1.5 rounded-full" :class="indexBadge.dotClass" />
              {{ indexBadge.label }}
            </button>
          </el-tooltip>
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
            class="surface-card group relative cursor-pointer overflow-hidden p-4 transition duration-200 hover:-translate-y-0.5 hover:border-[#c9b9a4] hover:shadow-soft focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#9a463c] active:scale-[0.995]"
            role="button"
            tabindex="0"
            :aria-label="`跳转到${stat.targetLabel}`"
            @click="handleStatClick(stat)"
            @keydown.enter.prevent="handleStatClick(stat)"
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
              <span class="ml-auto shrink-0 text-[8px] font-medium text-[#9a463c] opacity-0 transition group-hover:opacity-100">
                {{ stat.targetLabel }} →
              </span>
            </p>
          </div>
        </div>

        <div class="mt-5 grid items-start gap-5 xl:grid-cols-[minmax(0,1fr)_356px]">
          <section ref="listSection" class="surface-card min-w-0 scroll-mt-5 overflow-hidden">
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
                  <button
                    type="button"
                    class="app-tab"
                    :class="{ 'is-active': activeTab === 'documents' }"
                    @click="switchTab('documents')"
                  >
                    <el-icon :size="10"><Document /></el-icon>
                    文档库
                    <span class="app-tab-count">{{ overview.documentCount }}</span>
                  </button>
                </div>
                <span class="hidden text-[8px] text-slate-400 sm:inline">
                  {{ activeTab === 'courses' ? `${overview.knowledgePointCount} 个课程知识点` : activeTab === 'points' ? '知识点索引' : '原文与向量索引' }}
                </span>
              </div>

              <div v-if="activeTab !== 'documents'" class="app-search w-full sm:w-[236px]">
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
              <div
                v-if="filteredCourses.length"
                class="mb-3 flex items-center justify-between gap-3 text-[9px] text-slate-400"
              >
                <p>点击任意课程卡片，跳转学堂在线对应课程</p>
                <span class="shrink-0">{{ filteredCourses.length }} 门</span>
              </div>
              <div v-if="filteredCourses.length" class="grid gap-3 md:grid-cols-2">
                <CourseCard
                  v-for="course in filteredCourses"
                  :key="course.id"
                  :course="course"
                />
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

            <div v-else-if="activeTab === 'points'">
              <div
                v-if="filteredKnowledgePoints.length"
                class="divide-y divide-slate-50"
              >
                <button
                  v-for="point in filteredKnowledgePoints"
                  :key="point.id"
                  type="button"
                  class="group grid w-full cursor-pointer grid-cols-[minmax(0,1fr)_82px_56px] items-center gap-3 px-5 py-3 text-left transition hover:bg-slate-50/80 focus-visible:bg-slate-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[#9a463c] sm:grid-cols-[minmax(0,1fr)_150px_70px_60px]"
                  @click="openPoint(point)"
                >
                  <div class="flex min-w-0 items-center gap-2.5">
                    <span class="grid h-7 w-7 shrink-0 place-items-center rounded-md bg-slate-50 text-slate-400 transition group-hover:bg-white group-hover:text-[#9a463c]">
                      <el-icon :size="11"><Document /></el-icon>
                    </span>
                    <div class="min-w-0">
                      <p class="truncate text-[10px] font-medium text-slate-700 group-hover:text-[#7d302f]">
                        {{ point.name }}
                      </p>
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
                  <span class="flex items-center justify-self-end gap-1 font-mono text-[7.5px] text-slate-400">
                    {{ point.updatedAt.slice(5) }}
                    <el-icon
                      :size="9"
                      class="text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-[#9a463c]"
                    >
                      <ArrowRight />
                    </el-icon>
                  </span>
                </button>
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

            <div v-else>
              <DocumentManager
                :courses="overview.courses"
                :jump-request="documentJump"
                @changed="handleDocumentsChanged"
                @jump-consumed="handleDocumentJumpConsumed"
              />
            </div>

            <div
              v-if="activeTab !== 'documents'"
              class="flex items-center justify-between border-t border-slate-100 px-5 py-2.5"
            >
              <span class="text-[8px] text-slate-400">
                当前显示 {{ activeCount }} 条{{ activeTab === 'courses' ? '课程' : '知识点' }}
              </span>
              <span class="font-mono text-[7.5px] text-slate-300">
                LIVE KNOWLEDGE INDEX · {{ overview.chunkCount }} VECTORS
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
                <div class="flex items-center justify-between gap-2">
                  <div class="flex items-center gap-1.5">
                    <span class="h-1.5 w-1.5 rounded-full bg-indigo-400" />
                    <p class="text-[8px] font-semibold text-slate-500">当前检索策略</p>
                  </div>
                  <span
                    class="rounded border px-1.5 py-0.5 text-[7px] font-medium"
                    :class="configDirty ? 'border-amber-200 bg-amber-50 text-amber-600' : 'border-emerald-200 bg-emerald-50 text-emerald-600'"
                  >
                    {{ configDirty ? '草稿参数' : '已同步' }}
                  </span>
                </div>
                <p class="mt-1.5 font-mono text-[9px] leading-4 text-slate-500">
                  {{ strategyMode.label }} · {{ strategyMode.shortLabel }}<br />
                  召回：{{ strategyFormula }}<br />
                  重排：0.92 × 基础分 + 0.08 × 覆盖率 + 领域词加权<br />
                  排序 → 过滤 ≥ {{ draftThreshold.toFixed(2) }} → Top-{{ draftTopK }}
                </p>
                <p
                  class="mt-2 text-[8px] leading-4"
                  :class="configDirty ? 'text-amber-500' : 'text-emerald-600'"
                >
                  {{ configDirty ? '草稿参数保存后才会应用到 Agent 与检索调试。' : '参数已同步到 Agent 工作台与 RAG 检索调试。' }}
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
    <KnowledgePointDrawer
      v-model="pointDrawerOpen"
      :point="selectedPoint"
      @open-document="handleOpenDocument"
      @open-documents="handleOpenDocuments"
    />
  </div>
</template>
