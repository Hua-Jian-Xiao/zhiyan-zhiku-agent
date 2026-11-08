<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const title = computed(() =>
  typeof route.meta.title === 'string' ? route.meta.title : 'Agent 工作台',
)
</script>

<template>
  <nav class="flex min-w-0 items-center gap-2 text-[11px]" aria-label="面包屑导航">
    <router-link
      :to="{ name: 'workspace' }"
      class="text-[#8d806e] transition hover:text-[#7d302f]"
    >
      智研知库
    </router-link>
    <span class="text-[#b5a995]">/</span>
    <span class="text-[#8d806e]">工作区</span>
    <span class="text-[#b5a995]">/</span>
    <span class="truncate font-medium text-[#3f3830]">{{ title }}</span>
  </nav>
</template>
