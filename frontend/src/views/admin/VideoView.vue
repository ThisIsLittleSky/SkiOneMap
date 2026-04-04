<template>
  <div class="page-body">
    <div class="video-list">
      <div class="list-header">
        <h3>视频列表</h3>
        <div class="header-actions">
          <select v-model="filterCameraId" @change="loadVideos" class="camera-filter">
            <option :value="null">全部摄像头</option>
            <option v-for="cam in cameras" :key="cam.id" :value="cam.id">{{ cam.name }}</option>
          </select>
          <button class="btn-secondary" @click="loadVideos">刷新</button>
        </div>
      </div>
      <p v-if="loading" class="tip">加载中...</p>
      <p v-else-if="videos.length === 0" class="tip">暂无视频</p>
      <table v-else>
        <thead>
          <tr>
            <th>ID</th>
            <th>文件名</th>
            <th>所属摄像头</th>
            <th>状态</th>
            <th>上传时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="video in videos" :key="video.id" :class="{ selected: selectedVideoId === video.id }">
            <td>{{ video.id }}</td>
            <td class="filename-cell" :title="video.filename">{{ video.filename }}</td>
            <td>{{ getCameraName(video.cameraId) }}</td>
            <td>
              <span class="status-badge" :class="'status-' + video.status.toLowerCase()">
                {{ statusText(video.status) }}
              </span>
            </td>
            <td>{{ formatDate(video.createdAt) }}</td>
            <td class="actions-cell">
              <button class="btn-play" @click="openPlayer(video.id, video.filename)">原视频</button>
              <button
                v-if="video.status === 'ANALYZED'"
                class="btn-play annotated"
                @click="openPlayer(video.id, `${video.filename} · 标注版`, true)"
              >
                标注视频
              </button>
              <button
                class="btn-analyze"
                @click="startAnalysis(video.id)"
                :disabled="video.status === 'PROCESSING'"
              >
                {{ video.status === 'PROCESSING' ? '分析中...' : '开始分析' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <Teleport to="body">
      <div v-if="playerVisible" class="player-overlay" @click.self="closePlayer">
        <div class="player-modal">
          <div class="player-header">
            <span class="player-title">{{ playerFilename }}</span>
            <button class="player-close" @click="closePlayer">×</button>
          </div>
          <video ref="videoEl" class="video-el" controls autoplay :src="playerSrc">
            您的浏览器不支持视频播放
          </video>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { searchVideos, listVideos, createTask, listCameras, type VideoInfo, type CameraInfo } from '@/api'
import { useAlertStore } from '@/stores/alertStore'

const alertStore = useAlertStore()

const videos = ref<VideoInfo[]>([])
const cameras = ref<CameraInfo[]>([])
const loading = ref(false)
const selectedVideoId = ref<number | null>(null)
const filterCameraId = ref<number | null>(null)

const playerVisible = ref(false)
const playerSrc = ref('')
const playerFilename = ref('')
const videoEl = ref<HTMLVideoElement>()

function openPlayer(id: number, filename: string, annotated = false) {
  selectedVideoId.value = id
  playerFilename.value = filename
  playerSrc.value = annotated ? `/api/video/${id}/annotated/stream` : `/api/video/${id}/stream`
  playerVisible.value = true
}

function closePlayer() {
  playerVisible.value = false
  if (videoEl.value) { videoEl.value.pause(); videoEl.value.src = '' }
  playerSrc.value = ''
  selectedVideoId.value = null
}

async function loadVideos() {
  loading.value = true
  try {
    const res = filterCameraId.value 
      ? await searchVideos(filterCameraId.value) 
      : await listVideos()
    videos.value = res.data
  } catch (err) {
    console.error('Failed to load videos:', err)
  } finally {
    loading.value = false
  }
}

async function loadCameras() {
  try {
    const res = await listCameras()
    cameras.value = res.data
  } catch (err) {
    console.error('Failed to load cameras:', err)
  }
}

function getCameraName(cameraId?: number) {
  if (!cameraId) return '未关联'
  const cam = cameras.value.find(c => c.id === cameraId)
  return cam ? cam.name : `摄像头 #${cameraId}`
}

async function startAnalysis(videoId: number) {
  try {
    const res = await createTask(videoId)
    await loadVideos()
  } catch (err: any) {
    console.error('创建任务失败:', err)
  }
}

function statusText(s: string) {
  return ({ UPLOADED: '已上传', PROCESSING: '分析中', ANALYZED: '已分析', FAILED: '失败' } as Record<string, string>)[s] || s
}

function formatDate(d: string) {
  if (!d) return ''
  try { return new Date(d).toLocaleString('zh-CN') } catch { return d }
}

onMounted(() => {
  loadCameras()
  loadVideos()
  watch(() => alertStore.taskCompletedSignal, loadVideos)
})
</script>

<style scoped>
.page-body { padding: 24px 28px; max-width: 1000px; }

.video-list { margin-top: 8px; }
.list-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.header-actions { display: flex; gap: 10px; align-items: center; }
h3 { font-size: 15px; color: #90caf9; }

.camera-filter {
  padding: 5px 12px;
  background: #1a2e44;
  color: #90caf9;
  border: 1px solid #2a4a6a;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  outline: none;
}
.camera-filter:focus { border-color: #1976d2; }

.btn-secondary {
  padding: 5px 12px;
  background: #1a2e44;
  color: #90caf9;
  border: 1px solid #2a4a6a;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.tip { color: #37474f; font-size: 14px; padding: 20px 0; }

table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid #1a2e44; }
th { background: #0d1f33; color: #78909c; font-weight: 600; }
tr:hover td { background: rgba(21,101,192,0.08); }
tr.selected td { background: rgba(21,101,192,0.15); }

.filename-cell { max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.actions-cell { display: flex; gap: 8px; align-items: center; }

.status-badge { padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 500; }
.status-uploaded { background: rgba(21,101,192,0.2); color: #64b5f6; }
.status-processing { background: rgba(230,81,0,0.2); color: #ffb74d; }
.status-analyzed { background: rgba(46,125,50,0.2); color: #81c784; }
.status-failed { background: rgba(198,40,40,0.2); color: #ef9a9a; }

.btn-play { padding: 4px 12px; font-size: 12px; background: #0d47a1; color: #90caf9; border: 1px solid #1565c0; border-radius: 4px; cursor: pointer; }
.btn-play.annotated { background: rgba(46,125,50,0.16); color: #a5d6a7; border-color: #2e7d32; }
.btn-analyze { padding: 4px 12px; font-size: 12px; background: transparent; color: #4caf50; border: 1px solid #2e7d32; border-radius: 4px; cursor: pointer; }
.btn-analyze:disabled { opacity: 0.5; cursor: not-allowed; }

.player-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.75); z-index: 1000; display: flex; align-items: center; justify-content: center; }
.player-modal { background: #0d1f33; border: 1px solid #1e3a5f; border-radius: 10px; overflow: hidden; width: 80vw; max-width: 900px; }
.player-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; border-bottom: 1px solid #1e3a5f; }
.player-title { font-size: 14px; color: #90caf9; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.player-close { background: none; border: none; color: #78909c; font-size: 22px; cursor: pointer; line-height: 1; padding: 0 4px; }
.player-close:hover { color: #fff; }
.video-el { width: 100%; max-height: 70vh; background: #000; display: block; }
</style>
