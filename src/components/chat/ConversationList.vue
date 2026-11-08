<script setup lang="ts">
import { computed, ref } from 'vue'
import { Delete, Plus, Search } from '@element-plus/icons-vue'
import type { Conversation } from '@/types'
import { formatRelativeTime } from '@/utils/format'
import StatePanel from '@/components/feedback/StatePanel.vue'

const props = defineProps<{
  conversations: Conversation[]
  activeId: string | null
  streaming?: boolean
}>()

const emit = defineEmits<{
  (event: 'select', conversationId: string): void
  (event: 'create'): void
  (event: 'remove', conversation: Conversation): void
}>()

const keyword = ref('')

const filteredConversations = computed(() => {
  const normalized = keyword.value.trim().toLowerCase()
  if (!normalized) return props.conversations
  return props.conversations.filter((conversation) =>
    conversation.title.toLowerCase().includes(normalized),
  )
})

function messageCount(conversation: Conversation): number {
  return conversation.messages.filter((message) => message.role === 'user').length
}
</script>

<template>
  <div class="flex h-full w-full flex-col bg-[#f8f3e9]">
    <header class="border-b border-[#d8cebd] px-4 pb-3.5 pt-5">
      <div class="flex items-start justify-between">
        <div>
          <p class="font-mono text-[7px] font-medium uppercase tracking-[0.2em] text-[#a29582]">
            Contents / 目录
          </p>
          <h2 class="mt-1.5 font-serif text-[19px] font-medium tracking-[-0.02em] text-[#211c17]">会话目录</h2>
        </div>
        <el-tooltip content="新建会话" placement="bottom" :show-after="300">
          <button
            type="button"
            class="grid h-7 w-7 place-items-center border border-[#b9ab97] bg-[#682728] text-[#f8f1e5] transition hover:bg-[#552222] active:translate-y-px"
            aria-label="新建会话"
            @click="emit('create')"
          >
            <el-icon :size="13"><Plus /></el-icon>
          </button>
        </el-tooltip>
      </div>

      <div class="app-search mt-4 w-full">
        <el-icon :size="11" class="shrink-0 text-[#a29582]">
          <Search />
        </el-icon>
        <input
          v-model="keyword"
          type="search"
          placeholder="检索会话"
          aria-label="搜索会话"
        />
      </div>
    </header>

    <div class="min-h-0 flex-1 overflow-y-auto pb-4 scroll-thin">
      <div v-if="filteredConversations.length > 0">
        <p
          v-if="!keyword"
          class="px-4 pb-1.5 pt-3 font-mono text-[7px] uppercase tracking-[0.18em] text-[#a29582]"
        >
          Recent Notes / 最近
        </p>
        <button
          v-for="(conversation, index) in filteredConversations"
          :key="conversation.id"
          type="button"
          class="conversation-item group relative flex w-full flex-col border-b border-[#e2d9ca] px-4 py-3 text-left transition-all duration-200"
          :class="
            conversation.id === activeId
              ? 'bg-[#fffdf8]'
              : 'hover:bg-[#fbf7ee]'
          "
          @click="emit('select', conversation.id)"
        >
          <span
            v-if="conversation.id === activeId"
            class="absolute bottom-0 left-0 top-0 w-[2px] bg-[#9a463c]"
          />
          <div class="flex items-center gap-2">
            <span
              class="w-4 shrink-0 font-mono text-[7px]"
              :class="conversation.id === activeId ? 'text-[#9a463c]' : 'text-[#b5a995]'"
            >
              {{ String(index + 1).padStart(2, '0') }}
            </span>
            <span
              class="min-w-0 flex-1 truncate font-serif text-[11.5px] font-medium leading-5"
              :class="conversation.id === activeId ? 'text-[#211c17]' : 'text-[#5b5145]'"
            >
              {{ conversation.title || '新的学习会话' }}
            </span>
            <span
              v-if="streaming && conversation.id === activeId"
              class="h-1 w-1 shrink-0 animate-pulse rounded-full bg-[#9a463c]"
            />
            <span
              class="grid h-5 w-5 shrink-0 place-items-center text-[#a29582] opacity-0 transition hover:bg-[#f4e9e4] hover:text-[#8e3d35] group-hover:opacity-100"
              role="button"
              tabindex="0"
              aria-label="删除会话"
              @click.stop="emit('remove', conversation)"
              @keydown.enter.stop="emit('remove', conversation)"
            >
              <el-icon :size="10"><Delete /></el-icon>
            </span>
          </div>
          <div class="mt-1 flex items-center gap-1.5 pl-6 font-mono text-[7px] text-[#a29582]">
            <span>{{ messageCount(conversation) }} NOTES</span>
            <span class="text-[#d8cebd]">/</span>
            <span>{{ formatRelativeTime(conversation.updatedAt) }}</span>
            <span v-if="conversation.messages.some((message) => message.citations.length > 0)" class="ml-auto flex items-center gap-0.5 text-[#9a463c]">
              <span class="h-1 w-1 rounded-full bg-[#9a463c]" />
              RAG
            </span>
          </div>
        </button>
      </div>

      <StatePanel
        v-else-if="keyword"
        compact
        type="empty"
        title="没有匹配的会话"
        description="换一个关键词试试，或清空搜索条件。"
      />

      <StatePanel
        v-else
        compact
        type="empty"
        title="还没有会话"
        description="新建一个会话，开始你的第一次知识探索。"
        action-text="新建会话"
        @action="emit('create')"
      />
    </div>

    <footer class="border-t border-[#d8cebd] px-4 py-3">
      <div class="flex items-center justify-between font-mono text-[7px] uppercase tracking-[0.08em] text-[#a29582]">
        <span class="flex items-center gap-1.5">
          <span class="h-1 w-1 rounded-full bg-[#5c7a60]" />
          Local archive
        </span>
        <span>SSE MOCK</span>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.conversation-item {
  cursor: pointer;
  background: transparent;
}
</style>
