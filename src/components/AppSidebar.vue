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
  Share,
  SwitchButton,
} from '@element-plus/icons-vue'
import BrandMark from '@/components/BrandMark.vue'
import { useAuthStore } from '@/stores/auth'
import { useSystemStore } from '@/stores/system'

interface NavItem {
  name: string
  label: string
  description: string
  icon: Component
}

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const systemStore = useSystemStore()

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

async function handleSwitchUser(): Promise<void> {
  const redirect = route.fullPath
  await authStore.logout()
  ElMessage.success('已退出当前账号，请登录其他账号')
  await router.replace({ name: 'login', query: { redirect } })
}

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

  await authStore.logout()
  ElMessage.success('已安全退出')
  await router.replace({ name: 'login' })
}

async function handleAccountCommand(command: string | number | object): Promise<void> {
  if (command === 'profile') {
    await router.push({ name: 'profile' })
    return
  }
  if (command === 'switch') {
    await handleSwitchUser()
    return
  }
  if (command === 'logout') {
    await handleLogout()
  }
}
</script>

<template>
  <aside
    class="relative flex h-full w-full flex-col overflow-hidden border-r border-[#392f25] bg-[#17130f] text-[#d9cdb9]"
  >
    <div class="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
      <div class="absolute inset-0 dot-grid opacity-[0.035]" />
      <div class="absolute inset-y-0 right-0 w-px bg-gradient-to-b from-transparent via-[#9a463c]/40 to-transparent" />
    </div>

    <div class="relative px-5 pb-4 pt-6">
      <BrandMark />
      <div class="mt-5 border-t border-[#3d3328] pt-4">
        <router-link
          :to="{ name: 'knowledge' }"
          class="group -mx-2 flex items-center gap-3 border border-transparent px-2 py-2 transition hover:border-[#3b3126] hover:bg-white/[0.035]"
          title="进入知识库管理"
        >
          <span class="grid h-8 w-8 shrink-0 place-items-center border border-[#4c4033] text-[#b8a389] transition group-hover:border-[#6b5140] group-hover:text-[#d9cbb6]">
            <el-icon :size="14"><Grid /></el-icon>
          </span>
          <div class="min-w-0 flex-1">
            <p class="truncate text-[13px] font-medium text-[#e3d8c7] transition group-hover:text-white">
              计算机学科知识空间
            </p>
            <p class="mt-1 text-[11px] text-[#9d9180]">
              {{ systemStore.stats?.courseCount ?? '—' }} 门课程 ·
              {{ systemStore.stats?.knowledgePointCount ?? '—' }} 个知识点
            </p>
          </div>
          <ArrowRight
            class="h-4 w-4 shrink-0 text-[#786b5a] transition group-hover:translate-x-0.5 group-hover:text-[#c58a77]"
          />
        </router-link>
      </div>
    </div>

    <nav class="relative min-h-0 flex-1 overflow-y-auto pb-3 scroll-thin">
      <p class="mb-2 px-5 text-[11px] font-medium tracking-[0.08em] text-[#8f8170]">学习导航</p>
      <div>
        <router-link
          v-for="item in navItems"
          :key="item.name"
          :to="{ name: item.name }"
          class="group relative flex items-center gap-3 border-b border-[#2b241c] px-5 py-3 transition-colors duration-200"
          :class="
            activeName === item.name
              ? 'bg-[#221c16] text-[#f5ecdc]'
              : 'text-[#a79a88] hover:bg-white/[0.025] hover:text-[#e3d8c7]'
          "
        >
          <span
            v-if="activeName === item.name"
            class="absolute bottom-0 left-0 top-0 w-[2px] bg-[#9a463c]"
          />
          <el-icon
            :size="16"
            class="shrink-0 transition-colors"
            :class="activeName === item.name ? 'text-[#c58a77]' : 'text-[#786b5a] group-hover:text-[#b8a389]'"
          >
            <component :is="item.icon" />
          </el-icon>
          <span class="block min-w-0 flex-1 truncate text-[13px] font-medium">{{ item.label }}</span>
          <ArrowRight
            v-if="activeName === item.name"
            class="h-3.5 w-3.5 shrink-0 text-[#a75d50]"
          />
        </router-link>
      </div>

      <div class="mx-4 mt-6 border-t border-[#31291f] pt-4 text-[11px] text-[#8f8170]">
        <router-link
          :to="{ name: 'workspace' }"
          class="flex cursor-pointer items-center justify-between transition hover:text-[#e3d8c7]"
          title="打开内置 AI 工作台"
        >
          <span class="inline-flex items-center gap-1">
            {{ systemStore.llmLabel }}
            <el-icon :size="9"><ArrowRight /></el-icon>
          </span>
          <span class="flex items-center gap-1.5">
            <span class="h-1.5 w-1.5 rounded-full" :class="systemStore.health?.database === 'ok' ? 'bg-[#7a987e]' : 'bg-[#9a463c]'" />
            {{ systemStore.health?.database === 'ok' ? '服务在线' : '服务离线' }}
          </span>
        </router-link>
      </div>
    </nav>

    <div class="relative border-t border-[#31291f] px-4 pb-4 pt-3.5">
      <div class="flex items-center gap-2.5">
        <div class="grid h-9 w-9 shrink-0 place-items-center overflow-hidden border border-[#5c4c3a] bg-[#292118] font-serif text-[14px] text-[#e8dcc9]">
          <img
            v-if="authStore.user?.avatarUrl"
            :src="authStore.user.avatarUrl"
            alt="用户头像"
            class="h-full w-full object-cover"
          />
          <span v-else>{{ authStore.user?.avatarText ?? '访' }}</span>
        </div>
        <div class="min-w-0 flex-1">
          <p class="truncate text-[12px] font-medium text-[#e3d8c7]">
            {{ authStore.user?.displayName ?? '访客' }}
          </p>
          <p class="mt-0.5 truncate text-[10px] text-[#8f8170]">
            {{ authStore.profileHeadline }}
          </p>
        </div>
        <el-dropdown
          trigger="click"
          placement="top-end"
          popper-class="zhiyan-account-menu"
          @command="handleAccountCommand"
        >
          <button
            type="button"
            class="grid h-7 w-7 place-items-center border border-transparent text-[#8f8170] transition hover:border-[#3b3126] hover:text-[#c8baa6]"
            aria-label="账户操作"
            title="账户操作"
          >
            <el-icon :size="14"><SwitchButton /></el-icon>
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人中心</el-dropdown-item>
              <el-dropdown-item command="switch" divided>切换用户</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
      <div class="mt-3 border-t border-[#2b241c] pt-2 text-[10px] text-[#786b5a]">
        服务端会话 · RAG 知识库已连接
      </div>
    </div>
  </aside>
</template>
