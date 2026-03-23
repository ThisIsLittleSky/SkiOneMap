<template>
  <div class="panel">
    <div class="panel-title">今日分析汇总</div>
    <div class="panel-body">
      <div class="kpi-grid">
        <div class="kpi-item">
          <span class="kpi-num">{{ completedTasks }}</span>
          <span class="kpi-label">已完成任务</span>
        </div>
        <div class="kpi-item">
          <span class="kpi-num warn">{{ totalAlerts }}</span>
          <span class="kpi-label">总预警次数</span>
        </div>
        <div class="kpi-item">
          <span class="kpi-num">{{ totalTracks }}</span>
          <span class="kpi-label">检测轨迹数</span>
        </div>
        <div class="kpi-item">
          <span class="kpi-num danger">{{ processingCount }}</span>
          <span class="kpi-label">分析进行中</span>
        </div>
      </div>
      <div class="recent-title">最近任务</div>
      <div class="recent-list">
        <div v-for="a in recentTasks" :key="a.taskId" class="recent-item">
          <span class="r-id">#{{ a.taskId }}</span>
          <span class="r-status" :class="a.rawStatus?.toLowerCase()">{{ statusText(a.rawStatus) }}</span>
          <span class="r-count" v-if="a.alertCount">{{ a.alertCount }}警</span>
          <span class="r-time">{{ a.createdAt }}</span>
        </div>
        <div v-if="recentTasks.length === 0" class="empty">暂无数据</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAlertStore } from '@/stores/alertStore'

const alertStore = useAlertStore()

const completedTasks = computed(() => alertStore.alerts.filter(a => a.rawStatus === 'COMPLETED').length)
const totalAlerts = computed(() => alertStore.alerts.reduce((s, a) => s + (a.alertCount || 0), 0))
const totalTracks = computed(() => alertStore.alerts.reduce((s, a) => s + (a.trackCount || 0), 0))
const processingCount = computed(() => alertStore.alerts.filter(a => a.rawStatus === 'PROCESSING').length)
const recentTasks = computed(() => alertStore.alerts.slice(0, 5))

function statusText(s?: string) {
  return ({ COMPLETED: '完成', PROCESSING: '分析中', FAILED: '失败', PENDING: '等待' } as Record<string, string>)[s || ''] || s || '-'
}
</script>

<style scoped>
.panel { height: 100%; display: flex; flex-direction: column; }
.panel-title { font-size: 12px; font-weight: 600; color: #00e5ff; letter-spacing: 1px; padding-bottom: 8px; border-bottom: 1px solid #1e3a5f33; margin-bottom: 8px; }
.panel-body { flex: 1; display: flex; flex-direction: column; gap: 8px; overflow: hidden; }

.kpi-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.kpi-item { background: rgba(0,229,255,0.04); border: 1px solid #1e3a5f; border-radius: 6px; padding: 6px; display: flex; flex-direction: column; align-items: center; gap: 3px; }
.kpi-num { font-size: 22px; font-weight: 700; color: #00e5ff; line-height: 1; }
.kpi-num.warn { color: #ff9800; }
.kpi-num.danger { color: #ffb74d; }
.kpi-label { font-size: 10px; color: #90a4ae; }

.recent-title { font-size: 11px; color: #546e7a; }
.recent-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 3px; }
.recent-item { display: flex; align-items: center; gap: 5px; font-size: 11px; padding: 3px 0; border-bottom: 1px solid #1e3a5f22; }
.r-id { color: #00e5ff; width: 36px; flex-shrink: 0; }
.r-status { font-size: 9px; padding: 1px 5px; border-radius: 8px; flex-shrink: 0; }
.r-status.completed { background: rgba(0,229,255,0.1); color: #00e5ff; }
.r-status.processing { background: rgba(255,152,0,0.1); color: #ffb74d; }
.r-status.failed { background: rgba(244,67,54,0.1); color: #ef9a9a; }
.r-count { font-size: 10px; color: #ef9a9a; margin-left: auto; }
.r-time { color: #37474f; font-size: 10px; flex-shrink: 0; }
.empty { font-size: 12px; color: #37474f; text-align: center; padding: 8px; }
</style>
