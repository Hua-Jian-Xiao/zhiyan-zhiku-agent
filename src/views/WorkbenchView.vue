<script setup lang="ts">
import type { Component } from 'vue'
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowRight,
  Collection,
  Compass,
  Delete,
  MagicStick,
  Operation,
  Plus,
  Share,
} from '@element-plus/icons-vue'
import ChatComposer from '@/components/chat/ChatComposer.vue'
import ChatMessage from '@/components/chat/ChatMessage.vue'
import ConversationList from '@/components/chat/ConversationList.vue'
import AgentSidePanel from '@/components/chat/AgentSidePanel.vue'
import StatePanel from '@/components/feedback/StatePanel.vue'
import { starterPrompts } from '@/data/mockData'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { useRagStore } from '@/stores/rag'
import { createInitialTrace } from '@/services/mockAgentServer'
import {
  streamAgentReply,
  type AgentStreamEvent,
} from '@/services/agentService'
import type { ChatMessage as ChatMessageType, Conversation } from '@/types'
import { isAbortError } from '@/utils/async'
import { createId } from '@/utils/id'

const chatStore = useChatStore()
const ragStore = useRagStore()
const authStore = useAuthStore()

const scrollContainer = ref<HTMLElement | null>(null)
const mobileListOpen = ref(false)
const autoScroll = ref(true)
const activeController = ref<AbortController | null>(null)

const activeConversation = computed(() => chatStore.activeConversation)
const messages = computed(() => chatStore.activeMessages)
const latestAssistant = computed(() => chatStore.lastAssistantMessage)
const userMessageCount = computed(
  () => messages.value.filter((message) => message.role === 'user').length,
)

const starterIcons: Record<string, Component> = {
  route: Compass,
  graph: Share,
  spark: MagicStick,
  layers: Collection,
}

const headerSubtitle = computed(() => {
  if (chatStore.isStreaming) return 'Agent 正在检索并生成，可展开思考面板查看实时过程'
  if (!activeConversation.value) return '新建或选择一个会话开始学习'
  return `${userMessageCount.value} 轮对话 · 本地会话已自动保存`
})

function scrollToBottom(behavior: ScrollBehavior = 'auto'): void {
  nextTick(() => {
    const container = scrollContainer.value
    if (!container) return
    container.scrollTo({ top: container.scrollHeight, behavior })
  })
}

function handleScroll(): void {
  const container = scrollContainer.value
  if (!container) return
  autoScroll.value =
    container.scrollHeight - container.scrollTop - container.clientHeight < 120
}

watch(
  () => {
    const conversation = chatStore.activeConversation
    if (!conversation) return ''
    const last = conversation.messages[conversation.messages.length - 1]
    return [
      conversation.id,
      conversation.messages.length,
      last?.content.length ?? 0,
      last?.status ?? '',
      last?.trace?.steps.map((step) => step.status).join('-') ?? '',
      last?.trace?.tools.length ?? 0,
      last?.trace?.chunks.length ?? 0,
      last?.citations.length ?? 0,
    ].join('|')
  },
  () => {
    if (autoScroll.value) scrollToBottom()
  },
)

watch(
  () => chatStore.activeId,
  () => {
    autoScroll.value = true
    mobileListOpen.value = false
    scrollToBottom()
  },
)

function guardStreaming(): boolean {
  if (chatStore.isStreaming) {
    ElMessage.warning('当前回答仍在生成中，请先停止生成再切换操作')
    return false
  }
  return true
}

function handleCreateConversation(): void {
  if (!guardStreaming()) return
  chatStore.createConversation()
  mobileListOpen.value = false
  autoScroll.value = true
  scrollToBottom()
}

function handleSelectConversation(conversationId: string): void {
  if (conversationId === chatStore.activeId) {
    mobileListOpen.value = false
    return
  }
  if (!guardStreaming()) return
  chatStore.selectConversation(conversationId)
}

async function handleDeleteConversation(conversation: Conversation): Promise<void> {
  if (!guardStreaming()) return
  try {
    await ElMessageBox.confirm(
      `删除后「${conversation.title}」将无法恢复，确定继续吗？`,
      '删除会话',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      },
    )
  } catch {
    return
  }
  chatStore.deleteConversation(conversation.id)
  ElMessage.success('会话已删除')
}

async function handleClearConversation(): Promise<void> {
  const conversation = activeConversation.value
  if (!conversation || conversation.messages.length === 0) return
  if (!guardStreaming()) return
  try {
    await ElMessageBox.confirm('清空后当前会话的全部消息将被移除，确定继续吗？', '清空会话', {
      confirmButtonText: '清空',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger',
    })
  } catch {
    return
  }
  chatStore.clearConversation(conversation.id)
  scrollToBottom()
}

function applyStreamEvent(
  conversationId: string,
  messageId: string,
  event: AgentStreamEvent,
): void {
  const conversation = chatStore.getConversation(conversationId)
  const message = conversation?.messages.find((item) => item.id === messageId)
  if (!message) return

  switch (event.type) {
    case 'step': {
      const trace = message.trace ?? createInitialTrace()
      const steps = [...trace.steps]
      const index = steps.findIndex((step) => step.id === event.step.id)
      if (index >= 0) steps[index] = event.step
      else steps.push(event.step)
      chatStore.updateMessage(conversationId, messageId, { trace: { ...trace, steps } })
      break
    }
    case 'tool': {
      const trace = message.trace ?? createInitialTrace()
      const tools = [...trace.tools]
      const index = tools.findIndex((tool) => tool.id === event.tool.id)
      if (index >= 0) tools[index] = event.tool
      else tools.push(event.tool)
      chatStore.updateMessage(conversationId, messageId, { trace: { ...trace, tools } })
      break
    }
    case 'retrieval': {
      const trace = message.trace ?? createInitialTrace()
      chatStore.updateMessage(conversationId, messageId, {
        trace: { ...trace, chunks: event.chunks },
      })
      break
    }
    case 'citations':
      chatStore.updateMessage(conversationId, messageId, {
        citations: event.citations,
      })
      break
    case 'delta':
      chatStore.updateMessage(conversationId, messageId, {
        content: message.content + event.text,
      })
      break
    case 'done':
      chatStore.updateMessage(conversationId, messageId, {
        status: 'done',
        latencyMs: event.meta.latencyMs,
      })
      break
    default:
      break
  }
}

async function runAgent(conversationId: string, query: string): Promise<void> {
  const conversation = chatStore.getConversation(conversationId)
  if (!conversation) return

  const assistantMessage: ChatMessageType = {
    id: createId('msg'),
    role: 'assistant',
    content: '',
    createdAt: Date.now(),
    status: 'streaming',
    citations: [],
    trace: createInitialTrace(),
  }
  chatStore.appendMessage(conversationId, assistantMessage)

  const controller = new AbortController()
  activeController.value = controller
  chatStore.beginStreaming(conversationId, assistantMessage.id)
  autoScroll.value = true
  scrollToBottom()

  try {
    await streamAgentReply(
      {
        query,
        topK: ragStore.config.topK,
        threshold: ragStore.config.threshold,
      },
      (event) => applyStreamEvent(conversationId, assistantMessage.id, event),
      controller.signal,
    )
  } catch (error) {
    const currentMessage = chatStore
      .getConversation(conversationId)
      ?.messages.find((message) => message.id === assistantMessage.id)

    if (isAbortError(error)) {
      if (currentMessage && currentMessage.status !== 'done') {
        chatStore.updateMessage(conversationId, assistantMessage.id, {
          status: 'done',
          stopped: true,
        })
      }
    } else {
      chatStore.updateMessage(conversationId, assistantMessage.id, {
        status: 'error',
        error: error instanceof Error ? error.message : '流式连接异常，请稍后重试',
      })
      ElMessage.error('回答生成失败，请检查后重试')
    }
  } finally {
    chatStore.endStreaming()
    if (activeController.value === controller) activeController.value = null
  }
}

async function handleSend(rawText: string): Promise<void> {
  const text = rawText.trim()
  if (!text) return
  if (!guardStreaming()) return

  const conversation = chatStore.activeConversation ?? chatStore.createConversation()
  const userMessage: ChatMessageType = {
    id: createId('msg'),
    role: 'user',
    content: text,
    createdAt: Date.now(),
    status: 'done',
    citations: [],
  }
  chatStore.appendMessage(conversation.id, userMessage)
  autoScroll.value = true
  scrollToBottom()
  await runAgent(conversation.id, text)
}

function handleQuickPrompt(text: string): void {
  void handleSend(text)
}

function handleStop(): void {
  activeController.value?.abort()
}

async function handleRetry(message: ChatMessageType): Promise<void> {
  if (!guardStreaming()) return
  const conversation = activeConversation.value
  if (!conversation) return
  const index = conversation.messages.findIndex((item) => item.id === message.id)
  if (index === -1) return
  const previousUser = [...conversation.messages.slice(0, index)]
    .reverse()
    .find((item) => item.role === 'user')
  if (!previousUser) {
    ElMessage.error('找不到对应的原始问题，请重新输入')
    return
  }
  chatStore.removeMessage(conversation.id, message.id)
  await runAgent(conversation.id, previousUser.content)
}

onBeforeUnmount(() => {
  activeController.value?.abort()
  activeController.value = null
  chatStore.endStreaming()
})
</script>

<template>
  <div class="flex h-full flex-col p-2.5 sm:p-3 lg:p-4">
    <div
      class="flex min-h-0 flex-1 overflow-hidden rounded-[22px] border border-white/80 bg-white shadow-[0_20px_70px_-34px_rgba(15,23,42,0.28)]"
    >
      <div class="hidden w-[254px] shrink-0 border-r border-slate-100 lg:block">
        <ConversationList
          :conversations="chatStore.sortedConversations"
          :active-id="chatStore.activeId"
          :streaming="chatStore.isStreaming"
          @select="handleSelectConversation"
          @create="handleCreateConversation"
          @remove="handleDeleteConversation"
        />
      </div>

      <section class="flex min-w-0 flex-1 flex-col bg-white">
        <header class="flex h-[66px] shrink-0 items-center justify-between gap-3 border-b border-slate-100 px-3 sm:px-5">
          <div class="flex min-w-0 items-center gap-2.5">
            <button
              type="button"
              class="grid h-8 w-8 shrink-0 place-items-center rounded-lg border border-slate-200 bg-white text-slate-500 transition hover:bg-slate-50 lg:hidden"
              aria-label="打开会话列表"
              @click="mobileListOpen = true"
            >
              <el-icon :size="14"><Operation /></el-icon>
            </button>
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <h2 class="truncate text-[13px] font-semibold tracking-tight text-slate-800">
                  {{ activeConversation?.title || 'Agent 对话工作台' }}
                </h2>
                <span
                  v-if="chatStore.isStreaming"
                  class="hidden shrink-0 items-center gap-1 rounded-full border border-indigo-100 bg-indigo-50 px-1.5 py-px text-[7.5px] font-medium text-indigo-500 sm:inline-flex"
                >
                  <span class="h-1 w-1 animate-pulse rounded-full bg-indigo-500" />
                  LIVE
                </span>
              </div>
              <p class="mt-0.5 truncate text-[8px] text-slate-400">{{ headerSubtitle }}</p>
            </div>
          </div>

          <div class="flex shrink-0 items-center gap-1.5">
            <span
              class="hidden items-center gap-1.5 rounded-lg border border-slate-200/80 bg-slate-50/70 px-2 py-1 text-[8px] text-slate-500 xl:inline-flex"
            >
              <span class="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              {{ authStore.displayName }} · 已连接知识库
            </span>
            <el-tooltip content="新建会话" placement="bottom" :show-after="300">
              <button
                type="button"
                class="header-action"
                aria-label="新建会话"
                @click="handleCreateConversation"
              >
                <el-icon :size="13"><Plus /></el-icon>
              </button>
            </el-tooltip>
            <el-tooltip content="清空当前会话" placement="bottom" :show-after="300">
              <button
                type="button"
                class="header-action hover:!text-rose-500"
                :disabled="!activeConversation || activeConversation.messages.length === 0"
                aria-label="清空当前会话"
                @click="handleClearConversation"
              >
                <el-icon :size="13"><Delete /></el-icon>
              </button>
            </el-tooltip>
          </div>
        </header>

        <div
          ref="scrollContainer"
          class="min-h-0 flex-1 overflow-y-auto scroll-thin"
          @scroll.passive="handleScroll"
        >
          <div v-if="!activeConversation" class="flex h-full items-center justify-center">
            <StatePanel
              title="还没有打开的会话"
              description="从左侧选择一个历史会话，或新建一个会话继续你的学习。"
              action-text="新建会话"
              @action="handleCreateConversation"
            />
          </div>

          <div
            v-else-if="messages.length === 0"
            class="relative flex min-h-full items-center justify-center overflow-hidden px-4 py-8 sm:px-8"
          >
            <div class="pointer-events-none absolute inset-0" aria-hidden="true">
              <div class="absolute left-1/2 top-[8%] h-64 w-64 -translate-x-1/2 rounded-full bg-indigo-100/45 blur-[75px]" />
              <div class="absolute bottom-[8%] left-[18%] h-40 w-40 rounded-full bg-cyan-100/50 blur-[60px]" />
              <div class="absolute inset-0 dot-grid opacity-[0.18]" />
            </div>

            <div class="relative w-full max-w-[670px] animate-fade-up text-center">
              <div
                class="relative mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-indigo-500 via-indigo-500 to-cyan-400 text-white shadow-[0_18px_40px_-18px_rgba(79,70,229,0.7)]"
              >
                <span class="absolute -right-1.5 -top-1.5 grid h-5 w-5 place-items-center rounded-full border-2 border-white bg-[#0b1226]">
                  <span class="h-1.5 w-1.5 animate-soft-pulse rounded-full bg-cyan-300" />
                </span>
                <el-icon :size="25"><MagicStick /></el-icon>
              </div>

              <p class="mt-5 text-[8px] font-semibold uppercase tracking-[0.22em] text-indigo-400">
                RAG Learning Agent
              </p>
              <h1 class="mt-2 text-[27px] font-bold tracking-[-0.035em] text-ink-950 sm:text-[32px]">
                今天想研究什么？
              </h1>
              <p class="mx-auto mt-2.5 max-w-[470px] text-[11px] leading-6 text-slate-500">
                我会从 8 门计算机课程、326 个知识点中检索证据，
                用可追溯的引用陪你完成一次深度探索。
              </p>

              <div class="mt-7 grid gap-2.5 text-left sm:grid-cols-2">
                <button
                  v-for="prompt in starterPrompts"
                  :key="prompt.title"
                  type="button"
                  class="starter-card group"
                  @click="handleQuickPrompt(prompt.prompt)"
                >
                  <span class="starter-icon">
                    <el-icon :size="15"><component :is="starterIcons[prompt.icon]" /></el-icon>
                  </span>
                  <span class="min-w-0 flex-1">
                    <span class="block text-[10.5px] font-semibold text-slate-700">
                      {{ prompt.title }}
                    </span>
                    <span class="mt-1 block text-[9px] leading-4 text-slate-400">
                      {{ prompt.description }}
                    </span>
                  </span>
                  <el-icon
                    :size="11"
                    class="mt-0.5 shrink-0 text-slate-300 transition-all group-hover:translate-x-0.5 group-hover:text-indigo-400"
                  >
                    <ArrowRight />
                  </el-icon>
                </button>
              </div>

              <div class="mt-6 flex flex-wrap items-center justify-center gap-x-4 gap-y-1.5 text-[8px] text-slate-400">
                <span class="flex items-center gap-1.5">
                  <span class="h-1 w-1 rounded-full bg-emerald-400" />
                  知识库已连接
                </span>
                <span class="text-slate-200">|</span>
                <span>Top-K {{ ragStore.config.topK }}</span>
                <span class="text-slate-200">|</span>
                <span>引用阈值 {{ ragStore.config.threshold.toFixed(2) }}</span>
                <span class="text-slate-200">|</span>
                <span class="font-mono">MOCK SSE</span>
              </div>
            </div>
          </div>

          <div v-else class="mx-auto w-full max-w-[860px] px-4 pb-8 pt-5 sm:px-6">
            <div class="space-y-7">
              <ChatMessage
                v-for="message in messages"
                :key="message.id"
                :message="message"
                @retry="handleRetry"
              />
            </div>
            <div class="mt-5 flex items-center justify-center gap-2 text-[8px] text-slate-300">
              <span class="h-px w-12 bg-slate-100" />
              <span class="font-mono">END OF CONTEXT</span>
              <span class="h-px w-12 bg-slate-100" />
            </div>
          </div>
        </div>

        <div v-if="activeConversation" class="shrink-0 border-t border-slate-100 bg-gradient-to-t from-white via-white to-white/95 px-3 pb-2.5 pt-3 sm:px-5">
          <div class="mx-auto w-full max-w-[860px]">
            <ChatComposer
              :streaming="chatStore.isStreaming"
              :top-k="ragStore.config.topK"
              :threshold="ragStore.config.threshold"
              @send="handleSend"
              @quick="handleQuickPrompt"
              @stop="handleStop"
            />
          </div>
        </div>
      </section>

      <div class="hidden w-[286px] shrink-0 border-l border-slate-100 min-[1400px]:block">
        <AgentSidePanel
          :is-streaming="chatStore.isStreaming"
          :latest-message="latestAssistant"
        />
      </div>
    </div>

    <el-drawer
      v-model="mobileListOpen"
      direction="ltr"
      size="286px"
      :with-header="false"
      class="conversation-drawer"
    >
      <ConversationList
        :conversations="chatStore.sortedConversations"
        :active-id="chatStore.activeId"
        :streaming="chatStore.isStreaming"
        @select="handleSelectConversation"
        @create="handleCreateConversation"
        @remove="handleDeleteConversation"
      />
    </el-drawer>
  </div>
</template>

<style scoped>
.header-action {
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  color: #64748b;
  background: #fff;
  border: 1px solid #e8edf4;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.16s ease;
}

.header-action:hover:not(:disabled) {
  color: #4f46e5;
  background: #f8faff;
  border-color: #dbe3f1;
}

.header-action:disabled {
  color: #cbd5e1;
  cursor: not-allowed;
  opacity: 0.6;
}

.starter-card {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px;
  text-align: left;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 13px;
  box-shadow: 0 8px 28px -26px rgba(15, 23, 42, 0.4);
  cursor: pointer;
  transition: all 0.2s ease;
  backdrop-filter: blur(8px);
}

.starter-card:hover {
  background: #fff;
  border-color: #c7d2fe;
  box-shadow: 0 16px 34px -26px rgba(79, 70, 229, 0.45);
  transform: translateY(-2px);
}

.starter-icon {
  display: grid;
  width: 30px;
  height: 30px;
  flex-shrink: 0;
  place-items: center;
  color: #6366f1;
  background: linear-gradient(135deg, #eef2ff, #ecfeff);
  border: 1px solid #e0e7ff;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.starter-card:hover .starter-icon {
  color: #fff;
  background: linear-gradient(135deg, #6366f1, #06b6d4);
  border-color: transparent;
}

:deep(.conversation-drawer .el-drawer__body) {
  padding: 0;
  background: #fbfcfe;
}
</style>
