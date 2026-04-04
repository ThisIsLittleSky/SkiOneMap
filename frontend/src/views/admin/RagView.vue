<template>
  <div class="dashboard">
    <!-- 数据统计卡片区 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">文档数量</div>
        <div class="stat-value">{{ ragStatus?.documents || 0 }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">向量块数</div>
        <div class="stat-value">{{ ragStatus?.chunks || 0 }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">索引大小</div>
        <div class="stat-value">{{ ragStatus?.indexSizeMB || 0 }} MB</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">查询次数</div>
        <div class="stat-value">{{ ragStatus?.queryCount || 0 }}</div>
      </div>
    </div>

    <!-- 配置信息 -->
    <div class="config-card">
      <div class="config-row">
        <span class="label">索引状态</span>
        <span class="badge" :class="ragStatus?.initialized ? 'ok' : 'warn'">
          {{ ragStatus?.initialized ? '已初始化' : '未初始化' }}
        </span>
      </div>
      <div class="config-row">
        <span class="label">Embedding 模式</span>
        <div class="switch-container">
          <label class="switch">
            <input 
              type="checkbox" 
              :checked="ragStatus?.useEmbedding" 
              @change="handleToggleEmbedding"
              :disabled="switchingMode"
            />
            <span class="slider"></span>
          </label>
          <span class="badge" :class="ragStatus?.useEmbedding ? 'ok' : 'info'">
            {{ ragStatus?.useEmbedding ? '开启' : '关闭' }}
          </span>
        </div>
      </div>
      <div class="config-row">
        <span class="label">LLM 模型</span>
        <span class="value">{{ ragStatus?.llmModel || 'N/A' }}</span>
      </div>
      <div class="config-row" v-if="ragStatus?.embeddingModel">
        <span class="label">Embedding 模型</span>
        <span class="value">{{ ragStatus.embeddingModel }}</span>
      </div>
      <div class="config-row">
        <span class="label">最近上传</span>
        <span class="value">{{ formatTime(ragStatus?.lastUpload) }}</span>
      </div>
    </div>

    <!-- 主要功能区 -->
    <div class="main-grid">
      <!-- 左侧：文档管理 -->
      <div class="panel">
        <div class="panel-header">
          <h3>文档管理</h3>
          <button class="btn-icon" @click="loadDocuments" title="刷新">⟳</button>
        </div>

        <div class="upload-section">
          <label class="file-label">
            <input type="file" accept=".txt,.md,.pdf" multiple @change="handleFileChange" ref="fileInput" />
            {{ selectedFiles.length > 0 ? `已选 ${selectedFiles.length} 个文件` : '选择文档' }}
          </label>
          <button class="btn-primary" @click="handleUpload" :disabled="selectedFiles.length === 0 || uploading">
            {{ uploading ? `上传中 ${uploadProgress}%` : '上传' }}
          </button>
        </div>

        <div v-if="uploadMsg" class="message" :class="uploadErr ? 'error' : 'success'">
          {{ uploadMsg }}
        </div>

        <div class="doc-list">
          <div v-if="docsLoading" class="loading">加载中...</div>
          <div v-else-if="documents.length === 0" class="empty">暂无文档</div>
          <div v-else class="doc-item" v-for="doc in documents" :key="doc.filename">
            <div class="doc-info">
              <div class="doc-name">{{ doc.filename }}</div>
              <div class="doc-meta">{{ formatSize(doc.size) }} · {{ formatTime(doc.uploadTime) }}</div>
            </div>
            <div class="doc-actions">
              <button class="btn-icon" @click="previewDoc(doc.filename)" title="预览">👁</button>
              <button class="btn-icon danger" @click="deleteDoc(doc.filename)" title="删除">🗑</button>
            </div>
          </div>
        </div>

        <div class="panel-footer">
          <button class="btn-secondary" @click="handleRebuild" :disabled="rebuilding">
            {{ rebuilding ? '重建中...' : '重建索引' }}
          </button>
          <button class="btn-danger" @click="handleClear">清空知识库</button>
        </div>
      </div>

      <!-- 右侧：查询测试 -->
      <div class="panel">
        <div class="panel-header">
          <h3>查询测试</h3>
        </div>

        <div class="query-section">
          <textarea 
            v-model="testQueryText" 
            placeholder="输入测试问题，例如：逆行违规如何定责？"
            rows="3"
          ></textarea>
          <button class="btn-primary" @click="handleTestQuery" :disabled="!testQueryText.trim() || querying">
            {{ querying ? '查询中...' : '测试查询' }}
          </button>
        </div>

        <div v-if="queryResult" class="query-result">
          <div class="result-meta">耗时: {{ queryResult.elapsed }}s</div>

          <!-- 责任占比 -->
          <div v-if="queryResult.answer.liability.parties.length > 0" class="result-section">
            <div class="section-title">责任占比</div>
            <div class="liability-bars">
              <div v-for="(p, i) in queryResult.answer.liability.parties" :key="i" class="party-row">
                <span class="party-name">{{ p.name }}</span>
                <div class="party-bar-wrap">
                  <div class="party-bar" :style="{ width: p.percentage + '%', background: partyColors[i % partyColors.length] }"></div>
                </div>
                <span class="party-pct" :style="{ color: partyColors[i % partyColors.length] }">{{ p.percentage }}%</span>
              </div>
            </div>
            <div v-for="(p, i) in queryResult.answer.liability.parties" :key="'r'+i" class="party-reason">
              <strong>{{ p.name }}：</strong>{{ p.reason }}
            </div>
            <div v-if="queryResult.answer.liability.resort_liability && queryResult.answer.liability.resort_liability !== '无'" class="resort-liability">
              <strong>雪场连带责任：</strong>{{ queryResult.answer.liability.resort_liability }}
            </div>
          </div>

          <!-- 行为分析 -->
          <div v-if="queryResult.answer.behavior_analysis" class="result-section">
            <div class="section-title">行为分析</div>
            <div class="section-content">{{ queryResult.answer.behavior_analysis }}</div>
          </div>

          <!-- 参考文献 -->
          <div v-if="queryResult.answer.references.length > 0" class="result-section">
            <div class="section-title">参考文献</div>
            <div v-for="(ref, i) in queryResult.answer.references" :key="i" class="ref-item">
              <div class="ref-title">{{ ref.title }}</div>
              <div class="ref-content">{{ ref.content }}</div>
            </div>
          </div>

          <!-- 处理建议 -->
          <div v-if="queryResult.answer.suggestion" class="result-section">
            <div class="section-title">处理建议</div>
            <div class="section-content">{{ queryResult.answer.suggestion }}</div>
          </div>
        </div>

        <div class="divider"></div>

        <div class="panel-header">
          <h3>查询历史</h3>
          <button class="btn-icon" @click="loadHistory" title="刷新">⟳</button>
        </div>

        <div class="history-list">
          <div v-if="history.length === 0" class="empty">暂无查询记录</div>
          <div v-else class="history-item" v-for="(h, i) in history" :key="i">
            <div class="history-query">{{ h.query }}</div>
            <div class="history-meta">
              <span :class="h.success ? 'ok' : 'error'">{{ h.success ? '成功' : '失败' }}</span>
              · {{ h.elapsed }}s · {{ formatTime(h.timestamp) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 性能统计 -->
    <div class="stats-panel" v-if="stats">
      <h3>性能统计</h3>
      <div class="stats-row">
        <div class="stat-item">
          <span class="label">总查询数</span>
          <span class="value">{{ stats.totalQueries }}</span>
        </div>
        <div class="stat-item">
          <span class="label">平均耗时</span>
          <span class="value">{{ stats.avgElapsed }}s</span>
        </div>
        <div class="stat-item">
          <span class="label">最大耗时</span>
          <span class="value">{{ stats.maxElapsed }}s</span>
        </div>
        <div class="stat-item">
          <span class="label">成功率</span>
          <span class="value">{{ stats.successRate }}%</span>
        </div>
      </div>
    </div>

    <!-- 预览弹窗 -->
    <div v-if="previewModal" class="modal" @click="previewModal = null">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ previewModal.filename }}</h3>
          <button class="btn-icon" @click="previewModal = null">✕</button>
        </div>
        <div class="modal-body">
          <pre>{{ previewModal.preview }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { RagStatus, DocumentInfo, QueryTestResult, QueryHistory, RagStats } from '@/api'
import {
  uploadKnowledgeFile,
  getRagStatus,
  rebuildRagIndex,
  listDocuments,
  deleteDocument,
  previewDocument,
  testQuery,
  getQueryHistory,
  getRagStats,
  clearKnowledge,
  setEmbeddingMode,
} from '@/api'

const ragStatus = ref<RagStatus | null>(null)
const documents = ref<DocumentInfo[]>([])
const docsLoading = ref(false)

const selectedFiles = ref<File[]>([])
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadMsg = ref('')
const uploadErr = ref(false)
const fileInput = ref<HTMLInputElement>()

const rebuilding = ref(false)

const testQueryText = ref('')
const querying = ref(false)
const queryResult = ref<QueryTestResult | null>(null)

const history = ref<QueryHistory[]>([])
const stats = ref<RagStats | null>(null)

const previewModal = ref<{ filename: string; preview: string } | null>(null)
const switchingMode = ref(false)
const partyColors = ['#00e5ff', '#ff6b35', '#7c4dff', '#ff9800', '#4caf50']

async function handleToggleEmbedding(e: Event) {
  const target = e.target as HTMLInputElement
  const enabled = target.checked
  
  if (!confirm(`确定要${enabled ? '开启' : '关闭'} Embedding 模式吗？\n${enabled ? '开启后将使用向量检索，需要配置有效的 Embedding 模型。' : '关闭后将直接使用 LLM 处理文档。'}`)) {
    target.checked = !enabled
    return
  }
  
  switchingMode.value = true
  try {
    await setEmbeddingMode(enabled)
    await loadStatus()
    alert(`Embedding 模式已${enabled ? '开启' : '关闭'}`)
  } catch (err: any) {
    alert(`切换失败: ${err.response?.data?.detail || err.message}`)
    target.checked = !enabled
  } finally {
    switchingMode.value = false
  }
}

async function loadStatus() {
  try {
    const res = await getRagStatus()
    ragStatus.value = res.data
  } catch {
    ragStatus.value = null
  }
}

async function loadDocuments() {
  docsLoading.value = true
  try {
    const res = await listDocuments()
    documents.value = res.data.documents
  } catch {
    documents.value = []
  } finally {
    docsLoading.value = false
  }
}

async function loadHistory() {
  try {
    const res = await getQueryHistory(10)
    history.value = res.data.history
  } catch {
    history.value = []
  }
}

async function loadStats() {
  try {
    const res = await getRagStats()
    stats.value = res.data
  } catch {
    stats.value = null
  }
}

function handleFileChange(e: Event) {
  const t = e.target as HTMLInputElement
  if (t.files && t.files.length > 0) {
    selectedFiles.value = Array.from(t.files)
    uploadMsg.value = ''
  }
}

async function handleUpload() {
  if (selectedFiles.value.length === 0) return
  uploading.value = true
  uploadProgress.value = 0
  uploadMsg.value = ''
  uploadErr.value = false

  try {
    for (const file of selectedFiles.value) {
      await uploadKnowledgeFile(file, (p) => { uploadProgress.value = p })
    }
    uploadMsg.value = `成功上传 ${selectedFiles.value.length} 个文件`
    selectedFiles.value = []
    if (fileInput.value) fileInput.value.value = ''
    await Promise.all([loadStatus(), loadDocuments()])
  } catch (err: any) {
    uploadErr.value = true
    uploadMsg.value = `上传失败: ${err.response?.data?.detail || err.message}`
  } finally {
    uploading.value = false
  }
}

async function handleRebuild() {
  if (!confirm('确定要重建索引吗？')) return
  rebuilding.value = true
  try {
    await rebuildRagIndex()
    await Promise.all([loadStatus(), loadDocuments()])
    alert('重建完成')
  } catch (err: any) {
    alert(`重建失败: ${err.response?.data?.detail || err.message}`)
  } finally {
    rebuilding.value = false
  }
}

async function handleClear() {
  if (!confirm('确定要清空知识库吗？此操作不可恢复！')) return
  try {
    await clearKnowledge()
    await Promise.all([loadStatus(), loadDocuments()])
    alert('知识库已清空')
  } catch (err: any) {
    alert(`清空失败: ${err.response?.data?.detail || err.message}`)
  }
}

async function deleteDoc(filename: string) {
  if (!confirm(`确定删除 ${filename}？`)) return
  try {
    await deleteDocument(filename)
    await Promise.all([loadStatus(), loadDocuments()])
  } catch (err: any) {
    alert(`删除失败: ${err.response?.data?.detail || err.message}`)
  }
}

async function previewDoc(filename: string) {
  try {
    const res = await previewDocument(filename)
    previewModal.value = res.data
  } catch (err: any) {
    alert(`预览失败: ${err.response?.data?.detail || err.message}`)
  }
}

async function handleTestQuery() {
  if (!testQueryText.value.trim()) return
  querying.value = true
  queryResult.value = null
  try {
    const res = await testQuery(testQueryText.value)
    queryResult.value = res.data
    await Promise.all([loadHistory(), loadStats()])
  } catch (err: any) {
    alert(`查询失败: ${err.response?.data?.detail || err.message}`)
  } finally {
    querying.value = false
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function formatTime(iso: string | null | undefined): string {
  if (!iso) return 'N/A'
  const d = new Date(iso)
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  loadStatus()
  loadDocuments()
  loadHistory()
  loadStats()
})
</script>

<style scoped>
.dashboard { padding: 24px; max-width: 1400px; margin: 0 auto; }

/* 统计卡片网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: linear-gradient(135deg, #1a2e44 0%, #0d1f33 100%);
  border: 1px solid #2a4a6a;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
}

.stat-label {
  font-size: 12px;
  color: #546e7a;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #90caf9;
}

/* 配置卡片 */
.config-card {
  background: #0d1f33;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 24px;
}

.config-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #1e3a5f;
}

.config-row:last-child { border-bottom: none; }

.label { font-size: 13px; color: #546e7a; }
.value { font-size: 13px; color: #cfd8dc; }

.switch-container {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* Toggle Switch */
.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #2a4a6a;
  transition: 0.3s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: #546e7a;
  transition: 0.3s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #1565c0;
}

input:checked + .slider:before {
  background-color: #90caf9;
  transform: translateX(20px);
}

input:disabled + .slider {
  opacity: 0.5;
  cursor: not-allowed;
}

.badge {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.badge.ok { background: rgba(46,125,50,0.2); color: #81c784; }
.badge.warn { background: rgba(255,152,0,0.2); color: #ffb74d; }
.badge.info { background: rgba(33,150,243,0.2); color: #64b5f6; }

/* 主网格 */
.main-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

@media (max-width: 1024px) {
  .main-grid { grid-template-columns: 1fr; }
}

/* 面板 */
.panel {
  background: #0d1f33;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-header h3 {
  font-size: 15px;
  color: #90caf9;
  margin: 0;
}

.panel-footer {
  display: flex;
  gap: 10px;
  padding-top: 12px;
  border-top: 1px solid #1e3a5f;
}

/* 上传区 */
.upload-section {
  display: flex;
  gap: 10px;
  align-items: center;
}

.file-label {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 14px;
  background: #1a2e44;
  border: 1px solid #2a4a6a;
  border-radius: 4px;
  font-size: 13px;
  color: #90caf9;
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-label input { display: none; }

/* 文档列表 */
.doc-list {
  max-height: 400px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.doc-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: #1a2e44;
  border: 1px solid #2a4a6a;
  border-radius: 4px;
}

.doc-info { flex: 1; }

.doc-name {
  font-size: 13px;
  color: #cfd8dc;
  margin-bottom: 4px;
}

.doc-meta {
  font-size: 11px;
  color: #546e7a;
}

.doc-actions {
  display: flex;
  gap: 6px;
}

/* 查询区 */
.query-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.query-section textarea {
  width: 100%;
  padding: 10px;
  background: #1a2e44;
  border: 1px solid #2a4a6a;
  border-radius: 4px;
  color: #cfd8dc;
  font-size: 13px;
  font-family: inherit;
  resize: vertical;
}

.query-result {
  background: #1a2e44;
  border: 1px solid #2a4a6a;
  border-radius: 4px;
  padding: 12px;
}

.result-meta {
  font-size: 11px;
  color: #546e7a;
  margin-bottom: 8px;
}

.result-content {
  font-size: 13px;
  color: #cfd8dc;
  line-height: 1.6;
  white-space: pre-wrap;
}

/* 结构化结果 */
.result-section {
  margin-top: 12px;
  padding: 10px 12px;
  background: #0d1f33;
  border: 1px solid #1e3a5f;
  border-radius: 6px;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: #90caf9;
  margin-bottom: 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid #1e3a5f;
}

.section-content {
  font-size: 13px;
  color: #cfd8dc;
  line-height: 1.6;
}

.liability-bars {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 8px;
}

.party-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.party-name {
  font-size: 12px;
  color: #78909c;
  width: 80px;
  flex-shrink: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.party-bar-wrap {
  flex: 1;
  height: 8px;
  background: #1e3a5f;
  border-radius: 4px;
  overflow: hidden;
}

.party-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.8s ease;
}

.party-pct {
  font-size: 13px;
  font-weight: 600;
  width: 40px;
  text-align: right;
  flex-shrink: 0;
}

.party-reason {
  font-size: 12px;
  color: #90a4ae;
  margin-top: 4px;
  line-height: 1.5;
}

.resort-liability {
  font-size: 12px;
  color: #ffb74d;
  margin-top: 6px;
  padding: 6px 8px;
  background: rgba(255, 152, 0, 0.08);
  border-radius: 4px;
}

.ref-item {
  margin-bottom: 8px;
  padding: 6px 8px;
  background: rgba(124, 77, 255, 0.06);
  border-left: 3px solid #7c4dff33;
  border-radius: 0 4px 4px 0;
}

.ref-item:last-child {
  margin-bottom: 0;
}

.ref-title {
  font-size: 12px;
  font-weight: 500;
  color: #b39ddb;
  margin-bottom: 2px;
}

.ref-content {
  font-size: 12px;
  color: #90a4ae;
  line-height: 1.5;
}

/* 历史列表 */
.history-list {
  max-height: 300px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  padding: 10px 12px;
  background: #1a2e44;
  border: 1px solid #2a4a6a;
  border-radius: 4px;
}

.history-query {
  font-size: 13px;
  color: #cfd8dc;
  margin-bottom: 4px;
}

.history-meta {
  font-size: 11px;
  color: #546e7a;
}

.history-meta .ok { color: #81c784; }
.history-meta .error { color: #ef9a9a; }

/* 性能统计面板 */
.stats-panel {
  background: #0d1f33;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  padding: 20px;
}

.stats-panel h3 {
  font-size: 15px;
  color: #90caf9;
  margin: 0 0 16px 0;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stat-item .label {
  font-size: 12px;
  color: #546e7a;
}

.stat-item .value {
  font-size: 20px;
  font-weight: 600;
  color: #90caf9;
}

/* 按钮 */
.btn-primary, .btn-secondary, .btn-danger, .btn-icon {
  padding: 7px 14px;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-primary {
  background: #1565c0;
  color: #fff;
}

.btn-secondary {
  background: #1a2e44;
  color: #90caf9;
  border: 1px solid #2a4a6a;
}

.btn-danger {
  background: #b71c1c;
  color: #fff;
}

.btn-icon {
  background: transparent;
  color: #90caf9;
  padding: 4px 8px;
  font-size: 14px;
}

.btn-icon.danger { color: #ef9a9a; }

.btn-primary:disabled, .btn-secondary:disabled, .btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary:hover:not(:disabled), .btn-secondary:hover:not(:disabled), 
.btn-danger:hover:not(:disabled), .btn-icon:hover {
  opacity: 0.8;
}

/* 消息 */
.message {
  padding: 10px 14px;
  border-radius: 4px;
  font-size: 13px;
}

.message.success {
  background: rgba(46,125,50,0.15);
  color: #81c784;
  border: 1px solid #2e7d32;
}

.message.error {
  background: rgba(198,40,40,0.15);
  color: #ef9a9a;
  border: 1px solid #c62828;
}

/* 通用 */
.loading, .empty {
  text-align: center;
  padding: 20px;
  color: #546e7a;
  font-size: 13px;
}

.divider {
  border: none;
  border-top: 1px solid #1e3a5f;
  margin: 16px 0;
}

/* 模态框 */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #0d1f33;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  max-width: 600px;
  max-height: 80vh;
  width: 90%;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #1e3a5f;
}

.modal-header h3 {
  font-size: 15px;
  color: #90caf9;
  margin: 0;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
}

.modal-body pre {
  font-size: 12px;
  color: #cfd8dc;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
}
</style>
