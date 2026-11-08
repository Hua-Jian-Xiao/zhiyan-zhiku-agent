<script setup lang="ts">
withDefaults(
  defineProps<{
    subtitle?: string
    compact?: boolean
  }>(),
  {
    subtitle: 'RAG LEARNING LAB',
    compact: false,
  },
)
</script>

<template>
  <div class="flex min-w-0 items-center gap-3">
    <div
      class="relative grid shrink-0 place-items-center rounded-[13px] bg-gradient-to-br from-indigo-400 via-indigo-500 to-cyan-400 shadow-[0_8px_24px_-8px_rgba(99,102,241,0.8)]"
      :class="compact ? 'h-9 w-9' : 'h-10 w-10'"
    >
      <svg
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        :class="compact ? 'h-5 w-5' : 'h-[22px] w-[22px]'"
        aria-hidden="true"
      >
        <path
          d="M8.5 11.4 16 7.6l7.5 3.8L16 15.2 8.5 11.4Z"
          fill="white"
          fill-opacity="0.96"
        />
        <path
          d="M8.5 16 16 19.8l7.5-3.8"
          stroke="white"
          stroke-width="1.8"
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-opacity="0.88"
        />
        <path
          d="M8.5 20.5 16 24.3l7.5-3.8"
          stroke="white"
          stroke-width="1.8"
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-opacity="0.5"
        />
        <circle cx="24" cy="9" r="2.1" fill="#FDE68A" />
      </svg>
    </div>
    <div class="min-w-0">
      <div class="flex items-center gap-2">
        <span class="truncate text-[15px] font-bold tracking-[0.04em] text-white">智研知库</span>
        <span
          class="rounded-full border border-white/15 bg-white/10 px-1.5 py-px text-[8px] font-semibold tracking-wider text-cyan-200"
          >BETA</span
        >
      </div>
      <p
        v-if="!compact"
        class="mt-0.5 truncate text-[8px] font-semibold tracking-[0.23em] text-slate-400"
      >
        {{ subtitle }}
      </p>
    </div>
  </div>
</template>
