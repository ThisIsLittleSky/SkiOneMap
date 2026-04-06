<template>
  <div class="tracking-result">
    <div v-if="loading" class="loading">
      <span class="spinner"></span>
      <span>分析追踪结果中...</span>
    </div>

    <div v-else-if="task && task.status === 'COMPLETED'">
      <div class="result-summary">
        <div class="summary-item">
          <span class="label">任务状态</span>
          <span class="value success">已完成</span>
        </div>
        <div class="summary-item">
          <span class="label">匹配数量</span>
          <span class="value">{{ results.length }}</span>
        </div>
      </div>

      <div v-if="results.length === 0" class="no-results">
        <p>未在选定摄像头中找到目标人员</p>
      </div>

      <div v-else class="result-list">
        <div v-for="result in results" :key="result.id" class="result-card">
          <div class="result-header">
            <span class="camera-name">摄像头: {{ getCameraName(result.cameraId) }}</span>
            <span class="confidence" :class="getConfidenceClass(result.confidence)">
              置信度: {{ (result.confidence * 100).toFixed(1) }}%
            </span>
          </div>

          <div class="result-body">
            <div class="result-info">
              <p><strong>视频ID:</strong> {{ result.videoId }}</p>
              <p><strong>发现帧:</strong> {{ result.foundAtFrame }}</p>
            </div>

            <div class="video-action">
              <button class="btn-play" @click="toggleVideo(result.videoId)">
                {{ playingVideoId === result.videoId ? '收起视频' : '播放视频' }}
              </button>
            </div>

            <div v-if="playingVideoId === result.videoId" class="video-player-wrap">
              <video controls autoplay :src="getResultVideoUrl(result.videoId)" class="result-video"></video>
            </div>

            <div v-if="result.appearanceFeatures" class="appearance">
              <strong>穿着特征:</strong>
              <p>{{ result.appearanceFeatures }}</p>
            </div>

            <div v-if="result.predictedRoute" class="route">
              <strong>预测路线:</strong>
              <p>{{ result.predictedRoute }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="task && task.status === 'FAILED'" class="error">
      <p>追踪任务失败，请重试</p>
    </div>

    <div v-else-if="task && task.status === 'PROCESSING'" class="processing">
      <span class="spinner"></span>
      <p>正在处理追踪任务...</p>
    </div>

    <div v-else class="empty">
      <p>暂无追踪结果</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  task: any
  results: any[]
  loading: boolean
}>()

const playingVideoId = ref<number | null>(null)

function getCameraName(cameraId: number): string {
  return `摄像头 ${cameraId}`
}

function getConfidenceClass(confidence: number): string {
  if (confidence >= 0.8) return 'high'
  if (confidence >= 0.6) return 'medium'
  return 'low'
}

function getResultVideoUrl(videoId: number): string {
  return `/api/video/${videoId}/stream`
}

function toggleVideo(videoId: number) {
  playingVideoId.value = playingVideoId.value === videoId ? null : videoId
}
</script>

<style scoped>
.tracking-result { display: flex; flex-direction: column; gap: 12px; }

.loading, .processing, .empty, .error, .no-results { 
  text-align: center; 
  padding: 30px 0; 
  color: #78909c; 
  font-size: 13px; 
}

.loading, .processing { display: flex; flex-direction: column; align-items: center; gap: 12px; }

.spinner { 
  width: 24px; 
  height: 24px; 
  border: 3px solid #1e3a5f; 
  border-top-color: #1976d2; 
  border-radius: 50%; 
  animation: spin 0.8s linear infinite; 
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.result-summary { 
  display: grid; 
  grid-template-columns: 1fr 1fr; 
  gap: 12px; 
  margin-bottom: 16px; 
}

.summary-item { 
  background: #1a2e44; 
  padding: 12px; 
  border-radius: 6px; 
  display: flex; 
  flex-direction: column; 
  gap: 6px; 
}

.summary-item .label { 
  color: #78909c; 
  font-size: 12px; 
}

.summary-item .value { 
  color: #90caf9; 
  font-size: 18px; 
  font-weight: 600; 
}

.summary-item .value.success { color: #81c784; }

.result-list { 
  display: flex; 
  flex-direction: column; 
  gap: 12px; 
  max-height: 500px; 
  overflow-y: auto; 
}

.result-card { 
  background: #1a2e44; 
  border: 1px solid #2a4a6a; 
  border-radius: 8px; 
  overflow: hidden; 
}

.result-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  padding: 10px 14px; 
  background: rgba(25, 118, 210, 0.08); 
  border-bottom: 1px solid #2a4a6a; 
}

.camera-name { 
  color: #90caf9; 
  font-size: 14px; 
  font-weight: 500; 
}

.confidence { 
  font-size: 12px; 
  padding: 3px 10px; 
  border-radius: 12px; 
  font-weight: 500; 
}

.confidence.high { 
  background: rgba(76, 175, 80, 0.2); 
  color: #81c784; 
}

.confidence.medium { 
  background: rgba(255, 152, 0, 0.2); 
  color: #ffb74d; 
}

.confidence.low { 
  background: rgba(158, 158, 158, 0.2); 
  color: #bdbdbd; 
}

.result-body { 
  padding: 14px; 
  display: flex; 
  flex-direction: column; 
  gap: 12px; 
  font-size: 13px; 
  color: #90a4ae; 
}

.result-info p { margin: 4px 0; }

.video-action { display: flex; justify-content: flex-start; }

.btn-play {
  padding: 6px 12px;
  background: rgba(25, 118, 210, 0.15);
  color: #90caf9;
  border: 1px solid #2a4a6a;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.btn-play:hover { background: rgba(25, 118, 210, 0.3); }

.video-player-wrap {
  background: #0d1f33;
  border: 1px solid #2a4a6a;
  border-radius: 6px;
  padding: 10px;
}

.result-video {
  width: 100%;
  max-height: 260px;
  border-radius: 4px;
  background: #000;
}

.appearance, .route { 
  padding: 10px; 
  background: rgba(25, 118, 210, 0.05); 
  border-left: 3px solid #1976d2; 
  border-radius: 0 4px 4px 0; 
}

.appearance strong, .route strong { 
  color: #90caf9; 
  display: block; 
  margin-bottom: 6px; 
}

.appearance p, .route p { 
  margin: 0; 
  line-height: 1.6; 
  color: #b0bec5; 
}

.error { color: #ef9a9a; }

.result-list::-webkit-scrollbar { width: 6px; }
.result-list::-webkit-scrollbar-track { background: #0d1f33; }
.result-list::-webkit-scrollbar-thumb { background: #2a4a6a; border-radius: 3px; }
.result-list::-webkit-scrollbar-thumb:hover { background: #3a5a7a; }
</style>
