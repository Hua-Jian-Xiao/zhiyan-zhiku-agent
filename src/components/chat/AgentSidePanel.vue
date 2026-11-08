<script setup lang="ts">
import { computed } from 'vue'
import {
  ArrowRight,
  Collection,
  DataAnalysis,
  MagicStick,
  Share,
  Timer,
} from '@element-plus/icons-vue'
import type { ChatMessage } from '@/types'
import { useRagStore } from '@/stores/rag'
import { useSystemStore } from '@/stores/system'
import { getRetrievalModeLabel } from '@/utils/rag'

const props = defineProps<{
  isStreaming: boolean
  latestMessage: ChatMessage | null
}>()

const ragStore = useRagStore()
const systemStore = useSystemStore()

const trace = computed(() => props.latestMessage?.trace ?? null)
const citations = computed(() => props.latestMessage?.citations ?? [])
const doneSteps = computed(
  () => trace.value?.steps.filter((step) => step.status === 'done').length ?? 0,
)
const totalSteps = computed(() => trace.value?.steps.length ?? 4)
const toolCount = computed(() => trace.value?.tools.length ?? 0)
const chunkCount = computed(() => trace.value?.chunks.length ?? 0)
const statusLabel = computed(() => (props.isStreaming ? '推理中' : '待命'))
const recentCitations = computed(() => citations.value.slice(0, 3))
</script>

<template>
  <aside class="flex h-full w-full flex-col bg-[#f8f3e9]">
    <header class="flex h-[66px] shrink-0 items-center justify-between border-b border-[#d8cebd] px-4">
      <div>
        <p class="font-mono text-[7px] font-medium uppercase tracking-[0.2em] text-[#a29582]">
          Run Context / 现场
        </p>
        <h2 class="mt-1.5 font-serif text-[15px] font-medium tracking-[-0.01em] text-[#211c17]">Agent 运行台</h2>
      </div>
      <span
        class="inline-flex items-center gap-1.5 border px-2 py-0.5 font-mono text-[7px] tracking-[0.06em]"
        :class="
          isStreaming
            ? 'border-[#d8b8b1] bg-[#f6e9e4] text-[#8e3d35]'
            : 'border-[#c3d5c6] bg-[#eef3ee] text-[#48614c]'
        "
      >
        <span
          class="h-1 w-1 rounded-full"
          :class="isStreaming ? 'animate-pulse bg-[#9a463c]' : 'bg-[#5c7a60]'"
        />
        {{ statusLabel }}
      </span>
    </header>

    <div class="min-h-0 flex-1 space-y-3 overflow-y-auto p-3.5 scroll-thin">
      <section class="relative overflow-hidden border border-[#3d3328] bg-[#1a1510] p-4 text-[#f3e8d7]">
        <div class="pointer-events-none absolute inset-0" aria-hidden="true">
          <div class="absolute inset-0 dot-grid opacity-[0.04]" />
          <span class="absolute -right-2 -top-7 font-serif text-[96px] leading-none text-[#9a463c]/20">§</span>
        </div>

        <div class="relative flex items-start justify-between border-b border-[#3d3328] pb-2.5">
          <div class="flex items-center gap-2">
            <span class="grid h-7 w-7 place-items-center border border-[#5a4b3a] bg-[#241e18] text-[#c39e40]">
              <el-icon :size="13"><MagicStick /></el-icon>
            </span>
            <div>
              <p class="font-serif text-[11px] font-medium text-[#f3e8d7]">RAG-Agent</p>
              <p class="mt-0.5 font-mono text-[6.5px] tracking-[0.08em] text-[#817463]">v2.4 / LIVE RAG</p>
            </div>
          </div>
          <span class="border border-[#4c4032] px-1.5 py-0.5 font-mono text-[6.5px] tracking-[0.1em] text-[#9dbaa2]">
            {{ systemStore.health?.database === 'ok' ? 'ONLINE' : 'OFFLINE' }}
          </span>
        </div>

        <p class="relative mt-3 font-serif text-[9.5px] leading-[1.8] text-[#a49581]">
          面向计算机学科的检索增强学习 Agent，回答会显式绑定知识库证据。
        </p>

        <div class="relative mt-3.5 grid grid-cols-3 gap-1.5">
          <div class="border border-[#3d3328] px-2 py-1.5">
            <p class="font-serif text-[16px] leading-none text-[#f3e8d7]">
              {{ doneSteps }}<span class="font-mono text-[7px] text-[#817463]">/{{ totalSteps }}</span>
            </p>
            <p class="mt-1.5 font-mono text-[6px] uppercase tracking-[0.1em] text-[#817463]">TRACE</p>
          </div>
          <div class="border border-[#3d3328] px-2 py-1.5">
            <p class="font-serif text-[16px] leading-none text-[#f3e8d7]">{{ toolCount }}</p>
            <p class="mt-1.5 font-mono text-[6px] uppercase tracking-[0.1em] text-[#817463]">TOOLS</p>
          </div>
          <div class="border border-[#3d3328] px-2 py-1.5">
            <p class="font-serif text-[16px] leading-none text-[#f3e8d7]">{{ chunkCount }}</p>
            <p class="mt-1.5 font-mono text-[6px] uppercase tracking-[0.1em] text-[#817463]">EVIDENCE</p>
          </div>
        </div>

        <div class="relative mt-3 flex items-center justify-between border-t border-[#3d3328] pt-2.5 font-mono text-[6.5px] text-[#817463]">
          <span class="flex items-center gap-1">
            <el-icon :size="8"><Timer /></el-icon>
            {{ latestMessage?.latencyMs ? `${(latestMessage.latencyMs / 1000).toFixed(1)}s LAST RUN` : 'AWAITING FIRST RUN' }}
          </span>
          <span>CTX: 8K</span>
        </div>
      </section>

      <section class="rounded-2xl border border-slate-200/80 bg-white p-3.5">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <span class="grid h-5 w-5 place-items-center rounded-md bg-indigo-50 text-indigo-500">
              <el-icon :size="10"><Collection /></el-icon>
            </span>
            <p class="text-[9px] font-semibold text-slate-600">知识库状态</p>
          </div>
          <router-link
            :to="{ name: 'knowledge' }"
            class="flex items-center gap-0.5 text-[8px] text-slate-400 transition hover:text-indigo-500"
          >
            管理
            <el-icon :size="8"><ArrowRight /></el-icon>
          </router-link>
        </div>
        <p class="mt-2.5 text-[10px] font-medium text-slate-700">计算机学科知识空间</p>
        <div class="mt-2 flex items-center gap-4">
          <div>
            <span class="font-serif text-[17px] font-medium text-slate-800">{{ systemStore.stats?.courseCount ?? '—' }}</span>
            <span class="ml-1 text-[8px] text-slate-400">门课程</span>
          </div>
          <div class="h-3 w-px bg-slate-100" />
          <div>
            <span class="font-serif text-[17px] font-medium text-slate-800">{{ systemStore.stats?.knowledgePointCount ?? '—' }}</span>
            <span class="ml-1 text-[8px] text-slate-400">个知识点</span>
          </div>
        </div>
        <div class="mt-2.5 flex items-center gap-1.5 text-[8px] text-slate-400">
          <span class="h-1.5 w-1.5 rounded-full" :class="systemStore.health?.database === 'ok' ? 'bg-emerald-400' : 'bg-rose-400'" />
          {{ systemStore.health?.database === 'ok' ? `索引健康 · ${systemStore.lastSyncedAt} 同步` : '索引服务离线' }}
        </div>
      </section>

      <section class="rounded-2xl border border-slate-200/80 bg-white p-3.5">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <span class="grid h-5 w-5 place-items-center rounded-md bg-cyan-50 text-cyan-500">
              <el-icon :size="10"><DataAnalysis /></el-icon>
            </span>
            <p class="text-[9px] font-semibold text-slate-600">检索参数</p>
          </div>
          <router-link
            :to="{ name: 'rag-debug' }"
            class="flex items-center gap-0.5 text-[8px] text-slate-400 transition hover:text-indigo-500"
          >
            调试
            <el-icon :size="8"><ArrowRight /></el-icon>
          </router-link>
        </div>
        <div class="mt-2.5 grid grid-cols-2 gap-2">
          <div class="rounded-lg border border-slate-100 bg-slate-50/60 px-2.5 py-2">
            <p class="text-[7.5px] text-slate-400">Top-K</p>
            <p class="mt-0.5 font-mono text-[14px] font-semibold text-slate-700">
              {{ ragStore.config.topK }}
            </p>
          </div>
          <div class="rounded-lg border border-slate-100 bg-slate-50/60 px-2.5 py-2">
            <p class="text-[7.5px] text-slate-400">相似度阈值</p>
            <p class="mt-0.5 font-mono text-[14px] font-semibold text-slate-700">
              {{ ragStore.config.threshold.toFixed(2) }}
            </p>
          </div>
        </div>
        <div class="mt-2 flex items-center justify-between rounded-lg border border-indigo-100 bg-indigo-50/60 px-2.5 py-2">
          <span class="text-[7.5px] text-slate-400">检索模式</span>
          <span class="text-[9px] font-semibold text-indigo-600">
            {{ getRetrievalModeLabel(ragStore.config.retrievalMode) }}
          </span>
        </div>
        <p class="mt-2 text-[7.5px] leading-4 text-slate-400">
          参数与「知识库管理」「RAG 检索调试」实时同步
        </p>
      </section>

      <section v-if="recentCitations.length" class="rounded-2xl border border-slate-200/80 bg-white p-3.5">
        <div class="flex items-center justify-between">
          <p class="text-[9px] font-semibold text-slate-600">本轮引用</p>
          <span class="font-mono text-[8px] text-slate-400">{{ citations.length }} sources</span>
        </div>
        <div class="mt-2.5 space-y-1.5">
          <div
            v-for="citation in recentCitations"
            :key="citation.id"
            class="rounded-lg border border-slate-100 bg-slate-50/50 px-2 py-1.5"
          >
            <div class="flex items-start gap-1.5">
              <span class="mt-px grid h-3.5 w-3.5 shrink-0 place-items-center rounded bg-indigo-50 text-[7px] font-bold text-indigo-500">
                {{ citation.index }}
              </span>
              <p class="min-w-0 flex-1 truncate text-[8px] font-medium text-slate-600">
                {{ citation.title }}
              </p>
              <span class="shrink-0 font-mono text-[6.5px] text-slate-400">
                {{ citation.knowledgePointId }}
              </span>
              <span class="font-mono text-[7px] text-emerald-500">{{ citation.score.toFixed(3) }}</span>
            </div>
          </div>
        </div>
        <p v-if="citations.length > 3" class="mt-2 text-center text-[7.5px] text-slate-400">
          还有 {{ citations.length - 3 }} 条引用展示在消息下方
        </p>
      </section>

      <section class="rounded-2xl border border-slate-200/80 bg-white p-3">
        <div class="flex items-center justify-between">
          <p class="text-[9px] font-semibold text-slate-600">快捷跳转</p>
        </div>
        <router-link
          :to="{ name: 'graph' }"
          class="mt-2 flex items-center gap-2 rounded-lg border border-slate-100 px-2.5 py-2 transition hover:border-indigo-100 hover:bg-indigo-50/40"
        >
          <span class="grid h-6 w-6 place-items-center rounded-md bg-emerald-50 text-emerald-500">
            <el-icon :size="11"><Share /></el-icon>
          </span>
          <span class="min-w-0 flex-1">
            <span class="block text-[8.5px] font-medium text-slate-600">查看知识图谱</span>
            <span class="mt-0.5 block text-[7px] text-slate-400">{{ systemStore.stats?.graphNodeCount ?? '—' }} 个节点 · 客观依赖关系</span>
          </span>
          <el-icon :size="9" class="text-slate-400"><ArrowRight /></el-icon>
        </router-link>
      </section>
    </div>

    <footer class="shrink-0 border-t border-slate-100 px-4 py-2.5">
      <p class="text-center font-mono text-[7.5px] tracking-wide text-slate-300">
        LIVE RAG PIPELINE · SERVER EDITION
      </p>
    </footer>
  </aside>
</template>
