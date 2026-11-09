<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowRight, Menu } from '@element-plus/icons-vue'
import AppSidebar from '@/components/AppSidebar.vue'
import AppBreadcrumb from '@/components/AppBreadcrumb.vue'
import BrandMark from '@/components/BrandMark.vue'
import { useSystemStore } from '@/stores/system'
import { useRagStore } from '@/stores/rag'

const route = useRoute()
const systemStore = useSystemStore()
const ragStore = useRagStore()
const mobileSidebarOpen = ref(false)
let statusTimer: ReturnType<typeof setInterval> | null = null

const databaseStatus = computed(() => {
  if (systemStore.isLoading) {
    return {
      label: '状态同步中',
      dot: 'bg-[#c9a25a] animate-pulse',
      text: 'text-[#a58b62]',
    }
  }
  if (systemStore.error) {
    return {
      label: '状态异常',
      dot: 'bg-[#9a463c]',
      text: 'text-[#9a463c]',
    }
  }
  if (!systemStore.health) {
    return {
      label: '状态检查中',
      dot: 'bg-[#c9a25a] animate-pulse',
      text: 'text-[#a58b62]',
    }
  }
  if (systemStore.health.database === 'ok') {
    return {
      label: '知识库在线',
      dot: 'bg-[#5c7a60]',
      text: 'text-[#8d806e]',
    }
  }
  return {
    label: '数据库离线',
    dot: 'bg-[#9a463c]',
    text: 'text-[#9a463c]',
  }
})

async function refreshSystemStatus(showToast = true): Promise<void> {
  if (systemStore.isLoading) return
  try {
    await systemStore.loadStats()
    if (showToast) {
      if (systemStore.health?.database === 'ok') {
        ElMessage.success('知识库状态已刷新')
      } else {
        ElMessage.warning('知识库连接异常，请检查后端服务')
      }
    }
  } catch {
    if (showToast) ElMessage.error('知识库状态刷新失败')
  }
}

watch(
  () => route.fullPath,
  () => {
    mobileSidebarOpen.value = false
  },
)

onMounted(() => {
  void refreshSystemStatus(false)
  void ragStore.loadFromServer().catch(() => {
    // The locally cached retrieval configuration remains usable if offline.
  })
  statusTimer = window.setInterval(() => {
    if (!document.hidden) void refreshSystemStatus(false)
  }, 30000)
})

onBeforeUnmount(() => {
  if (statusTimer) {
    window.clearInterval(statusTimer)
    statusTimer = null
  }
})
</script>

<template>
  <div class="flex h-screen w-full overflow-hidden bg-[#eee8dc]">
    <div class="hidden w-[248px] shrink-0 lg:block">
      <AppSidebar />
    </div>

    <Transition name="fade">
      <div
        v-if="mobileSidebarOpen"
        class="fixed inset-0 z-40 bg-slate-950/55 backdrop-blur-[2px] lg:hidden"
        aria-hidden="true"
        @click="mobileSidebarOpen = false"
      />
    </Transition>

    <Transition name="drawer">
      <div
        v-if="mobileSidebarOpen"
        class="fixed inset-y-0 left-0 z-50 w-[268px] shadow-2xl lg:hidden"
      >
        <AppSidebar />
      </div>
    </Transition>

    <div class="flex min-w-0 flex-1 flex-col">
      <header
        class="flex h-14 shrink-0 items-center justify-between border-b border-[#3a3025] bg-[#17130f] px-4 lg:hidden"
      >
        <div class="flex items-center gap-3">
          <button
            type="button"
            class="grid h-8 w-8 place-items-center border border-[#443a2c] text-[#c9bca9]"
            aria-label="打开导航"
            @click="mobileSidebarOpen = true"
          >
            <el-icon :size="16"><Menu /></el-icon>
          </button>
          <BrandMark compact />
        </div>
        <span
          class="border border-[#4c5f4e] px-2 py-1 text-[10px]"
          :class="systemStore.health?.database === 'ok' ? 'text-[#9dbaa2]' : 'text-[#d3a28e]'"
        >
          {{ systemStore.health?.database === 'ok' ? '服务在线' : '服务离线' }}
        </span>
      </header>

      <header
        class="hidden h-[54px] shrink-0 items-center justify-between border-b-[3px] border-double border-[#c3b5a0] bg-[#fbf7ee] px-6 lg:flex"
      >
        <AppBreadcrumb />
        <div class="flex shrink-0 items-center gap-4 text-[11px] text-[#8d806e]">
          <button
            type="button"
            class="flex items-center gap-2 outline-none"
            :class="[databaseStatus.text, systemStore.isLoading ? 'cursor-wait' : 'cursor-pointer']"
            :aria-label="`${databaseStatus.label}，点击刷新知识库状态`"
            @click="refreshSystemStatus(true)"
          >
            <span class="h-1.5 w-1.5 rounded-full" :class="databaseStatus.dot" />
            {{ databaseStatus.label }}
          </button>
          <span class="h-3.5 w-px bg-[#d8cebd]" />
          <router-link
            v-if="systemStore.health?.llm.configured"
            :to="{ name: 'workspace' }"
            class="inline-flex items-center gap-1 transition hover:text-[#7d302f]"
            title="打开内置 AI 工作台"
          >
            {{ systemStore.llmLabel }}
            <el-icon :size="10"><ArrowRight /></el-icon>
          </router-link>
          <span v-else>{{ systemStore.llmLabel }}</span>
        </div>
      </header>

      <main class="min-h-0 min-w-0 flex-1 overflow-hidden">
        <router-view v-slot="{ Component, route: currentRoute }">
          <Transition name="page-fade" mode="out-in">
            <component :is="Component" :key="currentRoute.path" />
          </Transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<style scoped>
.drawer-enter-active,
.drawer-leave-active {
  transition: transform 0.25s cubic-bezier(0.22, 1, 0.36, 1);
}

.drawer-enter-from,
.drawer-leave-to {
  transform: translateX(-100%);
}
</style>
