import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { title: '登录' },
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: () => import('@/views/ForgotPasswordView.vue'),
      meta: { title: '找回密码' },
    },
    {
      path: '/',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          redirect: { name: 'workspace' },
        },
        {
          path: 'workspace',
          name: 'workspace',
          component: () => import('@/views/WorkbenchView.vue'),
          meta: { title: 'Agent 工作台' },
        },
        {
          path: 'knowledge',
          name: 'knowledge',
          component: () => import('@/views/KnowledgeBaseView.vue'),
          meta: { title: '知识库管理' },
        },
        {
          path: 'rag-debug',
          name: 'rag-debug',
          component: () => import('@/views/RagDebugView.vue'),
          meta: { title: 'RAG 检索调试' },
        },
        {
          path: 'graph',
          name: 'graph',
          component: () => import('@/views/KnowledgeGraphView.vue'),
          meta: { title: '知识图谱' },
        },
        {
          path: 'profile',
          name: 'profile',
          component: () => import('@/views/ProfileView.vue'),
          meta: { title: '个人中心' },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/workspace',
    },
  ],
})

router.beforeEach((to) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)

  if (requiresAuth && !authStore.isAuthenticated) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    }
  }

  if (to.name === 'login' && authStore.isAuthenticated) {
    return { name: 'workspace' }
  }

  return true
})

router.afterEach((to) => {
  const title = typeof to.meta.title === 'string' ? to.meta.title : ''
  document.title = title ? `${title} · 智研知库` : '智研知库 · RAG 智能学习 Agent'
})

if (typeof window !== 'undefined') {
  window.addEventListener('zhiyan:unauthorized', () => {
    const current = router.currentRoute.value
    if (current.name !== 'login') {
      void router.replace({
        name: 'login',
        query: { redirect: current.fullPath },
      })
    }
  })
}

export default router
