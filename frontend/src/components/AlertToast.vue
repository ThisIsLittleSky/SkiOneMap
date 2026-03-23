<template>
  <Teleport to="body">
    <div class="toast-container">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="toast"
          :class="'sev-' + toast.severity.toLowerCase()"
          @click="remove(toast.id)"
        >
          <div class="toast-icon">{{ severityIcon(toast.severity) }}</div>
          <div class="toast-body">
            <div class="toast-title">{{ toast.title }}</div>
            <div class="toast-msg">{{ toast.message }}</div>
          </div>
          <div class="toast-close">×</div>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useAlertStore } from '@/stores/alertStore'

interface Toast {
  id: number
  title: string
  message: string
  severity: string
}

const alertStore = useAlertStore()
const toasts = ref<Toast[]>([])

function severityIcon(sev: string): string {
  const s = sev.toUpperCase()
  if (s === 'DANGER' || s === 'ERROR') return '🚨'
  if (s === 'WARNING') return '⚠️'
  return 'ℹ️'
}

function remove(id: number) {
  toasts.value = toasts.value.filter(t => t.id !== id)
}

let prevLen = 0
watch(() => alertStore.alerts.length, (newLen) => {
  if (newLen <= prevLen) { prevLen = newLen; return }
  const latest = alertStore.alerts[0]
  if (!latest) { prevLen = newLen; return }

  const id = Date.now()
  toasts.value.push({
    id,
    title: latest.alertType || '预警通知',
    message: latest.description?.slice(0, 60) || '',
    severity: latest.severity || 'INFO',
  })
  prevLen = newLen

  setTimeout(() => remove(id), 5000)
})
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 70px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 8px;
  background: #1a2e44;
  border: 1px solid #2a4a6a;
  border-left: 4px solid #2196f3;
  color: #e3f2fd;
  font-size: 13px;
  max-width: 320px;
  cursor: pointer;
  pointer-events: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

.toast.sev-warning {
  border-left-color: #ff9800;
}

.toast.sev-danger,
.toast.sev-error {
  border-left-color: #f44336;
  background: #2a1a1a;
  border-color: #5a2a2a;
}

.toast.sev-info {
  border-left-color: #2196f3;
}

.toast-icon {
  font-size: 18px;
  flex-shrink: 0;
  line-height: 1;
}

.toast-body {
  flex: 1;
  min-width: 0;
}

.toast-title {
  font-weight: 600;
  color: #fff;
  margin-bottom: 2px;
}

.toast-msg {
  color: #90a4ae;
  line-height: 1.4;
  word-break: break-all;
}

.toast-close {
  color: #546e7a;
  font-size: 16px;
  flex-shrink: 0;
  line-height: 1;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(40px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(40px);
}
</style>
