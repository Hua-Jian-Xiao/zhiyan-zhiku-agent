<script setup lang="ts">
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  shallowRef,
  watch,
} from 'vue'
import * as echarts from 'echarts'
import type { ECharts, EChartsOption } from 'echarts'
import { ElMessage } from 'element-plus'
import {
  Close,
  Connection,
  Pointer,
  Refresh,
  RefreshLeft,
  Share,
} from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import StatePanel from '@/components/feedback/StatePanel.vue'
import { fetchGraph } from '@/services/api'
import type {
  GraphCategory,
  KnowledgeGraphData,
  KnowledgeGraphNode,
} from '@/types'
import { isAbortError } from '@/utils/async'
import { truncate } from '@/utils/format'

const graphData = ref<KnowledgeGraphData | null>(null)
const isLoading = ref(true)
const errorMessage = ref('')
const activeCategories = ref<GraphCategory[]>([])
const selectedNodeId = ref<string | null>(null)
const chartContainer = ref<HTMLDivElement | null>(null)
const chartInstance = shallowRef<ECharts | null>(null)
let controller: AbortController | null = null
let resizeObserver: ResizeObserver | null = null

const nodeCount = computed(() => graphData.value?.nodes.length ?? 0)
const edgeCount = computed(() => graphData.value?.edges.length ?? 0)

const activeSet = computed(() => new Set(activeCategories.value))
const visibleNodes = computed(
  () => graphData.value?.nodes.filter((node) => activeSet.value.has(node.category)) ?? [],
)
const visibleNodeIds = computed(() => new Set(visibleNodes.value.map((node) => node.id)))
const visibleEdges = computed(
  () =>
    graphData.value?.edges.filter(
      (edge) => visibleNodeIds.value.has(edge.source) && visibleNodeIds.value.has(edge.target),
    ) ?? [],
)

const selectedNode = computed(
  () => graphData.value?.nodes.find((node) => node.id === selectedNodeId.value) ?? null,
)

const nodeById = computed(() => {
  const map = new Map<string, KnowledgeGraphNode>()
  for (const node of graphData.value?.nodes ?? []) map.set(node.id, node)
  return map
})

const selectedPrerequisites = computed(() => {
  if (!selectedNode.value) return []
  return selectedNode.value.prerequisites
    .map((id) => nodeById.value.get(id))
    .filter((node): node is KnowledgeGraphNode => Boolean(node))
})

const selectedDependents = computed(() => {
  if (!selectedNode.value || !graphData.value) return []
  return graphData.value.edges
    .filter((edge) => edge.source === selectedNode.value?.id)
    .map((edge) => nodeById.value.get(edge.target))
    .filter((node): node is KnowledgeGraphNode => Boolean(node))
})

const selectedCategory = computed(() => {
  if (!selectedNode.value || !graphData.value) return null
  return (
    graphData.value.categories.find(
      (category) => category.key === selectedNode.value?.category,
    ) ?? null
  )
})

const selectedDegree = computed(() => {
  if (!selectedNode.value || !graphData.value) return 0
  const id = selectedNode.value.id
  return graphData.value.edges.filter((edge) => edge.source === id || edge.target === id).length
})

const categoryCounts = computed(() => {
  const counts = new Map<GraphCategory, number>()
  for (const category of graphData.value?.categories ?? []) counts.set(category.key, 0)
  for (const node of graphData.value?.nodes ?? []) {
    counts.set(node.category, (counts.get(node.category) ?? 0) + 1)
  }
  return counts
})

const degreeMap = computed(() => {
  const map = new Map<string, number>()
  for (const node of graphData.value?.nodes ?? []) map.set(node.id, 0)
  for (const edge of graphData.value?.edges ?? []) {
    map.set(edge.source, (map.get(edge.source) ?? 0) + 1)
    map.set(edge.target, (map.get(edge.target) ?? 0) + 1)
  }
  return map
})

function categoryLabel(key: GraphCategory): string {
  return graphData.value?.categories.find((category) => category.key === key)?.label ?? key
}

function categoryColor(key: GraphCategory): string {
  return graphData.value?.categories.find((category) => category.key === key)?.color ?? '#7d302f'
}

async function loadGraph(showToast = false): Promise<void> {
  controller?.abort()
  const currentController = new AbortController()
  controller = currentController
  const hadData = Boolean(graphData.value)
  isLoading.value = true
  errorMessage.value = ''

  try {
    const data = await fetchGraph(currentController.signal)
    if (currentController.signal.aborted) return
    graphData.value = data
    if (!hadData) {
      activeCategories.value = data.categories.map((category) => category.key)
    } else {
      const validKeys = new Set(data.categories.map((category) => category.key))
      activeCategories.value = activeCategories.value.filter((key) => validKeys.has(key))
    }
    if (
      selectedNodeId.value &&
      !data.nodes.some((node) => node.id === selectedNodeId.value)
    ) {
      selectedNodeId.value = null
    }
    await nextTick()
    renderChart()
    setupResizeObserver()
    if (showToast) ElMessage.success('知识图谱已刷新')
  } catch (error) {
    if (!isAbortError(error)) {
      const message = error instanceof Error ? error.message : '知识图谱加载失败'
      if (hadData) ElMessage.error(message)
      else errorMessage.value = message
    }
  } finally {
    if (controller === currentController) isLoading.value = false
  }
}

function buildChartOption(): EChartsOption {
  const data = graphData.value
  if (!data) return {}

  const categoryIndex = new Map<GraphCategory, number>()
  data.categories.forEach((category, index) => categoryIndex.set(category.key, index))
  const categoryMeta = new Map(
    data.categories.map((category) => [category.key, category] as const),
  )

  const nodes = visibleNodes.value.map((node) => {
    const degree = degreeMap.value.get(node.id) ?? 0
    const category = categoryMeta.get(node.category)
    return {
      id: node.id,
      name: node.name,
      category: categoryIndex.get(node.category) ?? 0,
      value: degree,
      symbol: 'circle',
      symbolSize: Math.min(46, 16 + degree * 3.6),
      itemStyle: {
        color: category?.color ?? '#7d302f',
        borderColor: '#ffffff',
        borderWidth: 2,
        shadowBlur: 14,
        shadowColor: `${category?.color ?? '#7d302f'}44`,
      },
      label: {
        show: true,
        position: 'right' as const,
        color: '#4d453b',
        fontFamily: 'Georgia, "Songti SC", SimSun, serif',
        fontSize: 10,
        fontWeight: 500,
      },
      description: node.description,
    }
  })

  const links = visibleEdges.value.map((edge) => ({
    source: edge.source,
    target: edge.target,
    value: 1,
    reason: edge.reason,
  }))

  return {
    backgroundColor: 'transparent',
    animationDuration: 700,
    animationEasing: 'cubicOut',
    tooltip: {
      trigger: 'item',
      confine: true,
      backgroundColor: '#1a1510',
      borderWidth: 0,
      padding: [10, 12],
      textStyle: { color: '#e9dece', fontSize: 11, fontFamily: 'Georgia, "Songti SC", SimSun, serif' },
      extraCssText:
        'border-radius:1px;border:1px solid #4b3f32;box-shadow:0 18px 40px -18px rgba(25,21,17,0.45);max-width:280px;',
      formatter: (params: any) => {
        const item = params.data ?? {}
        if (params.dataType === 'edge') {
          const source = nodeById.value.get(String(item.source))
          const target = nodeById.value.get(String(item.target))
          return `<div style="font-size:10px;color:#94a3b8;margin-bottom:4px;">客观依赖关系</div>
            <div style="font-weight:600;color:#f8fafc;font-size:12px;">${source?.name ?? item.source} → ${target?.name ?? item.target}</div>
            <div style="margin-top:6px;color:#94a3b8;font-size:10px;line-height:1.6;">${item.reason ?? ''}</div>`
        }
        const node = nodeById.value.get(String(item.id))
        if (!node) return ''
        const category = categoryMeta.get(node.category)
        const dependentsCount = data.edges.filter((edge) => edge.source === node.id).length
        return `<div style="display:flex;align-items:center;gap:6px;">
            <span style="width:6px;height:6px;border-radius:99px;background:${category?.color ?? '#7d302f'};"></span>
            <span style="font-size:10px;color:#94a3b8;">${category?.label ?? ''}</span>
          </div>
          <div style="margin-top:4px;font-weight:600;color:#f8fafc;font-size:12px;">${node.name}</div>
          <div style="margin-top:5px;color:#94a3b8;font-size:10px;line-height:1.6;">${truncate(node.description, 64)}</div>
          <div style="margin-top:7px;padding-top:6px;border-top:1px solid rgba(194,178,156,0.18);color:#9d8f7c;font-size:10px;">
            前置 ${node.prerequisites.length} · 直接后继 ${dependentsCount} · 点击查看详情
          </div>`
      },
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        selectedMode: 'single',
        categories: data.categories.map((category) => ({
          name: category.label,
          itemStyle: { color: category.color },
        })),
        data: nodes,
        links,
        force: {
          repulsion: 340,
          edgeLength: [72, 156],
          gravity: 0.07,
          friction: 0.18,
          layoutAnimation: true,
        },
        scaleLimit: { min: 0.55, max: 2.4 },
        lineStyle: {
          color: 'source',
          opacity: 0.42,
          width: 1.15,
          curveness: 0.065,
        },
        edgeSymbol: ['none', 'arrow'],
        edgeSymbolSize: 5,
        labelLayout: { hideOverlap: true },
        emphasis: {
          focus: 'adjacency',
          scale: 1.06,
          label: {
            show: true,
            color: '#2f2922',
            fontSize: 11,
            fontWeight: 600,
          },
          lineStyle: { color: '#7d302f', opacity: 0.9, width: 2 },
          itemStyle: { borderColor: '#fffdf8', borderWidth: 3 },
        },
        blur: {
          label: { opacity: 0.2 },
          itemStyle: { opacity: 0.2 },
          lineStyle: { opacity: 0.08 },
        },
        select: {
          label: { color: '#2f2922', fontSize: 11, fontWeight: 700 },
          itemStyle: { borderColor: '#7d302f', borderWidth: 3 },
        },
      },
    ],
  }
}

function renderChart(): void {
  if (!graphData.value || !chartContainer.value) return
  if (!chartInstance.value) {
    chartInstance.value = echarts.init(chartContainer.value, undefined, {
      renderer: 'canvas',
    })
    chartInstance.value.on('click', onChartClick)
  }

  chartInstance.value.setOption(buildChartOption(), true)
  chartInstance.value.resize()

  if (selectedNode.value && activeSet.value.has(selectedNode.value.category)) {
    chartInstance.value.dispatchAction({
      type: 'select',
      seriesIndex: 0,
      name: selectedNode.value.name,
    })
  }
}

function onChartClick(params: any): void {
  const data = params.data as { id?: string } | undefined
  if (params.dataType === 'node' && data?.id) {
    selectedNodeId.value = data.id
  }
}

function setupResizeObserver(): void {
  if (!chartContainer.value || typeof ResizeObserver === 'undefined') return
  resizeObserver?.disconnect()
  resizeObserver = new ResizeObserver(() => {
    chartInstance.value?.resize()
  })
  resizeObserver.observe(chartContainer.value)
}

function toggleCategory(key: GraphCategory): void {
  if (activeCategories.value.includes(key)) {
    if (activeCategories.value.length === 1) {
      ElMessage.info('请至少保留一个知识领域')
      return
    }
    activeCategories.value = activeCategories.value.filter((item) => item !== key)
  } else {
    activeCategories.value = [...activeCategories.value, key]
  }

  if (selectedNode.value && !activeCategories.value.includes(selectedNode.value.category)) {
    selectedNodeId.value = null
  }
  void nextTick(renderChart)
}

function resetView(): void {
  if (!graphData.value) return
  activeCategories.value = graphData.value.categories.map((category) => category.key)
  selectedNodeId.value = null
  void nextTick(renderChart)
}

function focusNode(node: KnowledgeGraphNode): void {
  if (!activeCategories.value.includes(node.category)) {
    activeCategories.value = [...activeCategories.value, node.category]
    void nextTick(() => {
      selectedNodeId.value = node.id
      renderChart()
    })
    return
  }
  selectedNodeId.value = node.id
  chartInstance.value?.dispatchAction({
    type: 'select',
    seriesIndex: 0,
    name: node.name,
  })
}

watch(
  () => activeCategories.value.join('|'),
  () => {
    if (graphData.value) void nextTick(renderChart)
  },
)

onMounted(() => {
  void loadGraph()
})

onBeforeUnmount(() => {
  controller?.abort()
  resizeObserver?.disconnect()
  resizeObserver = null
  chartInstance.value?.dispose()
  chartInstance.value = null
})
</script>

<template>
  <div class="page-scroll">
    <div class="page-container">
      <PageHeader
        title="知识图谱"
        description="以力导向图呈现计算机学科知识点之间的客观先修关系。图谱只描述课程知识结构，不包含个性化数据。"
      >
        <template #actions>
          <span
            v-if="graphData"
            class="hidden items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 font-mono text-[8px] text-slate-500 sm:inline-flex"
          >
            <span class="h-1.5 w-1.5 rounded-full bg-indigo-400" />
            {{ nodeCount }} NODES · {{ edgeCount }} EDGES
          </span>
          <el-button :loading="isLoading" @click="loadGraph(true)">
            <el-icon v-if="!isLoading" class="mr-1"><Refresh /></el-icon>
            刷新图谱
          </el-button>
        </template>
      </PageHeader>

      <div
        class="mt-5 flex items-start gap-3 border-y border-[#c9bdab] bg-[#fbf7ee] px-4 py-3"
      >
        <span class="mt-0.5 grid h-6 w-6 shrink-0 place-items-center border border-[#c99f98] text-[#7d302f]">
          <el-icon :size="11"><Connection /></el-icon>
        </span>
        <div class="min-w-0">
          <p class="font-mono text-[7.5px] font-medium uppercase tracking-[0.12em] text-[#7d302f]">Objective dependency view / 客观依赖</p>
          <p class="mt-1 text-[8.5px] leading-4 text-[#766b5b]">
            节点表示知识点，箭头表示「先修 → 后继」的课程依赖。所有关系来自课程大纲，与任何用户学习数据无关。
          </p>
        </div>
      </div>

      <div v-if="isLoading && !graphData" class="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_326px]">
        <div class="surface-card p-5">
          <div class="flex items-center justify-between">
            <div>
              <div class="skeleton h-3 w-36" />
              <div class="skeleton mt-2 h-2 w-56" />
            </div>
            <div class="skeleton h-8 w-20 rounded-lg" />
          </div>
          <div class="mt-4 flex gap-2">
            <div v-for="index in 4" :key="index" class="skeleton h-6 w-24 rounded-md" />
          </div>
          <div class="skeleton mt-4 h-[590px] rounded-2xl" />
        </div>
        <div class="space-y-4">
          <div class="surface-card p-4">
            <div class="grid grid-cols-3 gap-2">
              <div v-for="index in 3" :key="index" class="rounded-xl border border-slate-100 p-3">
                <div class="skeleton h-2 w-8" />
                <div class="skeleton mt-2 h-6 w-10" />
              </div>
            </div>
          </div>
          <div class="surface-card h-[360px] p-5">
            <div class="skeleton mx-auto h-14 w-14 rounded-2xl" />
            <div class="skeleton mx-auto mt-4 h-3 w-28" />
            <div class="skeleton mx-auto mt-2 h-2 w-48" />
          </div>
        </div>
      </div>

      <div v-else-if="errorMessage" class="surface-card mt-5">
        <StatePanel
          type="error"
          title="知识图谱加载失败"
          :description="errorMessage"
          action-text="重新加载"
          @action="loadGraph()"
        />
      </div>

      <div v-else-if="graphData" class="mt-5 grid items-start gap-5 xl:grid-cols-[minmax(0,1fr)_326px]">
        <section class="surface-card overflow-hidden">
          <div class="flex flex-wrap items-start justify-between gap-3 px-5 pb-3 pt-4">
            <div>
              <div class="flex items-center gap-2">
                <span class="grid h-6 w-6 place-items-center rounded-md bg-emerald-50 text-emerald-500">
                  <el-icon :size="11"><Share /></el-icon>
                </span>
                <h2 class="text-[12px] font-semibold text-slate-700">计算机学科知识依赖</h2>
                <span class="rounded-full border border-slate-100 bg-slate-50 px-1.5 py-0.5 font-mono text-[7px] text-slate-400">
                  FORCE LAYOUT
                </span>
              </div>
              <p class="mt-1.5 text-[8.5px] text-slate-400">
                当前显示 {{ visibleNodes.length }} 个节点 · {{ visibleEdges.length }} 条依赖
              </p>
            </div>
            <button
              type="button"
              class="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-[8px] font-medium text-slate-500 transition hover:border-indigo-200 hover:text-indigo-500"
              @click="resetView"
            >
              <el-icon :size="10"><RefreshLeft /></el-icon>
              重置视图
            </button>
          </div>

          <div class="flex flex-wrap gap-1.5 px-5 pb-3">
            <button
              v-for="category in graphData.categories"
              :key="category.key"
              type="button"
              class="graph-domain-chip"
              :class="{ 'is-active': activeCategories.includes(category.key) }"
              @click="toggleCategory(category.key)"
            >
              <span
                class="h-1.5 w-1.5 rounded-full transition-opacity"
                :style="{
                  backgroundColor: category.color,
                  opacity: activeCategories.includes(category.key) ? 1 : 0.3,
                }"
              />
              {{ category.label }}
              <span class="font-mono text-[7px] text-slate-400">
                {{ categoryCounts.get(category.key) ?? 0 }}
              </span>
            </button>
          </div>

          <StatePanel
            v-if="graphData.nodes.length === 0"
            type="empty"
            title="知识图谱暂无可视化节点"
            description="当前筛选条件下没有可展示的知识点，请稍后刷新图谱。"
            action-text="刷新图谱"
            @action="loadGraph()"
          />
          <div v-else class="mx-4 overflow-hidden rounded-2xl border border-slate-100 graph-canvas">
            <div ref="chartContainer" class="h-[590px] w-full" />
          </div>

          <div class="flex flex-wrap items-center justify-between gap-2 px-5 py-3">
            <p class="flex items-center gap-4 text-[8px] text-slate-400">
              <span class="flex items-center gap-1"><span class="h-1 w-1 rounded-full bg-indigo-400" />拖拽节点</span>
              <span class="flex items-center gap-1"><span class="h-1 w-1 rounded-full bg-cyan-400" />滚轮缩放</span>
              <span class="flex items-center gap-1"><span class="h-1 w-1 rounded-full bg-emerald-400" />点击查看依赖</span>
            </p>
            <span class="font-mono text-[7.5px] text-slate-300">
              OBJECTIVE COURSE DEPENDENCY GRAPH
            </span>
          </div>
        </section>

        <aside class="space-y-4">
          <section class="surface-card p-4">
            <div class="grid grid-cols-3 gap-2">
              <div class="rounded-xl border border-slate-100 bg-slate-50/50 px-2.5 py-2.5">
                <p class="text-[7.5px] text-slate-400">知识点</p>
                <p class="mt-1 font-mono text-[18px] font-semibold text-slate-700">{{ nodeCount }}</p>
              </div>
              <div class="rounded-xl border border-slate-100 bg-slate-50/50 px-2.5 py-2.5">
                <p class="text-[7.5px] text-slate-400">依赖边</p>
                <p class="mt-1 font-mono text-[18px] font-semibold text-slate-700">{{ edgeCount }}</p>
              </div>
              <div class="rounded-xl border border-slate-100 bg-slate-50/50 px-2.5 py-2.5">
                <p class="text-[7.5px] text-slate-400">知识领域</p>
                <p class="mt-1 font-mono text-[18px] font-semibold text-slate-700">{{ graphData.categories.length }}</p>
              </div>
            </div>
          </section>

          <section class="surface-card overflow-hidden">
            <div class="flex items-center justify-between border-b border-slate-100 px-4 py-3">
              <div>
                <p class="text-[10px] font-semibold text-slate-700">知识点详情卡</p>
                <p class="mt-0.5 text-[8px] text-slate-400">
                  {{ selectedNode ? '点击节点后弹出的客观依赖详情' : '从图谱中选择一个知识点' }}
                </p>
              </div>
              <button
                v-if="selectedNode"
                type="button"
                class="grid h-6 w-6 place-items-center rounded-md text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
                aria-label="清除选中节点"
                @click="selectedNodeId = null"
              >
                <el-icon :size="11"><Close /></el-icon>
              </button>
            </div>

            <div v-if="selectedNode" class="animate-fade-up p-4">
              <div class="flex items-start gap-3">
                <span
                  class="grid h-10 w-10 shrink-0 place-items-center rounded-xl text-[12px] font-bold"
                  :style="{
                    color: selectedCategory?.color,
                    backgroundColor: `${selectedCategory?.color}12`,
                    border: `1px solid ${selectedCategory?.color}24`,
                  }"
                >
                  {{ selectedNode.name.slice(0, 1) }}
                </span>
                <div class="min-w-0">
                  <div class="flex flex-wrap items-center gap-1.5">
                    <span
                      class="rounded border px-1.5 py-0.5 text-[7.5px]"
                      :style="{
                        color: selectedCategory?.color,
                        borderColor: `${selectedCategory?.color}25`,
                        backgroundColor: `${selectedCategory?.color}10`,
                      }"
                    >
                      {{ categoryLabel(selectedNode.category) }}
                    </span>
                    <span class="rounded border border-amber-100 bg-amber-50 px-1.5 py-0.5 text-[7.5px] text-amber-600">
                      {{ selectedNode.difficulty }}
                    </span>
                  </div>
                  <h3 class="mt-1.5 text-[14px] font-bold text-slate-800">{{ selectedNode.name }}</h3>
                  <p class="mt-0.5 text-[8px] text-slate-400">
                    {{ selectedNode.relatedCourse }} · 连接度 {{ selectedDegree }}
                  </p>
                  <p class="mt-1 font-mono text-[7px] uppercase tracking-wider text-slate-300">
                    NODE {{ selectedNode.id }}
                  </p>
                </div>
              </div>

              <p class="mt-3 text-[9px] leading-[1.8] text-slate-500">
                {{ selectedNode.description }}
              </p>

              <div class="mt-3.5 border-t border-slate-100 pt-3">
                <div class="flex items-center justify-between">
                  <p class="text-[8px] font-semibold uppercase tracking-wider text-slate-400">
                    前置知识
                  </p>
                  <span class="font-mono text-[7.5px] text-slate-400">
                    {{ selectedPrerequisites.length }}
                  </span>
                </div>
                <div v-if="selectedPrerequisites.length" class="mt-2 flex flex-wrap gap-1.5">
                  <button
                    v-for="node in selectedPrerequisites"
                    :key="node.id"
                    type="button"
                    class="related-node-chip"
                    @click="focusNode(node)"
                  >
                    <span
                      class="h-1.5 w-1.5 rounded-full"
                      :style="{ backgroundColor: categoryColor(node.category) }"
                    />
                    {{ node.name }}
                  </button>
                </div>
                <p v-else class="mt-2 rounded-lg border border-dashed border-slate-200 px-2.5 py-2 text-[8px] text-slate-400">
                  无前置依赖，可以从此节点开始学习。
                </p>
              </div>

              <div class="mt-3 border-t border-slate-100 pt-3">
                <div class="flex items-center justify-between">
                  <p class="text-[8px] font-semibold uppercase tracking-wider text-slate-400">
                    解锁的后继方向
                  </p>
                  <span class="font-mono text-[7.5px] text-slate-400">
                    {{ selectedDependents.length }}
                  </span>
                </div>
                <div v-if="selectedDependents.length" class="mt-2 flex flex-wrap gap-1.5">
                  <button
                    v-for="node in selectedDependents"
                    :key="node.id"
                    type="button"
                    class="related-node-chip"
                    @click="focusNode(node)"
                  >
                    <span
                      class="h-1.5 w-1.5 rounded-full"
                      :style="{ backgroundColor: categoryColor(node.category) }"
                    />
                    {{ node.name }}
                  </button>
                </div>
                <p v-else class="mt-2 rounded-lg border border-dashed border-slate-200 px-2.5 py-2 text-[8px] text-slate-400">
                  当前为知识链路的末端节点。
                </p>
              </div>
            </div>

            <div v-else class="flex min-h-[330px] flex-col items-center justify-center px-6 py-8 text-center">
              <div class="relative grid h-14 w-14 place-items-center rounded-2xl border border-indigo-100 bg-indigo-50/70 text-indigo-500">
                <span class="absolute inset-2 rounded-xl border border-indigo-100/80" />
                <el-icon :size="22"><Pointer /></el-icon>
              </div>
              <h3 class="mt-3.5 text-[11px] font-semibold text-slate-700">点击图谱中的知识点</h3>
              <p class="mt-1.5 max-w-[210px] text-[8.5px] leading-4 text-slate-400">
                查看它的领域、课程出处以及客观的前置与后继依赖。
              </p>
              <div class="mt-4 flex flex-wrap justify-center gap-1.5">
                <span class="rounded-md border border-slate-100 bg-slate-50 px-1.5 py-0.5 text-[7.5px] text-slate-400">
                  客观依赖
                </span>
                <span class="rounded-md border border-slate-100 bg-slate-50 px-1.5 py-0.5 text-[7.5px] text-slate-400">
                  仅客观关系
                </span>
                <span class="rounded-md border border-slate-100 bg-slate-50 px-1.5 py-0.5 text-[7.5px] text-slate-400">
                  可放大拖拽
                </span>
              </div>
            </div>
          </section>

          <section class="surface-card p-4">
            <div class="flex items-center justify-between">
              <p class="text-[9px] font-semibold text-slate-600">领域分布</p>
              <span class="font-mono text-[7.5px] text-slate-400">
                {{ visibleNodes.length }} / {{ nodeCount }} 可见
              </span>
            </div>
            <div class="mt-3 space-y-2.5">
              <button
                v-for="category in graphData.categories"
                :key="category.key"
                type="button"
                class="block w-full text-left transition-opacity"
                :class="activeCategories.includes(category.key) ? 'opacity-100' : 'opacity-40'"
                @click="toggleCategory(category.key)"
              >
                <div class="flex items-center justify-between text-[8px]">
                  <span class="flex items-center gap-1.5 text-slate-500">
                    <span class="h-1.5 w-1.5 rounded-full" :style="{ backgroundColor: category.color }" />
                    {{ category.label }}
                  </span>
                  <span class="font-mono text-slate-400">
                    {{ categoryCounts.get(category.key) ?? 0 }}
                  </span>
                </div>
                <div class="mt-1 h-1 overflow-hidden rounded-full bg-slate-100">
                  <div
                    class="h-full rounded-full transition-all duration-500"
                    :style="{
                      width: `${((categoryCounts.get(category.key) ?? 0) / Math.max(1, nodeCount)) * 100}%`,
                      backgroundColor: category.color,
                      opacity: 0.7,
                    }"
                  />
                </div>
              </button>
            </div>
          </section>

          <div class="rounded-2xl border border-slate-200/80 bg-slate-50/70 p-3.5">
            <p class="text-[8px] font-semibold uppercase tracking-wider text-slate-400">
              数据边界说明
            </p>
            <p class="mt-1.5 text-[8.5px] leading-4 text-slate-400">
              图谱仅编码课程大纲中的客观先修关系，不包含任何个性化学习数据。
            </p>
          </div>
        </aside>
      </div>
    </div>
  </div>
</template>

<style scoped>
.graph-canvas {
  background:
    linear-gradient(90deg, rgba(125, 48, 47, 0.025) 1px, transparent 1px),
    linear-gradient(rgba(125, 48, 47, 0.025) 1px, transparent 1px),
    radial-gradient(circle at 50% 42%, rgba(244, 236, 221, 0.85), transparent 62%),
    #fbf8f1;
  background-size: 24px 24px, 24px 24px, 100% 100%, 100% 100%;
}

.graph-domain-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 1px;
  color: #a29582;
  font-family: var(--app-mono);
  font-size: 10px;
  background: transparent;
  border: 0;
  border-bottom: 1px solid transparent;
  border-radius: 0;
  cursor: pointer;
  transition: all 0.16s ease;
}

.graph-domain-chip:hover {
  color: #6f6456;
}

.graph-domain-chip.is-active {
  color: #4d453b;
  background: transparent;
  border-bottom-color: #7d302f;
  box-shadow: none;
}

.related-node-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 7px;
  color: #6f6456;
  font-size: 10px;
  background: #fbf7ee;
  border: 1px solid #ded4c4;
  border-radius: 0;
  cursor: pointer;
  transition: all 0.16s ease;
}

.related-node-chip:hover {
  color: #7d302f;
  background: #f6ece4;
  border-color: #c99f98;
}
</style>
