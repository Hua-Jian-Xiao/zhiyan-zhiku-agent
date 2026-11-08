<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Menu } from '@element-plus/icons-vue'
import AppSidebar from '@/components/AppSidebar.vue'
import AppBreadcrumb from '@/components/AppBreadcrumb.vue'
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
  <div class="flex h-screen w-full overflow-hidden bg-[#eee8dc]">
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
          class="border border-[#4c5f4e] px-2 py-0.5 font-mono text-[7px] tracking-[0.1em] text-[#9dbaa2]"
        >
          AGENT ONLINE
        </span>
      </header>

      <header
        class="hidden h-[54px] shrink-0 items-center justify-between border-b-[3px] border-double border-[#c3b5a0] bg-[#fbf7ee] px-6 lg:flex"
      >
        <div class="flex min-w-0 items-center gap-5">
          <AppBreadcrumb />
          <span class="hidden h-4 w-px bg-[#d8cebd] xl:block" />
          <span class="hidden font-mono text-[7px] uppercase tracking-[0.18em] text-[#a29582] xl:block">
            Zhiyan Journal of Computational Studies
          </span>
        </div>
        <div class="flex shrink-0 items-center gap-3 font-mono text-[7px] tracking-[0.08em] text-[#9b8f7d]">
          <span class="hidden items-center gap-1.5 sm:flex">
            <span class="h-1 w-1 rounded-full bg-[#5c7a60]" />
            INDEX HEALTHY
          </span>
          <span class="h-3 w-px bg-[#d8cebd]" />
          <span class="hidden md:inline">VOL. 01 · NO. 07 / NOV 2026</span>
          <span class="border border-[#d0c2ad] px-1.5 py-0.5 text-[#7d302f]">MOCK SSE</span>
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
