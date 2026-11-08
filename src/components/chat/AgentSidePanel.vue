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

const props = defineProps<{
  isStreaming: boolean
  latestMessage: ChatMessage | null
}>()

const ragStore = useRagStore()

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
  <aside class="flex h-full w-full flex-col bg-[#fbfcfe]">
    <header class="flex h-[66px] shrink-0 items-center justify-between border-b border-slate-100 px-4">
      <div>
        <p class="text-[8px] font-semibold uppercase tracking-[0.2em] text-slate-400">
          Run Context
        </p>
        <h2 class="mt-1 text-[13px] font-semibold tracking-tight text-ink-950">Agent 运行台</h2>
      </div>
      <span
        class="inline-flex items-center gap-1.5 rounded-full border px-2 py-1 text-[8px] font-medium"
        :class="
          isStreaming
            ? 'border-indigo-100 bg-indigo-50 text-indigo-500'
            : 'border-emerald-100 bg-emerald-50 text-emerald-600'
        "
      >
        <span
          class="h-1.5 w-1.5 rounded-full"
          :class="isStreaming ? 'animate-pulse bg-indigo-500' : 'bg-emerald-400'"
        />
        {{ statusLabel }}
      </span>
    </header>

    <div class="min-h-0 flex-1 space-y-3 overflow-y-auto p-3.5 scroll-thin">
      <section class="relative overflow-hidden rounded-2xl bg-[#0b1326] p-4 text-white">
        <div class="pointer-events-none absolute inset-0" aria-hidden="true">
          <div class="absolute -right-8 -top-10 h-28 w-28 rounded-full bg-indigo-500/25 blur-2xl" />
          <div class="absolute -bottom-16 -left-10 h-28 w-28 rounded-full bg-cyan-400/10 blur-2xl" />
          <div class="absolute inset-0 dot-grid opacity-[0.07]" />
        </div>

        <div class="relative flex items-start justify-between">
          <div class="flex items-center gap-2">
            <span class="grid h-7 w-7 place-items-center rounded-lg border border-white/10 bg-white/[0.06] text-cyan-300">
              <el-icon :size="14"><MagicStick /></el-icon>
            </span>
            <div>
              <p class="text-[10px] font-semibold text-white">RAG-Agent</p>
              <p class="mt-0.5 font-mono text-[7.5px] text-slate-500">v2.4 · local mock</p>
            </div>
          </div>
          <span class="rounded border border-white/10 bg-white/[0.04] px-1.5 py-0.5 font-mono text-[7px] text-slate-500">
            ONLINE
          </span>
        </div>

        <p class="relative mt-3 text-[9px] leading-4 text-slate-400">
          面向计算机学科的检索增强学习 Agent，回答会显式绑定知识库证据。
        </p>

        <div class="relative mt-3.5 grid grid-cols-3 gap-1.5">
          <div class="rounded-lg border border-white/[0.06] bg-white/[0.035] px-2 py-1.5">
            <p class="font-mono text-[13px] font-semibold text-white">
              {{ doneSteps }}<span class="text-[7px] text-slate-600">/{{ totalSteps }}</span>
            </p>
            <p class="mt-0.5 text-[7px] text-slate-500">思考步骤</p>
          </div>
          <div class="rounded-lg border border-white/[0.06] bg-white/[0.035] px-2 py-1.5">
            <p class="font-mono text-[13px] font-semibold text-white">{{ toolCount }}</p>
            <p class="mt-0.5 text-[7px] text-slate-500">工具调用</p>
          </div>
          <div class="rounded-lg border border-white/[0.06] bg-white/[0.035] px-2 py-1.5">
            <p class="font-mono text-[13px] font-semibold text-white">{{ chunkCount }}</p>
            <p class="mt-0.5 text-[7px] text-slate-500">召回片段</p>
          </div>
        </div>

        <div class="relative mt-3 flex items-center justify-between text-[7.5px] text-slate-500">
          <span class="flex items-center gap-1">
            <el-icon :size="9"><Timer /></el-icon>
            {{ latestMessage?.latencyMs ? `${(latestMessage.latencyMs / 1000).toFixed(1)}s 最近耗时` : '等待首轮推理' }}
          </span>
          <span class="font-mono">ctx: 8k</span>
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
            <span class="font-mono text-[15px] font-semibold text-slate-800">8</span>
            <span class="ml-1 text-[8px] text-slate-400">门课程</span>
          </div>
          <div class="h-3 w-px bg-slate-100" />
          <div>
            <span class="font-mono text-[15px] font-semibold text-slate-800">326</span>
            <span class="ml-1 text-[8px] text-slate-400">个知识点</span>
          </div>
        </div>
        <div class="mt-2.5 flex items-center gap-1.5 text-[8px] text-slate-400">
          <span class="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          索引健康 · 3 分钟前同步
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
        <p class="mt-2 text-[7.5px] leading-3.5 text-slate-400">
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
            <span class="mt-0.5 block text-[7px] text-slate-400">23 个节点 · 客观依赖关系</span>
          </span>
          <el-icon :size="9" class="text-slate-400"><ArrowRight /></el-icon>
        </router-link>
      </section>
    </div>

    <footer class="shrink-0 border-t border-slate-100 px-4 py-2.5">
      <p class="text-center font-mono text-[7.5px] tracking-wide text-slate-300">
        MOCK RAG PIPELINE · NO MASTERY DATA
      </p>
    </footer>
  </aside>
</template>
