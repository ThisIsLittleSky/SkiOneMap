<template>
  <div class="panel">
    <div class="panel-title">摄像头状态</div>
    <div class="panel-body">
      <div class="summary">
        <div class="sum-item">
          <span class="sum-num online">{{ onlineCount }}</span>
          <span class="sum-label">在线</span>
        </div>
        <div class="divider"></div>
        <div class="sum-item">
          <span class="sum-num offline">{{ offlineCount }}</span>
          <span class="sum-label">离线</span>
        </div>
        <div class="divider"></div>
        <div class="sum-item">
          <span class="sum-num total">{{ cameras.length }}</span>
          <span class="sum-label">总计</span>
        </div>
      </div>
      <div class="cam-list">
        <div v-for="cam in cameras" :key="cam.id" class="cam-row">
          <span class="cam-dot" :class="cam.status === 'ONLINE' ? 'online' : 'offline'"></span>
          <span class="cam-name">{{ cam.name }}</span>
          <span class="cam-status" :class="cam.status === 'ONLINE' ? 'online' : 'offline'">
            {{ cam.status === 'ONLINE' ? '在线' : '离线' }}
          </span>
        </div>
        <div v-if="cameras.length === 0" class="empty">暂无摄像头</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { CameraInfo } from '@/api'

const props = defineProps<{ cameras: CameraInfo[] }>()

const onlineCount = computed(() => props.cameras.filter(c => c.status === 'ONLINE').length)
const offlineCount = computed(() => props.cameras.filter(c => c.status !== 'ONLINE').length)
</script>

<style scoped>
.panel { height: 100%; display: flex; flex-direction: column; }
.panel-title { font-size: 12px; font-weight: 600; color: #00e5ff; letter-spacing: 1px; padding-bottom: 8px; border-bottom: 1px solid #1e3a5f33; margin-bottom: 8px; }
.panel-body { flex: 1; display: flex; flex-direction: column; gap: 8px; overflow: hidden; }

.summary { display: flex; align-items: center; gap: 0; background: rgba(0,229,255,0.04); border: 1px solid #1e3a5f; border-radius: 6px; padding: 8px 0; }
.sum-item { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 2px; }
.sum-num { font-size: 22px; font-weight: 700; line-height: 1; }
.sum-num.online { color: #00e5ff; }
.sum-num.offline { color: #607d8b; }
.sum-num.total { color: #90caf9; }
.sum-label { font-size: 10px; color: #90a4ae; }
.divider { width: 1px; height: 30px; background: #1e3a5f; }

.cam-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 5px; }
.cam-row { display: flex; align-items: center; gap: 7px; font-size: 12px; padding: 3px 0; }
.cam-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.cam-dot.online { background: #00e5ff; box-shadow: 0 0 5px #00e5ff88; }
.cam-dot.offline { background: #607d8b; }
.cam-name { flex: 1; color: #b0bec5; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cam-status { font-size: 10px; }
.cam-status.online { color: #00e5ff; }
.cam-status.offline { color: #607d8b; }
.empty { font-size: 12px; color: #37474f; text-align: center; padding: 10px; }
</style>
