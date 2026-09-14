<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <div class="logo">
          <span class="logo-icon">🔬</span>
          <span class="logo-text">AI金相识别系统</span>
        </div>
        <p class="subtitle">钢铁行业智能金相检测平台</p>
      </div>

      <a-form :model="formState" :rules="rules" @finish="handleLogin" class="login-form" ref="formRef">
        <a-form-item name="username">
          <a-input v-model:value="formState.username" size="large" placeholder="请输入用户名/邮箱">
            <template #prefix><UserOutlined /></template>
          </a-input>
        </a-form-item>

        <a-form-item name="password">
          <a-input-password v-model:value="formState.password" size="large" placeholder="请输入密码">
            <template #prefix><LockOutlined /></template>
          </a-input-password>
        </a-form-item>

        <a-form-item>
          <a-button type="primary" html-type="submit" size="large" block :loading="loading">
            {{ loading ? '登录中...' : '登 录' }}
          </a-button>
        </a-form-item>

        <div class="form-footer">
          <span>还没有账号？</span>
          <router-link to="/auth/register">立即注册</router-link>
        </div>
      </a-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import type { FormInstance } from 'ant-design-vue'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref<FormInstance>()
const loading = ref(false)

const formState = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  try {
    loading.value = true
    await authStore.login(formState)
    message.success('登录成功')
    router.push('/dashboard')
  } catch (error: any) {
    const msg = error.response?.data?.message || '登录失败，请检查网络连接'
    message.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

.login-box {
  width: 400px;
  padding: 48px 40px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-icon {
  font-size: 40px;
}

.logo-text {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
  margin-left: 10px;
}

.subtitle {
  color: #888;
  margin-top: 8px;
  font-size: 14px;
}

.form-footer {
  text-align: center;
  margin-top: 16px;
  color: #888;
}

.form-footer a {
  color: #667eea;
  cursor: pointer;
}

.form-footer a:hover {
  color: #764ba2;
}
</style>