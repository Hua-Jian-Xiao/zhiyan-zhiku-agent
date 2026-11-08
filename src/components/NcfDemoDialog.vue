<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import {
  Close,
  MagicStick,
  Refresh,
  Timer,
  TrendCharts,
  User,
  WarningFilled,
} from '@element-plus/icons-vue'
import { mockUsers } from '@/data/mockData'
import { fetchNcfRecommendations } from '@/services/mockApi'
import type { NcfResult } from '@/types'
import { isAbortError } from '@/utils/async'
import { formatDuration } from '@/utils/format'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (event: 'update:modelValue', value: boolean): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

const selectedUserId = ref(mockUsers[0]?.id ?? '')
const topK = ref(5)
const isLoading = ref(false)
const errorMessage = ref('')
const result = ref<NcfResult | null>(null)
let controller: AbortController | null = null

const selectedUser = computed(() => mockUsers.find((user) => user.id === selectedUserId.value))

watch([selectedUserId, topK], () => {
  if (!isLoading.value) {
    result.value = null
    errorMessage.value = ''
  }
})

watch(visible, (isOpen) => {
  if (!isOpen) {
    controller?.abort()
    controller = null
    isLoading.value = false
  }
})

function selectUser(userId: string): void {
  if (isLoading.value) return
  selectedUserId.value = userId
}

async function runInference(): Promise<void> {
  if (isLoading.value) return
  controller?.abort()
  controller = new AbortController()
  isLoading.value = true
  errorMessage.value = ''
  result.value = null

  try {
    result.value = await fetchNcfRecommendations(
      selectedUserId.value,
      topK.value,
      controller.signal,
    )
  } catch (error) {
    if (!isAbortError(error)) {
      errorMessage.value = error instanceof Error ? error.message : 'NCF 推理失败，请重试'
    }
  } finally {
    isLoading.value = false
    controller = null
  }
}

function closeDialog(): void {
  visible.value = false
}

onBeforeUnmount(() => {
  controller?.abort()
})
</script>

<template>
  <el-dialog
    v-model="visible"
    width="920px"
    class="ncf-demo-dialog"
    :show-close="false"
    :close-on-click-modal="!isLoading"
    append-to-body
    destroy-on-close
  >
    <div class="ncf-demo">
      <header class="ncf-hero">
        <div class="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
          <div class="absolute -right-16 -top-20 h-64 w-64 rounded-full bg-cyan-400/15 blur-[80px]" />
          <div class="absolute -left-24 bottom-0 h-56 w-56 rounded-full bg-indigo-400/20 blur-[90px]" />
          <div class="absolute inset-0 dot-grid opacity-[0.08]" />
        </div>

        <div class="relative flex items-start justify-between gap-4">
          <div>
            <div class="flex items-center gap-2">
              <span
                class="rounded-full border border-amber-300/25 bg-amber-300/10 px-2 py-0.5 text-[9px] font-semibold tracking-[0.16em] text-amber-200"
              >
                ANNEX DEMO
              </span>
              <span class="text-[10px] text-slate-500">独立实验功能，不进入核心 RAG 流程</span>
            </div>
            <div class="mt-4 flex items-center gap-3">
              <span class="grid h-11 w-11 place-items-center rounded-2xl bg-white/[0.08] text-cyan-300">
                <el-icon :size="22"><MagicStick /></el-icon>
              </span>
              <div>
                <h2 class="text-[21px] font-bold tracking-tight text-white">NCF 个性化推荐</h2>
                <p class="mt-0.5 text-xs text-slate-400">
                  Neural Collaborative Filtering · 用学习行为预测下一步该学什么
                </p>
              </div>
            </div>
          </div>
          <button
            type="button"
            class="grid h-8 w-8 place-items-center rounded-full border border-white/10 bg-white/[0.04] text-slate-400 transition hover:bg-white/10 hover:text-white"
            aria-label="关闭弹窗"
            @click="closeDialog"
          >
            <el-icon :size="14"><Close /></el-icon>
          </button>
        </div>

        <div class="relative mt-6 flex flex-wrap items-center gap-x-8 gap-y-2 border-t border-white/[0.07] pt-4">
          <div class="flex items-center gap-2 text-[10px] text-slate-500">
            <span class="text-slate-400">架构</span>
            <span class="font-mono text-cyan-300/90">GMF + MLP</span>
          </div>
          <div class="flex items-center gap-2 text-[10px] text-slate-500">
            <span class="text-slate-400">Embedding</span>
            <span class="font-mono text-slate-300">32d</span>
          </div>
          <div class="flex items-center gap-2 text-[10px] text-slate-500">
            <span class="text-slate-400">离线评估</span>
            <span class="font-mono text-emerald-300/90">AUC 0.7842</span>
          </div>
          <div class="flex items-center gap-2 text-[10px] text-slate-500">
            <span class="text-slate-400">训练样本</span>
            <span class="font-mono text-slate-300">84,216</span>
          </div>
        </div>
      </header>

      <div class="ncf-body">
        <section class="ncf-config">
          <div>
            <p class="ncf-step-label"><span>01</span> 选择学习者</p>
            <div class="mt-3 space-y-2">
              <button
                v-for="userItem in mockUsers"
                :key="userItem.id"
                type="button"
                class="ncf-user-card"
                :class="{ 'is-active': selectedUserId === userItem.id }"
                :disabled="isLoading"
                @click="selectUser(userItem.id)"
              >
                <span
                  class="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-[11px] font-bold text-white"
                  :style="{ backgroundColor: userItem.color }"
                >
                  {{ userItem.avatar }}
                </span>
                <span class="min-w-0 flex-1 text-left">
                  <span class="block truncate text-[11px] font-semibold text-slate-800">
                    {{ userItem.name }}
                    <span class="ml-1 font-normal text-[9px] text-slate-400">{{ userItem.stage }}</span>
                  </span>
                  <span class="mt-0.5 block truncate text-[9px] text-slate-400">
                    {{ userItem.interests.join(' · ') }}
                  </span>
                </span>
                <span
                  class="h-2 w-2 shrink-0 rounded-full border"
                  :class="
                    selectedUserId === userItem.id
                      ? 'border-indigo-500 bg-indigo-500 shadow-[0_0_0_3px_rgba(99,102,241,0.12)]'
                      : 'border-slate-300 bg-white'
                  "
                />
              </button>
            </div>
          </div>

          <div class="mt-6">
            <div class="flex items-center justify-between">
              <p class="ncf-step-label"><span>02</span> 推荐数量</p>
              <span class="font-mono text-[10px] text-indigo-500">Top-{{ topK }}</span>
            </div>
            <div class="mt-2.5 grid grid-cols-3 gap-1.5 rounded-xl bg-slate-200/60 p-1">
              <button
                v-for="option in [3, 5, 8]"
                :key="option"
                type="button"
                class="rounded-lg py-1.5 text-[10px] font-medium transition"
                :class="
                  topK === option
                    ? 'bg-white text-indigo-600 shadow-sm'
                    : 'text-slate-500 hover:text-slate-700'
                "
                :disabled="isLoading"
                @click="topK = option"
              >
                {{ option }} 条
              </button>
            </div>
          </div>

          <div class="mt-5 rounded-xl border border-slate-200/80 bg-white p-3">
            <div class="flex items-center justify-between text-[10px]">
              <span class="text-slate-400">用户隐向量</span>
              <span class="font-mono text-slate-600">[0.12, -0.84, 0.33 …]</span>
            </div>
            <div class="mt-2 flex items-center justify-between text-[10px]">
              <span class="text-slate-400">推理设备</span>
              <span class="font-mono text-slate-600">Mock / CPU</span>
            </div>
            <div class="mt-2 flex items-center justify-between text-[10px]">
              <span class="text-slate-400">负采样策略</span>
              <span class="font-mono text-slate-600">4 negatives</span>
            </div>
          </div>

          <el-button
            type="primary"
            class="!mt-5 !h-10 !w-full !rounded-xl !text-xs"
            :loading="isLoading"
            @click="runInference"
          >
            <el-icon v-if="!isLoading" class="mr-1.5"><MagicStick /></el-icon>
            {{ isLoading ? '正在执行 NCF 推理…' : '运行推荐推理' }}
          </el-button>
          <p class="mt-2.5 text-center text-[9px] leading-4 text-slate-400">
            点击后通过 Mock API 生成推荐结果，用于交互演示
          </p>
        </section>

        <section class="ncf-result">
          <div v-if="!result && !isLoading && !errorMessage" class="ncf-empty">
            <div class="relative h-24 w-36" aria-hidden="true">
              <svg viewBox="0 0 180 110" fill="none" class="h-full w-full">
                <g stroke="#CBD5E1" stroke-width="1">
                  <path d="M25 30H78M25 30H78M25 30H78" opacity="0.25" />
                  <path d="M25 30L78 55M25 55L78 30M25 55L78 55M25 55L78 80" />
                  <path d="M25 80L78 55M25 80L78 80" />
                </g>
                <g stroke="#94A3B8" stroke-width="1">
                  <path d="M102 30L153 20M102 30L153 55M102 30L153 90" />
                  <path d="M102 55L153 20M102 55L153 55M102 55L153 90" />
                  <path d="M102 80L153 20M102 80L153 55M102 80L153 90" />
                </g>
                <g fill="#6366F1">
                  <circle cx="25" cy="30" r="5" />
                  <circle cx="25" cy="55" r="5" />
                  <circle cx="25" cy="80" r="5" />
                </g>
                <g fill="#22D3EE">
                  <circle cx="78" cy="30" r="6" />
                  <circle cx="78" cy="55" r="6" />
                  <circle cx="78" cy="80" r="6" />
                </g>
                <g fill="#94A3B8">
                  <circle cx="102" cy="30" r="4" />
                  <circle cx="102" cy="55" r="4" />
                  <circle cx="102" cy="80" r="4" />
                </g>
                <g fill="#F59E0B">
                  <circle cx="153" cy="20" r="3.5" />
                  <circle cx="153" cy="55" r="4.5" />
                  <circle cx="153" cy="90" r="3.5" />
                </g>
              </svg>
            </div>
            <h3 class="mt-4 text-sm font-semibold text-slate-700">等待生成个性化推荐</h3>
            <p class="mt-1.5 max-w-xs text-center text-[11px] leading-5 text-slate-400">
              选择一位学习者并运行推理，查看 NeuMF 对潜在交互的打分与推荐理由。
            </p>
            <div class="mt-5 flex flex-wrap justify-center gap-1.5">
              <span class="ncf-feature-chip">神经协同过滤</span>
              <span class="ncf-feature-chip">用户—物品交互</span>
              <span class="ncf-feature-chip">Top-N 排序</span>
            </div>
          </div>

          <div v-else-if="isLoading" class="py-2">
            <div class="flex items-center gap-3 rounded-xl border border-indigo-100 bg-indigo-50/60 p-3">
              <span class="relative flex h-8 w-8 items-center justify-center">
                <span class="absolute h-8 w-8 animate-ping rounded-full bg-indigo-300/30" />
                <el-icon class="relative animate-spin text-indigo-500" :size="16">
                  <Refresh />
                </el-icon>
              </span>
              <div>
                <p class="text-[11px] font-medium text-indigo-700">正在计算用户与资源的隐向量相似度</p>
                <p class="mt-0.5 text-[9px] text-indigo-400">Mock inference · 预计 1.2s</p>
              </div>
            </div>
            <div class="mt-4 space-y-2.5">
              <div v-for="index in topK" :key="index" class="rounded-xl border border-slate-100 p-3">
                <div class="flex items-center gap-3">
                  <div class="skeleton h-7 w-7 rounded-lg" />
                  <div class="flex-1">
                    <div class="skeleton h-3 w-2/5" />
                    <div class="skeleton mt-2 h-2 w-3/5" />
                  </div>
                  <div class="skeleton h-2 w-16" />
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="errorMessage" class="ncf-error">
            <div class="grid h-11 w-11 place-items-center rounded-xl bg-rose-50 text-rose-500">
              <el-icon :size="22"><WarningFilled /></el-icon>
            </div>
            <h3 class="mt-3 text-sm font-semibold text-slate-700">推理失败</h3>
            <p class="mt-1.5 max-w-sm text-center text-[11px] text-slate-400">{{ errorMessage }}</p>
            <el-button class="!mt-4" plain size="small" @click="runInference">重新运行</el-button>
          </div>

          <div v-else-if="result" class="ncf-results">
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div class="flex items-center gap-2">
                  <span class="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  <p class="text-[11px] font-semibold text-slate-700">
                    已为 {{ result.user.name }} 生成 {{ result.recommendations.length }} 条推荐
                  </p>
                </div>
                <p class="mt-1 text-[9px] text-slate-400">
                  {{ result.modelVersion }} · 依据兴趣标签与近期学习行为
                </p>
              </div>
              <div class="flex items-center gap-1.5">
                <span class="ncf-metric-chip">
                  <el-icon :size="10"><Timer /></el-icon>
                  {{ formatDuration(result.latencyMs) }}
                </span>
                <span class="ncf-metric-chip">
                  <el-icon :size="10"><TrendCharts /></el-icon>
                  NeuMF
                </span>
                <button
                  type="button"
                  class="grid h-6 w-6 place-items-center rounded-md text-slate-400 transition hover:bg-slate-100 hover:text-indigo-500"
                  aria-label="重新运行推荐"
                  @click="runInference"
                >
                  <el-icon :size="12"><Refresh /></el-icon>
                </button>
              </div>
            </div>

            <div class="mt-3 space-y-2.5">
              <article
                v-for="item in result.recommendations"
                :key="item.item.id"
                class="group rounded-xl border p-3 transition"
                :class="
                  item.rank === 1
                    ? 'border-indigo-200 bg-indigo-50/40 shadow-[0_8px_30px_-20px_rgba(79,70,229,0.5)]'
                    : 'border-slate-100 hover:border-slate-200 hover:bg-slate-50/50'
                "
              >
                <div class="flex items-start gap-3">
                  <span
                    class="grid h-7 w-7 shrink-0 place-items-center rounded-lg text-[10px] font-bold"
                    :class="
                      item.rank === 1
                        ? 'bg-indigo-600 text-white shadow-md shadow-indigo-200'
                        : 'bg-slate-100 text-slate-500'
                    "
                  >
                    {{ item.rank }}
                  </span>
                  <div class="min-w-0 flex-1">
                    <div class="flex flex-wrap items-center gap-2">
                      <h4 class="truncate text-[12px] font-semibold text-slate-800">
                        {{ item.item.title }}
                      </h4>
                      <span class="rounded border border-slate-200 bg-white px-1.5 py-px text-[8px] text-slate-400">
                        {{ item.item.type }}
                      </span>
                      <span class="text-[8px] text-slate-400">{{ item.item.category }}</span>
                    </div>
                    <p class="mt-1 text-[10px] leading-4 text-slate-500">{{ item.reason }}</p>
                    <div class="mt-2 flex items-center gap-2">
                      <div class="h-1 flex-1 overflow-hidden rounded-full bg-slate-100">
                        <div
                          class="h-full rounded-full bg-gradient-to-r from-indigo-400 to-cyan-400 transition-all duration-700"
                          :style="{ width: `${item.score * 100}%` }"
                        />
                      </div>
                      <span class="w-10 text-right font-mono text-[9px] text-slate-400">
                        {{ item.score.toFixed(3) }}
                      </span>
                    </div>
                  </div>
                </div>
              </article>
            </div>

            <div class="mt-4 flex items-center gap-2 rounded-lg bg-slate-50 px-3 py-2">
              <el-icon :size="12" class="text-slate-400"><User /></el-icon>
              <p class="text-[9px] leading-4 text-slate-400">
                近期行为：{{ result.user.recent.join(' · ') }}
              </p>
            </div>
          </div>
        </section>
      </div>

      <footer class="flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 bg-white px-6 py-3">
        <p class="text-[9px] text-slate-400">
          NCF 推荐为附属能力演示，不参与 RAG 检索与回答生成。
        </p>
        <p class="font-mono text-[9px] text-slate-300">mock://recommend/ncf · v0.1</p>
      </footer>
    </div>
  </el-dialog>
</template>

<style>
.ncf-demo-dialog {
  max-width: 94vw;
  padding: 0 !important;
}

.ncf-demo-dialog .el-dialog__header {
  display: none;
}

.ncf-demo-dialog .el-dialog__body {
  padding: 0;
}

.ncf-demo {
  overflow: hidden;
  border-radius: 22px;
  background: #fff;
}

.ncf-hero {
  position: relative;
  overflow: hidden;
  padding: 22px 26px 20px;
  background: #0a1020;
}

.ncf-body {
  display: grid;
  grid-template-columns: 286px minmax(0, 1fr);
  min-height: 452px;
}

.ncf-config {
  padding: 22px;
  border-right: 1px solid #eef1f6;
  background: #fafbfd;
}

.ncf-result {
  min-width: 0;
  padding: 22px 24px;
}

.ncf-step-label {
  display: flex;
  align-items: center;
  gap: 7px;
  color: #64748b;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.05em;
}

.ncf-step-label span {
  display: grid;
  width: 17px;
  height: 17px;
  place-items: center;
  color: #6366f1;
  background: #eef2ff;
  border-radius: 5px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 8px;
}

.ncf-user-card {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  color: inherit;
  background: #fff;
  border: 1px solid #edf0f5;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.18s ease;
}

.ncf-user-card:hover:not(:disabled) {
  border-color: #d7dce8;
  transform: translateY(-1px);
}

.ncf-user-card.is-active {
  background: #fff;
  border-color: #c7d2fe;
  box-shadow: 0 6px 20px -14px rgba(79, 70, 229, 0.5);
}

.ncf-user-card:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.ncf-feature-chip {
  padding: 3px 8px;
  color: #64748b;
  background: #f8fafc;
  border: 1px solid #eef1f6;
  border-radius: 6px;
  font-size: 9px;
}

.ncf-metric-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  color: #64748b;
  background: #f8fafc;
  border: 1px solid #edf0f5;
  border-radius: 5px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 8px;
}

.ncf-empty,
.ncf-error {
  display: flex;
  min-height: 400px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

@media (max-width: 760px) {
  .ncf-body {
    display: block;
  }

  .ncf-config {
    border-right: 0;
    border-bottom: 1px solid #eef1f6;
  }

  .ncf-result {
    padding: 20px 16px;
  }

  .ncf-empty {
    min-height: 300px;
  }
}
</style>
