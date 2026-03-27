<template>
  <div class="admin-layout">
    <aside class="sidebar">
      <div class="sidebar-brand">
        <span class="brand-icon">⛷</span>
        <span class="brand-text">后台管理</span>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/admin/video" class="nav-item" active-class="active">
          <span class="nav-icon">🎬</span>
          <span>视频管理</span>
        </router-link>
        <router-link to="/admin/cameras" class="nav-item" active-class="active">
          <span class="nav-icon">📷</span>
          <span>摄像头管理</span>
        </router-link>
        <router-link to="/admin/alerts" class="nav-item" active-class="active">
          <span class="nav-icon">🔔</span>
          <span>预警记录</span>
          <span v-if="alertCount > 0" class="badge">{{ alertCount }}</span>
        </router-link>
        <router-link to="/admin/rag" class="nav-item" active-class="active">
          <span class="nav-icon">📚</span>
          <span>知识库管理</span>
        </router-link>
        <router-link to="/admin/sos" class="nav-item" active-class="active">
          <span class="nav-icon">🆘</span>
          <span>事故救援</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="ws-status">
          <span class="ws-dot" :class="{ connected: alertStore.wsConnected }"></span>
          {{ alertStore.wsConnected ? '实时连接' : '未连接' }}
        </div>
        <router-link to="/" class="back-link">← 返回大屏</router-link>
        <button class="btn-logout" @click="handleLogout">退出登录</button>
      </div>
    </aside>

    <main class="admin-main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAlertStore } from '@/stores/alertStore'
import { logout, removeToken } from '@/api'

const alertStore = useAlertStore()
const alertCount = computed(() => alertStore.alerts.length)
const router = useRouter()

async function handleLogout() {
  try { await logout() } catch { /* ignore */ }
  removeToken()
  router.push('/login')
}
</script>

<style scoped>
.admin-layout {
  width: 100%;
  height: 100vh;
  display: flex;
  background: #0f1923;
  color: #e0e0e0;
}

.sidebar {
  width: 200px;
  flex-shrink: 0;
  background: #0a1929;
  border-right: 1px solid #1e3a5f;
  display: flex;
  flex-direction: column;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px 16px 16px;
  border-bottom: 1px solid #1e3a5f;
}

.brand-icon { font-size: 20px; }

.brand-text {
  font-size: 15px;
  font-weight: 700;
  color: #e3f2fd;
}

.sidebar-nav {
  flex: 1;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  border-radius: 6px;
  font-size: 13px;
  color: #90a4ae;
  text-decoration: none;
  transition: background 0.2s, color 0.2s;
  position: relative;
}

.nav-item:hover {
  background: rgba(144, 202, 249, 0.08);
  color: #e3f2fd;
}

.nav-item.active {
  background: #1565c0;
  color: #fff;
}

.nav-icon { font-size: 15px; flex-shrink: 0; }

.badge {
  margin-left: auto;
  background: #f44336;
  color: #fff;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
}

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid #1e3a5f;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ws-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #546e7a;
}

.ws-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #616161;
  flex-shrink: 0;
}

.ws-dot.connected {
  background: #4caf50;
  box-shadow: 0 0 5px #4caf50;
}

.back-link {
  font-size: 12px;
  color: #546e7a;
  text-decoration: none;
  transition: color 0.2s;
}

.back-link:hover { color: #90caf9; }

.btn-logout {
  background: none;
  border: 1px solid #37474f;
  color: #546e7a;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  text-align: left;
  transition: color 0.2s, border-color 0.2s;
}

.btn-logout:hover {
  color: #ef9a9a;
  border-color: #c62828;
}

.admin-main {
  flex: 1;
  overflow-y: auto;
  background: #0f1923;
}
</style>
