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
    class="group relative overflow-hidden border border-[#d8cebd] border-t-2 border-t-[#211c17] bg-[#fffdf8] p-4 transition-all duration-200 hover:border-[#b9ab97]"
  >
    <span
      v-if="rank === 1"
      class="absolute inset-y-0 left-0 w-[2px] bg-[#7d302f]"
    />

    <div class="flex items-start gap-3">
      <div class="flex shrink-0 flex-col items-center gap-1">
        <span
          class="grid h-8 w-8 place-items-center border font-serif text-[12px] font-semibold"
          :class="rank === 1 ? 'border-[#c99f98] bg-[#f6e9e4] text-[#7d302f]' : 'border-[#d8cebd] bg-[#f8f3e9] text-[#6f6456]'"
        >
          {{ rankLabel }}
        </span>
        <span class="font-mono text-[6px] tracking-[0.1em] text-[#b5a995]">RANK</span>
      </div>

      <div class="min-w-0 flex-1">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-1.5">
              <span class="border border-[#d8b8b1] bg-[#f6e9e4] px-1.5 py-0.5 text-[7.5px] font-medium text-[#8e3d35]">
                {{ chunk.course }}
              </span>
              <span class="border border-[#e1d0aa] bg-[#faf3e3] px-1.5 py-0.5 font-mono text-[7.5px] text-[#8a692a]">
                {{ chunk.knowledgePointId }}
              </span>
              <span class="border border-[#e2d9ca] bg-[#f8f3e9] px-1.5 py-0.5 text-[7.5px] text-[#8d806e]">
                {{ chunk.chapter }}
              </span>
            </div>
            <h3 class="mt-1.5 font-serif text-[13px] font-semibold leading-5 text-[#2f2922]">
              {{ chunk.title }}
            </h3>
            <p class="mt-1 flex min-w-0 items-center gap-1 font-mono text-[7px] text-[#a29582]">
              <el-icon :size="9"><Document /></el-icon>
              <span class="truncate">{{ chunk.source }}</span>
            </p>
          </div>

          <div class="shrink-0 text-right">
            <span
              class="border px-2 py-1 font-mono text-[14px] font-semibold"
              :class="[scoreTone.text, scoreTone.bg, scoreTone.border]"
            >
              {{ chunk.score.toFixed(3) }}
            </span>
            <p class="mt-1 font-mono text-[6px] tracking-[0.1em] text-[#b5a995]">SIMILARITY</p>
          </div>
        </div>

        <div class="mt-3 h-px overflow-hidden bg-[#e2d9ca]">
          <div
            class="h-full transition-all duration-700"
            :class="scoreTone.bar"
            :style="{ width: `${Math.max(6, chunk.score * 100)}%` }"
          />
        </div>

        <div class="mt-3 border-l-2 border-[#9a463c] bg-[#f8f3e9] px-3 py-2.5">
          <div class="mb-1 flex items-center gap-1.5">
            <span class="h-1 w-1 rounded-full bg-[#9a463c]" />
            <span class="font-mono text-[6.5px] font-medium uppercase tracking-[0.14em] text-[#a29582]">
              Retrieved passage / 原文
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
          <el-icon :size="8" class="text-[#b5a995]"><PriceTag /></el-icon>
          <span
            v-for="tag in chunk.tags"
            :key="tag"
            class="border-b border-[#e2d9ca] px-1 py-0.5 font-mono text-[6.5px] text-[#a29582]"
          >
            #{{ tag }}
          </span>
        </div>
      </div>
    </div>
  </article>
</template>
