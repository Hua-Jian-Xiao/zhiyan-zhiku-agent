<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ArrowDown, Cpu } from '@element-plus/icons-vue'
import type { AgentTrace, MessageStatus } from '@/types'
import { formatDuration } from '@/utils/format'

const props = withDefaults(
  defineProps<{
    trace: AgentTrace
    status?: MessageStatus
    defaultOpen?: boolean
  }>(),
  {
    status: 'done',
    defaultOpen: false,
  },
)

const open = ref(props.defaultOpen)
const isRunning = computed(() => props.status === 'streaming')

watch(
  () => props.status,
  (status, previousStatus) => {
    if (previousStatus === 'streaming' && status === 'done') {
      open.value = false
    }
  },
)
const doneSteps = computed(() => props.trace.steps.filter((step) => step.status === 'done').length)
const runningStep = computed(() => props.trace.steps.find((step) => step.status === 'running'))

const summary = computed(
  () =>
    `${doneSteps.value}/${props.trace.steps.length} 个步骤 · ${props.trace.tools.length} 次工具调用 · ${props.trace.chunks.length} 条知识片段`,
)
</script>

<template>
  <div class="mt-3.5 overflow-hidden rounded-xl border border-slate-200/90 bg-[#fafbfd]">
    <button
      type="button"
      class="flex w-full items-center gap-2.5 px-3.5 py-2.5 text-left transition hover:bg-slate-50/80"
      @click="open = !open"
    >
      <span
        class="grid h-6 w-6 shrink-0 place-items-center rounded-md border transition"
        :class="
          isRunning
            ? 'border-indigo-200 bg-indigo-50 text-indigo-500'
            : 'border-slate-200 bg-white text-slate-400'
        "
      >
        <el-icon :size="12" :class="{ 'animate-pulse': isRunning }"><Cpu /></el-icon>
      </span>
      <span class="min-w-0 flex-1">
        <span class="flex flex-wrap items-center gap-x-2 gap-y-0.5">
          <span class="text-[11px] font-semibold text-slate-700">Agent 思考面板</span>
          <span
            v-if="isRunning"
            class="inline-flex items-center gap-1 rounded-full bg-indigo-50 px-1.5 py-px text-[8px] font-medium text-indigo-500"
          >
            <span class="h-1 w-1 animate-pulse rounded-full bg-indigo-500" />
            思考中
          </span>
          <span
            v-else
            class="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-1.5 py-px text-[8px] font-medium text-emerald-600"
          >
            <span class="h-1 w-1 rounded-full bg-emerald-500" />
            已完成
          </span>
        </span>
        <span class="mt-0.5 block truncate text-[9px] text-slate-400">
          {{ runningStep?.detail || summary }}
        </span>
      </span>
      <span class="hidden shrink-0 font-mono text-[8px] text-slate-400 sm:inline">
        {{ summary }}
      </span>
      <el-icon
        :size="12"
        class="shrink-0 text-slate-400 transition-transform duration-200"
        :class="{ 'rotate-180': open }"
      >
        <ArrowDown />
      </el-icon>
    </button>

    <Transition name="panel">
      <div v-if="open" class="border-t border-slate-200/80">
        <div class="max-h-[440px] space-y-4 overflow-y-auto px-3.5 py-3.5 scroll-thin">
          <section>
            <div class="mb-2.5 flex items-center justify-between">
              <p class="section-eyebrow !text-[8px]">思考过程</p>
              <span class="font-mono text-[8px] text-slate-400">{{ doneSteps }}/{{ trace.steps.length }}</span>
            </div>
            <div>
              <div
                v-for="(step, index) in trace.steps"
                :key="step.id"
                class="relative flex gap-2.5"
              >
                <div class="flex w-4 shrink-0 flex-col items-center">
                  <span
                    class="relative z-10 mt-0.5 grid h-4 w-4 place-items-center rounded-full border"
                    :class="{
                      'border-emerald-200 bg-emerald-50 text-emerald-600': step.status === 'done',
                      'border-indigo-200 bg-indigo-50': step.status === 'running',
                      'border-slate-200 bg-white': step.status === 'pending',
                    }"
                  >
                    <svg
                      v-if="step.status === 'done'"
                      viewBox="0 0 12 12"
                      fill="none"
                      class="h-2 w-2"
                    >
                      <path
                        d="m2.3 6.1 2.2 2.2 5-5"
                        stroke="currentColor"
                        stroke-width="1.5"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      />
                    </svg>
                    <span
                      v-else-if="step.status === 'running'"
                      class="h-2.5 w-2.5 animate-spin rounded-full border border-indigo-500 border-r-transparent"
                    />
                    <span v-else class="h-1 w-1 rounded-full bg-slate-300" />
                  </span>
                  <span
                    v-if="index < trace.steps.length - 1"
                    class="w-px flex-1 bg-slate-200"
                  />
                </div>
                <div class="min-w-0 flex-1 pb-3">
                  <div class="flex items-center gap-2">
                    <p
                      class="text-[10px] font-medium"
                      :class="step.status === 'pending' ? 'text-slate-400' : 'text-slate-700'"
                    >
                      {{ step.title }}
                    </p>
                    <span v-if="step.durationMs" class="font-mono text-[7px] text-slate-400">
                      {{ formatDuration(step.durationMs) }}
                    </span>
                  </div>
                  <p class="mt-0.5 text-[9px] leading-4 text-slate-400">{{ step.detail }}</p>
                </div>
              </div>
            </div>
          </section>

          <section>
            <div class="mb-2 flex items-center justify-between">
              <p class="section-eyebrow !text-[8px]">工具调用</p>
              <span class="font-mono text-[8px] text-slate-400">{{ trace.tools.length }} calls</span>
            </div>
            <div v-if="trace.tools.length" class="space-y-1.5">
              <div
                v-for="tool in trace.tools"
                :key="tool.id"
                class="rounded-lg border border-slate-200/80 bg-white px-2.5 py-2"
              >
                <div class="flex items-center gap-2">
                  <span
                    class="h-1.5 w-1.5 shrink-0 rounded-full"
                    :class="tool.status === 'done' ? 'bg-emerald-400' : 'animate-pulse bg-indigo-400'"
                  />
                  <span class="min-w-0 flex-1 truncate text-[9px] font-medium text-slate-700">
                    {{ tool.label }}
                  </span>
                  <span class="font-mono text-[7px] text-slate-400">{{ tool.name }}</span>
                  <span v-if="tool.durationMs" class="font-mono text-[7px] text-slate-400">
                    {{ formatDuration(tool.durationMs) }}
                  </span>
                </div>
                <p class="mt-1 truncate rounded bg-slate-50 px-1.5 py-1 font-mono text-[7.5px] text-slate-500">
                  {{ tool.input }}
                </p>
                <p class="mt-1 flex items-start gap-1 text-[8px] leading-4 text-slate-400">
                  <span class="text-emerald-500">↳</span>
                  {{ tool.output }}
                </p>
              </div>
            </div>
            <p v-else class="rounded-lg border border-dashed border-slate-200 px-2.5 py-3 text-center text-[8px] text-slate-400">
              暂无工具调用记录
            </p>
          </section>

          <section>
            <div class="mb-2 flex items-center justify-between">
              <p class="section-eyebrow !text-[8px]">检索知识片段</p>
              <span class="font-mono text-[8px] text-slate-400">{{ trace.chunks.length }} chunks</span>
            </div>
            <div v-if="trace.chunks.length" class="space-y-1.5">
              <div
                v-for="chunk in trace.chunks"
                :key="chunk.id"
                class="rounded-lg border border-slate-200/80 bg-white px-2.5 py-2"
              >
                <div class="flex items-start gap-2">
                  <span class="mt-0.5 grid h-4 w-4 shrink-0 place-items-center rounded bg-indigo-50 text-[7px] font-bold text-indigo-500">
                    {{ chunk.id.includes('ml') ? 'ML' : chunk.course.slice(0, 1) }}
                  </span>
                  <div class="min-w-0 flex-1">
                    <div class="flex items-start justify-between gap-2">
                      <p class="text-[9px] font-medium text-slate-700">{{ chunk.title }}</p>
                      <span class="shrink-0 rounded bg-emerald-50 px-1 py-px font-mono text-[7px] text-emerald-600">
                        {{ chunk.score.toFixed(3) }}
                      </span>
                    </div>
                    <p class="mt-0.5 text-[7.5px] text-slate-400">
                      {{ chunk.course }} · {{ chunk.chapter }}
                    </p>
                    <p class="mt-1 line-clamp-2 text-[8px] leading-4 text-slate-500">
                      {{ chunk.content }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <p v-else class="rounded-lg border border-dashed border-slate-200 px-2.5 py-3 text-center text-[8px] text-slate-400">
              本次没有召回满足阈值的片段
            </p>
          </section>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.panel-enter-active,
.panel-leave-active {
  transition: opacity 0.18s ease;
}

.panel-enter-from,
.panel-leave-to {
  opacity: 0;
}
</style>
