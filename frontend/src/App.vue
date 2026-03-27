<template>
  <router-view />
  <AlertToast />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useAlertStore } from '@/stores/alertStore'
import { connectWebSocket } from '@/utils/websocket'
import { listTasks, getTaskTracks } from '@/api'
import AlertToast from '@/components/AlertToast.vue'

const alertStore = useAlertStore()
let ws: WebSocket | null = null

function formatTaskMessage(data: any): string {
  if (data.status === 'COMPLETED') {
    const alertPart = data.alertCount > 0
      ? `，发现 ${data.alertCount} 个危险行为预警`
      : '，未检测到危险行为'
    return `任务 ${data.taskId} 分析完成，共 ${data.trackCount || 0} 条轨迹${alertPart}`
  }
  if (data.status === 'FAILED') {
    return `任务 ${data.taskId} 分析失败: ${data.error || '未知错误'}`
  }
  if (data.status === 'PROCESSING') {
    return `任务 ${data.taskId} 正在分析中...`
  }
  return ''
}

onMounted(() => {
  // 拉取历史任务数据填充 alertStore
  loadHistoryTasks()

  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${wsProtocol}//${window.location.host}/ws/alerts`

  ws = connectWebSocket(
    wsUrl,
    (data) => {
      alertStore.addAlert({
        id: Date.now(),
        taskId: data.taskId || 0,
        alertType: data.alertType || data.status || 'INFO',
        severity: data.severity || (data.status === 'FAILED' ? 'ERROR' : 'INFO'),
        description: data.description || formatTaskMessage(data),
        positionX: data.positionX || 0,
        positionY: data.positionY || 0,
        createdAt: new Date().toLocaleString('zh-CN'),
        trackCount: data.trackCount,
        alertCount: data.alertCount,
        rawStatus: data.status,
        liabilitySuggestion: data.liabilitySuggestion || '',
        annotatedVideoAvailable: !!data.annotatedVideoAvailable,
        annotatedVideoUrl: data.annotatedVideoUrl || '',
        subAlerts: Array.isArray(data.alerts) ? data.alerts : []
      })
    },
    () => { alertStore.wsConnected = true },
    () => { alertStore.wsConnected = false }
  )
})

onUnmounted(() => {
  if (ws) {
    ws.close()
    ws = null
  }
})

async function loadHistoryTasks() {
  try {
    const res = await listTasks()
    const completedTasks = res.data.filter(t => t.status === 'COMPLETED').slice(0, 20)
    const details = await Promise.allSettled(
      completedTasks.map(t => getTaskTracks(t.id))
    )
    const historyAlerts = details
      .filter(r => r.status === 'fulfilled')
      .map((r, i) => {
        const d = (r as PromiseFulfilledResult<any>).value.data
        return {
          id: completedTasks[i].id,
          taskId: d.taskId || completedTasks[i].id,
          alertType: 'COMPLETED',
          severity: 'INFO',
          description: `任务 ${d.taskId} 分析完成，共 ${d.trackCount || 0} 条轨迹，${d.alerts?.length || 0} 个预警`,
          positionX: 0,
          positionY: 0,
          createdAt: completedTasks[i].createdAt
            ? new Date(completedTasks[i].createdAt).toLocaleString('zh-CN')
            : '',
          trackCount: d.trackCount,
          alertCount: d.alerts?.length || 0,
          rawStatus: 'COMPLETED',
          liabilitySuggestion: d.liabilitySuggestion || '',
          annotatedVideoAvailable: !!d.annotatedVideoAvailable,
          annotatedVideoUrl: d.annotatedVideoUrl || '',
          subAlerts: d.alerts || [],
        }
      })
    alertStore.setHistoryAlerts(historyAlerts)
  } catch {
    // 后端不可达时静默失败
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  width: 100%;
  height: 100%;
  font-family: 'Microsoft YaHei', sans-serif;
}
</style>
