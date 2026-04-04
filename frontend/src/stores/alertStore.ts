import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Alert {
  id: number
  taskId: number
  alertType: string
  severity: string
  description: string
  positionX: number
  positionY: number
  createdAt: string
  trackCount?: number
  alertCount?: number
  rawStatus?: string
  liabilitySuggestion?: string
  annotatedVideoAvailable?: boolean
  annotatedVideoUrl?: string
  subAlerts?: Array<{ alertType: string; description: string }>
}

export const useAlertStore = defineStore('alert', () => {
  const alerts = ref<Alert[]>([])
  const wsConnected = ref(false)
  const initialized = ref(false)
  const taskCompletedSignal = ref(0)

  function addAlert(alert: Alert) {
    // 如果已有相同 taskId，替换（WebSocket 更新覆盖历史拉取）
    const idx = alerts.value.findIndex(a => a.taskId === alert.taskId && alert.taskId !== 0)
    if (idx >= 0) {
      alerts.value.splice(idx, 1, alert)
    } else {
      alerts.value.unshift(alert)
    }
    // 保持最多 50 条
    if (alerts.value.length > 50) alerts.value.splice(50)
    // COMPLETED 状态时触发刷新信号
    if (alert.rawStatus === 'COMPLETED' || (alert as any).status === 'COMPLETED') {
      taskCompletedSignal.value++
    }
  }

  function setHistoryAlerts(list: Alert[]) {
    // 批量设置历史数据（不覆盖 WebSocket 已推送的新数据）
    list.forEach(a => {
      const exists = alerts.value.some(x => x.taskId === a.taskId && a.taskId !== 0)
      if (!exists) alerts.value.push(a)
    })
    initialized.value = true
  }

  function clearAlerts() {
    alerts.value = []
  }

  return { alerts, wsConnected, initialized, taskCompletedSignal, addAlert, setHistoryAlerts, clearAlerts }
})
