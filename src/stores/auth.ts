import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { mockLogin } from '@/services/mockApi'
import type { AuthSession } from '@/types'
import { readStorage, removeStorage, writeStorage } from '@/utils/storage'

const STORAGE_KEY = 'zhiyan.auth.session'

export const useAuthStore = defineStore('auth', () => {
  const session = ref<AuthSession | null>(readStorage<AuthSession | null>(STORAGE_KEY, null))
  const isLoading = ref(false)

  const isAuthenticated = computed(() => Boolean(session.value?.token))
  const user = computed(() => session.value?.user ?? null)
  const displayName = computed(() => session.value?.user.displayName ?? '访客')

  async function login(account: string, password: string): Promise<void> {
    isLoading.value = true
    try {
      const nextSession = await mockLogin(account, password)
      session.value = nextSession
      writeStorage(STORAGE_KEY, nextSession)
    } finally {
      isLoading.value = false
    }
  }

  function logout(): void {
    session.value = null
    removeStorage(STORAGE_KEY)
  }

  return {
    session,
    isLoading,
    isAuthenticated,
    user,
    displayName,
    login,
    logout,
  }
})
