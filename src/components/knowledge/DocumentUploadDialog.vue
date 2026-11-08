<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, WarningFilled } from '@element-plus/icons-vue'
import type { Course, KnowledgePoint } from '@/types'
import { fetchKnowledgePoints, uploadDocument } from '@/services/api'

const props = defineProps<{
  modelValue: boolean
  courses: Course[]
  initialCourseId?: string
}>()

const emit = defineEmits<{
  (event: 'update:modelValue', value: boolean): void
  (event: 'uploaded'): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

const courseId = ref('')
const knowledgePointId = ref('')
const title = ref('')
const selectedFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const knowledgePoints = ref<KnowledgePoint[]>([])
const loadingPoints = ref(false)
const uploading = ref(false)
const errorMessage = ref('')

watch(visible, (isOpen) => {
  if (isOpen) {
    reset()
  }
})

watch(courseId, async (value) => {
  knowledgePointId.value = ''
  knowledgePoints.value = []
  if (!value) return
  loadingPoints.value = true
  try {
    const response = await fetchKnowledgePoints({ courseId: value })
    knowledgePoints.value = response.items
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '知识点加载失败'
  } finally {
    loadingPoints.value = false
  }
})

function reset(): void {
  const preferred = props.courses.find((course) => course.id === props.initialCourseId)
  courseId.value = preferred?.id ?? props.courses[0]?.id ?? ''
  knowledgePointId.value = ''
  title.value = ''
  selectedFile.value = null
  errorMessage.value = ''
  uploading.value = false
  if (fileInput.value) fileInput.value.value = ''
}

function chooseFile(): void {
  fileInput.value?.click()
}

function handleFileChange(event: Event): void {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0] ?? null
  if (!file) return
  const extension = file.name.split('.').pop()?.toLowerCase()
  if (!extension || !['txt', 'md', 'markdown', 'pdf', 'docx'].includes(extension)) {
    errorMessage.value = '仅支持 TXT、Markdown、PDF、DOCX 文档'
    selectedFile.value = null
    return
  }
  if (file.size > 25 * 1024 * 1024) {
    errorMessage.value = '文档大小不能超过 25 MB'
    selectedFile.value = null
    return
  }
  selectedFile.value = file
  if (!title.value) title.value = file.name.replace(/\.[^.]+$/, '')
  errorMessage.value = ''
}

async function submit(): Promise<void> {
  if (!selectedFile.value) {
    errorMessage.value = '请选择要入库的文档'
    return
  }
  if (!courseId.value) {
    errorMessage.value = '请选择所属课程'
    return
  }
  uploading.value = true
  errorMessage.value = ''
  try {
    const document = await uploadDocument({
      file: selectedFile.value,
      courseId: courseId.value,
      knowledgePointId: knowledgePointId.value || undefined,
      title: title.value.trim() || undefined,
    })
    if (document.status === 'failed') {
      ElMessage.warning(`文档已保存，但解析失败：${document.errorMessage || '请检查文档格式'}`)
    } else {
      ElMessage.success(`入库完成，生成 ${document.chunkCount} 个知识片段`)
    }
    visible.value = false
    emit('uploaded')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '文档上传失败'
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <el-dialog
    v-model="visible"
    width="560px"
    title="文档入库"
    class="document-upload-dialog"
    :close-on-click-modal="!uploading"
  >
    <div class="pt-2">
      <p class="font-mono text-[7.5px] uppercase tracking-[0.14em] text-[#a29582]">
        Ingest to knowledge base
      </p>
      <h3 class="mt-1.5 font-serif text-[21px] font-medium text-[#211c17]">上传课程文档</h3>
      <p class="mt-1.5 text-[10px] leading-5 text-[#766b5b]">
        支持 TXT / Markdown / PDF / DOCX，最大 25 MB。服务端会自动解析、切分、向量化并建立检索索引。
      </p>

      <div class="mt-5 grid grid-cols-2 gap-3">
        <label class="block">
          <span class="mb-1.5 block font-mono text-[8px] uppercase tracking-[0.12em] text-[#6f6456]">所属课程 *</span>
          <el-select v-model="courseId" placeholder="选择课程" class="w-full" :disabled="uploading">
            <el-option v-for="course in courses" :key="course.id" :label="course.name" :value="course.id" />
          </el-select>
        </label>
        <label class="block">
          <span class="mb-1.5 block font-mono text-[8px] uppercase tracking-[0.12em] text-[#6f6456]">知识点（可选）</span>
          <el-select
            v-model="knowledgePointId"
            placeholder="自动匹配章节"
            clearable
            filterable
            class="w-full"
            :loading="loadingPoints"
            :disabled="uploading || !courseId"
          >
            <el-option
              v-for="point in knowledgePoints"
              :key="point.id"
              :label="`${point.name} · ${point.chapter}`"
              :value="point.id"
            />
          </el-select>
        </label>
      </div>

      <label class="mt-3 block">
        <span class="mb-1.5 block font-mono text-[8px] uppercase tracking-[0.12em] text-[#6f6456]">文档标题</span>
        <el-input v-model="title" placeholder="默认使用文件名" :disabled="uploading" />
      </label>

      <button
        type="button"
        class="mt-4 flex w-full flex-col items-center justify-center border border-dashed border-[#b9ab97] bg-[#fbf6ec] px-4 py-7 text-center transition hover:border-[#7d302f] hover:bg-[#f7eee7] disabled:cursor-not-allowed disabled:opacity-60"
        :disabled="uploading"
        @click="chooseFile"
      >
        <el-icon :size="24" class="text-[#9a463c]"><UploadFilled /></el-icon>
        <span class="mt-2 text-[10px] font-medium text-[#5b5145]">
          {{ selectedFile ? selectedFile.name : '点击选择课程文档' }}
        </span>
        <span class="mt-1 font-mono text-[7px] tracking-[0.08em] text-[#a29582]">
          {{ selectedFile ? `${(selectedFile.size / 1024).toFixed(1)} KB` : 'TXT · MD · PDF · DOCX' }}
        </span>
      </button>
      <input
        ref="fileInput"
        type="file"
        class="hidden"
        accept=".txt,.md,.markdown,.pdf,.docx"
        @change="handleFileChange"
      />

      <div
        v-if="errorMessage"
        class="mt-3 flex items-start gap-2 border border-rose-200 bg-rose-50 px-3 py-2.5 text-[10px] leading-5 text-rose-600"
      >
        <el-icon class="mt-0.5 shrink-0" :size="12"><WarningFilled /></el-icon>
        {{ errorMessage }}
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-end gap-2">
        <el-button :disabled="uploading" @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="submit">
          {{ uploading ? '正在解析与向量化…' : '开始入库' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style>
.document-upload-dialog {
  max-width: 92vw;
}
</style>
