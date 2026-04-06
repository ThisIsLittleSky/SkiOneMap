<template>
  <div class="color-search-panel">
    <h3>按衣服颜色搜索</h3>
    <div class="color-grid">
      <div 
        v-for="color in colors" 
        :key="color.value"
        class="color-option"
        :class="{ selected: selectedColor === color.value }"
        @click="selectColor(color.value)"
      >
        <span class="color-dot" :style="{ background: color.hex }"></span>
        <span class="color-label">{{ color.label }}</span>
      </div>
    </div>

    <div v-if="selectedColor" class="search-action">
      <span class="selected-tip">已选择: {{ selectedColorLabel }}</span>
      <button 
        class="btn-search" 
        :disabled="searching || cameraIds.length === 0"
        @click="$emit('search', selectedColor)"
      >
        {{ searching ? '搜索中...' : '搜索该颜色' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  cameraIds: number[]
  searching: boolean
}>()

defineEmits<{
  search: [color: string]
}>()

const colors = [
  { value: 'red', label: '红色', hex: '#e53935' },
  { value: 'orange', label: '橙色', hex: '#fb8c00' },
  { value: 'yellow', label: '黄色', hex: '#fdd835' },
  { value: 'green', label: '绿色', hex: '#43a047' },
  { value: 'blue', label: '蓝色', hex: '#1e88e5' },
  { value: 'purple', label: '紫色', hex: '#8e24aa' },
  { value: 'pink', label: '粉色', hex: '#ec407a' },
  { value: 'white', label: '白色', hex: '#fafafa' },
  { value: 'gray', label: '灰色', hex: '#9e9e9e' },
  { value: 'black', label: '黑色', hex: '#212121' },
]

const selectedColor = ref<string | null>(null)

const selectedColorLabel = computed(() => 
  colors.find(c => c.value === selectedColor.value)?.label || ''
)

function selectColor(color: string) {
  selectedColor.value = selectedColor.value === color ? null : color
}
</script>

<style scoped>
.color-search-panel {
  background: #0d1f33;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  padding: 16px;
}

h3 { color: #90caf9; font-size: 16px; margin: 0 0 12px 0; }

.color-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
}

.color-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 10px 4px;
  background: #1a2e44;
  border: 2px solid #2a4a6a;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.color-option:hover { border-color: #1976d2; transform: translateY(-1px); }

.color-option.selected {
  border-color: #1976d2;
  box-shadow: 0 0 10px rgba(25, 118, 210, 0.4);
  background: #1e3548;
}

.color-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid rgba(255,255,255,0.15);
}

.color-label {
  color: #90a4ae;
  font-size: 12px;
}

.search-action {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid #1e3a5f;
}

.selected-tip { color: #78909c; font-size: 13px; }

.btn-search {
  padding: 8px 20px;
  background: #1976d2;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.2s;
}

.btn-search:hover:not(:disabled) { background: #1565c0; }
.btn-search:disabled { background: #37474f; color: #78909c; cursor: not-allowed; }
</style>
