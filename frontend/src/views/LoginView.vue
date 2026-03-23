<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">
        <span class="logo-icon">⛷</span>
        <span class="logo-title">滑雪场 AI 安全监控系统</span>
      </div>
      <h2 class="login-subtitle">后台管理登录</h2>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-item">
          <label>用户名</label>
          <input
            v-model="username"
            type="text"
            placeholder="请输入用户名"
            autocomplete="username"
            :disabled="loading"
          />
        </div>
        <div class="form-item">
          <label>密码</label>
          <input
            v-model="password"
            type="password"
            placeholder="请输入密码"
            autocomplete="current-password"
            :disabled="loading"
          />
        </div>

        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>

        <button type="submit" class="btn-login" :disabled="loading || !username || !password">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>

      <p class="no-register">系统不开放注册，请联系管理员获取账号</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { login, setToken, removeToken } from '@/api'

const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')

// 每次到登录页都清除旧 token，强制重新登录
onMounted(() => {
  removeToken()
})

async function handleLogin() {
  if (!username.value || !password.value) return
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await login(username.value, password.value)
    setToken(res.data.token)
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch (err: any) {
    errorMsg.value = err.response?.data?.error || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  width: 100%;
  height: 100vh;
  background: #0a1929;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card {
  width: 380px;
  background: #0d1f33;
  border: 1px solid #1e3a5f;
  border-radius: 12px;
  padding: 40px 36px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.login-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.logo-icon { font-size: 28px; }

.logo-title {
  font-size: 15px;
  font-weight: 700;
  color: #e3f2fd;
  letter-spacing: 0.3px;
}

.login-subtitle {
  font-size: 14px;
  color: #546e7a;
  font-weight: 400;
  margin-bottom: 28px;
}

.login-form {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-item label {
  font-size: 12px;
  color: #78909c;
}

.form-item input {
  padding: 10px 14px;
  background: #0a1929;
  border: 1px solid #2a4a6a;
  border-radius: 6px;
  color: #e0e0e0;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.form-item input:focus {
  border-color: #1976d2;
}

.form-item input:disabled {
  opacity: 0.6;
}

.error-msg {
  padding: 8px 12px;
  background: rgba(198, 40, 40, 0.15);
  border: 1px solid #c62828;
  border-radius: 4px;
  color: #ef9a9a;
  font-size: 13px;
}

.btn-login {
  padding: 11px;
  background: #1565c0;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
  margin-top: 4px;
}

.btn-login:hover:not(:disabled) { background: #1976d2; }
.btn-login:disabled { opacity: 0.5; cursor: not-allowed; }

.no-register {
  margin-top: 20px;
  font-size: 12px;
  color: #37474f;
  text-align: center;
}
</style>
