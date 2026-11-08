<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Document, Refresh, Search, Upload, View } from '@element-plus/icons-vue'
import type { Course, DocumentItem, DocumentJumpRequest } from '@/types'
import {
  deleteDocument,
  fetchDocuments,
  reindexDocument,
} from '@/services/api'
import StatePanel from '@/components/feedback/StatePanel.vue'
import DocumentChunkDrawer from '@/components/knowledge/DocumentChunkDrawer.vue'
import DocumentUploadDialog from '@/components/knowledge/DocumentUploadDialog.vue'

const props = defineProps<{
  courses: Course[]
  jumpRequest?: DocumentJumpRequest | null
}>()

const emit = defineEmits<{
  (event: 'changed'): void
  (event: 'jump-consumed'): void
}>()

const documents = ref<DocumentItem[]>([])
const total = ref(0)
const isLoading = ref(true)
const errorMessage = ref('')
const keyword = ref('')
const courseFilter = ref('')
const uploadOpen = ref(false)
const busyId = ref('')
const chunksOpen = ref(false)
const activeDocumentId = ref('')
const activeDocumentTitle = ref('')

async function loadDocuments(): Promise<void> {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const response = await fetchDocuments({
      courseId: courseFilter.value || undefined,
      q: keyword.value.trim() || undefined,
    })
    documents.value = response.items
    total.value = response.total
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '文档列表加载失败'
  } finally {
    isLoading.value = false
  }
}

function formatBytes(bytes: number): string {
  if (!bytes) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function statusClass(status: DocumentItem['status']): string {
  if (status === 'ready') return 'border-emerald-200 bg-emerald-50 text-emerald-700'
  if (status === 'failed') return 'border-rose-200 bg-rose-50 text-rose-700'
  if (status === 'processing') return 'border-amber-200 bg-amber-50 text-amber-700'
  return 'border-slate-200 bg-slate-50 text-slate-500'
}

async function handleDelete(document: DocumentItem): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `删除「${document.title}」会同时删除其 ${document.chunkCount} 个向量片段。历史引用快照仍会保留。`,
      '删除文档',
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
  busyId.value = document.id
  try {
    await deleteDocument(document.id)
    ElMessage.success('文档与向量片段已删除')
    await loadDocuments()
    emit('changed')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '删除失败')
  } finally {
    busyId.value = ''
  }
}

async function handleReindex(document: DocumentItem): Promise<void> {
  busyId.value = document.id
  try {
    const updated = await reindexDocument(document.id)
    ElMessage.success(`重新解析完成，共 ${updated.chunkCount} 个片段`)
    await loadDocuments()
    emit('changed')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '重新解析失败')
  } finally {
    busyId.value = ''
  }
}

async function handleUploaded(): Promise<void> {
  await loadDocuments()
  emit('changed')
}

function openChunks(documentId: string, title: string): void {
  activeDocumentId.value = documentId
  activeDocumentTitle.value = title
  chunksOpen.value = true
}

watch(
  () => props.jumpRequest?.nonce,
  async () => {
    const request = props.jumpRequest
    if (!request) return
    if (request.courseId !== undefined) {
      courseFilter.value = request.courseId
      keyword.value = ''
      await loadDocuments()
    }
    if (request.documentId) {
      openChunks(request.documentId, request.documentTitle || '文档片段')
    }
    emit('jump-consumed')
  },
  { immediate: true },
)

onMounted(() => {
  if (!props.jumpRequest?.nonce) void loadDocuments()
})
</script>

<template>
  <div>
    <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-4">
      <div>
        <p class="font-mono text-[7px] uppercase tracking-[0.16em] text-[#a29582]">Ingestion ledger</p>
        <h3 class="mt-1 font-serif text-[14px] font-medium text-[#211c17]">课程文档与向量索引</h3>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <el-select
          v-model="courseFilter"
          placeholder="全部课程"
          clearable
          class="!w-[150px]"
          size="small"
          @change="loadDocuments"
        >
          <el-option v-for="course in props.courses" :key="course.id" :label="course.name" :value="course.id" />
        </el-select>
        <div class="app-search w-[180px]">
          <el-icon :size="10" class="text-[#a29582]"><Search /></el-icon>
          <input
            v-model="keyword"
            type="search"
            placeholder="搜索文档标题"
            @keyup.enter="loadDocuments"
          />
        </div>
        <el-button size="small" :loading="isLoading" @click="loadDocuments">刷新</el-button>
        <el-button type="primary" size="small" @click="uploadOpen = true">
          <el-icon class="mr-1"><Upload /></el-icon>
          上传文档
        </el-button>
      </div>
    </div>

    <div v-if="isLoading" class="space-y-2 p-4">
      <div v-for="index in 4" :key="index" class="flex items-center gap-3 border border-slate-100 p-3">
        <div class="skeleton h-8 w-8" />
        <div class="flex-1">
          <div class="skeleton h-3 w-2/5" />
          <div class="skeleton mt-2 h-2 w-1/4" />
        </div>
        <div class="skeleton h-2 w-16" />
      </div>
    </div>

    <div v-else-if="errorMessage" class="py-4">
      <StatePanel
        type="error"
        title="文档列表加载失败"
        :description="errorMessage"
        action-text="重新加载"
        @action="loadDocuments"
      />
    </div>

    <div v-else-if="documents.length" class="divide-y divide-slate-50">
      <div
        v-for="document in documents"
        :key="document.id"
        class="grid grid-cols-[minmax(0,1fr)_100px_90px_100px] items-center gap-3 px-5 py-3 transition hover:bg-slate-50/60"
      >
        <div class="flex min-w-0 items-center gap-2.5">
          <span class="grid h-7 w-7 shrink-0 place-items-center border border-slate-200 text-slate-400">
            <el-icon :size="12"><Document /></el-icon>
          </span>
          <div class="min-w-0">
            <p class="truncate font-serif text-[10.5px] font-medium text-slate-700">{{ document.title }}</p>
            <p class="mt-0.5 flex flex-wrap items-center gap-x-1.5 truncate font-mono text-[7px] text-slate-400">
              <span>{{ document.courseName }}</span>
              <span class="text-slate-200">/</span>
              <span>{{ document.sourceType.toUpperCase() }}</span>
              <span class="text-slate-200">/</span>
              <span>{{ formatBytes(document.byteSize) }}</span>
            </p>
            <p v-if="document.errorMessage" class="mt-0.5 truncate text-[7.5px] text-rose-500">
              {{ document.errorMessage }}
            </p>
          </div>
        </div>
        <span class="justify-self-start border px-1.5 py-0.5 font-mono text-[7px]" :class="statusClass(document.status)">
          {{ document.status.toUpperCase() }}
        </span>
        <span class="justify-self-start font-mono text-[8px] text-slate-500">{{ document.chunkCount }} chunks</span>
        <div class="flex items-center justify-end gap-1">
          <el-tooltip content="查看向量片段" :show-after="300">
            <button
              type="button"
              class="grid h-6 w-6 place-items-center text-slate-400 transition hover:bg-slate-100 hover:text-indigo-600"
              :aria-label="`查看 ${document.title} 的向量片段`"
              @click="openChunks(document.id, document.title)"
            >
              <el-icon :size="11"><View /></el-icon>
            </button>
          </el-tooltip>
          <el-tooltip content="重新解析并向量化" :show-after="300">
            <button
              type="button"
              class="grid h-6 w-6 place-items-center text-slate-400 transition hover:bg-slate-100 hover:text-indigo-600"
              :disabled="busyId === document.id"
              :aria-label="`重新解析 ${document.title}`"
              @click="handleReindex(document)"
            >
              <el-icon :size="11" :class="{ 'animate-spin': busyId === document.id }"><Refresh /></el-icon>
            </button>
          </el-tooltip>
          <el-tooltip content="删除文档" :show-after="300">
            <button
              type="button"
              class="grid h-6 w-6 place-items-center text-slate-400 transition hover:bg-rose-50 hover:text-rose-600"
              :disabled="busyId === document.id"
              :aria-label="`删除 ${document.title}`"
              @click="handleDelete(document)"
            >
              <el-icon :size="11"><Delete /></el-icon>
            </button>
          </el-tooltip>
        </div>
      </div>
    </div>

    <StatePanel
      v-else
      title="知识库还没有文档"
      description="上传 TXT、Markdown、PDF 或 DOCX 课程资料，系统会自动切分并建立向量索引。"
      action-text="上传第一份文档"
      @action="uploadOpen = true"
    />

    <div class="flex items-center justify-between border-t border-slate-100 px-5 py-2.5">
      <span class="font-mono text-[7px] text-slate-400">共 {{ total }} 份文档</span>
      <span class="font-mono text-[7px] text-slate-300">LIVE INGESTION · EMBEDDING INDEX</span>
    </div>

    <DocumentUploadDialog
      v-model="uploadOpen"
      :courses="props.courses"
      :initial-course-id="courseFilter"
      @uploaded="handleUploaded"
    />

    <DocumentChunkDrawer
      v-model="chunksOpen"
      :document-id="activeDocumentId"
      :document-title="activeDocumentTitle"
    />
  </div>
</template>
