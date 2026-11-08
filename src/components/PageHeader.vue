<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

withDefaults(
  defineProps<{
    eyebrow?: string
    title: string
    description?: string
  }>(),
  {
    eyebrow: '',
    description: '',
  },
)

const route = useRoute()

const sectionNumber = computed(() => {
  const sections: Record<string, string> = {
    workspace: '01',
    knowledge: '02',
    'rag-debug': '03',
    graph: '04',
  }
  return sections[String(route.name ?? '')] ?? '00'
})

const sectionCode = computed(() => {
  const codes: Record<string, string> = {
    workspace: 'FIELD NOTES',
    knowledge: 'ARCHIVE',
    'rag-debug': 'LABORATORY',
    graph: 'CARTOGRAPHY',
  }
  return codes[String(route.name ?? '')] ?? 'EDITORIAL'
})
</script>

<template>
  <header class="border-b border-[#c9bdab] pb-5">
    <div class="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
      <div class="min-w-0">
        <div class="mb-3 flex flex-wrap items-center gap-2.5">
          <span class="h-px w-6 bg-[#7d302f]" />
          <span class="section-eyebrow">{{ eyebrow || 'Editorial Section' }}</span>
          <span class="font-mono text-[7px] tracking-[0.14em] text-[#a99d8b]">
            § {{ sectionNumber }}
          </span>
          <span class="h-2.5 w-px bg-[#d8cebd]" />
          <span class="font-mono text-[7px] uppercase tracking-[0.16em] text-[#a99d8b]">
            {{ sectionCode }}
          </span>
        </div>
        <h1 class="font-serif text-[32px] font-medium leading-[1.15] tracking-[-0.025em] text-[#211c17] sm:text-[38px]">
          {{ title }}
        </h1>
        <p v-if="description" class="mt-3 max-w-2xl text-[11px] leading-6 text-[#766b5b]">
          {{ description }}
        </p>
      </div>
      <div v-if="$slots.actions" class="flex shrink-0 flex-wrap items-center gap-2.5">
        <slot name="actions" />
      </div>
    </div>
    <div class="mt-5 flex items-center justify-between text-[#a99d8b]">
      <span class="font-mono text-[7px] uppercase tracking-[0.16em]">
        ZHIYAN · COMPUTATIONAL STUDIES
      </span>
      <span class="font-mono text-[7px] tracking-[0.12em]">
        ISSUE {{ sectionNumber }} / 2026
      </span>
    </div>
  </header>
</template>
