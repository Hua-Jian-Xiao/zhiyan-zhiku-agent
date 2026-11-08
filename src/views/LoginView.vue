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

const account = ref('')
const password = ref('')
const accountError = ref('')
const passwordError = ref('')
const errorMessage = ref('')

function validateAccount(): boolean {
  if (!account.value.trim()) {
    accountError.value = '请输入账号'
    return false
  }
  if (account.value.trim().length < 2) {
    accountError.value = '账号至少需要 2 个字符'
    return false
  }
  accountError.value = ''
  return true
}

function validatePassword(): boolean {
  if (!password.value) {
    passwordError.value = '请输入密码'
    return false
  }
  if (password.value.length < 6) {
    passwordError.value = '密码至少需要 6 位'
    return false
  }
  passwordError.value = ''
  return true
}

async function handleLogin(): Promise<void> {
  if (authStore.isLoading) return
  errorMessage.value = ''

  const accountValid = validateAccount()
  const passwordValid = validatePassword()
  if (!accountValid || !passwordValid) return

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
  <div class="relative flex min-h-screen w-full overflow-hidden bg-[#17130f]">
    <div class="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
      <div class="absolute inset-0 dot-grid opacity-[0.04]" />
      <div class="absolute inset-y-0 left-10 w-px bg-[#6b5b48]/20" />
      <div class="absolute inset-y-0 left-[calc(57%-1px)] hidden w-px bg-[#c9bdab] lg:block" />
      <span class="absolute left-[16%] top-[15%] font-serif text-[180px] leading-none text-[#9a463c]/[0.045]">知</span>
    </div>

    <aside
      class="relative z-10 hidden min-h-screen shrink-0 flex-col justify-between px-12 py-9 lg:flex lg:w-[57%] xl:px-16 2xl:px-24"
    >
      <div class="flex items-start justify-between gap-6">
        <BrandMark />
        <div class="shrink-0 border-l border-[#4b3f32] pl-4 text-right font-mono text-[7px] leading-5 tracking-[0.14em] text-[#817463]">
          <p>VOL. 01 / NO. 07</p>
          <p>NOVEMBER 2026</p>
        </div>
      </div>

      <div class="my-9 max-w-[620px]">
        <div class="flex items-center gap-3">
          <span class="h-px flex-1 bg-[#4b3f32]" />
          <span class="font-mono text-[7px] uppercase tracking-[0.22em] text-[#a49179]">
            A Journal of Computational Studies
          </span>
        </div>

        <p class="mt-7 font-mono text-[8px] uppercase tracking-[0.2em] text-[#b17a68]">
          RAG · Learning Agent · Editorial Issue
        </p>
        <h1 class="mt-4 font-serif text-[44px] font-medium leading-[1.24] tracking-[-0.025em] text-[#f4ead9] xl:text-[54px]">
          让每一次提问，<br />
          都有<span class="text-[#d8b865]">知识</span>作为依据。
        </h1>
        <p class="mt-6 max-w-[490px] text-[11px] leading-7 text-[#9d8f7c]">
          智研知库把课程知识库、知识依赖图谱与检索增强生成整合到一个学习工作台，
          帮你从「知道答案」走向「理解知识从何而来」。
        </p>

        <div class="mt-9 max-w-[520px] border-t border-[#4b3f32]">
          <div class="login-feature">
            <span class="login-feature-index">I.</span>
            <div>
              <p class="text-[11px] font-medium text-[#e3d7c4]">可追溯的 RAG 回答</p>
              <p class="mt-1 text-[9px] leading-5 text-[#8c7f6d]">每个结论都绑定知识片段、知识点 ID 与相似度分数</p>
            </div>
          </div>
          <div class="login-feature">
            <span class="login-feature-index">II.</span>
            <div>
              <p class="text-[11px] font-medium text-[#e3d7c4]">客观知识依赖图谱</p>
              <p class="mt-1 text-[9px] leading-5 text-[#8c7f6d]">只呈现课程之间的客观先修关系</p>
            </div>
          </div>
          <div class="login-feature">
            <span class="login-feature-index">III.</span>
            <div>
              <p class="text-[11px] font-medium text-[#e3d7c4]">Agent 全流程可见</p>
              <p class="mt-1 text-[9px] leading-5 text-[#8c7f6d]">思考步骤、工具调用与检索片段全部展开可查</p>
            </div>
          </div>
        </div>

        <div class="mt-8 flex max-w-[520px] divide-x divide-[#4b3f32] border-y border-[#4b3f32] py-4">
          <div class="flex-1 pr-6">
            <p class="font-serif text-[24px] leading-none text-[#f0e4d1]">8</p>
            <p class="mt-2 font-mono text-[7px] tracking-[0.16em] text-[#817463]">COURSES</p>
          </div>
          <div class="flex-1 px-6">
            <p class="font-serif text-[24px] leading-none text-[#f0e4d1]">326</p>
            <p class="mt-2 font-mono text-[7px] tracking-[0.16em] text-[#817463]">CONCEPTS</p>
          </div>
          <div class="flex-1 pl-6">
            <p class="font-serif text-[24px] leading-none text-[#f0e4d1]">1,284</p>
            <p class="mt-2 font-mono text-[7px] tracking-[0.16em] text-[#817463]">PASSAGES</p>
          </div>
        </div>
      </div>

      <div class="flex items-center justify-between border-t border-[#4b3f32] pt-4 font-mono text-[7px] tracking-[0.1em] text-[#746857]">
        <span>© 2026 智研知库 · ZHIYAN KNOWLEDGE LAB</span>
        <span>PRINTED IN THE BROWSER</span>
      </div>
    </aside>

    <main
      class="journal-form-panel relative z-10 flex min-h-screen flex-1 items-center justify-center bg-[#f7f1e6] px-5 py-10 sm:px-8 lg:border-l lg:border-[#c9bdab]"
    >
      <div class="pointer-events-none absolute right-6 top-5 font-serif text-[96px] leading-none text-[#7d302f]/[0.055]">
        01
      </div>

      <div class="relative w-full max-w-[382px] animate-fade-up">
        <div class="mb-10 flex justify-center lg:hidden">
          <div class="border border-[#3d3328] bg-[#17130f] px-5 py-3">
            <BrandMark />
          </div>
        </div>

        <div class="flex items-center justify-between border-b border-[#bfb29e] pb-2.5">
          <p class="font-mono text-[8px] font-medium uppercase tracking-[0.2em] text-[#7d302f]">
            Subscriber Access
          </p>
          <span class="font-mono text-[7px] tracking-[0.14em] text-[#a49783]">SEC. 01</span>
        </div>

        <h2 class="mt-6 font-serif text-[31px] font-medium leading-tight tracking-[-0.02em] text-[#211c17]">
          登录你的学习空间
        </h2>
        <p class="mt-2.5 max-w-[330px] text-[10px] leading-6 text-[#766b5b]">
          一个账号，连接课程知识库、检索实验与 Agent 对话。
        </p>

        <form class="mt-9" novalidate @submit.prevent="handleLogin">
          <div class="space-y-5">
            <label class="block">
              <span class="mb-1.5 flex items-center justify-between font-mono text-[8px] uppercase tracking-[0.14em] text-[#6f6456]">
                <span>账号</span>
                <span class="text-[#a49783]">Account</span>
              </span>
              <el-input
                v-model="account"
                size="large"
                placeholder="请输入账号"
                :prefix-icon="User"
                autocomplete="username"
                class="login-input"
                :class="{ 'is-invalid': accountError }"
                :disabled="authStore.isLoading"
                @input="accountError = ''; errorMessage = ''"
                @blur="validateAccount"
              />
              <Transition name="fade">
                <span v-if="accountError" class="mt-1.5 flex items-center gap-1 text-[9px] text-rose-500">
                  <el-icon :size="9"><WarningFilled /></el-icon>
                  {{ accountError }}
                </span>
              </Transition>
            </label>

            <label class="block">
              <span class="mb-1.5 flex items-center justify-between font-mono text-[8px] uppercase tracking-[0.14em] text-[#6f6456]">
                <span>密码</span>
                <span class="text-[#a49783]">Password</span>
              </span>
              <el-input
                v-model="password"
                type="password"
                size="large"
                placeholder="请输入密码"
                show-password
                autocomplete="current-password"
                class="login-input"
                :class="{ 'is-invalid': passwordError }"
                :disabled="authStore.isLoading"
                @input="passwordError = ''; errorMessage = ''"
                @blur="validatePassword"
                @keyup.enter="handleLogin"
              />
              <Transition name="fade">
                <span v-if="passwordError" class="mt-1.5 flex items-center gap-1 text-[9px] text-rose-500">
                  <el-icon :size="9"><WarningFilled /></el-icon>
                  {{ passwordError }}
                </span>
              </Transition>
            </label>
          </div>

          <Transition name="fade">
            <div
              v-if="errorMessage"
              class="mt-4 flex items-start gap-2 border border-[#d6b6ae] bg-[#f6e9e4] px-3 py-2.5 text-[10px] leading-5 text-[#8e3d35]"
              role="alert"
            >
              <el-icon class="mt-0.5 shrink-0" :size="12"><WarningFilled /></el-icon>
              <span>{{ errorMessage }}</span>
            </div>
          </Transition>

          <el-button
            type="primary"
            native-type="submit"
            class="login-submit !mt-7 !h-[48px] !w-full !text-[11px]"
            :loading="authStore.isLoading"
            :disabled="authStore.isLoading"
          >
            <template v-if="!authStore.isLoading">
              登录
              <el-icon class="ml-2"><Right /></el-icon>
            </template>
            <template v-else>正在验证身份…</template>
          </el-button>
        </form>

        <div class="mt-9 border-t border-[#d8cebd] pt-4">
          <div class="flex items-start justify-between gap-5">
            <p class="font-mono text-[7px] leading-4 tracking-[0.06em] text-[#a49783]">
              MOCK ACCESS · LOCAL SESSION<br />
              登录状态仅保存在浏览器本地
            </p>
            <span class="border border-[#c9bdab] px-1.5 py-0.5 font-mono text-[6.5px] tracking-[0.14em] text-[#8d806e]">
              NO. 07
            </span>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.journal-form-panel {
  background-image:
    linear-gradient(90deg, rgba(125, 48, 47, 0.025), transparent 18%),
    radial-gradient(rgba(70, 57, 42, 0.04) 0.5px, transparent 0.5px);
  background-size: 100% 100%, 4px 4px;
}

.login-feature {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 14px 0;
  border-bottom: 1px solid #3f352a;
}

.login-feature-index {
  width: 22px;
  flex-shrink: 0;
  padding-top: 1px;
  color: #b17a68;
  font-family: var(--app-serif);
  font-size: 11px;
  font-style: italic;
}

.login-input :deep(.el-input__wrapper) {
  min-height: 43px;
  padding-right: 2px;
  padding-left: 0;
  background: transparent;
  border-radius: 0;
  box-shadow: none !important;
  border-bottom: 1px solid #bfb29e;
  transition: border-color 0.18s ease;
}

.login-input :deep(.el-input__wrapper:hover) {
  border-bottom-color: #8d806e;
}

.login-input :deep(.el-input__wrapper.is-focus) {
  border-bottom-color: #7d302f;
  box-shadow: none !important;
}

.login-input :deep(.el-input__prefix) {
  color: #8d806e;
}

.login-input :deep(.el-input__inner) {
  font-family: var(--app-font);
  font-size: 12px;
  color: #2f2922;
}

.login-input :deep(.el-input__inner::placeholder) {
  color: #a99d8b;
  font-style: italic;
}

.login-input.is-invalid :deep(.el-input__wrapper) {
  border-bottom-color: #b56b5f;
}

.login-input.is-invalid :deep(.el-input__wrapper.is-focus) {
  border-bottom-color: #8e3d35;
}

.login-submit {
  border-radius: 0 !important;
  font-family: var(--app-mono);
  letter-spacing: 0.14em;
}

.login-submit :deep(span) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>
