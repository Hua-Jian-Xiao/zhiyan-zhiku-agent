<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Menu } from '@element-plus/icons-vue'
import AppSidebar from '@/components/AppSidebar.vue'
import BrandMark from '@/components/BrandMark.vue'
import NcfDemoDialog from '@/components/NcfDemoDialog.vue'

const route = useRoute()
const mobileSidebarOpen = ref(false)
const ncfDialogOpen = ref(false)

watch(
  () => route.fullPath,
  () => {
    mobileSidebarOpen.value = false
  },
)

function openNcfDemo(): void {
  mobileSidebarOpen.value = false
  ncfDialogOpen.value = true
}
</script>

<template>
  <div class="flex h-screen w-full overflow-hidden bg-[#f2f5f9]">
    <div class="hidden w-[248px] shrink-0 lg:block">
      <AppSidebar @open-ncf="openNcfDemo" />
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
        <AppSidebar @open-ncf="openNcfDemo" />
      </div>
    </Transition>

    <div class="flex min-w-0 flex-1 flex-col">
      <header
        class="flex h-14 shrink-0 items-center justify-between border-b border-white/[0.05] bg-[#0a1020] px-4 lg:hidden"
      >
        <div class="flex items-center gap-3">
          <button
            type="button"
            class="grid h-8 w-8 place-items-center rounded-lg border border-white/10 bg-white/[0.04] text-slate-300"
            aria-label="打开导航"
            @click="mobileSidebarOpen = true"
          >
            <el-icon :size="16"><Menu /></el-icon>
          </button>
          <BrandMark compact />
        </div>
        <span
          class="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2 py-0.5 text-[9px] text-emerald-300"
        >
          Agent 在线
        </span>
      </header>

      <main class="min-h-0 min-w-0 flex-1 overflow-hidden">
        <router-view v-slot="{ Component, route: currentRoute }">
          <Transition name="page-fade" mode="out-in">
            <component :is="Component" :key="currentRoute.path" />
          </Transition>
        </router-view>
      </main>
    </div>

    <NcfDemoDialog v-model="ncfDialogOpen" />
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
