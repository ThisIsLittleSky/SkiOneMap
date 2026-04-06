<template>
  <div class="tracking-page">
    <div class="page-header">
      <h2>天眼追踪</h2>
      <div class="header-actions">
        <button 
          class="btn-mode" 
          :class="{ active: mode === 'color' }" 
          @click="mode = 'color'"
        >按颜色搜索</button>
        <button 
          class="btn-mode" 
          :class="{ active: mode === 'person' }" 
          @click="mode = 'person'"
        >按人员追踪</button>
        <button class="btn-back" @click="goBack">返回</button>
      </div>
    </div>

    <div class="tracking-container">
      <div class="left-panel">
        <div class="video-section">
          <h3>源视频</h3>
          <video v-if="videoUrl" class="video-player" controls :src="videoUrl"></video>
          <p v-else class="tip">加载视频中...</p>
        </div>

        <div v-if="mode === 'person'" class="persons-section">
          <h3>检测到的人员 ({{ persons.length }})</h3>
          <p v-if="personsLoading" class="tip">提取人员中...</p>
          <PersonGrid 
            v-else
            :persons="persons" 
            :selected-id="selectedPersonId"
            @select="selectPerson"
          />
        </div>

        <!-- Color search mode: show color match results in left panel -->
        <div v-if="mode === 'color' && colorSearched" class="persons-section">
          <h3>颜色搜索结果</h3>
          <ColorMatchResults
            :matches="colorMatches"
            :target-color="colorSearchColor"
            :loading="colorSearching"
            :searched="colorSearched"
            :selected-match-id="selectedColorMatchId"
            @select="selectColorMatch"
          />
        </div>
      </div>

      <div class="right-panel">
        <!-- Color search panel -->
        <div v-if="mode === 'color'" class="color-section">
          <ColorSearchPanel
            :camera-ids="selectedCameraIds"
            :searching="colorSearching"
            @search="handleColorSearch"
          />
        </div>

        <!-- Target person (both modes) -->
        <div class="target-section">
          <h3>目标人员</h3>
          <div v-if="effectiveSelectedPerson" class="target-info">
            <img :src="effectiveSelectedPerson.croppedImagePath || effectiveSelectedPerson.cropped_image_path" alt="目标人员" class="target-image" />
            <div class="target-details">
              <p>轨迹ID: {{ effectiveSelectedPerson.trackId || effectiveSelectedPerson.track_id }}</p>
              <p>出现帧数: {{ effectiveSelectedPerson.frameCount || effectiveSelectedPerson.frame_count }}</p>
              <p>帧范围: {{ effectiveSelectedPerson.firstFrame || effectiveSelectedPerson.first_frame }} - {{ effectiveSelectedPerson.lastFrame || effectiveSelectedPerson.last_frame }}</p>
              <p v-if="effectiveSelectedPerson.dominantColor || effectiveSelectedPerson.dominant_color">
                衣服颜色: {{ effectiveSelectedPerson.dominantColor || effectiveSelectedPerson.dominant_color }}
              </p>
            </div>
          </div>
          <p v-else class="tip">{{ mode === 'color' ? '请先选择颜色并搜索，然后选择目标人物' : '请选择要追踪的人员' }}</p>
        </div>

        <div class="camera-section">
          <h3>选择摄像头</h3>
          <CameraSelector 
            :cameras="cameras"
            :selected-ids="selectedCameraIds"
            @update="updateSelectedCameras"
          />
        </div>

        <div v-if="mode === 'person'" class="action-section">
          <button 
            class="btn-track" 
            :disabled="!canStartTracking || trackingInProgress"
            @click="startTracking"
          >
            {{ trackingInProgress ? '追踪中...' : '开始追踪' }}
          </button>
        </div>

        <div v-if="trackingTask" class="result-section">
          <h3>追踪结果</h3>
          <TrackingResult 
            :task="trackingTask"
            :results="trackingResults"
            :loading="resultsLoading"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PersonGrid from '@/components/PersonGrid.vue'
import CameraSelector from '@/components/CameraSelector.vue'
import TrackingResult from '@/components/TrackingResult.vue'
import ColorSearchPanel from '@/components/ColorSearchPanel.vue'
import ColorMatchResults from '@/components/ColorMatchResults.vue'
import { 
  getVideoPersons, 
  getCameraList, 
  createTrackingTask, 
  getTrackingResult,
  getVideoUrl,
  searchByColor,
} from '@/api'
import type { ColorSearchMatch } from '@/api'

const route = useRoute()
const router = useRouter()

const mode = ref<'person' | 'color'>('color')
const videoId = ref<number>(Number(route.query.videoId))
const videoUrl = ref('')
const persons = ref<any[]>([])
const personsLoading = ref(false)
const cameras = ref<any[]>([])
const selectedPersonId = ref<number | null>(null)
const selectedCameraIds = ref<number[]>([])
const trackingInProgress = ref(false)
const trackingTask = ref<any>(null)
const trackingResults = ref<any[]>([])
const resultsLoading = ref(false)

// Color search state
const colorSearching = ref(false)
const colorSearched = ref(false)
const colorSearchColor = ref('')
const colorMatches = ref<ColorSearchMatch[]>([])
const selectedColorMatch = ref<ColorSearchMatch | null>(null)
const selectedColorMatchId = ref<number | null>(null)

const selectedPerson = computed(() => 
  persons.value.find(p => p.id === selectedPersonId.value)
)

const effectiveSelectedPerson = computed(() => {
  if (mode.value === 'color' && selectedColorMatch.value) {
    return selectedColorMatch.value
  }
  return selectedPerson.value
})

const canStartTracking = computed(() => 
  selectedPersonId.value !== null && selectedCameraIds.value.length > 0
)

onMounted(async () => {
  await loadVideo()
  await loadPersons()
  await loadCameras()
})

async function loadVideo() {
  try {
    videoUrl.value = getVideoUrl(videoId.value)
  } catch (err) {
    console.error('Failed to load video:', err)
  }
}

async function loadPersons() {
  personsLoading.value = true
  try {
    const res = await getVideoPersons(videoId.value)
    persons.value = res.data
  } catch (err) {
    console.error('Failed to load persons:', err)
  } finally {
    personsLoading.value = false
  }
}

async function loadCameras() {
  try {
    const res = await getCameraList()
    cameras.value = res.data
  } catch (err) {
    console.error('Failed to load cameras:', err)
  }
}

function selectPerson(personId: number) {
  selectedPersonId.value = personId
}

function updateSelectedCameras(cameraIds: number[]) {
  selectedCameraIds.value = cameraIds
}

async function handleColorSearch(color: string) {
  if (selectedCameraIds.value.length === 0) return
  
  colorSearching.value = true
  colorSearched.value = false
  colorSearchColor.value = color
  colorMatches.value = []
  selectedColorMatch.value = null
  selectedColorMatchId.value = null
  
  try {
    const res = await searchByColor({
      target_color: color,
      camera_ids: selectedCameraIds.value,
    })
    colorMatches.value = res.data.matches
    colorSearched.value = true
  } catch (err) {
    console.error('Failed to search by color:', err)
    colorSearched.value = true
  } finally {
    colorSearching.value = false
  }
}

function selectColorMatch(match: ColorSearchMatch) {
  selectedColorMatch.value = match
  selectedColorMatchId.value = match.person_id
}

async function startTracking() {
  if (!canStartTracking.value) return
  
  trackingInProgress.value = true
  try {
    const person = selectedPerson.value
    const res = await createTrackingTask({
      videoId: videoId.value,
      targetTrackId: person.trackId,
      cameraIds: selectedCameraIds.value
    })
    
    trackingTask.value = res.data
    pollTrackingResult(res.data.id)
  } catch (err) {
    console.error('Failed to start tracking:', err)
    trackingInProgress.value = false
  }
}

async function pollTrackingResult(taskId: number) {
  resultsLoading.value = true
  const maxAttempts = 60
  let attempts = 0
  
  const poll = async () => {
    try {
      const res = await getTrackingResult(taskId)
      trackingTask.value = res.data.task
      trackingResults.value = res.data.results
      
      if (res.data.task.status === 'COMPLETED' || res.data.task.status === 'FAILED') {
        trackingInProgress.value = false
        resultsLoading.value = false
        return
      }
      
      attempts++
      if (attempts < maxAttempts) {
        setTimeout(poll, 3000)
      } else {
        trackingInProgress.value = false
        resultsLoading.value = false
      }
    } catch (err) {
      console.error('Failed to poll tracking result:', err)
      trackingInProgress.value = false
      resultsLoading.value = false
    }
  }
  
  poll()
}

function goBack() {
  router.push('/admin/alerts')
}
</script>

<style scoped>
.tracking-page { padding: 20px; max-width: 1600px; margin: 0 auto; }

.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { color: #90caf9; font-size: 24px; margin: 0; }

.header-actions { display: flex; gap: 8px; align-items: center; }

.btn-mode { 
  padding: 6px 16px; background: #1a2e44; color: #78909c; 
  border: 1px solid #2a4a6a; border-radius: 4px; cursor: pointer; font-size: 13px; transition: all 0.2s; 
}
.btn-mode.active { background: #1976d2; color: #fff; border-color: #1976d2; }
.btn-mode:hover:not(.active) { color: #90caf9; border-color: #1976d2; }

.btn-back { padding: 6px 16px; background: #1a2e44; color: #90caf9; border: 1px solid #2a4a6a; border-radius: 4px; cursor: pointer; font-size: 14px; }

.tracking-container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }

.left-panel, .right-panel { display: flex; flex-direction: column; gap: 20px; }

.video-section, .persons-section, .target-section, .camera-section, .result-section, .color-section { 
  background: #0d1f33; border: 1px solid #1e3a5f; border-radius: 8px; padding: 16px; 
}

h3 { color: #90caf9; font-size: 16px; margin: 0 0 12px 0; }

.video-player { width: 100%; max-height: 400px; background: #000; border-radius: 6px; }

.tip { color: #546e7a; font-size: 13px; text-align: center; padding: 20px 0; }

.target-info { display: flex; gap: 16px; align-items: flex-start; }
.target-image { width: 120px; height: 180px; object-fit: cover; border-radius: 6px; border: 2px solid #1976d2; }
.target-details { flex: 1; color: #90a4ae; font-size: 13px; }
.target-details p { margin: 6px 0; }

.action-section { display: flex; justify-content: center; }
.btn-track { 
  padding: 10px 32px; background: #1976d2; color: #fff; border: none; border-radius: 6px; 
  cursor: pointer; font-size: 15px; font-weight: 500; transition: background 0.2s; 
}
.btn-track:hover:not(:disabled) { background: #1565c0; }
.btn-track:disabled { background: #37474f; color: #78909c; cursor: not-allowed; }
</style>
