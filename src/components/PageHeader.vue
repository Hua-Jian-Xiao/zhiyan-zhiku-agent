<script setup lang="ts">
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
</script>

<template>
  <div class="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
    <div class="min-w-0">
      <div v-if="eyebrow" class="mb-2 flex items-center gap-2">
        <span class="h-1.5 w-1.5 rounded-full bg-indigo-500 shadow-[0_0_0_4px_rgba(99,102,241,0.1)]" />
        <span class="section-eyebrow">{{ eyebrow }}</span>
      </div>
      <h1 class="text-[26px] font-bold leading-tight tracking-[-0.02em] text-ink-950 sm:text-[30px]">
        {{ title }}
      </h1>
      <p v-if="description" class="mt-2 max-w-2xl text-[13px] leading-6 text-slate-500">
        {{ description }}
      </p>
    </div>
    <div v-if="$slots.actions" class="flex shrink-0 flex-wrap items-center gap-2.5">
      <slot name="actions" />
    </div>
  </div>
</template>
