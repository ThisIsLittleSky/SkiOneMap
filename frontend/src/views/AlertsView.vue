<template>
  <div class="alerts-page">
    <NavBar />
    <div class="page-body">
      <div class="tabs">
        <button :class="{ active: tab === 'alerts' }" @click="tab = 'alerts'">实时预警记录</button>
        <button :class="{ active: tab === 'tasks' }" @click="tab = 'tasks'; loadTasks()">任务列表</button>
      </div>

      <!-- 预警记录 -->
      <div v-if="tab === 'alerts'">
        <div class="section-header">
          <div class="ws-status">
            <span class="ws-dot" :class="{ connected: alertStore.wsConnected }"></span>
            {{ alertStore.wsConnected ? 'WebSocket 已连接' : '未连接' }}
          </div>
          <button class="btn-clear" @click="alertStore.clearAlerts()">清空记录</button>
        </div>

        <p v-if="alertStore.alerts.length === 0" class="tip">暂无预警记录</p>
        <div v-else class="alert-cards">
          <div
            v-for="(alert, index) in alertStore.alerts"
            :key="index"
            class="alert-card"
            :class="'severity-' + (alert.severity || 'info').toLowerCase()"
          >
            <div class="alert-card-header">
              <span class="alert-type">{{ alert.alertType || '任务通知' }}</span>
              <span class="alert-severity">{{ alert.severity || 'INFO' }}</span>
            </div>
            <div class="alert-card-body">
              <p>{{ alert.description }}</p>
              <div v-if="alert.subAlerts && alert.subAlerts.length > 0" class="sub-alerts">
                <strong>危险行为明细：</strong>
                <ul>
                  <li v-for="(sa, si) in alert.subAlerts" :key="si">
                    [{{ sa.alertType }}] {{ sa.description }}
                  </li>
                </ul>
              </div>
              <div v-if="alert.liabilitySuggestion" class="liability">
                <strong>定责建议：</strong>
                <pre>{{ alert.liabilitySuggestion }}</pre>
              </div>
            </div>
            <div class="alert-card-footer">
              <span v-if="alert.taskId">任务ID: {{ alert.taskId }}</span>
              <span v-if="alert.createdAt">{{ alert.createdAt }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 任务列表 -->
      <div v-if="tab === 'tasks'">
        <div class="section-header">
          <span class="tip-sm">共 {{ tasks.length }} 条任务</span>
          <button class="btn-clear" @click="loadTasks">刷新</button>
        </div>
        <p v-if="tasksLoading" class="tip">加载中...</p>
        <p v-else-if="tasks.length === 0" class="tip">暂无任务</p>
        <table v-else>
          <thead>
            <tr>
              <th>任务ID</th>
              <th>视频ID</th>
              <th>状态</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="task in tasks" :key="task.id">
              <td>{{ task.id }}</td>
              <td>{{ task.videoId }}</td>
              <td>
                <span class="status-badge" :class="'status-' + task.status.toLowerCase()">
                  {{ taskStatusText(task.status) }}
                </span>
              </td>
              <td>{{ formatDate(task.createdAt) }}</td>
              <td>
                <button class="btn-detail" @click="showTaskDetail(task.id)">查看结果</button>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- 任务结果详情 -->
        <div v-if="taskDetail" class="task-detail">
          <div class="detail-header">
            <span>任务 {{ taskDetail.taskId }} 分析结果</span>
            <button class="btn-close" @click="closeTaskDetail">×</button>
          </div>
          <div class="detail-body">
            <p>轨迹数量：{{ taskDetail.trackCount }}</p>
            <p>预警数量：{{ taskDetail.alerts.length }}</p>
            <div v-if="taskDetail.annotatedVideoAvailable" class="annotated-video">
              <strong>标注视频：</strong>
              <button class="btn-detail" @click="taskPlayerSrc = taskDetail.annotatedVideoUrl">播放标注视频</button>
              <video v-if="taskPlayerSrc" class="detail-video" controls :src="taskPlayerSrc"></video>
            </div>
            <div v-if="taskDetail.liabilitySuggestion" class="liability">
              <strong>定责建议：</strong>
              <pre>{{ taskDetail.liabilitySuggestion }}</pre>
            </div>
            <div v-if="taskDetail.alerts.length > 0" class="detail-alerts">
              <strong>预警明细：</strong>
              <ul>
                <li v-for="a in taskDetail.alerts" :key="a.id">
                  [{{ a.alertType }}] {{ a.description }} ({{ a.severity }})
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import NavBar from '@/components/NavBar.vue'
import { useAlertStore } from '@/stores/alertStore'
import { listTasks, getTaskTracks, type TrackSummary } from '@/api'

const alertStore = useAlertStore()
const tab = ref<'alerts' | 'tasks'>('alerts')

const tasks = ref<Array<{ id: number; videoId: number; status: string; createdAt: string }>>([])
const tasksLoading = ref(false)
const taskDetail = ref<TrackSummary | null>(null)
const taskPlayerSrc = ref('')
let tasksPollTimer: number | null = null

async function loadTasks() {
  tasksLoading.value = true
  try {
    const res = await listTasks()
    tasks.value = [...res.data].sort((a, b) => b.id - a.id)
  } catch (err) {
    console.error('Failed to load tasks:', err)
  } finally {
    tasksLoading.value = false
  }
}

function stopTaskPolling() {
  if (tasksPollTimer !== null) {
    window.clearInterval(tasksPollTimer)
    tasksPollTimer = null
  }
}

function startTaskPolling() {
  stopTaskPolling()
  loadTasks()
  tasksPollTimer = window.setInterval(() => {
    if (tab.value === 'tasks') loadTasks()
  }, 3000)
}

async function showTaskDetail(taskId: number) {
  try {
    const res = await getTaskTracks(taskId)
    taskDetail.value = res.data
    taskPlayerSrc.value = ''
  } catch (err) {
    console.error('Failed to load task detail:', err)
  }
}

function closeTaskDetail() {
  taskDetail.value = null
  taskPlayerSrc.value = ''
}

function taskStatusText(status: string): string {
  const map: Record<string, string> = {
    PENDING: '待处理', PROCESSING: '分析中', COMPLETED: '已完成', FAILED: '失败',
  }
  return map[status] || status
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  try { return new Date(dateStr).toLocaleString('zh-CN') } catch { return dateStr }
}

watch(tab, (value) => {
  if (value === 'tasks') startTaskPolling()
  else stopTaskPolling()
}, { immediate: true })

watch(() => alertStore.alerts.length, () => {
  if (tab.value === 'tasks') loadTasks()
})

onBeforeUnmount(() => {
  stopTaskPolling()
})
</script>

<style scoped>
.alerts-page {
  width: 100%;
  min-height: 100vh;
  background: #0a1929;
  color: #e0e0e0;
  display: flex;
  flex-direction: column;
}

.page-body {
  padding: 20px 28px;
  max-width: 1100px;
  width: 100%;
  margin: 0 auto;
}

.tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 16px;
  border-bottom: 1px solid #1e3a5f;
  padding-bottom: 0;
}

.tabs button {
  padding: 8px 20px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: #78909c;
  font-size: 14px;
  cursor: pointer;
  margin-bottom: -1px;
}

.tabs button.active {
  color: #90caf9;
  border-bottom-color: #1976d2;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.ws-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #78909c;
}

.ws-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #616161;
}

.ws-dot.connected {
  background: #4caf50;
  box-shadow: 0 0 5px #4caf50;
}

.btn-clear {
  padding: 4px 12px;
  font-size: 12px;
  background: #1a2e44;
  color: #90caf9;
  border: 1px solid #2a4a6a;
  border-radius: 4px;
  cursor: pointer;
}

.tip { color: #37474f; font-size: 14px; padding: 20px 0; }
.tip-sm { font-size: 12px; color: #546e7a; }

/* Alert cards */
.alert-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.alert-card {
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  overflow: hidden;
  border-left: 4px solid #2196f3;
  background: #0d1f33;
}

.alert-card.severity-warning { border-left-color: #ff9800; }
.alert-card.severity-danger,
.alert-card.severity-error { border-left-color: #f44336; }
.alert-card.severity-info { border-left-color: #2196f3; }

.alert-card-header {
  display: flex;
  justify-content: space-between;
  padding: 8px 14px;
  background: rgba(255,255,255,0.03);
  font-size: 13px;
  border-bottom: 1px solid #1e3a5f;
}

.alert-type { font-weight: 600; color: #cfd8dc; }

.alert-severity {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(33,150,243,0.15);
  color: #64b5f6;
}

.alert-card-body { padding: 10px 14px; font-size: 13px; color: #90a4ae; }

.sub-alerts { margin-top: 8px; }
.sub-alerts ul { margin-top: 4px; padding-left: 16px; }
.sub-alerts li { margin-bottom: 3px; line-height: 1.5; }

.liability {
  margin-top: 10px;
  padding: 8px 12px;
  background: rgba(25,118,210,0.08);
  border-left: 3px solid #1976d2;
  border-radius: 0 4px 4px 0;
  font-size: 12px;
}

.liability pre {
  white-space: pre-wrap;
  word-break: break-word;
  margin-top: 4px;
  font-family: 'Microsoft YaHei', sans-serif;
  font-size: 12px;
  line-height: 1.7;
  color: #b0bec5;
}

.alert-card-footer {
  display: flex;
  justify-content: space-between;
  padding: 6px 14px;
  font-size: 11px;
  color: #37474f;
  border-top: 1px solid #1a2e44;
}

/* Tasks table */
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

th, td {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid #1a2e44;
}

th { background: #0d1f33; color: #78909c; font-weight: 600; }
tr:hover td { background: rgba(21,101,192,0.06); }

.status-badge {
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.status-pending { background: rgba(96,125,139,0.2); color: #90a4ae; }
.status-processing { background: rgba(230,81,0,0.2); color: #ffb74d; }
.status-completed { background: rgba(46,125,50,0.2); color: #81c784; }
.status-failed { background: rgba(198,40,40,0.2); color: #ef9a9a; }

.btn-detail {
  padding: 4px 10px;
  font-size: 12px;
  background: transparent;
  color: #64b5f6;
  border: 1px solid #1565c0;
  border-radius: 4px;
  cursor: pointer;
}

/* Task detail panel */
.task-detail {
  margin-top: 20px;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  background: #0d1f33;
  overflow: hidden;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid #1e3a5f;
  font-size: 14px;
  color: #90caf9;
}

.btn-close {
  background: none;
  border: none;
  color: #546e7a;
  font-size: 20px;
  cursor: pointer;
}

.detail-body {
  padding: 14px 16px;
  font-size: 13px;
  color: #90a4ae;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.annotated-video { display: flex; flex-direction: column; gap: 8px; }

.detail-video {
  width: 100%;
  max-height: 420px;
  background: #000;
  border-radius: 6px;
}

.detail-alerts ul {
  margin-top: 6px;
  padding-left: 16px;
}

.detail-alerts li { margin-bottom: 4px; line-height: 1.5; }
</style>
