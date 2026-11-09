<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Camera, Lock, User } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import { changePassword } from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const displayName = ref(authStore.user?.displayName ?? '')
const email = ref(authStore.user?.email ?? '')
const major = ref(authStore.user?.major ?? '')
const grade = ref(authStore.user?.grade ?? '')
const bio = ref(authStore.user?.bio ?? '')
const securityQuestion = ref(authStore.user?.securityQuestion ?? '')
const securityAnswer = ref('')
const avatarFile = ref<File | null>(null)
const avatarPreview = ref(authStore.user?.avatarUrl ?? '')
const fileInput = ref<HTMLInputElement | null>(null)
const isSavingProfile = ref(false)
const isSavingSecurity = ref(false)
const isChangingPassword = ref(false)
const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
let previewUrl = ''

const SECURITY_QUESTIONS = [
  '我最喜欢的课程是？',
  '我的第一只宠物叫什么？',
  '我的小学名称是？',
  '我的出生城市是？',
  '我的第一份实习公司是？',
]

const securityQuestionOptions = computed(() => {
  const options = [...SECURITY_QUESTIONS]
  if (securityQuestion.value && !options.includes(securityQuestion.value)) {
    options.unshift(securityQuestion.value)
  }
  return options
})

const identityPreview = computed(() => {
  const parts = [major.value, grade.value]
    .map((part) => part.trim())
    .filter(Boolean)
  return parts.length ? parts.join(' · ') : (authStore.user?.role ?? '')
})

function chooseAvatar(): void {
  fileInput.value?.click()
}

function handleAvatarChange(event: Event): void {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    ElMessage.error('请选择图片文件')
    input.value = ''
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.error('头像不能超过 2 MB')
    input.value = ''
    return
  }
  avatarFile.value = file
  if (previewUrl) URL.revokeObjectURL(previewUrl)
  previewUrl = URL.createObjectURL(file)
  avatarPreview.value = previewUrl
}

async function saveProfile(): Promise<void> {
  if (!displayName.value.trim()) {
    ElMessage.warning('昵称不能为空')
    return
  }
  isSavingProfile.value = true
  try {
    const user = await authStore.updateProfile({
      displayName: displayName.value.trim(),
      email: email.value.trim(),
      major: major.value.trim(),
      grade: grade.value.trim(),
      bio: bio.value.trim(),
      avatar: avatarFile.value,
    })
    avatarFile.value = null
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
      previewUrl = ''
    }
    avatarPreview.value = user.avatarUrl || ''
    if (fileInput.value) fileInput.value.value = ''
    ElMessage.success('个人资料已更新')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '个人资料更新失败')
  } finally {
    isSavingProfile.value = false
  }
}

async function saveSecurityQuestion(): Promise<void> {
  if (!securityQuestion.value.trim()) {
    ElMessage.warning('请选择或输入安全问题')
    return
  }
  if (securityAnswer.value.trim().length < 2) {
    ElMessage.warning('安全问题答案至少需要 2 个字符')
    return
  }
  isSavingSecurity.value = true
  try {
    await authStore.updateProfile({
      securityQuestion: securityQuestion.value.trim(),
      securityAnswer: securityAnswer.value.trim(),
    })
    securityAnswer.value = ''
    ElMessage.success('安全问题已更新，忘记密码时可用于找回')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '安全问题更新失败')
  } finally {
    isSavingSecurity.value = false
  }
}

async function submitPasswordChange(): Promise<void> {
  if (!oldPassword.value) {
    ElMessage.warning('请输入当前密码')
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
  isChangingPassword.value = true
  try {
    const response = await changePassword({
      oldPassword: oldPassword.value,
      newPassword: newPassword.value,
    })
    oldPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
    ElMessage.success(response.detail || '密码已修改')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '密码修改失败')
  } finally {
    isChangingPassword.value = false
  }
}

onBeforeUnmount(() => {
  if (previewUrl) URL.revokeObjectURL(previewUrl)
})
</script>

<template>
  <div class="page-scroll">
    <div class="page-container">
      <PageHeader
        title="个人中心"
        description="维护头像、昵称、联系方式与安全问题，并在这里修改登录密码。"
      />

      <div class="mt-6 grid items-start gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
        <section class="surface-card overflow-hidden">
          <div class="flex items-center justify-between border-b border-slate-100 px-5 py-4">
            <div>
              <p class="font-mono text-[7px] uppercase tracking-[0.16em] text-[#a29582]">
                Profile / 个人资料
              </p>
              <h2 class="mt-1 font-serif text-[16px] font-medium text-[#211c17]">
                账户信息
              </h2>
            </div>
            <el-button type="primary" :loading="isSavingProfile" @click="saveProfile">
              保存资料
            </el-button>
          </div>

          <div class="grid gap-6 p-5 sm:grid-cols-[150px_minmax(0,1fr)]">
            <div class="flex flex-col items-center gap-3">
              <div class="grid h-24 w-24 place-items-center overflow-hidden border border-[#c9bdab] bg-[#f4eee2]">
                <img
                  v-if="avatarPreview"
                  :src="avatarPreview"
                  alt="用户头像"
                  class="h-full w-full object-cover"
                />
                <span v-else class="font-serif text-[34px] text-[#682728]">
                  {{ authStore.user?.avatarText ?? '访' }}
                </span>
              </div>
              <input
                ref="fileInput"
                type="file"
                accept="image/png,image/jpeg,image/webp,image/gif"
                class="hidden"
                @change="handleAvatarChange"
              />
              <button
                type="button"
                class="inline-flex items-center gap-1.5 border border-[#c9bdab] bg-[#fffdf8] px-3 py-1.5 text-[9px] font-medium text-[#6f6456] transition hover:border-[#a29582]"
                @click="chooseAvatar"
              >
                <el-icon :size="12"><Camera /></el-icon>
                更换头像
              </button>
              <p class="text-center text-[8px] leading-4 text-[#a29582]">
                PNG / JPG / WEBP<br />最大 2 MB
              </p>
            </div>

            <div class="grid gap-4 sm:grid-cols-2">
              <label class="block">
                <span class="mb-1.5 block text-[9px] font-semibold text-slate-600">昵称 *</span>
                <el-input v-model="displayName" maxlength="100" show-word-limit placeholder="展示名称" />
              </label>
              <label class="block">
                <span class="mb-1.5 block text-[9px] font-semibold text-slate-600">账号</span>
                <el-input :model-value="authStore.user?.username ?? ''" disabled />
              </label>
              <label class="block">
                <span class="mb-1.5 block text-[9px] font-semibold text-slate-600">邮箱</span>
                <el-input v-model="email" type="email" placeholder="用于联系与身份识别" />
              </label>
              <label class="block">
                <span class="mb-1.5 block text-[9px] font-semibold text-slate-600">身份预览</span>
                <el-input :model-value="identityPreview" disabled />
                <span class="mt-1 block text-[7.5px] text-slate-400">由专业和年级自动组合</span>
              </label>
              <label class="block">
                <span class="mb-1.5 block text-[9px] font-semibold text-slate-600">专业</span>
                <el-input v-model="major" maxlength="120" placeholder="例如：计算机科学与技术" />
              </label>
              <label class="block">
                <span class="mb-1.5 block text-[9px] font-semibold text-slate-600">年级</span>
                <el-input v-model="grade" maxlength="40" placeholder="例如：本科三年级" />
              </label>
              <label class="block sm:col-span-2">
                <span class="mb-1.5 block text-[9px] font-semibold text-slate-600">个人简介</span>
                <el-input
                  v-model="bio"
                  type="textarea"
                  :autosize="{ minRows: 3, maxRows: 5 }"
                  maxlength="500"
                  show-word-limit
                  placeholder="介绍一下你的学习方向或研究兴趣"
                />
              </label>
            </div>
          </div>
        </section>

        <div class="space-y-5">
          <section class="surface-card overflow-hidden">
            <div class="flex items-center justify-between border-b border-slate-100 px-5 py-4">
              <div class="flex items-center gap-2">
                <span class="grid h-8 w-8 place-items-center border border-[#d8cebd] text-[#7d302f]">
                  <el-icon :size="14"><User /></el-icon>
                </span>
                <div>
                  <h2 class="font-serif text-[14px] font-medium text-[#211c17]">安全问题</h2>
                  <p class="mt-0.5 text-[8px] text-slate-400">用于忘记密码时验证身份</p>
                </div>
              </div>
              <span
                class="rounded border px-1.5 py-0.5 text-[7px] font-medium"
                :class="authStore.user?.hasSecurityQuestion ? 'border-emerald-200 bg-emerald-50 text-emerald-600' : 'border-amber-200 bg-amber-50 text-amber-600'"
              >
                {{ authStore.user?.hasSecurityQuestion ? '已设置' : '未设置' }}
              </span>
            </div>
            <div class="space-y-4 p-5">
              <label class="block">
                <span class="mb-1.5 block text-[9px] font-semibold text-slate-600">安全问题</span>
                <el-select
                  v-model="securityQuestion"
                  filterable
                  allow-create
                  default-first-option
                  placeholder="选择或输入安全问题"
                  class="w-full"
                >
                  <el-option
                    v-for="question in securityQuestionOptions"
                    :key="question"
                    :label="question"
                    :value="question"
                  />
                </el-select>
              </label>
              <label class="block">
                <span class="mb-1.5 block text-[9px] font-semibold text-slate-600">答案 *</span>
                <el-input
                  v-model="securityAnswer"
                  type="password"
                  show-password
                  placeholder="至少 2 个字符"
                  @keyup.enter="saveSecurityQuestion"
                />
              </label>
              <el-button
                class="w-full"
                :loading="isSavingSecurity"
                @click="saveSecurityQuestion"
              >
                保存安全问题
              </el-button>
              <p class="text-[8px] leading-4 text-slate-400">
                修改问题或答案时需要重新填写答案；答案不区分大小写。
              </p>
            </div>
          </section>

          <section class="surface-card overflow-hidden">
            <div class="flex items-center gap-2 border-b border-slate-100 px-5 py-4">
              <span class="grid h-8 w-8 place-items-center border border-[#d8cebd] text-[#7d302f]">
                <el-icon :size="14"><Lock /></el-icon>
              </span>
              <div>
                <h2 class="font-serif text-[14px] font-medium text-[#211c17]">修改密码</h2>
                <p class="mt-0.5 text-[8px] text-slate-400">修改后当前登录状态保持有效</p>
              </div>
            </div>
            <div class="space-y-4 p-5">
              <label class="block">
                <span class="mb-1.5 block text-[9px] font-semibold text-slate-600">当前密码</span>
                <el-input v-model="oldPassword" type="password" show-password placeholder="输入当前密码" />
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
                  @keyup.enter="submitPasswordChange"
                />
              </label>
              <el-button
                class="w-full"
                type="primary"
                :loading="isChangingPassword"
                @click="submitPasswordChange"
              >
                修改密码
              </el-button>
            </div>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>
