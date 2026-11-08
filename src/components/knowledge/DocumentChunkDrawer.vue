<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ArrowDown, ArrowUp, Close, Document } from '@element-plus/icons-vue'
import type { RetrievedChunkLike } from '@/services/api'
import { fetchDocumentChunks } from '@/services/api'

const props = defineProps<{
  modelValue: boolean
  documentId: string
  documentTitle: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

const chunks = ref<RetrievedChunkLike[]>([])
const total = ref(0)
const isLoading = ref(false)
const errorMessage = ref('')
const expandedIds = ref<Set<string>>(new Set())
let requestId = 0

function needsExpand(content: string): boolean {
  return content.length > 200 || content.split('\n').length > 6
}

const longChunks = computed(() => chunks.value.filter((chunk) => needsExpand(chunk.content)))
const hasLongChunks = computed(() => longChunks.value.length > 0)
const allExpanded = computed(
  () => hasLongChunks.value && longChunks.value.every((chunk) => expandedIds.value.has(chunk.id)),
)

function isExpanded(id: string): boolean {
  return expandedIds.value.has(id)
}

function toggleExpanded(id: string): void {
  const next = new Set(expandedIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  expandedIds.value = next
}

function toggleAll(): void {
  expandedIds.value = allExpanded.value
    ? new Set()
    : new Set(longChunks.value.map((chunk) => chunk.id))
}

async function loadChunks(id: string): Promise<void> {
  const current = ++requestId
  isLoading.value = true
  errorMessage.value = ''
  chunks.value = []
  total.value = 0
  expandedIds.value = new Set()
  try {
    const data = await fetchDocumentChunks(id)
    if (current !== requestId) return
    chunks.value = data.items
    total.value = data.total
  } catch (error) {
    if (current !== requestId) return
    errorMessage.value = error instanceof Error ? error.message : '文档片段加载失败'
  } finally {
    if (current === requestId) isLoading.value = false
  }
}

watch(
  () => [props.modelValue, props.documentId] as const,
  ([open, id]) => {
    if (open && id) void loadChunks(id)
  },
  { immediate: true },
)
</script>

<template>
  <el-drawer
    v-model="visible"
    size="560px"
    :with-header="false"
    append-to-body
    destroy-on-close
    class="document-chunk-drawer"
  >
    <div class="flex h-full flex-col">
      <header class="relative overflow-hidden border-b border-[#3d3328] bg-[#1a1510] px-6 pb-5 pt-6 text-[#f4ead9]">
        <div class="pointer-events-none absolute inset-0 dot-grid opacity-[0.04]" />
        <span class="pointer-events-none absolute -right-2 -top-8 font-serif text-[110px] leading-none text-[#9a463c]/20">§</span>

        <div class="relative flex items-start justify-between gap-4">
          <div class="min-w-0">
            <p class="font-mono text-[8px] uppercase tracking-[0.18em] text-[#a49179]">
              Evidence ledger / 文档片段
            </p>
            <h2 class="mt-2 font-serif text-[20px] font-medium leading-tight text-[#f8efdf]">
              {{ documentTitle || '文档片段' }}
            </h2>
            <p class="mt-2 text-[9px] text-[#b6a58f]">
              共 {{ total }} 条向量片段，按原文顺序展示
            </p>
          </div>
          <button
            type="button"
            class="grid h-8 w-8 shrink-0 place-items-center border border-[#4c4033] text-[#a49179] transition hover:border-[#6b5140] hover:text-[#f4ead9]"
            aria-label="关闭文档片段"
            @click="visible = false"
          >
            <el-icon :size="14"><Close /></el-icon>
          </button>
        </div>
      </header>

      <div class="min-h-0 flex-1 overflow-y-auto px-6 py-5 scroll-thin">
        <div v-if="isLoading" class="space-y-3">
          <div v-for="index in 4" :key="index" class="border border-[#e4dbcd] bg-[#fffdf8] p-3">
            <div class="skeleton h-3 w-2/5" />
            <div class="skeleton mt-2 h-2 w-1/4" />
            <div class="skeleton mt-3 h-16 w-full" />
          </div>
        </div>

        <div v-else-if="errorMessage" class="border border-rose-200 bg-rose-50/70 p-5 text-center">
          <p class="font-serif text-[13px] font-semibold text-rose-700">文档片段加载失败</p>
          <p class="mt-1.5 text-[9px] leading-4 text-rose-500">{{ errorMessage }}</p>
          <button
            type="button"
            class="mt-3 border border-rose-200 bg-white px-3 py-1.5 text-[9px] font-medium text-rose-600 transition hover:border-rose-300"
            @click="loadChunks(documentId)"
          >
            重新加载
          </button>
        </div>

        <div v-else-if="chunks.length">
          <div class="mb-3 flex items-center justify-between gap-2">
            <span class="font-mono text-[8px] text-[#a29582]">共 {{ total }} 条向量片段</span>
            <button
              v-if="hasLongChunks"
              type="button"
              class="inline-flex items-center gap-1 border border-[#d8cebd] bg-[#fffdf8] px-2 py-1 text-[8px] font-medium text-[#6f6456] transition hover:border-[#a29582]"
              @click="toggleAll"
            >
              <el-icon :size="10">
                <component :is="allExpanded ? ArrowUp : ArrowDown" />
              </el-icon>
              {{ allExpanded ? '全部收起' : '全部展开' }}
            </button>
          </div>

          <div class="space-y-2.5">
          <article
            v-for="(chunk, index) in chunks"
            :key="chunk.id"
            class="border border-[#e4dbcd] bg-[#fffdf8] p-3.5"
          >
            <div class="flex items-start justify-between gap-2">
              <div class="flex min-w-0 items-center gap-2">
                <span class="grid h-6 w-6 shrink-0 place-items-center border border-[#e5dccd] text-[#a29582]">
                  <el-icon :size="11"><Document /></el-icon>
                </span>
                <h3 class="min-w-0 truncate font-serif text-[11px] font-semibold text-[#4a4034]">
                  {{ chunk.title }}
                </h3>
              </div>
              <span class="shrink-0 font-mono text-[7.5px] text-[#a29582]">#{{ index + 1 }}</span>
            </div>

            <p class="mt-1.5 flex flex-wrap items-center gap-x-1.5 gap-y-0.5 font-mono text-[7.5px] text-[#8f8170]">
              <span class="text-indigo-500">{{ chunk.knowledgePointId || 'UNMATCHED' }}</span>
              <span class="text-[#d8cebd]">/</span>
              <span>{{ chunk.chapter || '课程讲义' }}</span>
              <span class="text-[#d8cebd]">/</span>
              <span>{{ chunk.source }}</span>
            </p>

            <div class="relative mt-2">
              <p
                class="whitespace-pre-wrap text-[9px] leading-4 text-[#6f6456]"
                :class="isExpanded(chunk.id) ? '' : 'max-h-36 overflow-hidden'"
              >
                {{ chunk.content }}
              </p>
              <div
                v-if="!isExpanded(chunk.id) && needsExpand(chunk.content)"
                class="pointer-events-none absolute inset-x-0 bottom-0 h-8 bg-gradient-to-t from-[#fffdf8] to-transparent"
              />
            </div>
            <button
              v-if="needsExpand(chunk.content)"
              type="button"
              class="mt-1.5 inline-flex items-center gap-1 text-[8px] font-medium text-[#7d302f] transition hover:text-[#5e2320]"
              @click="toggleExpanded(chunk.id)"
            >
              <el-icon :size="10">
                <component :is="isExpanded(chunk.id) ? ArrowUp : ArrowDown" />
              </el-icon>
              {{ isExpanded(chunk.id) ? '收起全部内容' : '展开完整内容' }}
            </button>

            <div v-if="chunk.tags?.length" class="mt-2 flex flex-wrap gap-1">
              <span
                v-for="tag in chunk.tags.slice(0, 5)"
                :key="tag"
                class="rounded-full border border-[#e4dbcd] bg-[#fbf7ef] px-1.5 py-0.5 text-[7px] text-[#8f8170]"
              >
                {{ tag }}
              </span>
            </div>
          </article>
          </div>
        </div>

        <div v-else class="border border-dashed border-[#d8cebd] bg-[#fbf7ef] px-4 py-8 text-center">
          <p class="font-serif text-[12px] text-[#6f6456]">该文档还没有向量片段</p>
          <p class="mt-1.5 text-[8.5px] text-[#a29582]">
            可能仍在解析中，或文档内容为空。可在文档库中重新解析。
          </p>
        </div>
      </div>

      <footer class="flex items-center justify-between border-t border-[#d8cebd] bg-[#fbf7ef] px-6 py-4">
        <span class="font-mono text-[8px] text-[#a29582]">DOCUMENT CHUNKS · {{ total }}</span>
        <button
          type="button"
          class="border border-[#c9b9a4] bg-[#fffdf8] px-3 py-2 text-[9px] font-medium text-[#6f6456] transition hover:border-[#a29582]"
          @click="visible = false"
        >
          关闭
        </button>
      </footer>
    </div>
  </el-drawer>
</template>
