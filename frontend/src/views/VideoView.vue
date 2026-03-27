<template>
  <div class="video-page">
    <NavBar />
    <div class="page-body">
      <div class="upload-section">
        <label class="file-label">
          <input type="file" accept="video/*" @change="handleFileChange" ref="fileInput" />
          {{ selectedFile ? selectedFile.name : '选择视频文件' }}
        </label>
        <button @click="handleUpload" :disabled="!selectedFile || uploading" class="btn-primary">
          {{ uploading ? `上传中 ${uploadProgress}%` : '上传视频' }}
        </button>
        <div class="progress-bar" v-if="uploading">
          <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
        </div>
      </div>

      <div v-if="uploadMessage" class="message" :class="uploadError ? 'error' : 'success'">
        {{ uploadMessage }}
      </div>

      <div class="video-list">
        <div class="list-header">
          <h3>视频列表</h3>
          <button class="btn-secondary" @click="loadVideos">刷新</button>
        </div>
        <p v-if="loading" class="tip">加载中...</p>
        <p v-else-if="videos.length === 0" class="tip">暂无视频</p>
        <table v-else>
          <thead>
            <tr>
              <th>ID</th>
              <th>文件名</th>
              <th>状态</th>
              <th>上传时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="video in videos" :key="video.id" :class="{ selected: selectedVideoId === video.id }">
              <td>{{ video.id }}</td>
              <td class="filename-cell" :title="video.filename">{{ video.filename }}</td>
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
import NavBar from '@/components/NavBar.vue'
import { uploadVideo, listVideos, createTask, type VideoInfo } from '@/api'
import { useAlertStore } from '@/stores/alertStore'

const alertStore = useAlertStore()

const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadMessage = ref('')
const uploadError = ref(false)
const videos = ref<VideoInfo[]>([])
const loading = ref(false)
const fileInput = ref<HTMLInputElement>()
const selectedVideoId = ref<number | null>(null)

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
  if (videoEl.value) {
    videoEl.value.pause()
    videoEl.value.src = ''
  }
  playerSrc.value = ''
  selectedVideoId.value = null
}

function handleFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0]
    uploadMessage.value = ''
  }
}

async function handleUpload() {
  if (!selectedFile.value) return
  uploading.value = true
  uploadProgress.value = 0
  uploadMessage.value = ''
  uploadError.value = false
  try {
    const res = await uploadVideo(selectedFile.value, (percent) => {
      uploadProgress.value = percent
    })
    uploadMessage.value = `上传成功！视频ID: ${res.data.id}`
    selectedFile.value = null
    if (fileInput.value) fileInput.value.value = ''
    await loadVideos()
  } catch (err: any) {
    uploadError.value = true
    uploadMessage.value = `上传失败: ${err.response?.data?.error || err.message}`
  } finally {
    uploading.value = false
  }
}

async function loadVideos() {
  loading.value = true
  try {
    const res = await listVideos()
    videos.value = res.data
  } catch (err) {
    console.error('Failed to load videos:', err)
  } finally {
    loading.value = false
  }
}

async function startAnalysis(videoId: number) {
  try {
    const res = await createTask(videoId)
    uploadMessage.value = `分析任务已创建！任务ID: ${res.data.taskId}`
    uploadError.value = false
    await loadVideos()
  } catch (err: any) {
    uploadMessage.value = `创建任务失败: ${err.response?.data?.error || err.message}`
    uploadError.value = true
  }
}

function statusText(status: string): string {
  const map: Record<string, string> = {
    UPLOADED: '已上传', PROCESSING: '分析中', ANALYZED: '已分析', FAILED: '失败',
  }
  return map[status] || status
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  try { return new Date(dateStr).toLocaleString('zh-CN') } catch { return dateStr }
}

onMounted(() => {
  loadVideos()
  watch(() => alertStore.alerts.length, () => loadVideos())
})
</script>

<style scoped>
.video-page {
  width: 100%;
  min-height: 100vh;
  background: #0a1929;
  color: #e0e0e0;
  display: flex;
  flex-direction: column;
}

.page-body {
  padding: 20px 28px;
  max-width: 1100px;
  width: 100%;
  margin: 0 auto;
}

.upload-section {
  display: flex;
  gap: 10px;
  align-items: center;
  margin: 20px 0 12px;
  flex-wrap: wrap;
}

.file-label {
  display: inline-flex;
  align-items: center;
  padding: 7px 14px;
  background: #1a2e44;
  border: 1px solid #2a4a6a;
  border-radius: 4px;
  font-size: 13px;
  color: #90caf9;
  cursor: pointer;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-label input[type="file"] { display: none; }

.btn-primary {
  padding: 7px 18px;
  background: #1565c0;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-secondary {
  padding: 5px 12px;
  background: #1a2e44;
  color: #90caf9;
  border: 1px solid #2a4a6a;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.progress-bar {
  width: 160px;
  height: 6px;
  background: #1a2e44;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #42a5f5;
  transition: width 0.2s;
}

.message {
  padding: 10px 16px;
  border-radius: 4px;
  margin-bottom: 16px;
  font-size: 13px;
}

.message.success {
  background: rgba(46, 125, 50, 0.15);
  color: #81c784;
  border: 1px solid #2e7d32;
}

.message.error {
  background: rgba(198, 40, 40, 0.15);
  color: #ef9a9a;
  border: 1px solid #c62828;
}

.video-list { margin-top: 8px; }

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

h3 { font-size: 15px; color: #90caf9; }
.tip { color: #37474f; font-size: 14px; padding: 20px 0; }

table { width: 100%; border-collapse: collapse; font-size: 13px; }

th, td {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid #1a2e44;
}

th { background: #0d1f33; color: #78909c; font-weight: 600; }
tr:hover td { background: rgba(21, 101, 192, 0.08); }
tr.selected td { background: rgba(21, 101, 192, 0.15); }

.filename-cell {
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.actions-cell { display: flex; gap: 8px; align-items: center; }

.status-badge { padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 500; }
.status-uploaded { background: rgba(21,101,192,0.2); color: #64b5f6; }
.status-processing { background: rgba(230,81,0,0.2); color: #ffb74d; }
.status-analyzed { background: rgba(46,125,50,0.2); color: #81c784; }
.status-failed { background: rgba(198,40,40,0.2); color: #ef9a9a; }

.btn-play {
  padding: 4px 12px;
  font-size: 12px;
  background: #0d47a1;
  color: #90caf9;
  border: 1px solid #1565c0;
  border-radius: 4px;
  cursor: pointer;
}
.btn-play.annotated { background: rgba(46,125,50,0.16); color: #a5d6a7; border-color: #2e7d32; }

.btn-analyze {
  padding: 4px 12px;
  font-size: 12px;
  background: transparent;
  color: #4caf50;
  border: 1px solid #2e7d32;
  border-radius: 4px;
  cursor: pointer;
}

.btn-analyze:disabled { opacity: 0.5; cursor: not-allowed; }

.player-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.75);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.player-modal {
  background: #0d1f33;
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  overflow: hidden;
  width: 80vw;
  max-width: 900px;
}

.player-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-bottom: 1px solid #1e3a5f;
}

.player-title {
  font-size: 14px;
  color: #90caf9;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.player-close {
  background: none;
  border: none;
  color: #78909c;
  font-size: 22px;
  cursor: pointer;
  line-height: 1;
  padding: 0 4px;
}

.player-close:hover { color: #fff; }

.video-el {
  width: 100%;
  max-height: 70vh;
  background: #000;
  display: block;
}
</style>
