<script setup lang="ts">
import { computed, ref } from 'vue'
import { ChatLineRound, Delete, Plus, Search } from '@element-plus/icons-vue'
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
  <div class="flex h-full w-full flex-col bg-[#fbfcfe]">
    <header class="px-4 pb-3 pt-5">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-[8px] font-semibold uppercase tracking-[0.2em] text-slate-400">
            Conversations
          </p>
          <h2 class="mt-1 text-[16px] font-bold tracking-tight text-ink-950">会话</h2>
        </div>
        <el-tooltip content="新建会话" placement="bottom" :show-after="300">
          <button
            type="button"
            class="grid h-8 w-8 place-items-center rounded-lg border border-indigo-100 bg-indigo-50 text-indigo-500 transition hover:border-indigo-200 hover:bg-indigo-100 active:scale-95"
            aria-label="新建会话"
            @click="emit('create')"
          >
            <el-icon :size="14"><Plus /></el-icon>
          </button>
        </el-tooltip>
      </div>

      <div class="relative mt-4">
        <el-icon
          :size="13"
          class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
        >
          <Search />
        </el-icon>
        <input
          v-model="keyword"
          type="search"
          placeholder="搜索会话"
          class="h-8 w-full rounded-lg border border-slate-200/80 bg-white pl-8 pr-3 text-[10px] text-slate-600 outline-none transition placeholder:text-slate-400 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-50"
        />
      </div>
    </header>

    <div class="min-h-0 flex-1 overflow-y-auto px-2.5 pb-4 scroll-thin">
      <div v-if="filteredConversations.length > 0">
        <p
          v-if="!keyword"
          class="mb-1.5 px-2 text-[8px] font-semibold uppercase tracking-[0.16em] text-slate-400"
        >
          最近会话
        </p>
        <button
          v-for="conversation in filteredConversations"
          :key="conversation.id"
          type="button"
          class="conversation-item group relative mb-1 flex w-full flex-col rounded-xl border px-2.5 py-2.5 text-left transition-all duration-200"
          :class="
            conversation.id === activeId
              ? 'border-indigo-100 bg-white shadow-[0_8px_26px_-20px_rgba(79,70,229,0.6)]'
              : 'border-transparent hover:border-slate-100 hover:bg-white/80'
          "
          @click="emit('select', conversation.id)"
        >
          <span
            v-if="conversation.id === activeId"
            class="absolute left-0 top-1/2 h-5 w-[2px] -translate-y-1/2 rounded-r-full bg-indigo-500"
          />
          <div class="flex items-center gap-2">
            <span
              class="grid h-7 w-7 shrink-0 place-items-center rounded-lg transition"
              :class="
                conversation.id === activeId
                  ? 'bg-indigo-50 text-indigo-500'
                  : 'bg-slate-100/80 text-slate-400'
              "
            >
              <el-icon :size="13"><ChatLineRound /></el-icon>
            </span>
            <span
              class="min-w-0 flex-1 truncate text-[11px] font-medium"
              :class="conversation.id === activeId ? 'text-slate-800' : 'text-slate-600'"
            >
              {{ conversation.title || '新的学习会话' }}
            </span>
            <span
              v-if="streaming && conversation.id === activeId"
              class="h-1.5 w-1.5 shrink-0 animate-pulse rounded-full bg-indigo-500"
            />
            <span
              class="grid h-6 w-6 shrink-0 place-items-center rounded-md text-slate-400 opacity-0 transition hover:bg-rose-50 hover:text-rose-500 group-hover:opacity-100"
              role="button"
              tabindex="0"
              aria-label="删除会话"
              @click.stop="emit('remove', conversation)"
              @keydown.enter.stop="emit('remove', conversation)"
            >
              <el-icon :size="11"><Delete /></el-icon>
            </span>
          </div>
          <div class="mt-1 flex items-center gap-1.5 pl-9 text-[8px] text-slate-400">
            <span>{{ messageCount(conversation) }} 轮对话</span>
            <span class="text-slate-300">·</span>
            <span>{{ formatRelativeTime(conversation.updatedAt) }}</span>
            <span v-if="conversation.messages.some((message) => message.citations.length > 0)" class="ml-auto flex items-center gap-0.5 text-indigo-400">
              <span class="h-1 w-1 rounded-full bg-indigo-400" />
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

    <footer class="border-t border-slate-100 px-4 py-3">
      <div class="flex items-center justify-between">
        <span class="flex items-center gap-1.5 text-[8px] text-slate-400">
          <span class="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          本地会话自动保存
        </span>
        <span class="font-mono text-[8px] text-slate-300">SSE MOCK</span>
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
