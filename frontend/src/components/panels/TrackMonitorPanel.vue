<template>
  <div class="panel">
    <div class="panel-title">实时轨迹监控</div>
    <div class="panel-body">
      <div class="track-summary">
        <div class="ts-item">
          <span class="ts-num">{{ totalTracks }}</span>
          <span class="ts-label">累计轨迹</span>
        </div>
        <div class="ts-item">
          <span class="ts-num active">{{ activeTracks }}</span>
          <span class="ts-label">活跃轨迹</span>
        </div>
      </div>
      <div class="event-stream">
        <div class="stream-title">事件流</div>
        <div class="stream-list">
          <TransitionGroup name="stream">
            <div v-for="event in events" :key="event.id" class="stream-item" :class="event.level">
              <span class="event-dot"></span>
              <span class="event-type">{{ event.type }}</span>
              <span class="event-desc">{{ event.desc }}</span>
              <span class="event-time">{{ event.time }}</span>
            </div>
          </TransitionGroup>
          <div v-if="events.length === 0" class="empty">等待事件...</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAlertStore } from '@/stores/alertStore'

const alertStore = useAlertStore()

const totalTracks = computed(() => alertStore.alerts.reduce((s, a) => s + (a.trackCount || 0), 0))
const activeTracks = computed(() => {
  const last = alertStore.alerts.find(a => a.rawStatus === 'PROCESSING')
  return last?.trackCount || 0
})

const events = computed(() =>
  alertStore.alerts.flatMap(a =>
    (a.subAlerts || []).map((s, i) => ({
      id: `${a.id}-${i}`,
      type: s.alertType,
      desc: s.description?.slice(0, 24) || '',
      time: a.createdAt,
      level: ['COLLISION_RISK', 'STILL_DETECTED'].includes(s.alertType) ? 'danger' : 'warn',
    }))
  ).slice(0, 8)
)
</script>

<style scoped>
.panel { height: 100%; display: flex; flex-direction: column; }
.panel-title { font-size: 12px; font-weight: 600; color: #00e5ff; letter-spacing: 1px; padding-bottom: 8px; border-bottom: 1px solid #1e3a5f33; margin-bottom: 8px; }
.panel-body { flex: 1; display: flex; flex-direction: column; gap: 8px; overflow: hidden; }

.track-summary { display: flex; gap: 8px; }
.ts-item { flex: 1; background: rgba(0,229,255,0.04); border: 1px solid #1e3a5f; border-radius: 6px; padding: 8px; display: flex; flex-direction: column; align-items: center; gap: 3px; }
.ts-num { font-size: 22px; font-weight: 700; color: #90caf9; line-height: 1; }
.ts-num.active { color: #00e5ff; }
.ts-label { font-size: 10px; color: #90a4ae; }

.event-stream { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.stream-title { font-size: 11px; color: #546e7a; margin-bottom: 5px; }
.stream-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 4px; }

.stream-item { display: flex; align-items: center; gap: 6px; font-size: 11px; padding: 4px 6px; border-radius: 4px; background: rgba(255,255,255,0.02); border-left: 2px solid #546e7a; }
.stream-item.danger { border-left-color: #f44336; background: rgba(244,67,54,0.06); }
.stream-item.warn { border-left-color: #ff9800; background: rgba(255,152,0,0.06); }

.event-dot { width: 5px; height: 5px; border-radius: 50%; background: currentColor; flex-shrink: 0; }
.event-type { color: #90caf9; font-size: 10px; width: 72px; flex-shrink: 0; overflow: hidden; }
.event-desc { flex: 1; color: #78909c; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.event-time { color: #37474f; font-size: 10px; flex-shrink: 0; }

.empty { font-size: 12px; color: #37474f; text-align: center; padding: 10px; }

.stream-enter-active { transition: all 0.3s ease; }
.stream-enter-from { opacity: 0; transform: translateY(-8px); }
</style>
