<template>
  <div class="panel">
    <div class="panel-title">雪道安全指数</div>
    <div class="panel-body">
      <div class="index-circle">
        <svg viewBox="0 0 120 120" class="circle-svg">
          <!-- 背景轨道 -->
          <circle cx="60" cy="60" r="50" fill="none" stroke="#1e3a5f" stroke-width="8"/>
          <!-- 进度弧（从顶部顺时针，跨度 270°） -->
          <circle
            cx="60" cy="60" r="50" fill="none"
            :stroke="indexColor" stroke-width="8"
            stroke-linecap="round"
            :stroke-dasharray="`${safetyPct * 3.14159 * 100 / 100 * 2.7 / (2 * 3.14159) * 314.15} 314.15`"
            stroke-dashoffset="78.5"
            class="progress-circle"
          />
          <!-- 刻度 tick marks -->
          <g v-for="i in 9" :key="i">
            <line
              :x1="60 + 46 * Math.cos((-135 + i * 33.75) * Math.PI / 180)"
              :y1="60 + 46 * Math.sin((-135 + i * 33.75) * Math.PI / 180)"
              :x2="60 + 52 * Math.cos((-135 + i * 33.75) * Math.PI / 180)"
              :y2="60 + 52 * Math.sin((-135 + i * 33.75) * Math.PI / 180)"
              stroke="#1e3a5f" stroke-width="1.5"
            />
          </g>
        </svg>
        <div class="index-center">
          <div class="index-value" :style="{ color: indexColor }">{{ safetyIndex }}</div>
          <div class="index-label">安全评分</div>
          <div class="index-level" :style="{ color: indexColor }">{{ levelText }}</div>
        </div>
      </div>
      <div class="factors">
        <div class="factor" v-for="f in factors" :key="f.name">
          <span class="factor-name">{{ f.name }}</span>
          <div class="factor-bar-wrap">
            <div class="factor-bar" :style="{ width: f.val + '%', background: f.color }"></div>
          </div>
          <span class="factor-val" :style="{ color: f.color }">{{ f.val }}</span>
        </div>
      </div>
      <div class="risk-level-row">
        <div class="risk-dot" :style="{ background: indexColor, boxShadow: `0 0 8px ${indexColor}` }"></div>
        <span class="risk-text" :style="{ color: indexColor }">{{ levelText }}状态</span>
        <span class="risk-tip">{{ riskTip }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAlertStore } from '@/stores/alertStore'

const alertStore = useAlertStore()

const dangerCount = computed(() =>
  alertStore.alerts.flatMap(a => a.subAlerts || []).filter(s =>
    s.alertType === 'COLLISION_RISK' || s.alertType === 'STILL_DETECTED'
  ).length +
  alertStore.alerts.filter(a => ['COLLISION_RISK', 'STILL_DETECTED'].includes(a.alertType)).length
)

const safetyIndex = computed(() =>
  Math.max(0, Math.min(100, 100 - dangerCount.value * 8 - alertStore.alerts.filter(a => a.alertCount && a.alertCount > 0).length * 2))
)
const safetyPct = computed(() => safetyIndex.value)

const indexColor = computed(() => {
  if (safetyIndex.value >= 80) return '#00e5ff'
  if (safetyIndex.value >= 50) return '#ff9800'
  return '#f44336'
})

const levelText = computed(() => {
  if (safetyIndex.value >= 80) return '优良'
  if (safetyIndex.value >= 60) return '一般'
  if (safetyIndex.value >= 40) return '注意'
  return '危险'
})

const riskTip = computed(() => {
  if (safetyIndex.value >= 80) return '雪道运行正常'
  if (safetyIndex.value >= 60) return '请注意安全'
  if (safetyIndex.value >= 40) return '存在安全风险'
  return '立即介入处置'
})

const factors = computed(() => [
  { name: '逆行', val: Math.max(0, 100 - alertStore.alerts.filter(a => a.alertType === 'WRONG_WAY').length * 15), color: '#ff9800' },
  { name: '超速', val: Math.max(0, 100 - alertStore.alerts.filter(a => a.alertType === 'OVERSPEED').length * 15), color: '#f44336' },
  { name: '碰撞', val: Math.max(0, 100 - dangerCount.value * 20), color: '#e91e63' },
])
</script>

<style scoped>
.panel { height: 100%; display: flex; flex-direction: column; }
.panel-title { font-size: 12px; font-weight: 600; color: #00e5ff; letter-spacing: 1px; padding-bottom: 8px; border-bottom: 1px solid #1e3a5f33; margin-bottom: 8px; }
.panel-body { flex: 1; display: flex; flex-direction: column; gap: 8px; align-items: center; }

.index-circle {
  position: relative;
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.circle-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  transform: rotate(-135deg);
  filter: drop-shadow(0 0 6px currentColor);
}
.progress-circle { transition: stroke-dasharray 1.2s cubic-bezier(0.4,0,0.2,1); }

.index-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 1;
}
.index-value { font-size: 28px; font-weight: 800; line-height: 1; transition: color 0.5s; }
.index-label { font-size: 9px; color: #90a4ae; margin-top: 1px; }
.index-level { font-size: 11px; font-weight: 600; margin-top: 2px; }

.factors { width: 100%; display: flex; flex-direction: column; gap: 5px; }
.factor { display: flex; align-items: center; gap: 5px; }
.factor-name { width: 28px; font-size: 10px; color: #546e7a; flex-shrink: 0; }
.factor-bar-wrap { flex: 1; height: 4px; background: #1e3a5f; border-radius: 2px; overflow: hidden; }
.factor-bar { height: 100%; border-radius: 2px; transition: width 1s ease; }
.factor-val { font-size: 10px; width: 22px; text-align: right; flex-shrink: 0; }

.risk-level-row { display: flex; align-items: center; gap: 6px; width: 100%; }
.risk-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.5;} }
.risk-text { font-size: 11px; font-weight: 600; }
.risk-tip { font-size: 10px; color: #37474f; margin-left: auto; }
</style>
