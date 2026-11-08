<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowDown, Document } from '@element-plus/icons-vue'
import type { Citation } from '@/types'

const props = defineProps<{
  citation: Citation
}>()

const expanded = ref(false)
const scoreTone = computed(() => {
  if (props.citation.score >= 0.9) {
    return {
      text: 'text-emerald-600',
      bg: 'bg-emerald-50',
      border: 'border-emerald-100',
      bar: 'bg-emerald-400',
    }
  }
  if (props.citation.score >= 0.8) {
    return {
      text: 'text-indigo-600',
      bg: 'bg-indigo-50',
      border: 'border-indigo-100',
      bar: 'bg-indigo-400',
    }
  }
  return {
    text: 'text-amber-600',
    bg: 'bg-amber-50',
    border: 'border-amber-100',
    bar: 'bg-amber-400',
  }
})
</script>

<template>
  <article
    class="group flex min-w-0 flex-col rounded-xl border border-slate-200/85 bg-white p-3 transition-all duration-200 hover:border-indigo-200 hover:shadow-[0_10px_30px_-24px_rgba(79,70,229,0.6)]"
  >
    <div class="flex items-start justify-between gap-2">
      <div class="flex min-w-0 items-center gap-1.5">
        <span
          class="grid h-5 w-5 shrink-0 place-items-center rounded-md bg-indigo-50 text-[9px] font-bold text-indigo-500"
        >
          {{ citation.index }}
        </span>
        <span class="truncate text-[8px] font-medium text-slate-400">{{ citation.course }}</span>
      </div>
      <span
        class="shrink-0 rounded border px-1.5 py-px font-mono text-[8px]"
        :class="[scoreTone.text, scoreTone.bg, scoreTone.border]"
      >
        {{ citation.score.toFixed(3) }}
      </span>
    </div>

    <h4 class="mt-2 line-clamp-2 text-[10.5px] font-semibold leading-4 text-slate-700">
      {{ citation.title }}
    </h4>
    <p class="mt-1 truncate text-[8px] text-slate-400">
      {{ citation.chapter }} · {{ citation.source }}
    </p>

    <p
      class="mt-2 text-[9px] leading-[1.7] text-slate-500"
      :class="expanded ? '' : 'line-clamp-2'"
    >
      {{ citation.snippet }}
    </p>

    <div class="mt-auto flex items-center justify-between gap-2 pt-2">
      <span class="flex min-w-0 items-center gap-1 text-[8px] text-slate-400">
        <el-icon :size="9"><Document /></el-icon>
        知识库片段
      </span>
      <button
        type="button"
        class="flex shrink-0 items-center gap-0.5 text-[8px] text-slate-400 transition hover:text-indigo-500"
        @click="expanded = !expanded"
      >
        {{ expanded ? '收起' : '展开' }}
        <el-icon
          :size="9"
          class="transition-transform"
          :class="{ 'rotate-180': expanded }"
        >
          <ArrowDown />
        </el-icon>
      </button>
    </div>

    <div class="mt-2 h-0.5 overflow-hidden rounded-full bg-slate-100">
      <div
        class="h-full rounded-full transition-all duration-500"
        :class="scoreTone.bar"
        :style="{ width: `${citation.score * 100}%` }"
      />
    </div>
  </article>
</template>
