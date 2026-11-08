<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, Right, User, WarningFilled } from '@element-plus/icons-vue'
import BrandMark from '@/components/BrandMark.vue'
import { useAuthStore } from '@/stores/auth'
import { useSystemStore } from '@/stores/system'

const authStore = useAuthStore()
const systemStore = useSystemStore()
const router = useRouter()
const route = useRoute()

const mode = ref<'login' | 'register'>('login')
const account = ref('')
const displayName = ref('')
const password = ref('')
const confirmPassword = ref('')
const accountError = ref('')
const displayNameError = ref('')
const passwordError = ref('')
const confirmPasswordError = ref('')
const errorMessage = ref('')

const isRegister = computed(() => mode.value === 'register')

function validateAccount(): boolean {
  const value = account.value.trim()
  if (!value) {
    accountError.value = '请输入账号'
    return false
  }
  if (!/^[A-Za-z0-9_-]{2,32}$/.test(value)) {
    accountError.value = '账号需为 2-32 位字母、数字、下划线或短横线'
    return false
  }
  accountError.value = ''
  return true
}

function validateDisplayName(): boolean {
  if (displayName.value.trim().length > 20) {
    displayNameError.value = '昵称不能超过 20 个字符'
    return false
  }
  displayNameError.value = ''
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

function validateConfirmPassword(): boolean {
  if (!isRegister.value) return true
  if (!confirmPassword.value) {
    confirmPasswordError.value = '请再次输入密码'
    return false
  }
  if (confirmPassword.value !== password.value) {
    confirmPasswordError.value = '两次输入的密码不一致'
    return false
  }
  confirmPasswordError.value = ''
  return true
}

function switchMode(nextMode: 'login' | 'register'): void {
  if (authStore.isLoading) return
  mode.value = nextMode
  accountError.value = ''
  displayNameError.value = ''
  passwordError.value = ''
  confirmPasswordError.value = ''
  errorMessage.value = ''
  confirmPassword.value = ''
}

async function handleSubmit(): Promise<void> {
  if (authStore.isLoading) return
  errorMessage.value = ''

  const accountValid = validateAccount()
  const passwordValid = validatePassword()
  const displayNameValid = isRegister.value ? validateDisplayName() : true
  const confirmValid = validateConfirmPassword()
  if (!accountValid || !passwordValid || !displayNameValid || !confirmValid) return

  try {
    if (isRegister.value) {
      await authStore.register(account.value.trim(), password.value, displayName.value)
      ElMessage.success('注册成功，已为你登录')
    } else {
      await authStore.login(account.value.trim(), password.value)
      ElMessage.success('登录成功，欢迎回来')
    }
    const redirect =
      typeof route.query.redirect === 'string' &&
      route.query.redirect.startsWith('/') &&
      !route.query.redirect.startsWith('//')
        ? route.query.redirect
        : '/workspace'
    await router.replace(redirect)
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : isRegister.value
          ? '注册失败，请稍后重试'
          : '登录失败，请稍后重试'
  }
}

onMounted(() => {
  void systemStore.loadStats().catch(() => {
    // The form remains usable and will show a connection error on submit.
  })
})
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
      <BrandMark />

      <div class="my-9 max-w-[620px]">
        <span class="inline-flex border border-[#5a4b3a] px-3 py-1.5 text-[12px] tracking-[0.04em] text-[#c9bca9]">
          计算机学科 · RAG 智能学习工作台
        </span>
        <h1 class="mt-6 font-serif text-[44px] font-medium leading-[1.24] tracking-[-0.025em] text-[#f4ead9] xl:text-[54px]">
          让每一次提问，<br />
          都有<span class="text-[#d8b865]">知识</span>作为依据。
        </h1>
        <p class="mt-6 max-w-[490px] text-[13px] leading-7 text-[#9d8f7c]">
          智研知库把课程知识库、知识依赖图谱与检索增强生成整合到一个学习工作台，
          帮你从「知道答案」走向「理解知识从何而来」。
        </p>

        <div class="mt-9 max-w-[520px] border-t border-[#4b3f32]">
          <div class="login-feature">
            <span class="login-feature-index">I.</span>
            <div>
              <p class="text-[12px] font-medium text-[#e3d7c4]">可追溯的 RAG 回答</p>
              <p class="mt-1 text-[11px] leading-5 text-[#8c7f6d]">每个结论都绑定知识片段、知识点 ID 与相似度分数</p>
            </div>
          </div>
          <div class="login-feature">
            <span class="login-feature-index">II.</span>
            <div>
              <p class="text-[12px] font-medium text-[#e3d7c4]">客观知识依赖图谱</p>
              <p class="mt-1 text-[11px] leading-5 text-[#8c7f6d]">只呈现课程之间的客观先修关系</p>
            </div>
          </div>
          <div class="login-feature">
            <span class="login-feature-index">III.</span>
            <div>
              <p class="text-[12px] font-medium text-[#e3d7c4]">Agent 全流程可见</p>
              <p class="mt-1 text-[11px] leading-5 text-[#8c7f6d]">思考步骤、工具调用与检索片段全部展开可查</p>
            </div>
          </div>
        </div>

        <div class="mt-8 flex max-w-[520px] divide-x divide-[#4b3f32] border-y border-[#4b3f32] py-4">
          <div class="flex-1 pr-6">
            <p class="font-serif text-[26px] leading-none text-[#f0e4d1]">{{ systemStore.stats?.courseCount ?? '—' }}</p>
            <p class="mt-2 text-[10px] tracking-[0.08em] text-[#9d8f7c]">门课程</p>
          </div>
          <div class="flex-1 px-6">
            <p class="font-serif text-[26px] leading-none text-[#f0e4d1]">{{ systemStore.stats?.knowledgePointCount ?? '—' }}</p>
            <p class="mt-2 text-[10px] tracking-[0.08em] text-[#9d8f7c]">个知识点</p>
          </div>
          <div class="flex-1 pl-6">
            <p class="font-serif text-[26px] leading-none text-[#f0e4d1]">{{ systemStore.stats?.chunkCount ?? '—' }}</p>
            <p class="mt-2 text-[10px] tracking-[0.08em] text-[#9d8f7c]">个知识片段</p>
          </div>
        </div>
      </div>

      <div class="border-t border-[#4b3f32] pt-4 text-[10px] tracking-[0.04em] text-[#8c7f6d]">
        © 2026 智研知库 · RAG Learning Workbench
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

        <div class="grid grid-cols-2 border-b border-[#bfb29e]">
          <button
            type="button"
            class="auth-tab"
            :class="{ 'is-active': mode === 'login' }"
            @click="switchMode('login')"
          >
            登录
          </button>
          <button
            type="button"
            class="auth-tab"
            :class="{ 'is-active': mode === 'register' }"
            @click="switchMode('register')"
          >
            注册
          </button>
        </div>

        <h2 class="mt-5 font-serif text-[31px] font-medium leading-tight tracking-[-0.02em] text-[#211c17]">
          {{ isRegister ? '创建你的学习空间' : '登录你的学习空间' }}
        </h2>
        <p class="mt-2.5 max-w-[330px] text-[12px] leading-6 text-[#766b5b]">
          {{ isRegister ? '注册后即可使用 RAG 检索、Agent 对话与知识图谱。' : '一个账号，连接课程知识库、检索实验与 Agent 对话。' }}
        </p>

        <form class="mt-7" novalidate @submit.prevent="handleSubmit">
          <div class="space-y-4">
            <label v-if="isRegister" class="block">
              <span class="mb-1.5 block text-[12px] font-medium text-[#5b5145]">昵称（可选）</span>
              <el-input
                v-model="displayName"
                size="large"
                placeholder="例如：林晓"
                :prefix-icon="User"
                autocomplete="nickname"
                class="login-input"
                :class="{ 'is-invalid': displayNameError }"
                :disabled="authStore.isLoading"
                @input="displayNameError = ''; errorMessage = ''"
                @blur="validateDisplayName"
              />
              <Transition name="fade">
                <span v-if="displayNameError" class="mt-1.5 flex items-center gap-1 text-[11px] text-rose-500">
                  <el-icon :size="10"><WarningFilled /></el-icon>
                  {{ displayNameError }}
                </span>
              </Transition>
            </label>

            <label class="block">
              <span class="mb-1.5 block text-[12px] font-medium text-[#5b5145]">账号</span>
              <el-input
                v-model="account"
                size="large"
                placeholder="2-32 位字母、数字、下划线或短横线"
                :prefix-icon="User"
                autocomplete="username"
                class="login-input"
                :class="{ 'is-invalid': accountError }"
                :disabled="authStore.isLoading"
                @input="accountError = ''; errorMessage = ''"
                @blur="validateAccount"
              />
              <Transition name="fade">
                <span v-if="accountError" class="mt-1.5 flex items-center gap-1 text-[11px] text-rose-500">
                  <el-icon :size="10"><WarningFilled /></el-icon>
                  {{ accountError }}
                </span>
              </Transition>
            </label>

            <label class="block">
              <span class="mb-1.5 block text-[12px] font-medium text-[#5b5145]">密码</span>
              <el-input
                v-model="password"
                type="password"
                size="large"
                placeholder="至少 6 位密码"
                :prefix-icon="Lock"
                show-password
                :autocomplete="isRegister ? 'new-password' : 'current-password'"
                class="login-input"
                :class="{ 'is-invalid': passwordError }"
                :disabled="authStore.isLoading"
                @input="passwordError = ''; errorMessage = ''"
                @blur="validatePassword"
                @keyup.enter="handleSubmit"
              />
              <Transition name="fade">
                <span v-if="passwordError" class="mt-1.5 flex items-center gap-1 text-[11px] text-rose-500">
                  <el-icon :size="10"><WarningFilled /></el-icon>
                  {{ passwordError }}
                </span>
              </Transition>
            </label>

            <label v-if="isRegister" class="block">
              <span class="mb-1.5 block text-[12px] font-medium text-[#5b5145]">确认密码</span>
              <el-input
                v-model="confirmPassword"
                type="password"
                size="large"
                placeholder="请再次输入密码"
                :prefix-icon="Lock"
                show-password
                autocomplete="new-password"
                class="login-input"
                :class="{ 'is-invalid': confirmPasswordError }"
                :disabled="authStore.isLoading"
                @input="confirmPasswordError = ''; errorMessage = ''"
                @blur="validateConfirmPassword"
                @keyup.enter="handleSubmit"
              />
              <Transition name="fade">
                <span v-if="confirmPasswordError" class="mt-1.5 flex items-center gap-1 text-[11px] text-rose-500">
                  <el-icon :size="10"><WarningFilled /></el-icon>
                  {{ confirmPasswordError }}
                </span>
              </Transition>
            </label>
          </div>

          <Transition name="fade">
            <div
              v-if="errorMessage"
              class="mt-4 flex items-start gap-2 border border-[#d6b6ae] bg-[#f6e9e4] px-3 py-2.5 text-[12px] leading-5 text-[#8e3d35]"
              role="alert"
            >
              <el-icon class="mt-0.5 shrink-0" :size="12"><WarningFilled /></el-icon>
              <span>{{ errorMessage }}</span>
            </div>
          </Transition>

          <el-button
            type="primary"
            native-type="submit"
            class="login-submit !mt-6 !h-[48px] !w-full !text-[13px]"
            :loading="authStore.isLoading"
            :disabled="authStore.isLoading"
          >
            <template v-if="!authStore.isLoading">
              {{ isRegister ? '注册并进入工作台' : '登录' }}
              <el-icon class="ml-2"><Right /></el-icon>
            </template>
            <template v-else>{{ isRegister ? '正在创建账号…' : '正在验证身份…' }}</template>
          </el-button>
        </form>

        <div class="mt-6 border-t border-[#d8cebd] pt-4 text-[11px] leading-5 text-[#8d806e]">
          <template v-if="isRegister">
            <p>注册即创建独立的学习空间，会话与检索记录保存在服务端。</p>
          </template>
          <template v-else>
            <p>演示账号：<span class="font-mono text-[#5b5145]">student / student123</span></p>
            <p class="mt-1">还没有账号？可切换到上方「注册」创建新账号。</p>
          </template>
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

.auth-tab {
  padding-bottom: 12px;
  color: #8d806e;
  font-size: 13px;
  font-weight: 500;
  background: transparent;
  border: 0;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: color 0.18s ease, border-color 0.18s ease;
}

.auth-tab:hover {
  color: #5b5145;
}

.auth-tab.is-active {
  color: #7d302f;
  border-bottom-color: #7d302f;
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
