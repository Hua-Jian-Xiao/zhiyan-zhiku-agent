<script setup lang="ts">
withDefaults(
  defineProps<{
    subtitle?: string
    compact?: boolean
  }>(),
  {
    subtitle: 'COMPUTATIONAL STUDIES · 学术期刊',
    compact: false,
  },
)
</script>

<template>
  <div class="flex min-w-0 items-center gap-3">
    <div
      class="relative grid shrink-0 place-items-center border border-[#cdbfa7]/55 bg-[#f4eee2] text-[#682728]"
      :class="compact ? 'h-9 w-9' : 'h-11 w-11'"
    >
      <span
        class="font-serif leading-none"
        :class="compact ? 'text-[17px]' : 'text-[22px]'"
      >
        知
      </span>
      <span class="absolute inset-[3px] border border-[#682728]/18" />
      <span class="absolute -bottom-[3px] -right-[3px] h-1.5 w-1.5 bg-[#9a463c]" />
    </div>
    <div class="min-w-0">
      <div class="flex items-center gap-2">
        <span
          class="truncate font-serif font-semibold tracking-[0.13em] text-white"
          :class="compact ? 'text-[14px]' : 'text-[17px]'"
        >
          智研知库
        </span>
        <span
          class="shrink-0 border border-white/15 px-1.5 py-px font-mono text-[7px] font-medium tracking-[0.12em] text-[#d8c8ad]"
        >
          VOL.01
        </span>
      </div>
      <p
        v-if="!compact"
        class="mt-1 truncate font-mono text-[7px] tracking-[0.15em] text-[#8e8272]"
      >
        {{ subtitle }}
      </p>
    </div>
  </div>
</template>
