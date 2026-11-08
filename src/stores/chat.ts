import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'
import type { ChatMessage, Conversation } from '@/types'
import { createId } from '@/utils/id'
import { readStorage, writeStorage } from '@/utils/storage'
import { truncate } from '@/utils/format'

export const DEFAULT_CONVERSATION_TITLE = '新的学习会话'
const STORAGE_KEY = 'zhiyan.chat.state'

interface PersistedChatState {
  conversations: Conversation[]
  activeId: string | null
}

function makeConversation(title = DEFAULT_CONVERSATION_TITLE): Conversation {
  const now = Date.now()
  return {
    id: createId('conv'),
    title,
    createdAt: now,
    updatedAt: now,
    messages: [],
  }
}

function sanitizeConversations(conversations: Conversation[]): Conversation[] {
  return conversations.map((conversation) => ({
    ...conversation,
    messages: conversation.messages.map((message) => {
      if (message.status !== 'streaming') return message
      return {
        ...message,
        status: message.content ? 'done' : 'error',
        stopped: true,
        error: message.content ? undefined : '上一次生成被中断，请重试',
      }
    }),
  }))
}

function loadInitialState(): PersistedChatState {
  const persisted = readStorage<PersistedChatState | null>(STORAGE_KEY, null)
  if (persisted && Array.isArray(persisted.conversations) && persisted.conversations.length > 0) {
    const conversations = sanitizeConversations(persisted.conversations)
    const activeExists = conversations.some((conversation) => conversation.id === persisted.activeId)
    return {
      conversations,
      activeId: activeExists ? persisted.activeId : conversations[0]?.id ?? null,
    }
  }

  const conversation = makeConversation()
  return { conversations: [conversation], activeId: conversation.id }
}

export const useChatStore = defineStore('chat', () => {
  const initial = loadInitialState()
  const conversations = ref<Conversation[]>(initial.conversations)
  const activeId = ref<string | null>(initial.activeId)
  const isStreaming = ref(false)
  const streamingConversationId = ref<string | null>(null)
  const streamingMessageId = ref<string | null>(null)

  const activeConversation = computed(
    () => conversations.value.find((conversation) => conversation.id === activeId.value) ?? null,
  )
  const sortedConversations = computed(() =>
    [...conversations.value].sort((a, b) => b.updatedAt - a.updatedAt),
  )
  const activeMessages = computed(() => activeConversation.value?.messages ?? [])

  const lastAssistantMessage = computed(() => {
    const messages = activeConversation.value?.messages ?? []
    return [...messages].reverse().find((message) => message.role === 'assistant') ?? null
  })

  function getConversation(conversationId: string): Conversation | undefined {
    return conversations.value.find((conversation) => conversation.id === conversationId)
  }

  function createConversation(title = DEFAULT_CONVERSATION_TITLE): Conversation {
    const conversation = makeConversation(title)
    conversations.value.unshift(conversation)
    activeId.value = conversation.id
    return conversation
  }

  function deleteConversation(conversationId: string): void {
    if (isStreaming.value && streamingConversationId.value === conversationId) return
    conversations.value = conversations.value.filter(
      (conversation) => conversation.id !== conversationId,
    )
    if (activeId.value === conversationId) {
      activeId.value = sortedConversations.value[0]?.id ?? null
    }
  }

  function selectConversation(conversationId: string): void {
    if (getConversation(conversationId)) activeId.value = conversationId
  }

  function appendMessage(conversationId: string, message: ChatMessage): void {
    const conversation = getConversation(conversationId)
    if (!conversation) return
    conversation.messages.push(message)
    conversation.updatedAt = Date.now()
    if (
      message.role === 'user' &&
      (conversation.title === DEFAULT_CONVERSATION_TITLE || !conversation.title.trim())
    ) {
      conversation.title = truncate(message.content, 22)
    }
  }

  function updateMessage(
    conversationId: string,
    messageId: string,
    patch: Partial<ChatMessage>,
  ): ChatMessage | undefined {
    const conversation = getConversation(conversationId)
    const message = conversation?.messages.find((item) => item.id === messageId)
    if (!conversation || !message) return undefined
    Object.assign(message, patch)
    conversation.updatedAt = Date.now()
    return message
  }

  function removeMessage(conversationId: string, messageId: string): void {
    const conversation = getConversation(conversationId)
    if (!conversation) return
    conversation.messages = conversation.messages.filter((message) => message.id !== messageId)
    conversation.updatedAt = Date.now()
  }

  function clearConversation(conversationId: string): void {
    const conversation = getConversation(conversationId)
    if (!conversation) return
    conversation.messages = []
    conversation.title = DEFAULT_CONVERSATION_TITLE
    conversation.updatedAt = Date.now()
  }

  function beginStreaming(conversationId: string, messageId: string): void {
    isStreaming.value = true
    streamingConversationId.value = conversationId
    streamingMessageId.value = messageId
  }

  function endStreaming(): void {
    isStreaming.value = false
    streamingConversationId.value = null
    streamingMessageId.value = null
  }

  let persistTimer: number | undefined
  watch(
    [conversations, activeId],
    () => {
      window.clearTimeout(persistTimer)
      persistTimer = window.setTimeout(() => {
        writeStorage(STORAGE_KEY, {
          conversations: conversations.value,
          activeId: activeId.value,
        } satisfies PersistedChatState)
      }, 180)
    },
    { deep: true },
  )

  return {
    conversations,
    activeId,
    isStreaming,
    streamingConversationId,
    streamingMessageId,
    activeConversation,
    sortedConversations,
    activeMessages,
    lastAssistantMessage,
    getConversation,
    createConversation,
    deleteConversation,
    selectConversation,
    appendMessage,
    updateMessage,
    removeMessage,
    clearConversation,
    beginStreaming,
    endStreaming,
  }
})
