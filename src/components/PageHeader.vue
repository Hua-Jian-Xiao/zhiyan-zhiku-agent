<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string
    description?: string
  }>(),
  {
    description: '',
  },
)
</script>

<template>
  <header class="border-b border-[#c9bdab] pb-5">
    <div class="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
      <div class="min-w-0">
        <span class="mb-3 block h-px w-8 bg-[#7d302f]" />
        <h1 class="font-serif text-[34px] font-medium leading-[1.15] tracking-[-0.025em] text-[#211c17] sm:text-[40px]">
          {{ title }}
        </h1>
        <p v-if="description" class="mt-3 max-w-2xl text-[13px] leading-6 text-[#766b5b]">
          {{ description }}
        </p>
      </div>
      <div v-if="$slots.actions" class="flex shrink-0 flex-wrap items-center gap-2.5">
        <slot name="actions" />
      </div>
    </div>
  </header>
</template>
