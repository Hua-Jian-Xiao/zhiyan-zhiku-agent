<script setup lang="ts">
import type { Component } from 'vue'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowRight,
  ChatDotRound,
  Collection,
  DataAnalysis,
  Grid,
  MagicStick,
  Share,
  SwitchButton,
} from '@element-plus/icons-vue'
import BrandMark from '@/components/BrandMark.vue'
import { useAuthStore } from '@/stores/auth'

interface NavItem {
  name: string
  label: string
  description: string
  icon: Component
}

const emit = defineEmits<{
  (event: 'open-ncf'): void
}>()

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const navItems: NavItem[] = [
  {
    name: 'workspace',
    label: 'Agent 工作台',
    description: '与知识库对话',
    icon: ChatDotRound,
  },
  {
    name: 'knowledge',
    label: '知识库管理',
    description: '语料与检索配置',
    icon: Collection,
  },
  {
    name: 'rag-debug',
    label: 'RAG 检索调试',
    description: '召回效果可视化',
    icon: DataAnalysis,
  },
  {
    name: 'graph',
    label: '知识图谱',
    description: '课程依赖关系',
    icon: Share,
  },
]

const activeName = computed(() => String(route.name ?? ''))

async function handleLogout(): Promise<void> {
  try {
    await ElMessageBox.confirm('退出后本地会话仍会保留，下次登录可继续查看。', '退出登录', {
      confirmButtonText: '退出登录',
      cancelButtonText: '继续使用',
      type: 'warning',
      customClass: 'zhiyan-confirm',
    })
  } catch {
    return
  }

  authStore.logout()
  ElMessage.success('已安全退出')
  await router.replace({ name: 'login' })
}
</script>

<template>
  <aside
    class="relative flex h-full w-full flex-col overflow-hidden border-r border-white/[0.04] bg-[#0a1020] text-slate-200"
  >
    <div class="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
      <div
        class="absolute -left-24 -top-24 h-64 w-64 rounded-full bg-indigo-500/20 blur-[80px]"
      />
      <div
        class="absolute -right-16 top-[38%] h-44 w-44 rounded-full bg-cyan-400/10 blur-[70px]"
      />
      <div class="absolute inset-0 dot-grid opacity-[0.05]" />
    </div>

    <div class="relative px-5 pb-5 pt-6">
      <BrandMark />
      <div
        class="mt-6 flex items-center gap-2.5 rounded-xl border border-white/[0.07] bg-white/[0.04] px-3 py-2.5"
      >
        <div class="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-white/[0.07]">
          <el-icon :size="14" class="text-indigo-300"><Grid /></el-icon>
        </div>
        <div class="min-w-0 flex-1">
          <p class="truncate text-[11px] font-medium text-slate-200">计算机学科知识空间</p>
          <p class="mt-0.5 text-[9px] tracking-wide text-slate-500">8 门课程 · 326 个知识点</p>
        </div>
        <span class="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
      </div>
    </div>

    <nav class="relative min-h-0 flex-1 overflow-y-auto px-3 pb-4 scroll-thin">
      <p class="mb-2 px-3 text-[9px] font-semibold uppercase tracking-[0.2em] text-slate-600">
        学习工作区
      </p>
      <div class="space-y-1">
        <router-link
          v-for="item in navItems"
          :key="item.name"
          :to="{ name: item.name }"
          class="group relative flex items-center gap-3 rounded-xl px-3 py-2.5 transition-all duration-200"
          :class="
            activeName === item.name
              ? 'bg-gradient-to-r from-indigo-500/[0.18] to-indigo-400/[0.04] text-white'
              : 'text-slate-400 hover:bg-white/[0.04] hover:text-slate-200'
          "
        >
          <span
            v-if="activeName === item.name"
            class="absolute -left-3 top-1/2 h-5 w-[2px] -translate-y-1/2 rounded-r-full bg-indigo-400"
          />
          <span
            class="grid h-8 w-8 shrink-0 place-items-center rounded-lg border transition-colors"
            :class="
              activeName === item.name
                ? 'border-indigo-400/25 bg-indigo-400/15 text-indigo-200'
                : 'border-white/[0.05] bg-white/[0.025] text-slate-500 group-hover:text-slate-300'
            "
          >
            <el-icon :size="16"><component :is="item.icon" /></el-icon>
          </span>
          <span class="min-w-0 flex-1">
            <span class="block truncate text-[12px] font-medium">{{ item.label }}</span>
            <span class="mt-0.5 block truncate text-[9px] text-slate-600 group-hover:text-slate-500">
              {{ item.description }}
            </span>
          </span>
          <ArrowRight
            v-if="activeName === item.name"
            class="h-3 w-3 shrink-0 text-indigo-300/70"
          />
        </router-link>
      </div>

      <p class="mb-2 mt-6 px-3 text-[9px] font-semibold uppercase tracking-[0.2em] text-slate-600">
        实验功能
      </p>
      <button
        type="button"
        class="group relative w-full overflow-hidden rounded-2xl border border-white/[0.08] bg-white/[0.035] p-3.5 text-left transition duration-200 hover:border-indigo-400/30 hover:bg-white/[0.06]"
        @click="emit('open-ncf')"
      >
        <span
          class="pointer-events-none absolute -right-8 -top-8 h-24 w-24 rounded-full bg-cyan-400/10 blur-2xl transition group-hover:bg-cyan-400/20"
        />
        <div class="relative flex items-start justify-between gap-2">
          <span
            class="grid h-8 w-8 place-items-center rounded-lg border border-cyan-300/15 bg-cyan-400/10 text-cyan-300"
          >
            <el-icon :size="16"><MagicStick /></el-icon>
          </span>
          <span
            class="rounded-full border border-amber-300/20 bg-amber-300/10 px-2 py-0.5 text-[8px] font-semibold tracking-wider text-amber-200"
          >
            附属演示
          </span>
        </div>
        <p class="relative mt-3 text-[12px] font-medium text-slate-100">NCF 推荐 Demo</p>
        <p class="relative mt-1 text-[9px] leading-4 text-slate-500">
          基于神经协同过滤的个性化学习资源推荐
        </p>
        <span
          class="relative mt-3 inline-flex items-center gap-1 text-[9px] font-medium text-indigo-300/90 transition group-hover:text-indigo-200"
        >
          打开独立演示
          <el-icon :size="10"><ArrowRight /></el-icon>
        </span>
      </button>
    </nav>

    <div class="relative border-t border-white/[0.06] px-4 pb-4 pt-4">
      <div class="flex items-center gap-2.5">
        <div
          class="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-indigo-400 to-cyan-400 text-[12px] font-bold text-white shadow-lg shadow-indigo-950/40"
        >
          {{ authStore.user?.avatarText ?? '访' }}
        </div>
        <div class="min-w-0 flex-1">
          <p class="truncate text-[11px] font-medium text-slate-200">
            {{ authStore.user?.displayName ?? '访客' }}
          </p>
          <p class="mt-0.5 truncate text-[9px] text-slate-500">
            {{ authStore.user?.role ?? '未登录' }}
          </p>
        </div>
        <el-tooltip content="退出登录" placement="top" :show-after="300">
          <button
            type="button"
            class="grid h-7 w-7 place-items-center rounded-lg text-slate-500 transition hover:bg-white/[0.06] hover:text-slate-300"
            aria-label="退出登录"
            @click="handleLogout"
          >
            <el-icon :size="14"><SwitchButton /></el-icon>
          </button>
        </el-tooltip>
      </div>
      <div class="mt-3 flex items-center justify-between px-0.5 text-[8px] text-slate-700">
        <span>Mock SSE · Local workspace</span>
        <span>v0.1.0</span>
      </div>
    </div>
  </aside>
</template>
