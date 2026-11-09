import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { AuthSession, ProfileUpdatePayload, UserProfile } from '@/types'
import {
  login as loginRequest,
  logout as logoutRequest,
  register as registerRequest,
  updateProfile as updateProfileRequest,
} from '@/services/api'
import { clearSession, readSession, writeSession } from '@/services/http'

export const useAuthStore = defineStore('auth', () => {
  const session = ref<AuthSession | null>(readSession())
  const isLoading = ref(false)

  const isAuthenticated = computed(() => Boolean(session.value?.token))
  const user = computed(() => session.value?.user ?? null)
  const displayName = computed(() => session.value?.user.displayName ?? '访客')
  const profileHeadline = computed(() => {
    const current = session.value?.user
    if (!current) return '未登录'
    const parts = [current.major, current.grade]
      .map((part) => (part || '').trim())
      .filter(Boolean)
    return parts.length ? parts.join(' · ') : current.role || '学习者'
  })

  function syncSession(next: AuthSession | null): void {
    session.value = next
  }

  if (typeof window !== 'undefined') {
    window.addEventListener('zhiyan:session-updated', (event) => {
      syncSession((event as CustomEvent<AuthSession>).detail)
    })
    window.addEventListener('zhiyan:session-cleared', () => syncSession(null))
  }

  async function login(account: string, password: string): Promise<void> {
    isLoading.value = true
    try {
      const nextSession = await loginRequest(account, password)
      session.value = nextSession
      writeSession(nextSession)
    } finally {
      isLoading.value = false
    }
  }

  async function register(
    account: string,
    password: string,
    displayName?: string,
  ): Promise<void> {
    isLoading.value = true
    try {
      const nextSession = await registerRequest({
        username: account,
        password,
        displayName: displayName?.trim() || undefined,
      })
      session.value = nextSession
      writeSession(nextSession)
    } finally {
      isLoading.value = false
    }
  }

  async function logout(): Promise<void> {
    try {
      if (session.value?.token) await logoutRequest()
    } catch {
      // Local cleanup must succeed even if the API session is already gone.
    } finally {
      session.value = null
      clearSession()
    }
  }

  async function updateProfile(payload: ProfileUpdatePayload): Promise<UserProfile> {
    const result = await updateProfileRequest(payload)
    if (session.value) {
      const next = { ...session.value, user: result.user }
      session.value = next
      writeSession(next)
    }
    return result.user
  }

  return {
    session,
    isLoading,
    isAuthenticated,
    user,
    displayName,
    profileHeadline,
    login,
    register,
    logout,
    updateProfile,
  }
})
