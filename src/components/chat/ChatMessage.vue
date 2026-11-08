<script setup lang="ts">
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  CopyDocument,
  Link,
  MagicStick,
  Refresh,
  Timer,
  WarningFilled,
} from '@element-plus/icons-vue'
import type { ChatMessage } from '@/types'
import { formatDuration } from '@/utils/format'
import { useAuthStore } from '@/stores/auth'
import MarkdownView from '@/components/chat/MarkdownView.vue'
import ThinkingPanel from '@/components/chat/ThinkingPanel.vue'
import CitationCard from '@/components/chat/CitationCard.vue'

const props = defineProps<{
  message: ChatMessage
}>()

const emit = defineEmits<{
  (event: 'retry', message: ChatMessage): void
}>()

const authStore = useAuthStore()

const timeLabel = computed(() =>
  new Date(props.message.createdAt).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }),
)

const isStreaming = computed(() => props.message.status === 'streaming')

async function copyContent(): Promise<void> {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(props.message.content)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = props.message.content
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }
    ElMessage.success('回答已复制')
  } catch {
    ElMessage.error('复制失败，请手动选择文本')
  }
}
</script>

<template>
  <div v-if="message.role === 'user'" class="flex animate-fade-up justify-end gap-2.5">
    <div class="flex max-w-[86%] flex-col items-end sm:max-w-[78%]">
      <div
        class="rounded-2xl rounded-tr-[5px] bg-[#101a34] px-4 py-2.5 text-[12px] leading-6 text-slate-100 shadow-[0_12px_30px_-20px_rgba(2,6,23,0.75)]"
      >
        <p class="whitespace-pre-wrap break-words">{{ message.content }}</p>
      </div>
      <div class="mt-1.5 flex items-center gap-1.5 pr-1 text-[8px] text-slate-400">
        <span>{{ timeLabel }}</span>
        <span class="text-slate-300">·</span>
        <span>{{ authStore.user?.displayName ?? '我' }}</span>
      </div>
    </div>
    <div
      class="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-slate-100 text-[10px] font-bold text-slate-500"
    >
      {{ authStore.user?.avatarText ?? '我' }}
    </div>
  </div>

  <div v-else class="flex animate-fade-up gap-2.5 sm:gap-3">
    <div
      class="relative mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-[10px] bg-gradient-to-br from-indigo-500 via-indigo-500 to-cyan-400 text-white shadow-[0_10px_24px_-12px_rgba(79,70,229,0.7)]"
    >
      <el-icon :size="15"><MagicStick /></el-icon>
      <span
        class="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-white bg-emerald-400"
      />
    </div>

    <div class="min-w-0 flex-1">
      <div class="flex min-h-5 flex-wrap items-center gap-2">
        <span class="text-[11.5px] font-semibold text-slate-800">智研 Agent</span>
        <span
          class="rounded border border-indigo-100 bg-indigo-50 px-1 py-px text-[7.5px] font-semibold tracking-wide text-indigo-500"
        >
          RAG
        </span>
        <span class="text-[8px] text-slate-400">{{ timeLabel }}</span>
        <span
          v-if="isStreaming"
          class="inline-flex items-center gap-1 rounded-full bg-indigo-50 px-1.5 py-px text-[8px] font-medium text-indigo-500"
        >
          <span class="flex items-center gap-[2px]">
            <span class="thinking-dot h-[3px] w-[3px] rounded-full bg-indigo-500" />
            <span class="thinking-dot h-[3px] w-[3px] rounded-full bg-indigo-500 [animation-delay:150ms]" />
            <span class="thinking-dot h-[3px] w-[3px] rounded-full bg-indigo-500 [animation-delay:300ms]" />
          </span>
          生成中
        </span>
        <span
          v-else-if="message.latencyMs"
          class="hidden items-center gap-1 rounded-full border border-slate-200 bg-white px-1.5 py-px font-mono text-[7.5px] text-slate-400 sm:inline-flex"
        >
          <el-icon :size="8"><Timer /></el-icon>
          {{ formatDuration(message.latencyMs) }}
        </span>
      </div>

      <div class="mt-2 min-w-0">
        <div
          v-if="isStreaming && !message.content"
          class="flex items-center gap-2 rounded-xl border border-slate-100 bg-slate-50/70 px-3 py-3"
        >
          <span class="relative flex h-5 w-5 items-center justify-center">
            <span class="absolute h-5 w-5 animate-ping rounded-full bg-indigo-200/50" />
            <span class="relative h-2 w-2 rounded-full bg-indigo-500" />
          </span>
          <div>
            <p class="text-[10px] font-medium text-slate-500">正在检索知识库并组织回答</p>
            <p class="mt-0.5 text-[8px] text-slate-400">展开下方思考面板可查看实时推理过程</p>
          </div>
        </div>

        <ThinkingPanel
          v-if="message.trace"
          :trace="message.trace"
          :status="message.status"
          :default-open="isStreaming"
        />

        <MarkdownView
          v-if="message.content"
          :content="message.content"
          :streaming="isStreaming"
          :class="message.trace ? 'mt-2.5' : ''"
        />

        <div
          v-if="message.status === 'error'"
          class="mt-2 flex items-start gap-2.5 rounded-xl border border-rose-100 bg-rose-50/80 px-3 py-2.5"
        >
          <el-icon class="mt-0.5 shrink-0 text-rose-500" :size="14"><WarningFilled /></el-icon>
          <div class="min-w-0 flex-1">
            <p class="text-[10px] font-semibold text-rose-600">回答生成失败</p>
            <p class="mt-0.5 text-[9px] leading-4 text-rose-500/80">
              {{ message.error || '流式连接异常，请重试。' }}
            </p>
          </div>
          <button
            type="button"
            class="inline-flex shrink-0 items-center gap-1 rounded-md border border-rose-200 bg-white px-2 py-1 text-[8px] font-medium text-rose-500 transition hover:bg-rose-100"
            @click="emit('retry', message)"
          >
            <el-icon :size="9"><Refresh /></el-icon>
            重试
          </button>
        </div>

        <p
          v-if="message.stopped"
          class="mt-2 inline-flex items-center gap-1 rounded-md bg-amber-50 px-2 py-1 text-[8px] text-amber-600"
        >
          <span class="h-1 w-1 rounded-full bg-amber-500" />
          已手动停止生成，以上为已生成内容
        </p>

        <section v-if="message.citations.length && !isStreaming" class="mt-4">
          <div class="mb-2.5 flex items-center gap-2">
            <span class="grid h-4 w-4 place-items-center rounded bg-indigo-50 text-indigo-500">
              <el-icon :size="9"><Link /></el-icon>
            </span>
            <p class="text-[9px] font-semibold tracking-wide text-slate-500">RAG 引用来源</p>
            <span class="rounded-full bg-slate-100 px-1.5 py-px font-mono text-[7.5px] text-slate-400">
              {{ message.citations.length }} 条
            </span>
            <span class="h-px flex-1 bg-gradient-to-r from-slate-200 to-transparent" />
          </div>
          <div class="grid gap-2 sm:grid-cols-2">
            <CitationCard
              v-for="citation in message.citations"
              :key="citation.id"
              :citation="citation"
            />
          </div>
        </section>

        <div
          v-if="!isStreaming && message.status === 'done' && message.content"
          class="mt-3 flex items-center gap-1.5"
        >
          <button
            type="button"
            class="message-action"
            @click="copyContent"
          >
            <el-icon :size="10"><CopyDocument /></el-icon>
            复制回答
          </button>
          <span class="text-slate-200">|</span>
          <span class="font-mono text-[8px] text-slate-400">
            {{ message.citations.length }} citations · mock SSE
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.message-action {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 7px;
  color: #94a3b8;
  font-size: 8px;
  background: transparent;
  border: 0;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.16s ease;
}

.message-action:hover {
  color: #4f46e5;
  background: #f5f3ff;
}

.thinking-dot {
  animation: thinking-dot 1.2s ease-in-out infinite;
}
</style>
