<template>
  <div class="color-match-results">
    <div v-if="loading" class="loading">
      <span class="spinner"></span>
      <span>正在搜索{{ colorLabel }}衣服的滑雪者...</span>
    </div>

    <template v-else-if="matches.length > 0">
      <div class="results-header">
        <span>找到 <strong>{{ matches.length }}</strong> 位穿{{ colorLabel }}衣服的滑雪者</span>
        <span class="hint">请点击选择目标人物</span>
      </div>

      <div class="match-grid">
        <div 
          v-for="match in matches" 
          :key="`${match.video_id}_${match.track_id}`"
          class="match-card"
          :class="{ selected: selectedMatchId === match.person_id }"
          @click="$emit('select', match)"
        >
          <div class="match-image-wrap">
            <img :src="match.cropped_image_path" :alt="`Track ${match.track_id}`" class="match-image" />
            <span class="color-badge" :style="{ background: colorHex }">{{ colorLabel }}</span>
            <span class="ratio-badge">{{ (match.color_ratio * 100).toFixed(0) }}%</span>
          </div>
          <div class="match-info">
            <span class="camera-label">摄像头 {{ match.camera_id }}</span>
            <span class="frame-range">帧 {{ match.first_frame }}-{{ match.last_frame }}</span>
          </div>
          <div class="match-actions">
            <button 
              v-if="match.clip_path" 
              class="btn-play"
              @click.stop="playingClip = playingClip === match.person_id ? null : match.person_id"
            >
              {{ playingClip === match.person_id ? '收起视频' : '播放片段' }}
            </button>
          </div>
          <div v-if="playingClip === match.person_id && match.clip_path" class="clip-player">
            <video controls autoplay :src="match.clip_path" class="clip-video"></video>
          </div>
        </div>
      </div>
    </template>

    <div v-else-if="searched" class="no-results">
      <p>未找到穿{{ colorLabel }}衣服的滑雪者</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { ColorSearchMatch } from '@/api'

const COLOR_MAP: Record<string, { label: string; hex: string }> = {
  red: { label: '红色', hex: '#e53935' },
  orange: { label: '橙色', hex: '#fb8c00' },
  yellow: { label: '黄色', hex: '#fdd835' },
  green: { label: '绿色', hex: '#43a047' },
  blue: { label: '蓝色', hex: '#1e88e5' },
  purple: { label: '紫色', hex: '#8e24aa' },
  pink: { label: '粉色', hex: '#ec407a' },
  white: { label: '白色', hex: '#fafafa' },
  gray: { label: '灰色', hex: '#9e9e9e' },
  black: { label: '黑色', hex: '#212121' },
}

const props = defineProps<{
  matches: ColorSearchMatch[]
  targetColor: string
  loading: boolean
  searched: boolean
  selectedMatchId: number | null
}>()

defineEmits<{
  select: [match: ColorSearchMatch]
}>()

const playingClip = ref<number | null>(null)

const colorLabel = computed(() => COLOR_MAP[props.targetColor]?.label || props.targetColor)
const colorHex = computed(() => COLOR_MAP[props.targetColor]?.hex || '#888')
</script>

<style scoped>
.color-match-results { display: flex; flex-direction: column; gap: 12px; }

.loading { 
  text-align: center; padding: 30px 0; color: #78909c; font-size: 13px; 
  display: flex; flex-direction: column; align-items: center; gap: 12px; 
}

.spinner { 
  width: 24px; height: 24px; border: 3px solid #1e3a5f; 
  border-top-color: #1976d2; border-radius: 50%; animation: spin 0.8s linear infinite; 
}

@keyframes spin { to { transform: rotate(360deg); } }

.results-header { 
  display: flex; justify-content: space-between; align-items: center; 
  color: #90caf9; font-size: 14px; padding-bottom: 8px; border-bottom: 1px solid #1e3a5f; 
}

.results-header strong { color: #fff; font-size: 18px; }
.hint { color: #546e7a; font-size: 12px; }

.match-grid { 
  display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); 
  gap: 12px; max-height: 600px; overflow-y: auto; 
}

.match-card { 
  background: #1a2e44; border: 2px solid #2a4a6a; border-radius: 8px; 
  overflow: hidden; cursor: pointer; transition: all 0.2s; 
}

.match-card:hover { border-color: #1976d2; transform: translateY(-2px); }

.match-card.selected { 
  border-color: #1976d2; box-shadow: 0 0 12px rgba(25, 118, 210, 0.4); 
}

.match-image-wrap { position: relative; }

.match-image { width: 100%; height: 220px; object-fit: cover; background: #0d1f33; }

.color-badge { 
  position: absolute; top: 8px; left: 8px; padding: 3px 10px; border-radius: 12px; 
  color: #fff; font-size: 11px; font-weight: 600; 
  text-shadow: 0 1px 2px rgba(0,0,0,0.5); 
}

.ratio-badge { 
  position: absolute; top: 8px; right: 8px; padding: 3px 8px; border-radius: 12px; 
  background: rgba(0,0,0,0.6); color: #81c784; font-size: 11px; font-weight: 600; 
}

.match-info { 
  padding: 8px 10px; display: flex; justify-content: space-between; align-items: center; 
}

.camera-label { color: #90caf9; font-size: 12px; font-weight: 500; }
.frame-range { color: #546e7a; font-size: 11px; }

.match-actions { padding: 0 10px 8px; }

.btn-play { 
  width: 100%; padding: 6px 0; background: rgba(25, 118, 210, 0.15); 
  color: #90caf9; border: 1px solid #2a4a6a; border-radius: 4px; 
  cursor: pointer; font-size: 12px; transition: background 0.2s; 
}

.btn-play:hover { background: rgba(25, 118, 210, 0.3); }

.clip-player { padding: 0 10px 10px; }

.clip-video { width: 100%; border-radius: 4px; background: #000; max-height: 200px; }

.no-results { text-align: center; padding: 30px 0; color: #78909c; font-size: 13px; }

.match-grid::-webkit-scrollbar { width: 6px; }
.match-grid::-webkit-scrollbar-track { background: #0d1f33; }
.match-grid::-webkit-scrollbar-thumb { background: #2a4a6a; border-radius: 3px; }
.match-grid::-webkit-scrollbar-thumb:hover { background: #3a5a7a; }
</style>
