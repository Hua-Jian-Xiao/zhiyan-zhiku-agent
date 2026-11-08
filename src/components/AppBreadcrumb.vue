<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const title = computed(() =>
  typeof route.meta.title === 'string' ? route.meta.title : 'Agent 工作台',
)
</script>

<template>
  <nav class="flex min-w-0 items-center gap-2.5" aria-label="面包屑导航">
    <router-link
      :to="{ name: 'workspace' }"
      class="font-mono text-[8px] uppercase tracking-[0.18em] text-[#8d806e] transition hover:text-[#7d302f]"
    >
      智研知库
    </router-link>
    <span class="text-[#c1b4a0]">/</span>
    <span class="font-mono text-[8px] uppercase tracking-[0.18em] text-[#a29582]">工作区</span>
    <span class="text-[#c1b4a0]">/</span>
    <span class="truncate font-serif text-[12px] font-medium text-[#3f3830]">{{ title }}</span>
  </nav>
</template>
