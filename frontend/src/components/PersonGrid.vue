<template>
  <div class="person-grid">
    <div 
      v-for="person in persons" 
      :key="person.id"
      class="person-card"
      :class="{ selected: person.id === selectedId }"
      @click="$emit('select', person.id)"
    >
      <img :src="person.croppedImagePath" :alt="`Track ${person.trackId}`" class="person-image" />
      <div class="person-info">
        <span class="track-id">ID: {{ person.trackId }}</span>
        <span class="frame-count">{{ person.frameCount }} 帧</span>
      </div>
    </div>
    <p v-if="persons.length === 0" class="empty-tip">暂无检测到的人员</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  persons: any[]
  selectedId: number | null
}>()

defineEmits<{
  select: [id: number]
}>()
</script>

<style scoped>
.person-grid { 
  display: grid; 
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); 
  gap: 12px; 
  max-height: 500px; 
  overflow-y: auto; 
}

.person-card { 
  background: #1a2e44; 
  border: 2px solid #2a4a6a; 
  border-radius: 8px; 
  overflow: hidden; 
  cursor: pointer; 
  transition: all 0.2s; 
}

.person-card:hover { 
  border-color: #1976d2; 
  transform: translateY(-2px); 
}

.person-card.selected { 
  border-color: #1976d2; 
  box-shadow: 0 0 12px rgba(25, 118, 210, 0.4); 
}

.person-image { 
  width: 100%; 
  height: 180px; 
  object-fit: cover; 
  background: #0d1f33; 
}

.person-info { 
  padding: 8px; 
  display: flex; 
  flex-direction: column; 
  gap: 4px; 
}

.track-id { 
  color: #90caf9; 
  font-size: 13px; 
  font-weight: 500; 
}

.frame-count { 
  color: #78909c; 
  font-size: 11px; 
}

.empty-tip { 
  grid-column: 1 / -1; 
  color: #546e7a; 
  text-align: center; 
  padding: 40px 0; 
  font-size: 13px; 
}

.person-grid::-webkit-scrollbar { width: 6px; }
.person-grid::-webkit-scrollbar-track { background: #0d1f33; }
.person-grid::-webkit-scrollbar-thumb { background: #2a4a6a; border-radius: 3px; }
.person-grid::-webkit-scrollbar-thumb:hover { background: #3a5a7a; }
</style>
