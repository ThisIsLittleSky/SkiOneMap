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
        <div
          v-for="cam in cameras" :key="cam.id"
          class="cam-row"
          :class="{ active: selectedId === cam.id }"
          @click="emit('select-camera', cam.id)"
        >
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

const props = defineProps<{ cameras: CameraInfo[]; selectedId?: number | null }>()
const emit = defineEmits<{ (e: 'select-camera', id: number): void }>()

const onlineCount = computed(() => props.cameras.filter(c => c.status === 'ONLINE').length)
const offlineCount = computed(() => props.cameras.filter(c => c.status !== 'ONLINE').length)
</script>

<style scoped>
.panel { height: 100%; display: flex; flex-direction: column; }
.panel-title { font-size: 12px; font-weight: 600; color: var(--color-primary); letter-spacing: 1px; padding-bottom: 8px; border-bottom: 1px solid var(--panel-title-border); margin-bottom: 8px; }
.panel-body { flex: 1; display: flex; flex-direction: column; gap: 8px; overflow: hidden; }

.summary { display: flex; align-items: center; gap: 0; background: var(--bg-card); border: 1px solid var(--border-primary); border-radius: 6px; padding: 8px 0; }
.sum-item { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 2px; }
.sum-num { font-size: 22px; font-weight: 700; line-height: 1; }
.sum-num.online { color: var(--color-primary); }
.sum-num.offline { color: var(--color-offline); }
.sum-num.total { color: var(--text-secondary); }
.sum-label { font-size: 10px; color: var(--text-muted); }
.divider { width: 1px; height: 30px; background: var(--border-primary); }

.cam-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 5px; }
.cam-row { display: flex; align-items: center; gap: 7px; font-size: 12px; padding: 5px 6px; border-radius: 4px; cursor: pointer; transition: background 0.15s; }
.cam-row:hover { background: var(--bg-card-hover); }
.cam-row.active { background: var(--bg-card-active); border: 1px solid var(--border-accent); }
.cam-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.cam-dot.online { background: var(--color-primary); box-shadow: 0 0 5px var(--color-primary-glow); }
.cam-dot.offline { background: var(--color-offline); }
.cam-name { flex: 1; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cam-status { font-size: 10px; }
.cam-status.online { color: var(--color-primary); }
.cam-status.offline { color: var(--color-offline); }
.empty { font-size: 12px; color: var(--text-dark); text-align: center; padding: 10px; }
</style>
