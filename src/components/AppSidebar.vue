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
    class="relative flex h-full w-full flex-col overflow-hidden border-r border-[#392f25] bg-[#17130f] text-[#d9cdb9]"
  >
    <div class="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
      <div class="absolute inset-0 dot-grid opacity-[0.035]" />
      <div class="absolute inset-y-0 right-0 w-px bg-gradient-to-b from-transparent via-[#9a463c]/40 to-transparent" />
      <div class="absolute left-5 top-0 h-24 w-px bg-[#9a463c]/50" />
    </div>

    <div class="relative px-5 pb-4 pt-6">
      <BrandMark />
      <div class="mt-6 border-t border-[#3d3328] pt-4">
        <div class="flex items-center justify-between">
          <p class="folio !text-[#7f7260]">CURRENT ISSUE / 知识空间</p>
          <span class="flex items-center gap-1.5 font-mono text-[7px] text-[#7f7260]">
            <span class="h-1 w-1 rounded-full bg-[#7a987e]" />
            ONLINE
          </span>
        </div>
        <div class="mt-2.5 flex items-center gap-2.5">
          <span class="grid h-6 w-6 shrink-0 place-items-center border border-[#4c4033] text-[#b8a389]">
            <el-icon :size="11"><Grid /></el-icon>
          </span>
          <div class="min-w-0 flex-1">
            <p class="truncate text-[10px] font-medium text-[#e3d8c7]">计算机学科知识空间</p>
            <p class="mt-0.5 font-mono text-[7.5px] tracking-wide text-[#7f7260]">
              8 COURSES · 326 CONCEPTS
            </p>
          </div>
        </div>
      </div>
    </div>

    <nav class="relative min-h-0 flex-1 overflow-y-auto pb-3 scroll-thin">
      <p class="mb-1.5 px-5 font-mono text-[7.5px] font-medium uppercase tracking-[0.24em] text-[#6d6254]">
        目录 / Index
      </p>
      <div>
        <router-link
          v-for="(item, index) in navItems"
          :key="item.name"
          :to="{ name: item.name }"
          class="group relative flex items-center gap-2.5 border-b border-[#2b241c] px-5 py-2.5 transition-colors duration-200"
          :class="
            activeName === item.name
              ? 'bg-[#221c16] text-[#f5ecdc]'
              : 'text-[#9d9180] hover:bg-white/[0.025] hover:text-[#d9cdb9]'
          "
        >
          <span
            v-if="activeName === item.name"
            class="absolute bottom-0 left-0 top-0 w-[2px] bg-[#9a463c]"
          />
          <span
            class="w-4 shrink-0 font-mono text-[7.5px] tabular-nums transition-colors"
            :class="activeName === item.name ? 'text-[#c58a77]' : 'text-[#5f5549]'"
          >
            {{ String(index + 1).padStart(2, '0') }}
          </span>
          <el-icon
            :size="13"
            class="shrink-0 transition-colors"
            :class="activeName === item.name ? 'text-[#c58a77]' : 'text-[#665b4d] group-hover:text-[#a79a88]'"
          >
            <component :is="item.icon" />
          </el-icon>
          <span class="min-w-0 flex-1">
            <span class="block truncate text-[11px] font-medium">{{ item.label }}</span>
            <span
              class="mt-0.5 block truncate text-[8px]"
              :class="activeName === item.name ? 'text-[#8f8170]' : 'text-[#5f5549] group-hover:text-[#7f7260]'"
            >
              {{ item.description }}
            </span>
          </span>
          <ArrowRight
            v-if="activeName === item.name"
            class="h-3 w-3 shrink-0 text-[#a75d50]"
          />
        </router-link>
      </div>

      <p class="mb-1.5 mt-6 px-5 font-mono text-[7.5px] font-medium uppercase tracking-[0.24em] text-[#6d6254]">
        附录 / Annex
      </p>
      <div class="px-4">
        <button
          type="button"
          class="group relative w-full border border-[#3b3126] bg-[#1e1914] p-3 text-left transition duration-200 hover:border-[#6b5140] hover:bg-[#241e18]"
          @click="emit('open-ncf')"
        >
          <span class="absolute inset-x-0 top-0 h-[2px] bg-[#9a463c]/55" />
          <div class="flex items-start justify-between gap-2">
            <span class="grid h-7 w-7 place-items-center border border-[#4b4032] text-[#c39e40]">
              <el-icon :size="13"><MagicStick /></el-icon>
            </span>
            <span class="border border-[#6d5225]/60 px-1.5 py-0.5 font-mono text-[6.5px] font-medium tracking-[0.16em] text-[#c39e40]">
              ANNEX
            </span>
          </div>
          <p class="relative mt-3 font-serif text-[12px] font-medium text-[#eee2d1]">NCF推荐Demo</p>
          <p class="relative mt-1 text-[8.5px] leading-4 text-[#857867]">
            神经协同过滤推荐弹窗 · 独立附属演示
          </p>
          <span
            class="relative mt-3 inline-flex items-center gap-1 font-mono text-[7.5px] tracking-[0.08em] text-[#b17a68] transition group-hover:text-[#d3a28e]"
          >
            OPEN SUPPLEMENT
            <el-icon :size="9"><ArrowRight /></el-icon>
          </span>
        </button>
      </div>
    </nav>

    <div class="relative border-t border-[#31291f] px-4 pb-3 pt-3.5">
      <div class="flex items-center gap-2.5">
        <div class="grid h-9 w-9 shrink-0 place-items-center border border-[#5c4c3a] bg-[#292118] font-serif text-[14px] text-[#e8dcc9]">
          {{ authStore.user?.avatarText ?? '访' }}
        </div>
        <div class="min-w-0 flex-1">
          <p class="truncate text-[10.5px] font-medium text-[#e3d8c7]">
            {{ authStore.user?.displayName ?? '访客' }}
          </p>
          <p class="mt-0.5 truncate font-mono text-[7.5px] text-[#7f7260]">
            {{ authStore.user?.role ?? '未登录' }}
          </p>
        </div>
        <el-tooltip content="退出登录" placement="top" :show-after="300">
          <button
            type="button"
            class="grid h-7 w-7 place-items-center border border-transparent text-[#756958] transition hover:border-[#3b3126] hover:text-[#c8baa6]"
            aria-label="退出登录"
            @click="handleLogout"
          >
            <el-icon :size="13"><SwitchButton /></el-icon>
          </button>
        </el-tooltip>
      </div>
      <div class="mt-3 flex items-center justify-between border-t border-[#2b241c] pt-2 font-mono text-[6.5px] tracking-[0.08em] text-[#5b5145]">
        <span>MOCK SSE · LOCAL EDITION</span>
        <span>VOL.01 / 2026</span>
      </div>
    </div>
  </aside>
</template>
