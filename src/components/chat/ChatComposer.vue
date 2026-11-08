<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { MagicStick, Promotion, VideoPause } from '@element-plus/icons-vue'
import { quickPrompts } from '@/mock'
import type { RetrievalMode } from '@/types'
import { getRetrievalModeLabel } from '@/utils/rag'

const props = withDefaults(
  defineProps<{
    streaming?: boolean
    disabled?: boolean
    topK?: number
    threshold?: number
    retrievalMode?: RetrievalMode
  }>(),
  {
    streaming: false,
    disabled: false,
    topK: 5,
    threshold: 0.72,
    retrievalMode: 'hybrid',
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

const modeLabel = computed(() => getRetrievalModeLabel(props.retrievalMode))

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
      <span class="mr-1 flex items-center gap-1 font-mono text-[7px] font-medium uppercase tracking-[0.16em] text-[#a29582]">
        <el-icon :size="9" class="text-[#9a463c]"><MagicStick /></el-icon>
        Quick notes / 快捷提问
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

    <div class="composer-shell" :class="{ 'is-focused': focused }">
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
          <span class="inline-flex items-center gap-1.5 border border-[#d8cebd] px-1.5 py-0.5 font-mono text-[7px] tracking-[0.04em] text-[#6f6456]">
            <span class="h-1 w-1 rounded-full bg-[#5c7a60]" />
            RAG-AGENT / v2
          </span>
          <span class="hidden font-mono text-[7px] text-[#a29582] sm:inline">
            {{ modeLabel }} · TOP-K {{ topK }} · 阈值 {{ threshold.toFixed(2) }}
          </span>
        </div>

        <div class="flex shrink-0 items-center gap-2">
          <span class="hidden font-mono text-[7px] text-[#a29582] md:inline">ENTER 发送 / SHIFT+ENTER 换行</span>
          <button v-if="streaming" type="button" class="composer-stop" @click="stop">
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

    <p class="mt-2 text-center font-mono text-[7px] leading-4 tracking-[0.04em] text-[#a29582]">
      回答由 RAG Agent 基于课程知识库生成，引用内容请以来源卡片为准
      <span class="mx-1 text-[#d8cebd]">/</span>
      Mock SSE Stream
    </p>
  </div>
</template>

<style scoped>
.composer-wrap {
  width: 100%;
}

.quick-chip {
  padding: 3px 1px;
  color: #6f6456;
  font-family: var(--app-font);
  font-size: 8.5px;
  font-weight: 500;
  background: transparent;
  border: 0;
  border-bottom: 1px solid #c9bdab;
  border-radius: 0;
  cursor: pointer;
  transition: all 0.18s ease;
}

.quick-chip:hover:not(:disabled) {
  color: #7d302f;
  border-bottom-color: #7d302f;
}

.quick-chip:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.composer-shell {
  padding: 9px 10px 7px;
  background: #fffdf8;
  border: 1px solid #b9ab97;
  border-top: 2px solid #211c17;
  border-radius: 0;
  box-shadow: none;
  transition: border-color 0.18s ease;
}

.composer-shell.is-focused {
  border-color: #9a463c;
  border-top-color: #7d302f;
  box-shadow: none;
}

.composer-textarea {
  display: block;
  width: 100%;
  min-height: 34px;
  max-height: 132px;
  padding: 5px 7px;
  overflow-y: auto;
  color: #2f2922;
  font-family: var(--app-font);
  font-size: 12px;
  line-height: 1.75;
  background: transparent;
  border: 0;
  outline: 0;
  resize: none;
}

.composer-textarea::placeholder {
  color: #a99d8b;
  font-style: italic;
}

.composer-textarea:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.composer-send {
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  color: #fffdf8;
  background: #682728;
  border: 1px solid #682728;
  border-radius: 0;
  box-shadow: none;
  cursor: pointer;
  transition: all 0.18s ease;
}

.composer-send:hover:not(:disabled) {
  background: #552222;
  border-color: #552222;
}

.composer-send:disabled {
  color: #b5a995;
  background: #efe7da;
  border-color: #d8cebd;
  box-shadow: none;
  cursor: not-allowed;
}

.composer-stop {
  display: inline-flex;
  height: 30px;
  align-items: center;
  gap: 4px;
  padding: 0 10px;
  color: #8e3d35;
  font-family: var(--app-mono);
  font-size: 8px;
  letter-spacing: 0.04em;
  background: #f6e9e4;
  border: 1px solid #d8b8b1;
  border-radius: 0;
  cursor: pointer;
  transition: all 0.18s ease;
}

.composer-stop:hover {
  background: #efdcd5;
}
</style>
