<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Key } from '@element-plus/icons-vue'
import { fetchSecurityQuestion, resetPassword } from '@/services/api'

const username = ref('')
const canonicalUsername = ref('')
const question = ref('')
const answer = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const isLoadingQuestion = ref(false)
const isResetting = ref(false)
const errorMessage = ref('')
const success = ref(false)

function resetQuestionState(): void {
  question.value = ''
  canonicalUsername.value = ''
  answer.value = ''
  newPassword.value = ''
  confirmPassword.value = ''
  success.value = false
  errorMessage.value = ''
}

async function loadQuestion(): Promise<void> {
  const account = username.value.trim()
  if (!account) {
    ElMessage.warning('请输入账号')
    return
  }
  isLoadingQuestion.value = true
  errorMessage.value = ''
  try {
    const data = await fetchSecurityQuestion(account)
    canonicalUsername.value = data.username
    question.value = data.securityQuestion
    answer.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
    success.value = false
  } catch (error) {
    question.value = ''
    canonicalUsername.value = ''
    errorMessage.value = error instanceof Error ? error.message : '无法获取安全问题'
    ElMessage.error(errorMessage.value)
  } finally {
    isLoadingQuestion.value = false
  }
}

async function submitReset(): Promise<void> {
  if (!question.value) {
    ElMessage.warning('请先获取安全问题')
    return
  }
  if (!answer.value.trim()) {
    ElMessage.warning('请输入安全问题答案')
    return
  }
  if (newPassword.value.length < 6) {
    ElMessage.warning('新密码至少需要 6 位')
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }

  isResetting.value = true
  errorMessage.value = ''
  try {
    const response = await resetPassword({
      username: canonicalUsername.value || username.value.trim(),
      answer: answer.value.trim(),
      newPassword: newPassword.value,
    })
    success.value = true
    answer.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
    ElMessage.success(response.detail || '密码已重置')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '密码重置失败'
    ElMessage.error(errorMessage.value)
  } finally {
    isResetting.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-[#eee8dc] px-4 py-10">
    <div class="w-full max-w-[500px]">
      <router-link
        :to="{ name: 'login' }"
        class="mb-4 inline-flex items-center gap-1.5 text-[10px] text-[#8d806e] transition hover:text-[#7d302f]"
      >
        <el-icon :size="11"><ArrowLeft /></el-icon>
        返回登录
      </router-link>

      <div class="surface-card overflow-hidden">
        <div class="border-b border-[#d8cebd] bg-[#fbf7ee] px-7 py-6">
          <div class="flex items-center gap-3">
            <span class="grid h-11 w-11 place-items-center border border-[#7d302f]/35 bg-[#fbf5e9] font-serif text-[20px] text-[#682728]">
              知
            </span>
            <div>
              <p class="font-mono text-[7px] uppercase tracking-[0.18em] text-[#a29582]">
                Account recovery
              </p>
              <h1 class="mt-1 font-serif text-[22px] font-medium text-[#211c17]">
                找回密码
              </h1>
            </div>
          </div>
          <p class="mt-4 text-[10px] leading-5 text-[#766b5b]">
            输入账号并回答安全问题，验证通过后可以设置新的登录密码。
          </p>
        </div>

        <div class="p-7">
          <div v-if="success" class="py-4 text-center">
            <span class="mx-auto grid h-12 w-12 place-items-center border border-emerald-200 bg-emerald-50 text-emerald-600">
              <el-icon :size="22"><Key /></el-icon>
            </span>
            <h2 class="mt-4 font-serif text-[18px] font-medium text-[#211c17]">密码已重置</h2>
            <p class="mt-2 text-[10px] leading-5 text-[#766b5b]">
              请使用新密码重新登录。安全问题保持不变，之后仍可用于找回密码。
            </p>
            <router-link
              :to="{ name: 'login' }"
              class="mt-5 inline-flex border border-[#7d302f] bg-[#7d302f] px-5 py-2 text-[10px] font-medium text-white transition hover:bg-[#692825]"
            >
              返回登录
            </router-link>
          </div>

          <template v-else>
            <label class="block">
              <span class="mb-1.5 block text-[9px] font-semibold text-slate-600">账号</span>
              <div class="flex gap-2">
                <el-input
                  v-model="username"
                  placeholder="输入你的登录账号"
                  @input="resetQuestionState"
                  @keyup.enter="loadQuestion"
                />
                <el-button :loading="isLoadingQuestion" @click="loadQuestion">
                  获取问题
                </el-button>
              </div>
            </label>

            <div v-if="question" class="mt-5 space-y-4">
              <div class="border border-[#d8cebd] bg-[#fbf7ee] px-4 py-3">
                <p class="font-mono text-[7px] uppercase tracking-[0.14em] text-[#a29582]">
                  Security question
                </p>
                <p class="mt-1.5 text-[11px] font-medium text-[#4d453b]">{{ question }}</p>
              </div>

              <label class="block">
                <span class="mb-1.5 block text-[9px] font-semibold text-slate-600">安全问题答案</span>
                <el-input v-model="answer" type="password" show-password placeholder="输入你设置的答案" />
              </label>
              <label class="block">
                <span class="mb-1.5 block text-[9px] font-semibold text-slate-600">新密码</span>
                <el-input v-model="newPassword" type="password" show-password placeholder="至少 6 位" />
              </label>
              <label class="block">
                <span class="mb-1.5 block text-[9px] font-semibold text-slate-600">确认新密码</span>
                <el-input
                  v-model="confirmPassword"
                  type="password"
                  show-password
                  placeholder="再次输入新密码"
                  @keyup.enter="submitReset"
                />
              </label>
              <el-button
                type="primary"
                class="!w-full"
                :loading="isResetting"
                @click="submitReset"
              >
                重置密码
              </el-button>
            </div>

            <p
              v-if="errorMessage"
              class="mt-4 border border-rose-100 bg-rose-50 px-3 py-2 text-[9px] leading-4 text-rose-600"
            >
              {{ errorMessage }}
            </p>

            <p class="mt-5 border-t border-slate-100 pt-4 text-[8.5px] leading-4 text-slate-400">
              如果账号还没有设置安全问题，请先登录，在「个人中心 → 安全问题」中完成设置。
            </p>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>
