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
      text: 'text-emerald-700',
      bg: 'bg-emerald-50',
      border: 'border-emerald-200',
      bar: 'bg-emerald-500',
    }
  }
  if (props.citation.score >= 0.8) {
    return {
      text: 'text-indigo-700',
      bg: 'bg-indigo-50',
      border: 'border-indigo-200',
      bar: 'bg-indigo-500',
    }
  }
  return {
    text: 'text-amber-700',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    bar: 'bg-amber-500',
  }
})
</script>

<template>
  <article
    class="group flex min-w-0 flex-col border-t-2 border-[#211c17] bg-[#fffdf8] px-3 pb-3 pt-2.5 transition-colors duration-200 hover:bg-[#fbf6ec]"
  >
    <div class="flex items-start justify-between gap-2">
      <div class="flex min-w-0 items-center gap-1.5">
        <span class="font-serif text-[11px] italic text-[#7d302f]">[{{ citation.index }}]</span>
        <span class="truncate text-[8.5px] font-medium text-[#5b5145]">{{ citation.course }}</span>
        <span class="shrink-0 border border-[#d8cebd] px-1 py-px font-mono text-[6.5px] text-[#8d806e]">
          {{ citation.knowledgePointId }}
        </span>
      </div>
      <span
        class="shrink-0 border px-1.5 py-px font-mono text-[7px]"
        :class="[scoreTone.text, scoreTone.bg, scoreTone.border]"
      >
        {{ citation.score.toFixed(3) }}
      </span>
    </div>

    <h4 class="mt-2 line-clamp-2 font-serif text-[11px] font-semibold leading-4 text-[#2f2922]">
      {{ citation.title }}
    </h4>
    <p class="mt-1 truncate font-mono text-[7px] text-[#a29582]">
      {{ citation.chapter }} / {{ citation.source }}
    </p>

    <p
      class="mt-2 text-[9px] leading-[1.75] text-[#6f6456]"
      :class="expanded ? '' : 'line-clamp-2'"
    >
      {{ citation.snippet }}
    </p>

    <div class="mt-auto flex items-center justify-between gap-2 pt-2">
      <span class="flex min-w-0 items-center gap-1 font-mono text-[7px] uppercase tracking-[0.06em] text-[#a29582]">
        <el-icon :size="8"><Document /></el-icon>
        Source fragment
      </span>
      <button
        type="button"
        class="flex shrink-0 items-center gap-0.5 font-mono text-[7px] text-[#8d806e] transition hover:text-[#7d302f]"
        @click="expanded = !expanded"
      >
        {{ expanded ? '收起' : '展开' }}
        <el-icon
          :size="8"
          class="transition-transform"
          :class="{ 'rotate-180': expanded }"
        >
          <ArrowDown />
        </el-icon>
      </button>
    </div>

    <div class="mt-2 h-px overflow-hidden bg-[#e2d9ca]">
      <div
        class="h-full transition-all duration-500"
        :class="scoreTone.bar"
        :style="{ width: `${citation.score * 100}%` }"
      />
    </div>
  </article>
</template>
