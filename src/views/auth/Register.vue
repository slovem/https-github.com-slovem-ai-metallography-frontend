<template>
  <div class="register-container">
    <div class="register-box">
      <div class="register-header">
        <div class="logo">
          <span class="logo-icon">🔬</span>
          <span class="logo-text">AI金相识别系统</span>
        </div>
        <p class="subtitle">注册新账号，等待管理员审核</p>
      </div>

      <a-form
        :model="formState"
        :rules="rules"
        @finish="handleRegister"
        class="register-form"
        ref="formRef"
        layout="vertical"
      >
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="用户名" name="username">
              <a-input
                v-model:value="formState.username"
                placeholder="请设置用户名"
              >
                <template #prefix><UserOutlined /></template>
              </a-input>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="邮箱" name="email">
              <a-input
                v-model:value="formState.email"
                placeholder="请输入邮箱"
              >
                <template #prefix><MailOutlined /></template>
              </a-input>
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="密码" name="password">
              <a-input-password
                v-model:value="formState.password"
                placeholder="至少6位"
              >
                <template #prefix><LockOutlined /></template>
              </a-input-password>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="确认密码" name="confirmPassword">
              <a-input-password
                v-model:value="formState.confirmPassword"
                placeholder="再次输入密码"
              >
                <template #prefix><LockOutlined /></template>
              </a-input-password>
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="真实姓名" name="realName">
              <a-input
                v-model:value="formState.realName"
                placeholder="请输入真实姓名"
              >
                <template #prefix><IdcardOutlined /></template>
              </a-input>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="手机号" name="phone">
              <a-input
                v-model:value="formState.phone"
                placeholder="请输入手机号"
              >
                <template #prefix><PhoneOutlined /></template>
              </a-input>
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="部门" name="department">
          <a-input
            v-model:value="formState.department"
            placeholder="请输入所属部门"
          >
            <template #prefix><TeamOutlined /></template>
          </a-input>
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            size="large"
            block
            :loading="loading"
          >
            {{ loading ? '注册中...' : '注 册' }}
          </a-button>
        </a-form-item>

        <div class="form-footer">
          <span>已有账号？</span>
          <router-link to="/login">立即登录</router-link>
        </div>

        <div class="register-tip">
          <a-alert
            message="注册须知"
            description="提交注册后，需要等待管理员审核通过方可登录使用。"
            type="info"
            show-icon
          />
        </div>
      </a-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { request } from '@/api/request'
import type { FormInstance } from 'ant-design-vue'

const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)

const formState = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  realName: '',
  phone: '',
  department: ''
})

// 验证确认密码
const validateConfirmPassword = (_rule: any, value: string) => {
  if (!value) {
    return Promise.reject('请确认密码')
  }
  if (value !== formState.password) {
    return Promise.reject('两次输入的密码不一致')
  }
  return Promise.resolve()
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度3-20位', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ],
  realName: [
    { required: true, message: '请输入真实姓名', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ]
}

const handleRegister = async () => {
  try {
    loading.value = true
    await request.post('/auth/register', {
      username: formState.username,
      email: formState.email,
      password: formState.password,
      realName: formState.realName,
      phone: formState.phone,
      department: formState.department
    })
    message.success('注册成功，请等待管理员审核')
    // 跳转到登录页
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  } catch (error: any) {
    const msg = error.response?.data?.message || '注册失败'
    message.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  padding: 40px 20px;
}

.register-box {
  width: 600px;
  max-width: 100%;
  padding: 40px 48px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.register-header {
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

.register-tip {
  margin-top: 16px;
}

.form-footer {
  text-align: center;
  margin-top: 16px;
  color: #888;
}

.form-footer a {
  color: #667eea;
}

.form-footer a:hover {
  color: #764ba2;
}
</style>