<template>
  <div class="page-body">
    <div class="section-header">
      <h3>知识库状态</h3>
      <button class="btn-secondary" @click="loadStatus">刷新</button>
    </div>

    <div class="status-card" v-if="ragStatus">
      <div class="status-row">
        <span class="label">索引状态</span>
        <span class="value" :class="ragStatus.initialized ? 'ok' : 'warn'">
          {{ ragStatus.initialized ? '已初始化' : '未初始化' }}
        </span>
      </div>
      <div class="status-row">
        <span class="label">文档数量</span>
        <span class="value">{{ ragStatus.documents }}</span>
      </div>
      <div class="status-row">
        <span class="label">向量块数量</span>
        <span class="value">{{ ragStatus.chunks }}</span>
      </div>
    </div>
    <p v-else-if="statusLoading" class="tip">加载中...</p>
    <p v-else class="tip warn-tip">无法获取知识库状态（AI 引擎可能未启动）</p>

    <div class="divider"></div>

    <h3>上传知识库文档</h3>
    <p class="hint">支持 .txt、.md、.pdf 格式，上传后自动向量化入库</p>

    <div class="upload-section">
      <label class="file-label">
        <input type="file" accept=".txt,.md,.pdf" @change="handleFileChange" ref="fileInput" />
        {{ selectedFile ? selectedFile.name : '选择文档文件' }}
      </label>
      <button class="btn-primary" @click="handleUpload" :disabled="!selectedFile || uploading">
        {{ uploading ? `上传中 ${uploadProgress}%` : '上传并入库' }}
      </button>
      <div class="progress-bar" v-if="uploading">
        <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
      </div>
    </div>

    <div v-if="uploadMsg" class="message" :class="uploadErr ? 'error' : 'success'">
      {{ uploadMsg }}
    </div>

    <div class="divider"></div>

    <div class="section-header">
      <h3>重建索引</h3>
    </div>
    <p class="hint">将知识库目录中所有文档重新向量化，适用于手动放置文件后使用</p>
    <button class="btn-danger" @click="handleRebuild" :disabled="rebuilding">
      {{ rebuilding ? '重建中...' : '重建向量索引' }}
    </button>
    <div v-if="rebuildMsg" class="message" :class="rebuildErr ? 'error' : 'success'">
      {{ rebuildMsg }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { uploadKnowledgeFile, getRagStatus, rebuildRagIndex } from '@/api'

const ragStatus = ref<{ initialized: boolean; chunks: number; documents: number } | null>(null)
const statusLoading = ref(false)

const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadMsg = ref('')
const uploadErr = ref(false)
const fileInput = ref<HTMLInputElement>()

const rebuilding = ref(false)
const rebuildMsg = ref('')
const rebuildErr = ref(false)

async function loadStatus() {
  statusLoading.value = true
  try {
    const res = await getRagStatus()
    ragStatus.value = res.data
  } catch {
    ragStatus.value = null
  } finally {
    statusLoading.value = false
  }
}

function handleFileChange(e: Event) {
  const t = e.target as HTMLInputElement
  if (t.files && t.files.length > 0) {
    selectedFile.value = t.files[0]
    uploadMsg.value = ''
  }
}

async function handleUpload() {
  if (!selectedFile.value) return
  uploading.value = true
  uploadProgress.value = 0
  uploadMsg.value = ''
  uploadErr.value = false
  try {
    const res = await uploadKnowledgeFile(selectedFile.value, (p) => { uploadProgress.value = p })
    uploadMsg.value = `上传成功：${res.data.filename}，向量化 ${res.data.chunks} 个块`
    selectedFile.value = null
    if (fileInput.value) fileInput.value.value = ''
    await loadStatus()
  } catch (err: any) {
    uploadErr.value = true
    uploadMsg.value = `上传失败: ${err.response?.data?.detail || err.message}`
  } finally {
    uploading.value = false
  }
}

async function handleRebuild() {
  rebuilding.value = true
  rebuildMsg.value = ''
  rebuildErr.value = false
  try {
    const res = await rebuildRagIndex()
    rebuildMsg.value = `重建完成，共 ${res.data.chunks} 个向量块`
    await loadStatus()
  } catch (err: any) {
    rebuildErr.value = true
    rebuildMsg.value = `重建失败: ${err.response?.data?.detail || err.message}`
  } finally {
    rebuilding.value = false
  }
}

onMounted(loadStatus)
</script>

<style scoped>
.page-body { padding: 24px 28px; max-width: 800px; }

h3 { font-size: 15px; color: #90caf9; margin-bottom: 10px; }
.hint { font-size: 12px; color: #546e7a; margin-bottom: 12px; }
.divider { border: none; border-top: 1px solid #1e3a5f; margin: 24px 0; }

.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }

.status-card {
  background: #0d1f33;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 4px;
}

.status-row { display: flex; align-items: center; gap: 12px; font-size: 13px; }
.label { color: #546e7a; width: 100px; flex-shrink: 0; }
.value { color: #cfd8dc; font-weight: 500; }
.value.ok { color: #81c784; }
.value.warn { color: #ffb74d; }

.tip { color: #37474f; font-size: 14px; padding: 12px 0; }
.warn-tip { color: #ff9800; }

.upload-section { display: flex; gap: 10px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }

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
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-label input { display: none; }

.btn-primary { padding: 7px 18px; background: #1565c0; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-secondary { padding: 5px 12px; background: #1a2e44; color: #90caf9; border: 1px solid #2a4a6a; border-radius: 4px; cursor: pointer; font-size: 12px; }

.btn-danger { padding: 7px 18px; background: #b71c1c; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }

.progress-bar { width: 140px; height: 6px; background: #1a2e44; border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: #42a5f5; transition: width 0.2s; }

.message { padding: 10px 16px; border-radius: 4px; margin-top: 10px; font-size: 13px; }
.message.success { background: rgba(46,125,50,0.15); color: #81c784; border: 1px solid #2e7d32; }
.message.error { background: rgba(198,40,40,0.15); color: #ef9a9a; border: 1px solid #c62828; }
</style>
