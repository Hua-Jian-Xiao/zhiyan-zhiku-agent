import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { ChatMessage, Conversation } from '@/types'
import { createId } from '@/utils/id'
import { truncate } from '@/utils/format'
import {
  clearConversation as clearConversationRequest,
  createConversation as createConversationRequest,
  deleteConversation as deleteConversationRequest,
  fetchConversations,
} from '@/services/api'

export const DEFAULT_CONVERSATION_TITLE = '新的学习会话'

export const useChatStore = defineStore('chat', () => {
  const conversations = ref<Conversation[]>([])
  const activeId = ref<string | null>(null)
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

  async function hydrateFromServer(): Promise<void> {
    const response = await fetchConversations()
    conversations.value = response.conversations
    if (!conversations.value.some((conversation) => conversation.id === activeId.value)) {
      activeId.value = sortedConversations.value[0]?.id ?? null
    }
  }

  function getConversation(conversationId: string): Conversation | undefined {
    return conversations.value.find((conversation) => conversation.id === conversationId)
  }

  async function createConversation(title = DEFAULT_CONVERSATION_TITLE): Promise<Conversation> {
    const conversation = await createConversationRequest({
      id: createId('conv'),
      title,
    })
    conversations.value = [conversation, ...conversations.value]
    activeId.value = conversation.id
    return conversation
  }

  async function deleteConversation(conversationId: string): Promise<void> {
    await deleteConversationRequest(conversationId)
    conversations.value = conversations.value.filter(
      (conversation) => conversation.id !== conversationId,
    )
    if (activeId.value === conversationId) {
      activeId.value = sortedConversations.value[0]?.id ?? null
    }
  }

  async function clearConversation(conversationId: string): Promise<void> {
    await clearConversationRequest(conversationId)
    const conversation = getConversation(conversationId)
    if (!conversation) return
    conversation.messages = []
    conversation.title = DEFAULT_CONVERSATION_TITLE
    conversation.updatedAt = Date.now()
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

  function updateConversationTitle(conversationId: string, title: string): void {
    const conversation = getConversation(conversationId)
    if (!conversation || !title) return
    conversation.title = title
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
    hydrateFromServer,
    getConversation,
    createConversation,
    deleteConversation,
    clearConversation,
    selectConversation,
    appendMessage,
    updateMessage,
    removeMessage,
    updateConversationTitle,
    beginStreaming,
    endStreaming,
  }
})
