<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { MagicStick, Promotion, VideoPause } from '@element-plus/icons-vue'
import { quickPrompts } from '@/data/mockData'

const props = withDefaults(
  defineProps<{
    streaming?: boolean
    disabled?: boolean
    topK?: number
    threshold?: number
  }>(),
  {
    streaming: false,
    disabled: false,
    topK: 5,
    threshold: 0.72,
  },
)

const emit = defineEmits<{
  (event: 'send', text: string): void
  (event: 'quick', text: string): void
  (event: 'stop'): void
}>()

const draft = ref('')
const focused = ref(false)
const textareaRef = ref<HTMLTextAreaElement | null>(null)

const canSend = computed(
  () => draft.value.trim().length > 0 && !props.streaming && !props.disabled,
)

function resizeTextarea(): void {
  const textarea = textareaRef.value
  if (!textarea) return
  textarea.style.height = 'auto'
  textarea.style.height = `${Math.min(textarea.scrollHeight, 132)}px`
}

function submit(): void {
  const text = draft.value.trim()
  if (!text || props.streaming || props.disabled) return
  emit('send', text)
  draft.value = ''
  nextTick(resizeTextarea)
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key !== 'Enter' || event.shiftKey || event.isComposing) return
  event.preventDefault()
  submit()
}

function handleQuick(text: string): void {
  if (props.streaming || props.disabled) return
  emit('quick', text)
}

function stop(): void {
  emit('stop')
}
</script>

<template>
  <div class="composer-wrap">
    <div class="mb-2.5 flex flex-wrap items-center gap-1.5 px-0.5">
      <span class="mr-0.5 flex items-center gap-1 text-[8px] font-medium uppercase tracking-[0.12em] text-slate-400">
        <el-icon :size="10" class="text-indigo-400"><MagicStick /></el-icon>
        快捷提问
      </span>
      <button
        v-for="prompt in quickPrompts"
        :key="prompt.label"
        type="button"
        class="quick-chip"
        :disabled="streaming || disabled"
        @click="handleQuick(prompt.prompt)"
      >
        {{ prompt.label }}
      </button>
    </div>

    <div
      class="composer-shell"
      :class="{ 'is-focused': focused }"
    >
      <textarea
        ref="textareaRef"
        v-model="draft"
        rows="1"
        class="composer-textarea"
        :disabled="disabled"
        placeholder="输入你的问题，或从上方选择一条学习任务…"
        @focus="focused = true"
        @blur="focused = false"
        @input="resizeTextarea"
        @keydown="handleKeydown"
      />

      <div class="mt-1 flex items-center justify-between gap-2 px-1.5 pb-0.5">
        <div class="flex min-w-0 items-center gap-2">
          <span class="inline-flex items-center gap-1.5 rounded-md border border-slate-200/70 bg-white px-1.5 py-0.5 text-[8px] font-medium text-slate-500">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            RAG-Agent v2
          </span>
          <span class="hidden font-mono text-[8px] text-slate-400 sm:inline">
            Top-K {{ topK }} · 阈值 {{ threshold.toFixed(2) }}
          </span>
        </div>

        <div class="flex shrink-0 items-center gap-2">
          <span class="hidden text-[8px] text-slate-400 md:inline">Enter 发送 · Shift + Enter 换行</span>
          <button
            v-if="streaming"
            type="button"
            class="composer-stop"
            @click="stop"
          >
            <el-icon :size="11"><VideoPause /></el-icon>
            停止
          </button>
          <button
            v-else
            type="button"
            class="composer-send"
            :disabled="!canSend"
            aria-label="发送消息"
            @click="submit"
          >
            <el-icon :size="15"><Promotion /></el-icon>
          </button>
        </div>
      </div>
    </div>

    <p class="mt-2 text-center text-[8px] leading-4 text-slate-400">
      回答由 RAG Agent 基于课程知识库生成，引用内容请以来源卡片为准
      <span class="mx-1 text-slate-300">·</span>
      <span class="font-mono">Mock SSE Stream</span>
    </p>
  </div>
</template>

<style scoped>
.composer-wrap {
  width: 100%;
}

.quick-chip {
  padding: 4px 9px;
  color: #5b6477;
  font-size: 9px;
  font-weight: 500;
  background: #f8fafc;
  border: 1px solid #e8edf4;
  border-radius: 7px;
  cursor: pointer;
  transition: all 0.18s ease;
}

.quick-chip:hover:not(:disabled) {
  color: #4f46e5;
  background: #f5f3ff;
  border-color: #ddd6fe;
  transform: translateY(-1px);
}

.quick-chip:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.composer-shell {
  padding: 11px 11px 8px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid #e3e8f1;
  border-radius: 16px;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.03),
    0 14px 36px -24px rgba(30, 41, 59, 0.28);
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease;
}

.composer-shell.is-focused {
  border-color: #c7d2fe;
  box-shadow:
    0 0 0 3px rgba(99, 102, 241, 0.06),
    0 16px 38px -24px rgba(79, 70, 229, 0.32);
}

.composer-textarea {
  display: block;
  width: 100%;
  min-height: 34px;
  max-height: 132px;
  padding: 5px 8px;
  overflow-y: auto;
  color: #1e293b;
  font-family: var(--app-font);
  font-size: 12.5px;
  line-height: 1.7;
  background: transparent;
  border: 0;
  outline: 0;
  resize: none;
}

.composer-textarea::placeholder {
  color: #9aa5b8;
}

.composer-textarea:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.composer-send {
  display: grid;
  width: 31px;
  height: 31px;
  place-items: center;
  color: #fff;
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  border: 0;
  border-radius: 9px;
  box-shadow: 0 8px 18px -8px rgba(79, 70, 229, 0.62);
  cursor: pointer;
  transition: all 0.18s ease;
}

.composer-send:hover:not(:disabled) {
  background: linear-gradient(135deg, #4f46e5, #4338ca);
  transform: translateY(-1px);
}

.composer-send:disabled {
  color: #cbd5e1;
  background: #f1f5f9;
  box-shadow: none;
  cursor: not-allowed;
}

.composer-stop {
  display: inline-flex;
  height: 31px;
  align-items: center;
  gap: 4px;
  padding: 0 11px;
  color: #dc2626;
  font-size: 10px;
  font-weight: 500;
  background: #fff5f5;
  border: 1px solid #fecaca;
  border-radius: 9px;
  cursor: pointer;
  transition: all 0.18s ease;
}

.composer-stop:hover {
  background: #fee2e2;
}
</style>
