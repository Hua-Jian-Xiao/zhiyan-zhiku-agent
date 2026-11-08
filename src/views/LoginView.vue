<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Right, User, WarningFilled } from '@element-plus/icons-vue'
import BrandMark from '@/components/BrandMark.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const account = ref('admin')
const password = ref('123456')
const errorMessage = ref('')

function fillDemoAccount(): void {
  account.value = 'admin'
  password.value = '123456'
  errorMessage.value = ''
}

async function handleLogin(): Promise<void> {
  if (authStore.isLoading) return
  errorMessage.value = ''

  if (!account.value.trim()) {
    errorMessage.value = '请输入账号'
    return
  }
  if (!password.value) {
    errorMessage.value = '请输入密码'
    return
  }

  try {
    await authStore.login(account.value, password.value)
    ElMessage.success('登录成功，欢迎回来')
    const redirect =
      typeof route.query.redirect === 'string' &&
      route.query.redirect.startsWith('/') &&
      !route.query.redirect.startsWith('//')
        ? route.query.redirect
        : '/workspace'
    await router.replace(redirect)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '登录失败，请稍后重试'
  }
}
</script>

<template>
  <div class="relative flex min-h-screen w-full overflow-hidden bg-[#060c19]">
    <div class="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
      <div class="login-orb login-orb-a" />
      <div class="login-orb login-orb-b" />
      <div class="absolute inset-0 dot-grid opacity-[0.06]" />
      <div class="absolute left-0 top-0 h-px w-full bg-gradient-to-r from-transparent via-indigo-400/20 to-transparent" />
    </div>

    <aside
      class="relative z-10 hidden min-h-screen shrink-0 flex-col justify-between px-12 py-10 lg:flex lg:w-[57%] xl:px-16 2xl:px-24"
    >
      <BrandMark />

      <div class="my-10 max-w-[600px]">
        <div
          class="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-[10px] tracking-wide text-slate-300"
        >
          <span class="h-1.5 w-1.5 animate-soft-pulse rounded-full bg-cyan-300" />
          计算机学科 · RAG 智能学习 Agent
        </div>

        <h1
          class="mt-7 text-[44px] font-bold leading-[1.18] tracking-[-0.035em] text-white xl:text-[52px]"
        >
          让每一次提问，<br />
          都有
          <span class="bg-gradient-to-r from-indigo-300 via-cyan-300 to-indigo-200 bg-clip-text text-transparent">
            知识作为依据
          </span>
          。
        </h1>
        <p class="mt-6 max-w-[480px] text-[13px] leading-7 text-slate-400">
          智研知库把课程知识库、知识依赖图谱与检索增强生成整合到一个学习工作台，
          帮你从「知道答案」走向「理解知识从何而来」。
        </p>

        <div class="mt-8 grid max-w-[510px] gap-2.5">
          <div class="login-feature">
            <span class="login-feature-icon">
              <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M4 3.5h9.5A2.5 2.5 0 0 1 16 6v10.5H6.5A2.5 2.5 0 0 1 4 14V3.5Z" />
                <path d="M4 13.5h12M7 7h6M7 10h4" />
              </svg>
            </span>
            <div>
              <p class="text-[11px] font-medium text-slate-200">可追溯的 RAG 回答</p>
              <p class="mt-0.5 text-[10px] text-slate-500">每个结论都绑定知识片段与相似度分数</p>
            </div>
          </div>
          <div class="login-feature">
            <span class="login-feature-icon">
              <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="5" cy="10" r="2" />
                <circle cx="15" cy="5" r="2" />
                <circle cx="15" cy="15" r="2" />
                <path d="M7 9l6-3M7 11l6 3" />
              </svg>
            </span>
            <div>
              <p class="text-[11px] font-medium text-slate-200">客观知识依赖图谱</p>
              <p class="mt-0.5 text-[10px] text-slate-500">只描述课程知识关系，不掺杂掌握度推断</p>
            </div>
          </div>
          <div class="login-feature">
            <span class="login-feature-icon">
              <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M3 13.5V16h2.5L15 6.5 13.5 5 3 13.5Z" />
                <path d="M12 6.5l1.5 1.5M5.5 14l.5.5" />
              </svg>
            </span>
            <div>
              <p class="text-[11px] font-medium text-slate-200">Agent 全流程可见</p>
              <p class="mt-0.5 text-[10px] text-slate-500">思考步骤、工具调用与检索片段全部展开可查</p>
            </div>
          </div>
        </div>

        <div class="mt-9 flex max-w-[510px] divide-x divide-white/10 border-y border-white/[0.07] py-4">
          <div class="flex-1 pr-6">
            <p class="font-mono text-[19px] font-semibold text-white">8</p>
            <p class="mt-1 text-[9px] tracking-wide text-slate-500">门课程</p>
          </div>
          <div class="flex-1 px-6">
            <p class="font-mono text-[19px] font-semibold text-white">326</p>
            <p class="mt-1 text-[9px] tracking-wide text-slate-500">个知识点</p>
          </div>
          <div class="flex-1 pl-6">
            <p class="font-mono text-[19px] font-semibold text-white">1,284</p>
            <p class="mt-1 text-[9px] tracking-wide text-slate-500">条知识片段</p>
          </div>
        </div>
      </div>

      <div class="flex items-center justify-between text-[9px] tracking-wide text-slate-600">
        <span>© 2026 智研知库 · Zhiyan Knowledge Lab</span>
        <span class="font-mono">MOCK ENVIRONMENT</span>
      </div>
    </aside>

    <main
      class="relative z-10 flex min-h-screen flex-1 items-center justify-center bg-[#f5f7fb] px-5 py-10 shadow-[-30px_0_80px_-40px_rgba(0,0,0,0.5)] sm:px-8 lg:rounded-l-[42px]"
    >
      <div class="pointer-events-none absolute right-0 top-0 h-72 w-72 rounded-full bg-indigo-100/60 blur-3xl" />
      <div class="pointer-events-none absolute bottom-0 left-0 h-64 w-64 rounded-full bg-cyan-100/50 blur-3xl" />

      <div class="relative w-full max-w-[392px] animate-fade-up">
        <div class="mb-10 flex justify-center lg:hidden">
          <div class="rounded-2xl bg-[#0a1020] px-5 py-3 shadow-xl shadow-indigo-950/20">
            <BrandMark />
          </div>
        </div>

        <p class="section-eyebrow">WELCOME BACK</p>
        <h2 class="mt-2.5 text-[28px] font-bold tracking-[-0.03em] text-ink-950">
          登录你的学习空间
        </h2>
        <p class="mt-2 text-[12px] leading-6 text-slate-500">
          一个账号，连接课程知识库、检索实验与 Agent 对话。
        </p>

        <form class="mt-8" novalidate @submit.prevent="handleLogin">
          <div class="space-y-4">
            <label class="block">
              <span class="mb-1.5 block text-[11px] font-medium text-slate-600">账号</span>
              <el-input
                v-model="account"
                size="large"
                placeholder="请输入账号"
                :prefix-icon="User"
                autocomplete="username"
                class="login-input"
                @input="errorMessage = ''"
              />
            </label>

            <label class="block">
              <span class="mb-1.5 block text-[11px] font-medium text-slate-600">密码</span>
              <el-input
                v-model="password"
                type="password"
                size="large"
                placeholder="请输入密码"
                show-password
                autocomplete="current-password"
                class="login-input"
                @input="errorMessage = ''"
                @keyup.enter="handleLogin"
              />
            </label>
          </div>

          <Transition name="fade">
            <div
              v-if="errorMessage"
              class="mt-3.5 flex items-start gap-2 rounded-lg border border-rose-100 bg-rose-50 px-3 py-2.5 text-[11px] leading-5 text-rose-600"
              role="alert"
            >
              <el-icon class="mt-0.5 shrink-0" :size="13"><WarningFilled /></el-icon>
              <span>{{ errorMessage }}</span>
            </div>
          </Transition>

          <el-button
            type="primary"
            native-type="submit"
            class="login-submit !mt-6 !h-[46px] !w-full !rounded-xl !text-[12px]"
            :loading="authStore.isLoading"
          >
            <template v-if="!authStore.isLoading">
              进入工作台
              <el-icon class="ml-1.5"><Right /></el-icon>
            </template>
            <template v-else>正在验证身份…</template>
          </el-button>
        </form>

        <div
          class="mt-5 flex items-center justify-between rounded-xl border border-dashed border-slate-200 bg-white/80 px-3.5 py-3"
        >
          <div>
            <p class="text-[9px] font-medium uppercase tracking-[0.14em] text-slate-400">
              演示账号
            </p>
            <p class="mt-1 font-mono text-[11px] text-slate-600">admin / 123456</p>
          </div>
          <button
            type="button"
            class="rounded-lg px-2 py-1 text-[10px] font-medium text-indigo-500 transition hover:bg-indigo-50"
            @click="fillDemoAccount"
          >
            一键填入
          </button>
        </div>

        <p class="mt-8 text-center text-[9px] leading-5 text-slate-400">
          当前为纯前端 Mock 环境，不连接真实后端服务<br />
          登录状态仅保存在浏览器本地
        </p>
      </div>
    </main>
  </div>
</template>

<style scoped>
.login-orb {
  position: absolute;
  border-radius: 999px;
  filter: blur(100px);
  pointer-events: none;
}

.login-orb-a {
  top: -10%;
  left: 18%;
  width: 460px;
  height: 460px;
  background: rgba(79, 70, 229, 0.22);
  animation: orb-float 12s ease-in-out infinite;
}

.login-orb-b {
  right: 38%;
  bottom: -14%;
  width: 380px;
  height: 380px;
  background: rgba(34, 211, 238, 0.12);
  animation: orb-float 15s ease-in-out infinite reverse;
}

.login-feature {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 9px 12px;
  background: rgba(255, 255, 255, 0.025);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 11px;
  backdrop-filter: blur(10px);
}

.login-feature-icon {
  display: grid;
  width: 30px;
  height: 30px;
  flex-shrink: 0;
  place-items: center;
  color: #a5b4fc;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(129, 140, 248, 0.12);
  border-radius: 8px;
}

.login-feature-icon svg {
  width: 16px;
  height: 16px;
}

.login-input :deep(.el-input__wrapper) {
  min-height: 46px;
  padding-right: 14px;
  padding-left: 14px;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 11px;
  box-shadow: 0 0 0 1px #e4e8f0 inset;
  transition: box-shadow 0.18s ease;
}

.login-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #cbd3e1 inset;
}

.login-input :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    0 0 0 1px #6366f1 inset,
    0 0 0 4px rgba(99, 102, 241, 0.08) !important;
}

.login-submit {
  box-shadow: 0 14px 32px -12px rgba(79, 70, 229, 0.55) !important;
}

@keyframes orb-float {
  0%,
  100% {
    transform: translate3d(0, 0, 0) scale(1);
  }
  50% {
    transform: translate3d(20px, -24px, 0) scale(1.06);
  }
}

@media (max-width: 1023px) {
  main {
    background:
      radial-gradient(circle at 85% 8%, rgba(224, 231, 255, 0.8), transparent 36%),
      radial-gradient(circle at 6% 95%, rgba(207, 250, 254, 0.7), transparent 34%),
      #f5f7fb;
  }
}
</style>
