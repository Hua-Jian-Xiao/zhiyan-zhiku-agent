<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Close, CopyDocument, TopRight } from '@element-plus/icons-vue'
import type { KnowledgePoint, KnowledgePointDetail } from '@/types'
import { fetchKnowledgePointDetail } from '@/services/api'

const props = defineProps<{
  modelValue: boolean
  point: KnowledgePoint | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'open-document': [payload: { documentId: string; courseId: string; documentTitle: string }]
  'open-documents': [payload: { courseId: string }]
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

const detail = ref<KnowledgePointDetail | null>(null)
const isLoading = ref(false)
const errorMessage = ref('')
let requestId = 0

const displayPoint = computed(() => detail.value ?? props.point)
const tags = computed(() => displayPoint.value?.tags ?? [])

function difficultyClass(difficulty: KnowledgePoint['difficulty'] | undefined): string {
  if (difficulty === '入门') return 'border-emerald-300/30 bg-emerald-300/10 text-emerald-200'
  if (difficulty === '进阶') return 'border-indigo-300/30 bg-indigo-300/10 text-indigo-200'
  return 'border-amber-300/30 bg-amber-300/10 text-amber-200'
}

async function loadDetail(id: string): Promise<void> {
  const current = ++requestId
  isLoading.value = true
  errorMessage.value = ''
  detail.value = null
  try {
    const data = await fetchKnowledgePointDetail(id)
    if (current !== requestId) return
    detail.value = data
  } catch (error) {
    if (current !== requestId) return
    errorMessage.value = error instanceof Error ? error.message : '知识点详情加载失败'
  } finally {
    if (current === requestId) isLoading.value = false
  }
}

function reloadDetail(): void {
  if (displayPoint.value?.id) void loadDetail(displayPoint.value.id)
}

function openCourse(): void {
  const url = displayPoint.value?.courseSourceUrl
  if (!url) {
    ElMessage.warning('该课程暂未配置学堂在线链接')
    return
  }
  window.open(url, '_blank', 'noopener,noreferrer')
}

async function copyId(): Promise<void> {
  const id = displayPoint.value?.id
  if (!id) return
  try {
    await navigator.clipboard.writeText(id)
    ElMessage.success('知识点 ID 已复制')
  } catch {
    ElMessage.error('复制失败，请手动选择知识点 ID')
  }
}

watch(
  () => [props.modelValue, props.point?.id] as const,
  ([open, id]) => {
    if (open && id) void loadDetail(id)
  },
  { immediate: true },
)
</script>

<template>
  <el-drawer
    v-model="visible"
    size="520px"
    :with-header="false"
    append-to-body
    destroy-on-close
    class="knowledge-point-drawer"
  >
    <div v-if="displayPoint" class="flex h-full flex-col">
      <header class="relative overflow-hidden border-b border-[#3d3328] bg-[#1a1510] px-6 pb-5 pt-6 text-[#f4ead9]">
        <div class="pointer-events-none absolute inset-0 dot-grid opacity-[0.04]" />
        <span class="pointer-events-none absolute -right-2 -top-8 font-serif text-[110px] leading-none text-[#9a463c]/20">§</span>

        <div class="relative flex items-start justify-between gap-4">
          <div class="min-w-0">
            <p class="font-mono text-[8px] uppercase tracking-[0.18em] text-[#a49179]">
              Knowledge point / 知识点
            </p>
            <h2 class="mt-2 font-serif text-[21px] font-medium leading-tight text-[#f8efdf]">
              {{ displayPoint.name }}
            </h2>
            <p class="mt-2 flex flex-wrap items-center gap-1.5 text-[9px] text-[#b6a58f]">
              <span class="font-mono text-[#c39e40]">{{ displayPoint.id }}</span>
              <span class="text-[#6f6353]">·</span>
              <span>{{ displayPoint.course }}</span>
              <span class="text-[#6f6353]">·</span>
              <span>{{ displayPoint.chapter }}</span>
            </p>
          </div>

          <button
            type="button"
            class="grid h-8 w-8 shrink-0 place-items-center border border-[#4c4033] text-[#a49179] transition hover:border-[#6b5140] hover:text-[#f4ead9]"
            aria-label="关闭知识点详情"
            @click="visible = false"
          >
            <el-icon :size="14"><Close /></el-icon>
          </button>
        </div>

        <div class="relative mt-4 flex flex-wrap items-center gap-1.5">
          <span
            class="rounded border px-2 py-0.5 text-[8px] font-medium"
            :class="difficultyClass(displayPoint.difficulty)"
          >
            {{ displayPoint.difficulty }}
          </span>
          <span class="rounded border border-[#4c4033] bg-white/[0.03] px-2 py-0.5 text-[8px] text-[#b6a58f]">
            第 {{ displayPoint.chapterNo || '—' }} 章
          </span>
          <span class="rounded border border-[#4c4033] bg-white/[0.03] px-2 py-0.5 text-[8px] text-[#b6a58f]">
            {{ displayPoint.chunkCount || 0 }} 个关联片段
          </span>
          <span class="ml-auto font-mono text-[7.5px] text-[#8f8170]">
            更新于 {{ displayPoint.updatedAt }}
          </span>
        </div>
      </header>

      <div class="min-h-0 flex-1 overflow-y-auto px-6 py-5 scroll-thin">
        <div v-if="isLoading" class="space-y-4">
          <div class="skeleton h-3 w-24" />
          <div class="skeleton h-20 w-full" />
          <div class="skeleton h-3 w-20" />
          <div class="skeleton h-24 w-full" />
        </div>

        <div v-else-if="errorMessage" class="border border-rose-200 bg-rose-50/70 p-5 text-center">
          <p class="font-serif text-[13px] font-semibold text-rose-700">知识点详情加载失败</p>
          <p class="mt-1.5 text-[9px] leading-4 text-rose-500">{{ errorMessage }}</p>
          <button
            type="button"
            class="mt-3 border border-rose-200 bg-white px-3 py-1.5 text-[9px] font-medium text-rose-600 transition hover:border-rose-300"
            @click="reloadDetail"
          >
            重新加载
          </button>
        </div>

        <template v-else>
          <section>
            <p class="font-mono text-[8px] uppercase tracking-[0.14em] text-[#a29582]">Summary / 知识点说明</p>
            <p class="mt-2 border-l-2 border-[#d8cebd] pl-3 text-[10px] leading-5 text-[#5d5346]">
              {{ displayPoint.description || '暂无详细描述，可在知识点管理中补充。' }}
            </p>
          </section>

          <section v-if="tags.length" class="mt-5">
            <p class="font-mono text-[8px] uppercase tracking-[0.14em] text-[#a29582]">Tags / 标签</p>
            <div class="mt-2 flex flex-wrap gap-1.5">
              <span
                v-for="tag in tags"
                :key="tag"
                class="rounded-full border border-[#d8cebd] bg-[#fffdf8] px-2 py-0.5 text-[8px] text-[#6f6456]"
              >
                {{ tag }}
              </span>
            </div>
          </section>

          <section class="mt-5">
            <p class="font-mono text-[8px] uppercase tracking-[0.14em] text-[#a29582]">Course / 所属课程</p>
            <button
              type="button"
              class="group mt-2 flex w-full items-center gap-3 border border-[#ded4c4] bg-[#fffdf8] p-3 text-left transition hover:border-[#b9ab97] hover:shadow-sm"
              @click="openCourse"
            >
              <span class="grid h-12 w-16 shrink-0 place-items-center overflow-hidden border border-[#e5dccd] bg-[#f4eee3]">
                <img
                  v-if="displayPoint.courseCoverUrl"
                  :src="displayPoint.courseCoverUrl"
                  :alt="displayPoint.course"
                  loading="lazy"
                  referrerpolicy="no-referrer"
                  class="h-full w-full object-cover"
                />
                <span v-else class="font-serif text-[16px] text-[#a29582]">课</span>
              </span>
              <span class="min-w-0 flex-1">
                <span class="block truncate font-serif text-[12px] font-semibold text-[#3a3229]">
                  {{ displayPoint.course }}
                </span>
                <span class="mt-0.5 block text-[8px] text-[#8f8170]">
                  点击打开学堂在线课程页
                </span>
              </span>
              <el-icon :size="13" class="shrink-0 text-[#a29582] transition group-hover:translate-x-0.5 group-hover:text-[#7d302f]">
                <TopRight />
              </el-icon>
            </button>
          </section>

          <section class="mt-5">
            <div class="flex items-center justify-between gap-2">
              <p class="font-mono text-[8px] uppercase tracking-[0.14em] text-[#a29582]">Evidence / 关联片段</p>
              <span class="font-mono text-[8px] text-[#a29582]">{{ displayPoint.chunkCount || 0 }} 条</span>
            </div>

            <div v-if="detail?.chunks?.length" class="mt-2 space-y-2">
              <article
                v-for="chunk in detail.chunks"
                :key="chunk.id"
                class="border border-[#e4dbcd] bg-[#fffdf8] p-3"
              >
                <div class="flex items-start justify-between gap-2">
                  <h4 class="min-w-0 truncate font-serif text-[11px] font-semibold text-[#4a4034]">
                    {{ chunk.title }}
                  </h4>
                  <span class="shrink-0 font-mono text-[7.5px] text-[#a29582]">
                    #{{ chunk.ordinal }}
                  </span>
                </div>
                <p class="mt-1 truncate text-[8px] text-[#8f8170]">
                  {{ chunk.chapter }} · {{ chunk.source }}
                </p>
                <p class="mt-2 line-clamp-3 text-[9px] leading-4 text-[#6f6456]">
                  {{ chunk.content }}
                </p>
                <button
                  type="button"
                  class="mt-2 inline-flex items-center gap-1 text-[8px] font-medium text-[#7d302f] transition hover:text-[#5e2320]"
                  @click="emit('open-document', { documentId: chunk.documentId, courseId: displayPoint.courseId, documentTitle: chunk.documentTitle })"
                >
                  查看原文片段
                  <el-icon :size="10"><TopRight /></el-icon>
                </button>
              </article>
            </div>

            <div v-else class="mt-2 border border-dashed border-[#d8cebd] bg-[#fbf7ef] px-4 py-6 text-center">
              <p class="font-serif text-[11px] text-[#6f6456]">暂无关联片段</p>
              <p class="mt-1 text-[8px] text-[#a29582]">
                上传课程文档后，服务端会自动匹配章节并建立向量索引。
              </p>
              <button
                type="button"
                class="mt-3 inline-flex items-center gap-1.5 border border-[#c9b9a4] bg-[#fffdf8] px-3 py-1.5 text-[8.5px] font-medium text-[#6f6456] transition hover:border-[#a29582]"
                @click="emit('open-documents', { courseId: displayPoint.courseId })"
              >
                去文档库补充文档
                <el-icon :size="10"><TopRight /></el-icon>
              </button>
            </div>
          </section>
        </template>
      </div>

      <footer class="flex items-center gap-2 border-t border-[#d8cebd] bg-[#fbf7ef] px-6 py-4">
        <button
          type="button"
          class="inline-flex items-center gap-1.5 border border-[#c9b9a4] bg-[#fffdf8] px-3 py-2 text-[9px] font-medium text-[#6f6456] transition hover:border-[#a29582]"
          @click="copyId"
        >
          <el-icon :size="12"><CopyDocument /></el-icon>
          复制 ID
        </button>
        <button
          type="button"
          class="inline-flex flex-1 items-center justify-center gap-1.5 bg-[#7d302f] px-3 py-2 text-[9px] font-medium text-white transition hover:bg-[#692825] disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="!displayPoint.courseSourceUrl"
          @click="openCourse"
        >
          打开所属课程
          <el-icon :size="12"><TopRight /></el-icon>
        </button>
      </footer>
    </div>
  </el-drawer>
</template>
