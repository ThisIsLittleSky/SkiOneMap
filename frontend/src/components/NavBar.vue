<template>
  <nav class="nav-bar">
    <div class="nav-brand">
      <span class="brand-icon">⛷</span>
      <span class="brand-text">滑雪场 AI 安全监控系统</span>
    </div>
    <div class="nav-links">
      <router-link to="/" class="nav-link" exact-active-class="active">
        <span class="nav-icon">🗺</span>监控大屏
      </router-link>
      <router-link to="/video" class="nav-link" active-class="active">
        <span class="nav-icon">🎬</span>视频管理
      </router-link>
      <router-link to="/alerts" class="nav-link" active-class="active">
        <span class="nav-icon">🔔</span>预警记录
        <span v-if="unreadCount > 0" class="badge">{{ unreadCount }}</span>
      </router-link>
    </div>
    <div class="nav-status">
      <span class="ws-indicator">
        <span class="ws-dot" :class="{ connected: alertStore.wsConnected }"></span>
        {{ alertStore.wsConnected ? '实时连接' : '未连接' }}
      </span>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAlertStore } from '@/stores/alertStore'

const alertStore = useAlertStore()
const unreadCount = computed(() => alertStore.alerts.length)
</script>

<style scoped>
.nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
  background: linear-gradient(90deg, var(--bg-nav-start) 0%, var(--bg-nav-end) 100%);
  border-bottom: 1px solid var(--border-primary);
  flex-shrink: 0;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 8px;
}

.brand-icon {
  font-size: 22px;
}

.brand-text {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.5px;
}

.nav-links {
  display: flex;
  gap: 4px;
  align-items: center;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-secondary);
  text-decoration: none;
  padding: 6px 16px;
  border-radius: 6px;
  font-size: 14px;
  transition: background 0.2s, color 0.2s;
  position: relative;
}

.nav-link:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
}

.nav-link.active {
  background: var(--color-nav-active-bg);
  color: var(--text-white);
}

.nav-icon {
  font-size: 15px;
}

.badge {
  position: absolute;
  top: 2px;
  right: 4px;
  background: var(--color-danger);
  color: var(--text-white);
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 10px;
  min-width: 16px;
  text-align: center;
  line-height: 1.4;
}

.nav-status {
  display: flex;
  align-items: center;
}

.ws-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-muted);
}

.ws-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-ws-dot-off);
  transition: background 0.3s;
}

.ws-dot.connected {
  background: var(--color-success);
  box-shadow: 0 0 6px var(--color-success);
}
</style>
