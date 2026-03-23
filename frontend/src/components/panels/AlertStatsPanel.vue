<template>
  <div class="panel">
    <div class="panel-title">预警统计</div>
    <div class="panel-body">
      <div class="stat-row" v-for="s in stats" :key="s.type">
        <span class="stat-type">{{ s.label }}</span>
        <div class="stat-bar-wrap">
          <div class="stat-bar" :style="{ width: s.pct + '%', background: s.color }"></div>
        </div>
        <span class="stat-count" :style="{ color: s.color }">{{ s.count }}</span>
      </div>
      <div class="total-row">
        <span class="total-label">今日总预警</span>
        <span class="total-num">{{ total }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAlertStore } from '@/stores/alertStore'

const alertStore = useAlertStore()

const TYPES = [
  { type: 'WRONG_WAY', label: '逆行', color: '#ff9800' },
  { type: 'OVERSPEED', label: '超速', color: '#f44336' },
  { type: 'COLLISION_RISK', label: '碰撞风险', color: '#e91e63' },
  { type: 'STILL_DETECTED', label: '静止预警', color: '#9c27b0' },
]

const total = computed(() =>
  alertStore.alerts.flatMap(a => a.subAlerts || []).length
  + alertStore.alerts.filter(a => TYPES.some(t => a.alertType === t.type)).length
)

const stats = computed(() => {
  const counts: Record<string, number> = {}
  TYPES.forEach(t => { counts[t.type] = 0 })
  alertStore.alerts.forEach(a => {
    if (counts[a.alertType] !== undefined) counts[a.alertType]++
    ;(a.subAlerts || []).forEach(s => { if (counts[s.alertType] !== undefined) counts[s.alertType]++ })
  })
  const max = Math.max(1, ...Object.values(counts))
  return TYPES.map(t => ({ ...t, count: counts[t.type], pct: (counts[t.type] / max) * 100 }))
})
</script>

<style scoped>
.panel { height: 100%; display: flex; flex-direction: column; }
.panel-title { font-size: 12px; font-weight: 600; color: #00e5ff; letter-spacing: 1px; padding-bottom: 8px; border-bottom: 1px solid #1e3a5f33; margin-bottom: 10px; }
.panel-body { flex: 1; display: flex; flex-direction: column; gap: 8px; justify-content: center; }

.stat-row { display: flex; align-items: center; gap: 8px; }
.stat-type { width: 56px; font-size: 11px; color: #78909c; flex-shrink: 0; }
.stat-bar-wrap { flex: 1; height: 6px; background: #1e3a5f; border-radius: 3px; overflow: hidden; }
.stat-bar { height: 100%; border-radius: 3px; transition: width 0.8s ease; }
.stat-count { width: 24px; font-size: 12px; font-weight: 600; text-align: right; }

.total-row { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; padding-top: 8px; border-top: 1px solid #1e3a5f33; }
.total-label { font-size: 11px; color: #546e7a; }
.total-num { font-size: 20px; font-weight: 700; color: #00e5ff; }
</style>
