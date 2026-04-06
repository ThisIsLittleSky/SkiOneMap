<template>
  <div class="camera-selector">
    <div v-if="cameras.length === 0" class="empty-tip">暂无可用摄像头</div>
    <div v-else class="camera-list">
      <label 
        v-for="camera in cameras" 
        :key="camera.id"
        class="camera-item"
      >
        <input 
          type="checkbox" 
          :value="camera.id"
          :checked="selectedIds.includes(camera.id)"
          @change="toggleCamera(camera.id)"
        />
        <div class="camera-info">
          <span class="camera-name">{{ camera.name }}</span>
          <span class="camera-desc">{{ camera.description || '无描述' }}</span>
          <span class="camera-status" :class="camera.status.toLowerCase()">
            {{ camera.status }}
          </span>
        </div>
      </label>
    </div>
    <div v-if="cameras.length > 0" class="selector-footer">
      <span class="selected-count">已选择 {{ selectedIds.length }} 个摄像头</span>
      <button class="btn-clear" @click="clearAll">清空</button>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  cameras: any[]
  selectedIds: number[]
}>()

const emit = defineEmits<{
  update: [ids: number[]]
}>()

function toggleCamera(cameraId: number) {
  const newIds = props.selectedIds.includes(cameraId)
    ? props.selectedIds.filter(id => id !== cameraId)
    : [...props.selectedIds, cameraId]
  emit('update', newIds)
}

function clearAll() {
  emit('update', [])
}
</script>

<style scoped>
.camera-selector { display: flex; flex-direction: column; gap: 12px; }

.camera-list { 
  display: flex; 
  flex-direction: column; 
  gap: 8px; 
  max-height: 300px; 
  overflow-y: auto; 
}

.camera-item { 
  display: flex; 
  align-items: center; 
  gap: 10px; 
  padding: 10px; 
  background: #1a2e44; 
  border: 1px solid #2a4a6a; 
  border-radius: 6px; 
  cursor: pointer; 
  transition: background 0.2s; 
}

.camera-item:hover { background: #1e3548; }

.camera-item input[type="checkbox"] { 
  width: 16px; 
  height: 16px; 
  cursor: pointer; 
  accent-color: #1976d2; 
}

.camera-info { 
  flex: 1; 
  display: flex; 
  flex-direction: column; 
  gap: 4px; 
}

.camera-name { 
  color: #90caf9; 
  font-size: 14px; 
  font-weight: 500; 
}

.camera-desc { 
  color: #78909c; 
  font-size: 12px; 
}

.camera-status { 
  font-size: 11px; 
  padding: 2px 8px; 
  border-radius: 10px; 
  width: fit-content; 
}

.camera-status.online { 
  background: rgba(76, 175, 80, 0.2); 
  color: #81c784; 
}

.camera-status.offline { 
  background: rgba(158, 158, 158, 0.2); 
  color: #bdbdbd; 
}

.selector-footer { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  padding-top: 8px; 
  border-top: 1px solid #1e3a5f; 
}

.selected-count { 
  color: #78909c; 
  font-size: 12px; 
}

.btn-clear { 
  padding: 4px 12px; 
  background: transparent; 
  color: #90caf9; 
  border: 1px solid #2a4a6a; 
  border-radius: 4px; 
  cursor: pointer; 
  font-size: 12px; 
}

.btn-clear:hover { background: #1a2e44; }

.empty-tip { 
  color: #546e7a; 
  text-align: center; 
  padding: 20px 0; 
  font-size: 13px; 
}

.camera-list::-webkit-scrollbar { width: 6px; }
.camera-list::-webkit-scrollbar-track { background: #0d1f33; }
.camera-list::-webkit-scrollbar-thumb { background: #2a4a6a; border-radius: 3px; }
.camera-list::-webkit-scrollbar-thumb:hover { background: #3a5a7a; }
</style>
