<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowDown, Document, PriceTag } from '@element-plus/icons-vue'
import type { RetrievedChunk } from '@/types'

const props = defineProps<{
  chunk: RetrievedChunk
  rank: number
}>()

const expanded = ref(false)

const rankLabel = computed(() => String(props.rank).padStart(2, '0'))
const scoreTone = computed(() => {
  if (props.chunk.score >= 0.9) {
    return {
      text: 'text-emerald-600',
      bg: 'bg-emerald-50',
      border: 'border-emerald-100',
      bar: 'from-emerald-400 to-teal-400',
    }
  }
  if (props.chunk.score >= 0.8) {
    return {
      text: 'text-indigo-600',
      bg: 'bg-indigo-50',
      border: 'border-indigo-100',
      bar: 'from-indigo-500 to-cyan-400',
    }
  }
  return {
    text: 'text-amber-600',
    bg: 'bg-amber-50',
    border: 'border-amber-100',
    bar: 'from-amber-400 to-orange-400',
  }
})
</script>

<template>
  <article
    class="group relative overflow-hidden rounded-2xl border border-slate-200/85 bg-white p-4 transition-all duration-200 hover:border-indigo-200 hover:shadow-[0_18px_44px_-32px_rgba(79,70,229,0.45)]"
  >
    <span
      v-if="rank === 1"
      class="absolute inset-y-0 left-0 w-[2px] bg-gradient-to-b from-indigo-500 to-cyan-400"
    />

    <div class="flex items-start gap-3">
      <div class="flex shrink-0 flex-col items-center gap-1">
        <span
          class="grid h-8 w-8 place-items-center rounded-lg border font-mono text-[10px] font-semibold"
          :class="rank === 1 ? 'border-indigo-200 bg-indigo-50 text-indigo-600' : 'border-slate-200 bg-slate-50 text-slate-500'"
        >
          {{ rankLabel }}
        </span>
        <span class="text-[7px] text-slate-300">RANK</span>
      </div>

      <div class="min-w-0 flex-1">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-1.5">
              <span class="rounded border border-indigo-100 bg-indigo-50 px-1.5 py-0.5 text-[7.5px] font-medium text-indigo-500">
                {{ chunk.course }}
              </span>
              <span class="rounded border border-slate-100 bg-slate-50 px-1.5 py-0.5 text-[7.5px] text-slate-400">
                {{ chunk.chapter }}
              </span>
            </div>
            <h3 class="mt-1.5 text-[12px] font-semibold leading-5 text-slate-700">
              {{ chunk.title }}
            </h3>
            <p class="mt-1 flex min-w-0 items-center gap-1 text-[8px] text-slate-400">
              <el-icon :size="9"><Document /></el-icon>
              <span class="truncate">{{ chunk.source }}</span>
            </p>
          </div>

          <div class="shrink-0 text-right">
            <span
              class="rounded-lg border px-2 py-1 font-mono text-[13px] font-semibold"
              :class="[scoreTone.text, scoreTone.bg, scoreTone.border]"
            >
              {{ chunk.score.toFixed(3) }}
            </span>
            <p class="mt-1 font-mono text-[7px] text-slate-300">SIMILARITY</p>
          </div>
        </div>

        <div class="mt-3 h-1 overflow-hidden rounded-full bg-slate-100">
          <div
            class="h-full rounded-full bg-gradient-to-r transition-all duration-700"
            :class="scoreTone.bar"
            :style="{ width: `${Math.max(6, chunk.score * 100)}%` }"
          />
        </div>

        <div class="mt-3 rounded-xl border border-slate-100 bg-slate-50/70 px-3 py-2.5">
          <div class="mb-1 flex items-center gap-1.5">
            <span class="h-1 w-1 rounded-full bg-indigo-400" />
            <span class="text-[7.5px] font-semibold uppercase tracking-wider text-slate-400">
              Retrieved Chunk
            </span>
          </div>
          <p
            class="text-[9.5px] leading-[1.8] text-slate-500"
            :class="expanded ? '' : 'line-clamp-3'"
          >
            {{ chunk.content }}
          </p>
          <button
            type="button"
            class="mt-1.5 flex items-center gap-0.5 text-[8px] font-medium text-slate-400 transition hover:text-indigo-500"
            @click="expanded = !expanded"
          >
            {{ expanded ? '收起片段' : '查看完整片段' }}
            <el-icon :size="8" class="transition-transform" :class="{ 'rotate-180': expanded }">
              <ArrowDown />
            </el-icon>
          </button>
        </div>

        <div class="mt-2.5 flex flex-wrap items-center gap-1.5">
          <el-icon :size="9" class="text-slate-300"><PriceTag /></el-icon>
          <span
            v-for="tag in chunk.tags"
            :key="tag"
            class="rounded bg-slate-50 px-1.5 py-0.5 text-[7.5px] text-slate-400"
          >
            #{{ tag }}
          </span>
        </div>
      </div>
    </div>
  </article>
</template>
