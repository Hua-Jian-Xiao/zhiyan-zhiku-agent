<script setup lang="ts">
import { WarningFilled } from '@element-plus/icons-vue'

withDefaults(
  defineProps<{
    type?: 'empty' | 'error'
    title?: string
    description?: string
    actionText?: string
    compact?: boolean
  }>(),
  {
    type: 'empty',
    title: '',
    description: '',
    actionText: '',
    compact: false,
  },
)

defineEmits<{
  (event: 'action'): void
}>()
</script>

<template>
  <div
    class="flex flex-col items-center justify-center px-6 text-center"
    :class="compact ? 'py-8' : 'py-14'"
  >
    <div
      class="relative mb-4 grid place-items-center rounded-2xl border"
      :class="[
        compact ? 'h-12 w-12' : 'h-16 w-16',
        type === 'error'
          ? 'border-rose-100 bg-rose-50 text-rose-500'
          : 'border-indigo-100 bg-indigo-50/70 text-indigo-500',
      ]"
    >
      <span
        v-if="type === 'empty'"
        class="absolute inset-2 rounded-xl border border-indigo-100/80"
      />
      <el-icon v-if="type === 'error'" :size="compact ? 22 : 28">
        <WarningFilled />
      </el-icon>
      <svg
        v-else
        :class="compact ? 'h-5 w-5' : 'h-7 w-7'"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.6"
        aria-hidden="true"
      >
        <ellipse cx="12" cy="5.5" rx="7" ry="3" />
        <path d="M5 5.5v6c0 1.66 3.13 3 7 3s7-1.34 7-3v-6" />
        <path d="M5 11.5v6c0 1.66 3.13 3 7 3s7-1.34 7-3v-6" />
      </svg>
    </div>
    <h3 class="text-[15px] font-semibold text-slate-800">
      {{ title || (type === 'error' ? '数据加载失败' : '这里还没有内容') }}
    </h3>
    <p v-if="description" class="mt-1.5 max-w-sm text-xs leading-5 text-slate-400">
      {{ description }}
    </p>
    <el-button
      v-if="actionText"
      class="!mt-5"
      :type="type === 'error' ? 'default' : 'primary'"
      plain
      size="small"
      @click="$emit('action')"
    >
      {{ actionText }}
    </el-button>
    <slot />
  </div>
</template>
