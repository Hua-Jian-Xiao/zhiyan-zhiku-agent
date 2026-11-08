<script setup lang="ts">
import type { Component } from 'vue'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
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
import { starterPrompts } from '@/constants/app'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { useRagStore } from '@/stores/rag'
import { useSystemStore } from '@/stores/system'
import { createInitialTrace } from '@/services/agentTrace'
import { streamAgentReply, type AgentStreamEvent } from '@/services/agentService'
import { deleteMessage } from '@/services/api'
import type { ChatMessage as ChatMessageType, Conversation } from '@/types'
import { isAbortError } from '@/utils/async'
import { createId } from '@/utils/id'

const chatStore = useChatStore()
const ragStore = useRagStore()
const systemStore = useSystemStore()
const authStore = useAuthStore()

const scrollContainer = ref<HTMLElement | null>(null)
const mobileListOpen = ref(false)
const autoScroll = ref(true)
const activeController = ref<AbortController | null>(null)
const isBooting = ref(true)
const bootError = ref('')

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
  if (!activeConversation.value) return '新建或选择一个会话开始探索'
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

function reloadWorkspace(): void {
  window.location.reload()
}

async function handleCreateConversation(): Promise<void> {
  if (!guardStreaming()) return
  try {
    await chatStore.createConversation()
    mobileListOpen.value = false
    autoScroll.value = true
    scrollToBottom()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '新建会话失败')
  }
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
  try {
    await chatStore.deleteConversation(conversation.id)
    ElMessage.success('会话已删除')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '删除会话失败')
  }
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
  try {
    await chatStore.clearConversation(conversation.id)
    scrollToBottom()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '清空会话失败')
  }
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
    case 'title':
      chatStore.updateConversationTitle(conversationId, event.title)
      break
    case 'done':
      chatStore.updateMessage(conversationId, messageId, {
        status: 'done',
        latencyMs: event.meta.latencyMs,
      })
      if (event.meta.title) {
        chatStore.updateConversationTitle(conversationId, event.meta.title)
      }
      break
    default:
      break
  }
}

async function runAgent(
  conversationId: string,
  query: string,
  userMessageId: string,
): Promise<void> {
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
        conversationId,
        query,
        topK: ragStore.config.topK,
        threshold: ragStore.config.threshold,
        retrievalMode: ragStore.config.retrievalMode,
        userMessageId,
        assistantMessageId: assistantMessage.id,
        conversationTitle: conversation.title,
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

  let conversation = chatStore.activeConversation
  if (!conversation) {
    try {
      conversation = await chatStore.createConversation()
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : '新建会话失败')
      return
    }
  }
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
  await runAgent(conversation.id, text, userMessage.id)
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
  try {
    await deleteMessage(message.id)
  } catch {
    // The local retry should still work if the failed message was not persisted.
  }
  chatStore.removeMessage(conversation.id, message.id)
  await runAgent(conversation.id, previousUser.content, previousUser.id)
}

onMounted(async () => {
  try {
    await chatStore.hydrateFromServer()
    await systemStore.loadStats().catch(() => null)
    await ragStore.loadFromServer().catch(() => null)
    if (!chatStore.conversations.length) {
      await chatStore.createConversation()
    } else if (!chatStore.activeConversation) {
      chatStore.selectConversation(chatStore.conversations[0].id)
    }
    scrollToBottom()
  } catch (error) {
    bootError.value =
      error instanceof Error ? error.message : '工作台初始化失败，请确认后端已启动'
  } finally {
    isBooting.value = false
  }
})

onBeforeUnmount(() => {
  activeController.value?.abort()
  activeController.value = null
  chatStore.endStreaming()
})
</script>

<template>
  <div class="flex h-full flex-col p-2.5 sm:p-3 lg:p-4">
    <div
      class="flex min-h-0 flex-1 overflow-hidden border border-[#b9ab97] bg-[#fffdf8]"
    >
      <template v-if="isBooting">
        <div class="hidden w-[254px] shrink-0 space-y-3 border-r border-[#ddd2c1] bg-[#f8f3e9] p-4 lg:block">
          <div class="flex items-center justify-between">
            <div class="skeleton h-4 w-16" />
            <div class="skeleton h-8 w-8" />
          </div>
          <div class="skeleton h-8 w-full" />
          <div v-for="index in 4" :key="index" class="skeleton h-[58px] w-full rounded-xl" />
        </div>
        <div class="flex min-w-0 flex-1 flex-col">
          <div class="flex h-[66px] items-center justify-between border-b border-slate-100 px-5">
            <div>
              <div class="skeleton h-3 w-40" />
              <div class="skeleton mt-2 h-2 w-56" />
            </div>
            <div class="skeleton h-8 w-20 rounded-lg" />
          </div>
          <div class="flex-1 space-y-5 px-8 py-8">
            <div class="mx-auto max-w-[600px] space-y-4">
              <div class="skeleton mx-auto h-14 w-14 rounded-2xl" />
              <div class="skeleton mx-auto h-5 w-64" />
              <div class="skeleton mx-auto h-3 w-96" />
              <div class="mt-6 grid grid-cols-2 gap-3">
                <div v-for="index in 4" :key="index" class="skeleton h-[74px] rounded-xl" />
              </div>
            </div>
          </div>
          <div class="border-t border-slate-100 p-4">
            <div class="skeleton h-[92px] w-full rounded-2xl" />
          </div>
        </div>
        <div class="hidden w-[286px] shrink-0 space-y-3 border-l border-[#ddd2c1] bg-[#f8f3e9] p-4 min-[1400px]:block">
          <div class="skeleton h-[176px] rounded-2xl" />
          <div class="skeleton h-[140px] rounded-2xl" />
          <div class="skeleton h-[130px] rounded-2xl" />
        </div>
      </template>

      <div v-else-if="bootError" class="flex min-h-0 flex-1 items-center justify-center">
        <StatePanel
          type="error"
          title="工作台初始化失败"
          :description="bootError"
          action-text="刷新页面"
          @action="reloadWorkspace"
        />
      </div>

      <template v-else>
        <div class="hidden w-[254px] shrink-0 border-r border-[#d8cebd] lg:block">
          <ConversationList
            :conversations="chatStore.sortedConversations"
            :active-id="chatStore.activeId"
            :streaming="chatStore.isStreaming"
            @select="handleSelectConversation"
            @create="handleCreateConversation"
            @remove="handleDeleteConversation"
          />
        </div>

        <section class="flex min-w-0 flex-1 flex-col bg-[#fffdf8]">
          <header class="flex h-[66px] shrink-0 items-center justify-between gap-3 border-b border-[#d8cebd] px-3 sm:px-5">
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
                  <h2 class="truncate font-serif text-[15px] font-medium tracking-[-0.01em] text-[#211c17]">
                    {{ activeConversation?.title || 'Agent 对话工作台' }}
                  </h2>
                  <span
                    v-if="chatStore.isStreaming"
                    class="hidden shrink-0 items-center gap-1 border border-[#d8b8b1] bg-[#f6e9e4] px-1.5 py-px font-mono text-[7px] tracking-[0.08em] text-[#8e3d35] sm:inline-flex"
                  >
                    <span class="h-1 w-1 animate-pulse rounded-full bg-[#9a463c]" />
                    LIVE
                  </span>
                </div>
                <p class="mt-1 truncate font-mono text-[7px] uppercase tracking-[0.08em] text-[#a29582]">{{ headerSubtitle }}</p>
              </div>
            </div>

            <div class="flex shrink-0 items-center gap-1.5">
              <span class="hidden items-center gap-1.5 border border-[#d8cebd] px-2 py-1 font-mono text-[7px] uppercase tracking-[0.06em] text-[#8d806e] xl:inline-flex">
                <span class="h-1 w-1 rounded-full bg-[#5c7a60]" />
                {{ authStore.displayName }} · INDEX CONNECTED
              </span>
              <el-tooltip content="新建会话" placement="bottom" :show-after="300">
                <button type="button" class="header-action" aria-label="新建会话" @click="handleCreateConversation">
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
                description="从左侧选择一个历史会话，或新建一个会话继续探索。"
                action-text="新建会话"
                @action="handleCreateConversation"
              />
            </div>

            <div
              v-else-if="messages.length === 0"
              class="relative flex min-h-full items-center justify-center overflow-hidden px-4 py-8 sm:px-8"
            >
              <div class="pointer-events-none absolute inset-0" aria-hidden="true">
                <div class="absolute inset-0 dot-grid opacity-[0.11]" />
                <div class="absolute inset-y-0 left-1/2 w-px bg-[#e4dbcc]" />
                <span class="absolute left-1/2 top-[6%] -translate-x-1/2 font-serif text-[220px] leading-none text-[#7d302f]/[0.035]">§</span>
                <div class="absolute inset-x-8 top-8 h-px bg-[#e4dbcc]" />
                <div class="absolute inset-x-8 bottom-8 h-px bg-[#e4dbcc]" />
              </div>

              <div class="relative w-full max-w-[670px] animate-fade-up text-center">
                <div class="relative mx-auto grid h-14 w-14 place-items-center border border-[#7d302f]/35 bg-[#fbf5e9] text-[#682728]">
                  <span class="absolute inset-[4px] border border-[#7d302f]/15" />
                  <span class="font-serif text-[22px] leading-none">知</span>
                  <span class="absolute -bottom-[5px] -right-[5px] h-2 w-2 bg-[#7d302f]" />
                </div>

                <p class="mt-5 font-mono text-[7.5px] font-medium uppercase tracking-[0.24em] text-[#9a463c]">
                  Field Notes · RAG Learning Agent
                </p>
                <h1 class="mt-3 font-serif text-[31px] font-medium tracking-[-0.025em] text-[#211c17] sm:text-[38px]">
                  今天想研究什么？
                </h1>
                <p class="mx-auto mt-3 max-w-[470px] text-[10.5px] leading-6 text-[#766b5b]">
                  我会从 {{ systemStore.stats?.courseCount ?? '—' }} 门计算机课程、
                  {{ systemStore.stats?.knowledgePointCount ?? '—' }} 个知识点中检索证据，
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
                    <el-icon :size="11" class="mt-0.5 shrink-0 text-slate-300 transition-all group-hover:translate-x-0.5 group-hover:text-indigo-400">
                      <ArrowRight />
                    </el-icon>
                  </button>
                </div>

                <div class="mt-6 flex flex-wrap items-center justify-center gap-x-4 gap-y-1.5 font-mono text-[7px] uppercase tracking-[0.08em] text-[#a29582]">
                  <span class="flex items-center gap-1.5">
                    <span class="h-1 w-1 rounded-full bg-[#5c7a60]" />
                    INDEX CONNECTED
                  </span>
                  <span class="text-[#d8cebd]">|</span>
                  <span>{{ ragStore.configLabel }}</span>
                  <span class="text-[#d8cebd]">|</span>
                  <span>LIVE SSE</span>
                </div>
              </div>
            </div>

            <div v-else class="mx-auto w-full max-w-[800px] px-4 pb-8 pt-6 sm:px-7">
              <div class="space-y-8">
                <ChatMessage
                  v-for="message in messages"
                  :key="message.id"
                  :message="message"
                  @retry="handleRetry"
                />
              </div>
              <div class="mt-6 flex items-center justify-center gap-3 font-mono text-[7px] tracking-[0.14em] text-[#b5a995]">
                <span class="h-px w-12 bg-[#e1d7c8]" />
                <span>END OF FIELD NOTES</span>
                <span class="h-px w-12 bg-[#e1d7c8]" />
              </div>
            </div>
          </div>

          <div v-if="activeConversation" class="shrink-0 border-t border-[#d8cebd] bg-[#fbf7ee] px-3 pb-2.5 pt-3 sm:px-5">
            <div class="mx-auto w-full max-w-[800px]">
              <ChatComposer
                :streaming="chatStore.isStreaming"
                :top-k="ragStore.config.topK"
                :threshold="ragStore.config.threshold"
                :retrieval-mode="ragStore.config.retrievalMode"
                @send="handleSend"
                @quick="handleQuickPrompt"
                @stop="handleStop"
              />
            </div>
          </div>
        </section>

        <div class="hidden w-[286px] shrink-0 border-l border-[#d8cebd] bg-[#f8f3e9] min-[1400px]:block">
          <AgentSidePanel
            :is-streaming="chatStore.isStreaming"
            :latest-message="latestAssistant"
          />
        </div>
      </template>
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
  width: 29px;
  height: 29px;
  place-items: center;
  color: #766b5b;
  background: transparent;
  border: 1px solid #d8cebd;
  border-radius: 0;
  cursor: pointer;
  transition: all 0.16s ease;
}

.header-action:hover:not(:disabled) {
  color: #7d302f;
  background: #f8f2e8;
  border-color: #b9ab97;
}

.header-action:disabled {
  color: #cbbfaf;
  cursor: not-allowed;
  opacity: 0.6;
}

.starter-card {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 13px 13px 12px;
  text-align: left;
  background: rgba(255, 253, 248, 0.92);
  border: 1px solid #d8cebd;
  border-top: 2px solid #bfb29e;
  border-radius: 0;
  box-shadow: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.starter-card:hover {
  background: #fffdf9;
  border-color: #b9ab97;
  border-top-color: #7d302f;
  box-shadow: none;
  transform: translateY(-1px);
}

.starter-icon {
  display: grid;
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  place-items: center;
  color: #7d302f;
  background: #f8f1e5;
  border: 1px solid #d8cebd;
  border-radius: 0;
  transition: all 0.2s ease;
}

.starter-card:hover .starter-icon {
  color: #fffdf8;
  background: #682728;
  border-color: #682728;
}

:deep(.conversation-drawer .el-drawer__body) {
  padding: 0;
  background: #f8f3e9;
}
</style>
