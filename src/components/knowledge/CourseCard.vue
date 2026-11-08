<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { Course } from '@/types'

const props = defineProps<{
  course: Course
}>()

const imageFailed = ref(false)

const hasCover = computed(() => Boolean(props.course.coverUrl) && !imageFailed.value)

const coverStyle = computed(() => ({
  background: `linear-gradient(135deg, ${props.course.color}24, ${props.course.color}08)`,
}))

function handleImageError(): void {
  imageFailed.value = true
}

function formatPopularity(value: number): string {
  if (!value) return '暂无学习数据'
  if (value >= 10000) return `${(value / 10000).toFixed(1)} 万人学习`
  return `${value.toLocaleString('en-US')} 人学习`
}

function openCourse(): void {
  if (!props.course.sourceUrl) {
    ElMessage.warning('该课程暂未配置学堂在线链接')
    return
  }
  window.open(props.course.sourceUrl, '_blank', 'noopener,noreferrer')
}
</script>

<template>
  <article
    class="group flex cursor-pointer flex-col overflow-hidden border border-[#ded4c4] border-t-2 border-t-[#bfb29e] bg-[#fffdf8] transition-all duration-200 hover:-translate-y-0.5 hover:border-[#b9ab97] hover:border-t-[#7d302f] hover:shadow-[0_10px_24px_-18px_rgba(52,38,24,0.55)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#9a463c]"
    role="link"
    tabindex="0"
    :aria-label="`打开 ${course.name} 的学堂在线课程`"
    @click="openCourse"
    @keydown.enter.prevent="openCourse"
  >
    <!-- 封面：优先使用课程海报，缺图或加载失败时使用自动生成的封面 -->
    <div class="relative aspect-[16/9] overflow-hidden border-b border-[#e9e1d4]" :style="coverStyle">
      <img
        v-if="hasCover"
        :src="course.coverUrl"
        :alt="course.name"
        loading="lazy"
        referrerpolicy="no-referrer"
        class="h-full w-full object-cover transition duration-500 group-hover:scale-105"
        @error="handleImageError"
      />
      <div v-else class="flex h-full w-full flex-col items-center justify-center px-4 text-center">
        <span class="font-serif text-[26px] font-semibold leading-none" :style="{ color: course.color }">
          {{ course.shortName }}
        </span>
        <span class="mt-2 text-[8px] tracking-[0.16em] text-slate-400">
          {{ course.category || '计算机学科' }}
        </span>
      </div>

      <div class="absolute inset-0 bg-gradient-to-t from-black/35 via-transparent to-transparent opacity-0 transition duration-300 group-hover:opacity-100" />

      <div class="absolute left-2 top-2 flex flex-wrap gap-1">
        <span
          v-if="course.category"
          class="rounded-full bg-black/55 px-2 py-0.5 text-[7px] font-medium text-white backdrop-blur-sm"
        >
          {{ course.category }}
        </span>
      </div>

      <span
        class="absolute right-2 top-2 rounded-full bg-white/90 px-2 py-0.5 text-[7px] font-medium text-slate-600 opacity-0 shadow-sm transition duration-200 group-hover:opacity-100"
      >
        学堂在线 ↗
      </span>
    </div>

    <div class="flex flex-1 flex-col p-3.5">
      <div class="flex items-start justify-between gap-2">
        <h3 class="line-clamp-2 font-serif text-[12px] font-semibold leading-4 text-slate-700">
          {{ course.name }}
        </h3>
        <span class="shrink-0 font-mono text-[7.5px] text-slate-300">
          {{ course.code }}
        </span>
      </div>

      <p class="mt-1 truncate text-[8px] text-slate-400">
        {{ course.teacher }}<span v-if="course.school"> · {{ course.school }}</span>
      </p>
      <p class="mt-0.5 text-[7.5px] text-slate-300">更新于 {{ course.updatedAt }}</p>

      <p class="mt-2 line-clamp-2 text-[9px] leading-4 text-slate-500">
        {{ course.description }}
      </p>

      <div class="mt-3 flex items-center gap-1.5">
        <span class="rounded-md border border-slate-100 bg-slate-50 px-1.5 py-0.5 text-[8px] text-slate-500">
          {{ course.knowledgePointCount }} 知识点
        </span>
        <span class="rounded-md border border-slate-100 bg-slate-50 px-1.5 py-0.5 text-[8px] text-slate-500">
          {{ course.documentCount }} 文档
        </span>
        <span
          class="ml-auto flex items-center gap-1 text-[7.5px]"
          :class="course.documentCount > 0 ? 'text-emerald-500' : 'text-amber-500'"
        >
          <span
            class="h-1 w-1 rounded-full"
            :class="course.documentCount > 0 ? 'bg-emerald-400' : 'bg-amber-400'"
          />
          {{ course.documentCount > 0 ? '已索引' : '待建索引' }}
        </span>
      </div>

      <div class="mt-auto flex items-center justify-between border-t border-slate-100 pt-2">
        <span class="text-[7.5px] text-slate-400">{{ formatPopularity(course.popularity) }}</span>
        <span class="text-[7.5px] font-medium text-[#7d302f] opacity-0 transition group-hover:opacity-100">
          打开课程 →
        </span>
      </div>
    </div>
  </article>
</template>
