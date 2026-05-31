<template>
  <div class="admin-layout">
    <aside class="sidebar">
      <div class="sidebar-brand">
        <button
          class="theme-toggle-top"
          @click="toggleTheme"
          :title="theme === 'dark' ? '切换到冰雪极简风' : '切换到暗黑科技风'"
        >
          <svg v-if="theme === 'dark'" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <line x1="12" y1="2" x2="12" y2="22"/><line x1="2" y1="12" x2="22" y2="12"/>
            <line x1="4" y1="4" x2="20" y2="20"/><line x1="20" y1="4" x2="4" y2="20"/>
          </svg>
          <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
          </svg>
        </button>
        <span class="brand-icon">⛷</span>
        <span class="brand-text">后台管理</span>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/admin/ai" class="nav-item" active-class="active">
          <span class="nav-icon">🦊</span>
          <span>雪境智判AI</span>
        </router-link>
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
import { useTheme } from '@/composables/useTheme'
import { logout, removeToken } from '@/api'

const alertStore = useAlertStore()
const alertCount = computed(() => alertStore.alerts.length)
const router = useRouter()
const { theme, toggleTheme } = useTheme()

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
  background: var(--bg-admin-page);
  color: var(--text-primary);
}

.sidebar {
  width: 200px;
  flex-shrink: 0;
  background: var(--bg-admin-input-alt);
  border-right: 1px solid var(--border-primary);
  display: flex;
  flex-direction: column;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  border-bottom: 1px solid var(--border-primary);
}

.theme-toggle-top {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  margin: 0;
  background: var(--bg-admin-input);
  color: var(--text-secondary);
  border: 1px solid var(--border-admin-input);
  border-radius: 4px;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.25s;
}

.theme-toggle-top:hover {
  background: var(--bg-card-active);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.theme-toggle-top svg {
  flex-shrink: 0;
  opacity: 0.85;
}

.theme-toggle-top:hover svg {
  opacity: 1;
}

.brand-icon { font-size: 20px; }

.brand-text {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
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
  color: var(--text-muted);
  text-decoration: none;
  transition: background 0.2s, color 0.2s;
  position: relative;
}

.nav-item:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--color-nav-active-bg);
  color: var(--text-primary);
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
  border-top: 1px solid var(--border-primary);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ws-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-dim);
}

.ws-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-ws-dot-off);
  flex-shrink: 0;
}

.ws-dot.connected {
  background: var(--color-success);
  box-shadow: 0 0 5px var(--color-success);
}

.back-link {
  font-size: 12px;
  color: var(--text-dim);
  text-decoration: none;
  transition: color 0.2s;
}

.back-link:hover { color: var(--text-secondary); }

.btn-logout {
  background: none;
  border: 1px solid var(--text-dark);
  color: var(--text-dim);
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  text-align: left;
  transition: color 0.2s, border-color 0.2s;
}

.btn-logout:hover {
  color: var(--text-danger);
  border-color: #c62828;
}

.admin-main {
  flex: 1;
  overflow-y: auto;
  background: var(--bg-admin-page);
}
</style>
