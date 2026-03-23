<template>
  <div class="dashboard">
    <!-- 顶部标题栏 -->
    <header class="dash-header">
      <!-- 顶部装饰角 -->
      <div class="corner-deco top-left"></div>
      <div class="corner-deco top-right"></div>

      <div class="header-left">
        <div class="header-sub">崇礼滑雪场 · 智慧安全监控平台</div>
        <div class="datetime">{{ currentTime }}</div>
      </div>
      <div class="header-center">
        <div class="header-title">
          <span class="title-glow">雪境智判一张图</span>
        </div>
        <div class="title-badge">AI · 数字孪生</div>
      </div>
      <div class="header-right">
        <WeatherPanel :city-code="weatherCityCode" />
        <div class="header-actions">
          <span class="ws-indicator">
            <span class="ws-dot" :class="{ connected: alertStore.wsConnected }"></span>
            {{ alertStore.wsConnected ? '实时' : '断线' }}
          </span>
          <router-link to="/admin" class="btn-admin">后台管理</router-link>
        </div>
      </div>
    </header>

    <!-- 主体：3D 场景 + 绝对定位面板 -->
    <div class="scene-wrapper">
      <!-- 3D 场景 -->
      <SkiScene3D :cameras="cameras" :selected-camera-id="selectedCameraId" class="scene-3d" />

      <!-- 左侧面板（上下两个） -->
      <div class="panel-container left-top">
        <LiabilityPanel />
      </div>
      <div class="panel-container left-bottom">
        <AlertStatsPanel />
      </div>

      <!-- 右侧面板（上下两个） -->
      <div class="panel-container right-top">
      <CameraStatusPanel :cameras="cameras" :selected-id="selectedCameraId" @select-camera="selectedCameraId = $event" />
      </div>
      <div class="panel-container right-bottom">
        <SafetyIndexPanel />
      </div>

      <!-- 底部面板（左右两个） -->
      <div class="panel-container bottom-left">
        <AnalysisSummaryPanel />
      </div>
      <div class="panel-container bottom-right">
        <TrackMonitorPanel />
      </div>

      <!-- 顶部扫描线装饰 -->
      <div class="scan-line"></div>
    </div>

    <!-- 全局 Toast -->
    <AlertToast />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useAlertStore } from '@/stores/alertStore'
import { listCameras, getSceneConfig, type CameraInfo } from '@/api'

import SkiScene3D from '@/components/SkiScene3D.vue'
import WeatherPanel from '@/components/WeatherPanel.vue'
import AlertToast from '@/components/AlertToast.vue'
import LiabilityPanel from '@/components/panels/LiabilityPanel.vue'
import AlertStatsPanel from '@/components/panels/AlertStatsPanel.vue'
import CameraStatusPanel from '@/components/panels/CameraStatusPanel.vue'
import SafetyIndexPanel from '@/components/panels/SafetyIndexPanel.vue'
import AnalysisSummaryPanel from '@/components/panels/AnalysisSummaryPanel.vue'
import TrackMonitorPanel from '@/components/panels/TrackMonitorPanel.vue'

const alertStore = useAlertStore()
const cameras = ref<CameraInfo[]>([])
const weatherCityCode = ref('101090301')
const currentTime = ref('')
const selectedCameraId = ref<number | null>(null)

let timer: ReturnType<typeof setInterval>

function updateTime() {
  currentTime.value = new Date().toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: false,
  })
}

onMounted(async () => {
  updateTime()
  timer = setInterval(updateTime, 1000)
  try {
    const [camRes, cfgRes] = await Promise.all([listCameras(), getSceneConfig()])
    cameras.value = camRes.data
    weatherCityCode.value = cfgRes.data.weatherCityCode || '101090301'
  } catch {}
})

onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.dashboard {
  width: 100%;
  height: 100vh;
  background: #030d18;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
}

/* ── 顶部标题栏 ── */
.dash-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 64px;
  background: linear-gradient(180deg, #061220 0%, #030d18 100%);
  border-bottom: 1px solid #00e5ff22;
  flex-shrink: 0;
  position: relative;
  z-index: 10;
}

.dash-header::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, #00e5ff88, transparent);
}

.header-left { display: flex; flex-direction: column; gap: 2px; }
.header-title { font-size: 22px; font-weight: 700; letter-spacing: 2px; display: flex; align-items: center; gap: 8px; }
.title-glow {
  background: linear-gradient(90deg, #00e5ff, #7c4dff, #00e5ff);
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: shine 4s linear infinite;
}
@keyframes shine { to { background-position: 200% center; } }
.title-badge {
  font-size: 10px;
  padding: 2px 8px;
  background: rgba(124, 77, 255, 0.15);
  color: #b39ddb;
  border: 1px solid #7c4dff44;
  border-radius: 10px;
  letter-spacing: 1px;
  font-weight: 400;
}
.header-sub { font-size: 11px; color: #37474f; letter-spacing: 1px; }

.header-left { display: flex; flex-direction: column; gap: 3px; }
.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
}
.datetime { font-size: 13px; color: #546e7a; font-variant-numeric: tabular-nums; letter-spacing: 1px; }

/* 装饰角 */
.corner-deco {
  position: absolute;
  width: 16px;
  height: 16px;
}
.corner-deco.top-left {
  top: 8px;
  left: 10px;
  border-top: 2px solid #00e5ff66;
  border-left: 2px solid #00e5ff66;
}
.corner-deco.top-right {
  top: 8px;
  right: 10px;
  border-top: 2px solid #00e5ff66;
  border-right: 2px solid #00e5ff66;
}

.header-right { display: flex; align-items: center; gap: 20px; }

.header-actions { display: flex; align-items: center; gap: 12px; }
.ws-indicator { display: flex; align-items: center; gap: 5px; font-size: 11px; color: #37474f; }
.ws-dot { width: 7px; height: 7px; border-radius: 50%; background: #616161; }
.ws-dot.connected { background: #00e5ff; box-shadow: 0 0 6px #00e5ff; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }

.btn-admin {
  padding: 5px 14px;
  background: transparent;
  color: #00e5ff;
  border: 1px solid #00e5ff44;
  border-radius: 4px;
  text-decoration: none;
  font-size: 12px;
  transition: all 0.2s;
}
.btn-admin:hover { background: #00e5ff11; border-color: #00e5ff; }

/* ── 主体场景区域 ── */
.scene-wrapper {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.scene-3d {
  position: absolute;
  inset: 0;
}

/* ── 6个面板定位 ── */
.panel-container {
  position: absolute;
  background: rgba(3, 13, 24, 0.82);
  border: 1px solid #00e5ff1a;
  border-radius: 8px;
  padding: 12px 14px;
  backdrop-filter: blur(12px);
  box-shadow: 0 0 30px rgba(0, 229, 255, 0.05), inset 0 0 20px rgba(0, 229, 255, 0.02);
  transition: border-color 0.3s;
}

.panel-container:hover {
  border-color: #00e5ff44;
}

/* 左侧上 */
.left-top {
  left: 12px;
  top: 12px;
  width: 240px;
  height: calc(50% - 20px);
}

/* 左侧下 */
.left-bottom {
  left: 12px;
  bottom: 12px;
  width: 240px;
  height: calc(50% - 20px);
}

/* 右侧上 */
.right-top {
  right: 12px;
  top: 12px;
  width: 240px;
  height: calc(50% - 20px);
}

/* 右侧下 */
.right-bottom {
  right: 12px;
  bottom: 12px;
  width: 240px;
  height: calc(50% - 20px);
}

/* 底部左 */
.bottom-left {
  left: 264px;
  bottom: 12px;
  width: calc(50% - 280px);
  height: 180px;
}

/* 底部右 */
.bottom-right {
  right: 264px;
  bottom: 12px;
  width: calc(50% - 280px);
  height: 180px;
}

/* 扫描线装饰 */
.scan-line {
  position: absolute;
  left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #00e5ff66, transparent);
  animation: scan 6s linear infinite;
  pointer-events: none;
  top: 0;
}
@keyframes scan {
  0% { top: 0; opacity: 1; }
  90% { opacity: 1; }
  100% { top: 100%; opacity: 0; }
}
</style>
