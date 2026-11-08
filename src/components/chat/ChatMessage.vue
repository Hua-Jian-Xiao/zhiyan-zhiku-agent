<script setup lang="ts">
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  CopyDocument,
  Link,
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
        class="rounded-none bg-[#211c17] px-4 py-2.5 text-[12px] leading-6 text-[#f4ead9]"
      >
        <p class="whitespace-pre-wrap break-words">{{ message.content }}</p>
      </div>
      <div class="mt-1.5 flex items-center gap-1.5 pr-1 font-mono text-[7px] text-[#a29582]">
        <span>{{ timeLabel }}</span>
        <span class="text-[#d8cebd]">/</span>
        <span>{{ authStore.user?.displayName ?? '我' }}</span>
      </div>
    </div>
    <div
      class="mt-0.5 grid h-7 w-7 shrink-0 place-items-center border border-[#c9bdab] bg-[#f8f1e5] font-serif text-[11px] text-[#682728]"
    >
      {{ authStore.user?.avatarText ?? '我' }}
    </div>
  </div>

  <div v-else class="flex animate-fade-up gap-2.5 sm:gap-3">
    <div
      class="relative mt-0.5 grid h-8 w-8 shrink-0 place-items-center border border-[#b9ab97] bg-[#f8f1e5] font-serif text-[11px] text-[#682728]"
    >
      AI
      <span
        class="absolute -bottom-0.5 -right-0.5 h-2 w-2 border border-[#fffdf8] bg-[#5c7a60]"
      />
    </div>

    <div class="min-w-0 flex-1">
      <div class="flex min-h-5 flex-wrap items-center gap-2 border-b border-[#e6ddcf] pb-2">
        <span class="font-serif text-[12px] font-semibold text-[#211c17]">智研 Agent</span>
        <span
          class="border border-[#d8cebd] px-1 py-px font-mono text-[7px] tracking-[0.1em] text-[#8d806e]"
        >
          RAG / ARTICLE
        </span>
        <span class="font-mono text-[7px] text-[#a29582]">{{ timeLabel }}</span>
        <span
          v-if="isStreaming"
          class="inline-flex items-center gap-1 border border-[#d8b8b1] bg-[#f6e9e4] px-1.5 py-px font-mono text-[7px] text-[#8e3d35]"
        >
          <span class="flex items-center gap-[2px]">
            <span class="thinking-dot h-[2px] w-[2px] rounded-full bg-[#9a463c]" />
            <span class="thinking-dot h-[2px] w-[2px] rounded-full bg-[#9a463c] [animation-delay:150ms]" />
            <span class="thinking-dot h-[2px] w-[2px] rounded-full bg-[#9a463c] [animation-delay:300ms]" />
          </span>
          COMPOSING
        </span>
        <span
          v-else-if="message.latencyMs"
          class="hidden items-center gap-1 border border-[#d8cebd] px-1.5 py-px font-mono text-[7px] text-[#a29582] sm:inline-flex"
        >
          <el-icon :size="8"><Timer /></el-icon>
          {{ formatDuration(message.latencyMs) }}
        </span>
      </div>

      <div class="mt-3 min-w-0">
        <div
          v-if="isStreaming && !message.content"
          class="flex items-center gap-2 border-l-2 border-[#9a463c] bg-[#f8f3e9] px-3 py-3"
        >
          <span class="relative flex h-5 w-5 items-center justify-center">
            <span class="absolute h-5 w-5 animate-ping rounded-full bg-[#d9c2b6]/60" />
            <span class="relative h-1.5 w-1.5 rounded-full bg-[#9a463c]" />
          </span>
          <div>
            <p class="text-[10px] font-medium text-[#5b5145]">正在检索知识库并组织回答</p>
            <p class="mt-0.5 font-mono text-[7px] uppercase tracking-[0.06em] text-[#a29582]">Retrieving evidence · compose draft</p>
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
          class="mt-2 flex items-start gap-2.5 border border-rose-200 bg-rose-50 px-3 py-2.5"
        >
          <el-icon class="mt-0.5 shrink-0 text-rose-500" :size="14"><WarningFilled /></el-icon>
          <div class="min-w-0 flex-1">
            <p class="font-serif text-[11px] font-semibold text-rose-700">回答生成失败</p>
            <p class="mt-0.5 text-[9px] leading-4 text-rose-600/80">
              {{ message.error || '流式连接异常，请重试。' }}
            </p>
          </div>
          <button
            type="button"
            class="inline-flex shrink-0 items-center gap-1 border border-rose-300 bg-white px-2 py-1 font-mono text-[7.5px] text-rose-600 transition hover:bg-rose-100"
            @click="emit('retry', message)"
          >
            <el-icon :size="9"><Refresh /></el-icon>
            重试
          </button>
        </div>

        <p
          v-if="message.stopped"
          class="mt-2 inline-flex items-center gap-1.5 border border-amber-200 bg-amber-50 px-2 py-1 font-mono text-[7.5px] text-amber-700"
        >
          <span class="h-1 w-1 rounded-full bg-amber-500" />
          已手动停止生成，以上为已生成内容
        </p>

        <section v-if="message.citations.length && !isStreaming" class="mt-5">
          <div class="mb-2.5 flex items-center gap-2 border-b border-[#c9bdab] pb-2">
            <el-icon :size="10" class="text-[#7d302f]"><Link /></el-icon>
            <p class="font-mono text-[7.5px] font-medium uppercase tracking-[0.16em] text-[#5b5145]">
              References / 引用来源
            </p>
            <span class="font-mono text-[7px] text-[#a29582]">
              [{{ message.citations.length }}]
            </span>
            <span class="h-px flex-1" />
            <span class="font-mono text-[6.5px] tracking-[0.1em] text-[#b5a995]">FOOTNOTES</span>
          </div>
          <div class="grid gap-x-4 gap-y-3 sm:grid-cols-2">
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
          <span class="text-[#d8cebd]">/</span>
          <span class="font-mono text-[7px] uppercase tracking-[0.06em] text-[#a29582]">
            {{ message.citations.length }} citations · live sse
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
  padding: 3px 6px;
  color: #8d806e;
  font-family: var(--app-mono);
  font-size: 10px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 0;
  cursor: pointer;
  transition: all 0.16s ease;
}

.message-action:hover {
  color: #7d302f;
  border-color: #d8cebd;
  background: #fbf6ec;
}

.thinking-dot {
  animation: thinking-dot 1.2s ease-in-out infinite;
}
</style>
