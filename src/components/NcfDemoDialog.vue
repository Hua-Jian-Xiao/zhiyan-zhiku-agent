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
import { mockUsers } from '@/mock'
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
          <div class="absolute inset-0 dot-grid opacity-[0.04]" />
          <span class="absolute -right-2 -top-8 font-serif text-[130px] leading-none text-[#9a463c]/15">§</span>
        </div>

        <div class="relative flex items-start justify-between gap-4">
          <div>
            <div class="flex items-center gap-2">
              <span class="border border-[#6d5225]/60 px-2 py-0.5 font-mono text-[8px] font-medium tracking-[0.16em] text-[#c39e40]">
                ANNEX / SUPPLEMENT
              </span>
              <span class="font-mono text-[8px] tracking-[0.04em] text-[#817463]">独立实验功能 · 不进入核心 RAG 流程</span>
            </div>
            <div class="mt-4 flex items-center gap-3">
              <span class="grid h-11 w-11 place-items-center border border-[#5a4b3a] bg-[#241e18] text-[#c39e40]">
                <el-icon :size="21"><MagicStick /></el-icon>
              </span>
              <div>
                <h2 class="font-serif text-[23px] font-medium tracking-[-0.01em] text-[#f4ead9]">NCF推荐Demo</h2>
                <p class="mt-1 font-mono text-[8px] tracking-[0.04em] text-[#9d8f7c]">
                  NEURAL COLLABORATIVE FILTERING · 神经协同过滤推荐演示
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
                      ? 'border-[#7d302f] bg-[#7d302f] shadow-[0_0_0_3px_rgba(125,48,47,0.1)]'
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
                <g stroke="#CBBFAE" stroke-width="1">
                  <path d="M25 30L78 30M25 30L78 55M25 30L78 80" />
                  <path d="M25 55L78 30M25 55L78 55M25 55L78 80" />
                  <path d="M25 80L78 30M25 80L78 55M25 80L78 80" />
                </g>
                <g stroke="#B5A995" stroke-width="1">
                  <path d="M102 30L153 20M102 30L153 55M102 30L153 90" />
                  <path d="M102 55L153 20M102 55L153 55M102 55L153 90" />
                  <path d="M102 80L153 20M102 80L153 55M102 80L153 90" />
                </g>
                <g fill="#7D302F">
                  <circle cx="25" cy="30" r="5" />
                  <circle cx="25" cy="55" r="5" />
                  <circle cx="25" cy="80" r="5" />
                </g>
                <g fill="#3D5266">
                  <circle cx="78" cy="30" r="6" />
                  <circle cx="78" cy="55" r="6" />
                  <circle cx="78" cy="80" r="6" />
                </g>
                <g fill="#B5A995">
                  <circle cx="102" cy="30" r="4" />
                  <circle cx="102" cy="55" r="4" />
                  <circle cx="102" cy="80" r="4" />
                </g>
                <g fill="#A37B2B">
                  <circle cx="153" cy="20" r="3.5" />
                  <circle cx="153" cy="55" r="4.5" />
                  <circle cx="153" cy="90" r="3.5" />
                </g>
              </svg>
            </div>
            <h3 class="mt-4 text-sm font-semibold text-slate-700">等待生成推荐</h3>
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
                  {{ result.modelVersion }} · 依据兴趣标签与近期行为
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
                class="rounded-xl border p-3 transition"
                :class="
                  item.rank === 1
                    ? 'border-[#c99f98] bg-[#fbf1ec]'
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
                          class="h-full bg-[#9a463c] transition-all duration-700"
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
  border-radius: 2px;
  background: #fffdf8;
}

.ncf-hero {
  position: relative;
  overflow: hidden;
  padding: 22px 26px 20px;
  background: #17130f;
  border-bottom: 1px solid #3d3328;
}

.ncf-body {
  display: grid;
  grid-template-columns: 286px minmax(0, 1fr);
  min-height: 452px;
}

.ncf-config {
  padding: 22px;
  border-right: 1px solid #ddd2c1;
  background: #f8f3e9;
}

.ncf-result {
  min-width: 0;
  padding: 22px 24px;
}

.ncf-step-label {
  display: flex;
  align-items: center;
  gap: 7px;
  color: #6f6456;
  font-family: var(--app-mono);
  font-size: 8px;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.ncf-step-label span {
  display: grid;
  width: 17px;
  height: 17px;
  place-items: center;
  color: #7d302f;
  background: #f4e8e2;
  border: 1px solid #d8b8b1;
  border-radius: 0;
  font-family: var(--app-mono);
  font-size: 7px;
}

.ncf-user-card {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  color: inherit;
  background: #fffdf8;
  border: 1px solid #ded4c4;
  border-radius: 0;
  cursor: pointer;
  transition: all 0.18s ease;
}

.ncf-user-card:hover:not(:disabled) {
  border-color: #b9ab97;
}

.ncf-user-card.is-active {
  background: #fffdf8;
  border-color: #c99f98;
  box-shadow: inset 2px 0 #7d302f;
}

.ncf-user-card:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.ncf-feature-chip {
  padding: 3px 8px;
  color: #8d806e;
  background: #fffdf8;
  border: 1px solid #ded4c4;
  border-radius: 0;
  font-family: var(--app-mono);
  font-size: 8px;
}

.ncf-metric-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  color: #8d806e;
  background: #f8f3e9;
  border: 1px solid #ded4c4;
  border-radius: 0;
  font-family: var(--app-mono);
  font-size: 7.5px;
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
