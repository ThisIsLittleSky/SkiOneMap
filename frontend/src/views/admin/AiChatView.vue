<template>
  <div class="ai-chat" :class="{ 'is-empty': messages.length === 0 }">
    <!-- 消息列表 -->
    <div class="messages-area" ref="messagesRef">
      <div v-if="messages.length === 0" class="welcome">
        <div class="welcome-icon">⛷</div>
        <h2>雪境智判 AI</h2>
        <p>上传事故视频或输入问题，AI 将为您分析事故责任</p>
      </div>

      <div
        v-for="msg in messages"
        :key="msg.id"
        class="message-row"
        :class="msg.role"
      >
        <div class="message-bubble" :class="msg.role">
          <template v-if="msg.role === 'user'">
            <div v-if="msg.text" class="msg-text">{{ msg.text }}</div>
            <div v-if="msg.videoName" class="msg-video-tag">
              <span class="video-icon">🎬</span>
              {{ msg.videoName }}
            </div>
            <div v-if="msg.videoUrl" class="msg-video-preview">
              <video
                :src="msg.videoUrl"
                controls
                class="user-video"
                preload="metadata"
              ></video>
            </div>
          </template>

          <template v-if="msg.role === 'ai'">
            <!-- 流程链表 -->
            <div v-if="msg.progressSteps && msg.progressSteps.length" class="progress-chain">
              <div
                v-for="(step, idx) in msg.progressSteps"
                :key="idx"
                class="progress-step"
                :class="step.status"
              >
                <div class="step-indicator">
                  <div class="step-ball" :class="step.status">
                    <span v-if="step.status === 'done'" class="check">✓</span>
                  </div>
                  <div v-if="idx < msg.progressSteps.length - 1" class="step-line" :class="step.status"></div>
                </div>
                <span class="step-label">{{ step.label }}</span>
              </div>
            </div>

            <!-- 视频卡片 -->
            <div v-if="msg.annotatedVideoUrl" class="video-card">
              <div class="video-card-header">
                <span class="video-card-icon">🎬</span>
                <span>YOLO 标注视频</span>
              </div>
              <video
                :src="msg.annotatedVideoUrl"
                controls
                class="annotated-video"
                preload="metadata"
              ></video>
            </div>

            <!-- 事故分析报告卡片 -->
            <div v-if="msg.done && msg.report" class="report-card" @click="showReportModal(msg)">
              <div class="report-card-header">
                <span class="report-card-icon">📋</span>
                <span class="report-card-title">事故分析报告</span>
              </div>
              <div class="report-card-hint">点击查看详细报告</div>
            </div>

            <!-- 错误信息 -->
            <div v-if="msg.error" class="error-msg">{{ msg.error }}</div>

            <!-- 导出按钮 -->
            <button
              v-if="msg.done && (msg.report || msg.annotatedVideoUrl)"
              class="btn-export-pdf"
              @click="exportPdf(msg)"
              :disabled="exportingId === msg.id"
            >
              {{ exportingId === msg.id ? '导出中...' : '导出事故分析报告.pdf' }}
            </button>
          </template>
        </div>
      </div>

      <div class="scroll-bottom" ref="scrollBottom"></div>
    </div>

    <!-- 输入区 -->
    <div class="input-area" :class="{ 'input-empty': messages.length === 0 }">
      <div class="input-row">
        <label class="btn-video-upload" :class="{ hasVideo: !!selectedFile }">
          <input
            type="file"
            accept="video/*"
            @change="handleFileChange"
            ref="videoInput"
            hidden
          />
          <span class="upload-icon">
            <svg v-if="!selectedFile" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 1 1 5.66 5.66l-9.2 9.19a2 2 0 1 1-2.83-2.83l8.49-8.48"/></svg>
            <span v-else>🎬</span>
          </span>
        </label>

        <textarea
          v-model="inputText"
          class="chat-input"
          :placeholder="selectedFile ? '描述事故情况（可选）...' : '输入问题，或上传事故视频...'"
          rows="1"
          @keydown.enter.exact.prevent="handleSend"
          @input="autoResize"
          ref="textareaRef"
        ></textarea>

        <button
          class="btn-send"
          @click="handleSend"
          :disabled="sending || (!inputText.trim() && !selectedFile)"
        >
          <span v-if="sending" class="sending-icon">●</span>
          <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </button>
      </div>
      <div v-if="selectedFile" class="file-preview">
        <span class="file-name">{{ selectedFile.name }}</span>
        <button class="btn-remove-file" @click="clearFile">✕</button>
      </div>
    </div>

    <!-- 预设问题 -->
    <div v-if="messages.length === 0" class="welcome-hints">
      <span class="hint" @click="setInput('滑雪者逆行撞人如何定责？')">滑雪者逆行撞人如何定责？</span>
      <span class="hint" @click="setInput('两人相撞责任如何划分？')">两人相撞责任如何划分？</span>
      <span class="hint" @click="setInput('雪场是否需要承担连带责任？')">雪场是否需要承担连带责任？</span>
    </div>
  </div>

  <!-- 报告弹窗 -->
  <Teleport to="body">
    <div v-if="activeReport" class="report-modal-overlay" @click.self="closeReportModal">
      <div class="report-modal">
        <div class="report-modal-header">
          <span class="report-modal-title">事故分析报告</span>
          <button class="report-modal-close" @click="closeReportModal">✕</button>
        </div>
        <div class="report-modal-body">
          <div v-if="activeReport.liability?.parties?.length" class="report-block">
            <div class="block-title">责任占比</div>
            <div class="liability-bars">
              <div v-for="(p, i) in activeReport.liability.parties" :key="i" class="party-row">
                <span class="party-name">{{ p.name }}</span>
                <div class="party-bar-wrap">
                  <div class="party-bar" :style="{ width: p.percentage + '%', background: partyColors[i % 5] }"></div>
                </div>
                <span class="party-pct" :style="{ color: partyColors[i % 5] }">{{ p.percentage }}%</span>
              </div>
            </div>
            <div v-for="(p, i) in activeReport.liability.parties" :key="'r'+i" class="party-reason">
              <strong>{{ p.name }}：</strong>{{ p.reason }}
            </div>
            <div v-if="activeReport.liability.resort_liability && activeReport.liability.resort_liability !== '无'" class="resort-note">
              <strong>雪场连带责任：</strong>{{ activeReport.liability.resort_liability }}
            </div>
          </div>

          <div v-if="activeReport.behavior_analysis" class="report-block">
            <div class="block-title">行为分析</div>
            <div class="block-text">{{ activeReport.behavior_analysis }}</div>
          </div>

          <div v-if="activeReport.references?.length" class="report-block">
            <div class="block-title">参考文献</div>
            <div v-for="(ref, i) in activeReport.references" :key="i" class="ref-item">
              <div class="ref-title">{{ ref.title }}</div>
              <div class="ref-text">{{ ref.content }}</div>
            </div>
          </div>

          <div v-if="activeReport.suggestion" class="report-block">
            <div class="block-title">处理建议</div>
            <div class="block-text">{{ activeReport.suggestion }}</div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import type { LiabilityResult } from '@/api'
import {
  testQuery,
  uploadVideo,
  createTask,
  getTaskStatus,
  getTaskTracks,
  getVideoUrl,
} from '@/api'
import axios from 'axios'

// ── 类型 ──
interface ProgressStep {
  label: string
  status: 'pending' | 'active' | 'done'
}

interface ChatMessage {
  id: string
  role: 'user' | 'ai'
  text?: string
  videoName?: string
  videoUrl?: string
  annotatedVideoUrl?: string
  report?: LiabilityResult
  thinking?: boolean
  progressSteps?: ProgressStep[]
  queryText?: string
  done?: boolean
  error?: string
}

// ── 状态 ──
const messages = ref<ChatMessage[]>([])
const inputText = ref('')
const selectedFile = ref<File | null>(null)
const sending = ref(false)
const exportingId = ref<string | null>(null)
const videoInput = ref<HTMLInputElement>()
const textareaRef = ref<HTMLTextAreaElement>()
const messagesRef = ref<HTMLElement>()
const scrollBottom = ref<HTMLElement>()

const PROGRESS_STEPS_VIDEO = [
  '视频上传中',
  '调用视觉算法分析中',
  '事故行为量化中',
  '检索法律向量库中',
  '行为量化与法律知识结合中',
  '生成报告中',
]

const PROGRESS_STEPS_TEXT = [
  '检索法律向量库中',
  '生成报告中',
]

function getSteps(hasFile: boolean): string[] {
  return hasFile ? PROGRESS_STEPS_VIDEO : PROGRESS_STEPS_TEXT
}

const activeReport = ref<LiabilityResult | null>(null)

function showReportModal(msg: ChatMessage) {
  activeReport.value = msg.report || null
}

function closeReportModal() {
  activeReport.value = null
}

const partyColors = ['#00e5ff', '#ff6b35', '#7c4dff', '#ff9800', '#4caf50']

function setInput(text: string) {
  inputText.value = text
}

// ── 文件处理 ──
function handleFileChange(e: Event) {
  const t = e.target as HTMLInputElement
  if (t.files && t.files.length > 0) {
    selectedFile.value = t.files[0]
  }
}

function clearFile() {
  selectedFile.value = null
  if (videoInput.value) videoInput.value.value = ''
}

// ── 发送消息 ──
function randomStepDelay(): number {
  return 4000 + Math.random() * 4000  // 4s ~ 8s
}

async function handleSend() {
  if (sending.value) return
  if (!inputText.value.trim() && !selectedFile.value) return

  const userText = inputText.value.trim()
  const file = selectedFile.value

  const userMsg: ChatMessage = {
    id: genId(),
    role: 'user',
    text: userText || undefined,
    videoName: file?.name,
  }
  messages.value.push(userMsg)

  inputText.value = ''
  clearFile()
  sending.value = true

  await nextTick()
  scrollToBottom()

  const steps = getSteps(!!file)
  const lastIdx = steps.length - 1
  let aiMsg: ChatMessage = {
    id: genId(),
    role: 'ai',
    thinking: true,
    progressSteps: steps.map(label => ({ label, status: 'pending' as const })),
    done: false,
  }
  messages.value.push(aiMsg)
  aiMsg = messages.value[messages.value.length - 1]
  await nextTick()
  scrollToBottom()

  try {
    let videoContext = ''
    let annotatedVideoUrl = ''
    let videoError: string | null = null

    // 视频处理在后台异步进行
    let signalVideoDone: (() => void) | null = null
    const videoDone = file ? new Promise<void>(resolve => { signalVideoDone = resolve }) : Promise.resolve()

    if (file) {
      (async () => {
        try {
          const uploadRes = await uploadVideo(file)
          const videoId = uploadRes.data.id
          userMsg.videoUrl = getVideoUrl(videoId)

          const taskRes = await createTask(videoId)
          const taskId = taskRes.data.taskId

          let taskCompleted = false
          let retries = 0
          const maxRetries = 120
          while (!taskCompleted && retries < maxRetries) {
            try {
              const statusRes = await getTaskStatus(taskId)
              if (statusRes.data.status === 'COMPLETED') {
                taskCompleted = true
              } else if (statusRes.data.status === 'FAILED') {
                throw new Error('视频分析任务失败')
              }
            } catch (e: any) {
              if (e.message === '视频分析任务失败') throw e
            }
            if (!taskCompleted) {
              await delay(2000)
              retries++
            }
          }
          if (!taskCompleted) throw new Error('视频分析超时')

          const tracksRes = await getTaskTracks(taskId)
          const tracksData = tracksRes.data

          if (tracksData.annotatedVideoAvailable) {
            annotatedVideoUrl = tracksData.annotatedVideoUrl
          }

          videoContext = JSON.stringify({
            trackCount: tracksData.trackCount || 0,
            totalFrames: tracksData.totalFrames || 0,
            liabilitySuggestion: tracksData.liabilitySuggestion || '',
            alerts: (tracksData.alerts || []).map((a: any) => ({
              type: a.alertType,
              severity: a.severity,
              description: a.description,
            })),
          })
        } catch (e: any) {
          videoError = e.message || '视频处理失败'
        } finally {
          signalVideoDone!()
        }
      })()
    }

    // 所有非最后步骤：按随机秒数自动推进
    for (let i = 0; i < lastIdx; i++) {
      aiMsg.progressSteps![i].status = 'active'
      await nextTick()
      await delay(randomStepDelay())
      aiMsg.progressSteps![i].status = 'done'
    }

    // 最后一步：等待 AI 真正响应完
    aiMsg.progressSteps![lastIdx].status = 'active'
    await nextTick()
    scrollToBottom()

    await videoDone

    if (videoError) {
      throw new Error(videoError)
    }

    let queryText = userText || '请分析这起滑雪事故的责任归属'
    if (videoContext) {
      queryText = `${queryText}\n\n【视频分析数据】\n${videoContext}`
    }

    const queryRes = await testQuery(queryText)
    const report = queryRes.data.answer

    aiMsg.progressSteps![lastIdx].status = 'done'
    await delay(400)
    await nextTick()
    scrollToBottom()

    aiMsg.thinking = false
    aiMsg.done = true
    aiMsg.report = report
    aiMsg.annotatedVideoUrl = annotatedVideoUrl || undefined
    aiMsg.queryText = queryText
    aiMsg.progressSteps = undefined

  } catch (err: any) {
    aiMsg.thinking = false
    aiMsg.done = true
    aiMsg.error = `处理出错：${err.response?.data?.detail || err.message || '未知错误'}`
    aiMsg.progressSteps = undefined
  } finally {
    sending.value = false
    await nextTick()
    scrollToBottom()
  }
}

// ── 导出 PDF ──
async function exportPdf(msg: ChatMessage) {
  if (exportingId.value) return
  exportingId.value = msg.id
  try {
    const res = await axios.post(
      '/ai/rag/export-pdf',
      {
        query: msg.queryText || '事故分析',
        answer: msg.report || {},
        elapsed: 0,
      },
      {
        responseType: 'blob',
        baseURL: '',
        timeout: 30000,
      }
    )
    const blob = new Blob([res.data], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = '事故分析报告.pdf'
    a.click()
    URL.revokeObjectURL(url)
  } catch (err: any) {
    alert(`导出失败：${err.response?.data?.detail || err.message || '未知错误'}`)
  } finally {
    exportingId.value = null
  }
}

// ── 辅助 ──
function genId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
}

function delay(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

function scrollToBottom() {
  nextTick(() => {
    scrollBottom.value?.scrollIntoView({ behavior: 'smooth' })
  })
}

function autoResize() {
  const el = textareaRef.value
  if (el) {
    el.style.height = 'auto'
    el.style.height = el.scrollHeight + 'px'
  }
}
</script>

<style scoped>
.ai-chat {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background: var(--bg-admin-page);
}

.ai-chat.is-empty {
  justify-content: center;
}

.ai-chat.is-empty .messages-area {
  flex: 0 0 auto;
  overflow: visible;
}

/* ── 消息区 ── */
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 20px 20px 0;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.welcome h2 {
  font-size: 28px;
  color: var(--text-primary);
  margin: 0 0 10px 0;
  font-weight: 600;
}

.welcome p {
  font-size: 17px;
  color: var(--text-dim);
  margin: 0;
}

/* ── 预设问题 ── */
.welcome-hints {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  padding: 16px 20px 0;
}

.hint {
  padding: 7px 16px;
  background: var(--bg-admin-input);
  border: 1px solid var(--border-admin-input);
  border-radius: 16px;
  font-size: 12px;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s;
}

.hint:hover {
  border-color: var(--color-primary);
  color: var(--text-secondary);
}

/* ── 消息行 ── */
.message-row {
  display: flex;
  max-width: 85%;
}

.message-row.user {
  align-self: flex-end;
  justify-content: flex-end;
}

.message-row.ai {
  align-self: flex-start;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.55;
  word-break: break-word;
}

.message-bubble.user {
  background: var(--color-admin-focus);
  color: #fff;
  border-bottom-right-radius: 4px;
  max-width: 100%;
}

.message-bubble.ai {
  background: var(--bg-admin-card);
  border: 1px solid var(--border-primary);
  color: var(--text-primary);
  border-bottom-left-radius: 4px;
  max-width: 100%;
}

.msg-video-tag {
  margin-top: 8px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: rgba(255,255,255,0.15);
  border-radius: 6px;
  font-size: 12px;
}

.msg-video-preview {
  margin-top: 8px;
}

.user-video {
  width: 100%;
  max-width: 320px;
  max-height: 240px;
  border-radius: 8px;
  display: block;
  background: #000;
}

.video-icon { font-size: 14px; }

/* ── 流程链表（垂直时间线） ── */
.progress-chain {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: 4px 0;
}

.progress-step {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.step-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  width: 22px;
}

.step-ball {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 2px solid var(--border-admin-input);
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  transition: background 0.3s, border-color 0.3s;
  flex-shrink: 0;
  box-sizing: border-box;
  position: relative;
}

/* pending (default) — gray hollow circle */

/* active — the ball border highlights, inner ring spins */
.step-ball.active {
  border-color: var(--color-primary);
  background: rgba(0, 229, 255, 0.08);
  animation: none;
}

.step-ball.active::after {
  content: '';
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  border: 2.5px solid transparent;
  border-top-color: var(--color-primary);
  border-right-color: var(--color-primary);
  animation: spin 0.7s linear infinite;
}

/* done — green filled circle with white checkmark */
.step-ball.done {
  background: #4caf50;
  border-color: #4caf50;
  animation: none;
}

.step-ball.done::after {
  display: none;
}

.check {
  font-weight: bold;
  font-size: 13px;
  color: #fff;
  line-height: 1;
  position: relative;
  z-index: 1;
}

@keyframes spin { to { transform: rotate(360deg); } }

.step-line {
  width: 2px;
  height: 22px;
  background: var(--border-admin-input);
  margin: 3px 0;
  transition: background 0.4s;
}

.step-line.done { background: var(--color-success); }

.step-label {
  font-size: 13px;
  color: var(--text-dim);
  padding-top: 1px;
  line-height: 1.5;
}

.progress-step.done .step-label { color: var(--text-muted); }
.progress-step.active .step-label { color: var(--color-primary); font-weight: 500; }

/* ── 错误信息 ── */
.error-msg {
  margin-top: 8px;
  font-size: 13px;
  color: var(--text-danger);
  padding: 6px 10px;
  background: rgba(244, 67, 54, 0.08);
  border-radius: 6px;
}

/* ── 视频卡片 ── */
.video-card {
  margin-top: 12px;
  background: var(--bg-admin-input);
  border: 1px solid var(--border-admin-input);
  border-radius: 10px;
  overflow: hidden;
}

.video-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  font-size: 13px;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-admin-input);
}

.annotated-video {
  width: 100%;
  max-height: 360px;
  display: block;
  background: #000;
}

/* ── 报告卡片 ── */
.report-card {
  margin-top: 12px;
  padding: 14px 16px;
  background: var(--bg-admin-input);
  border: 1px solid var(--border-admin-input);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 14px;
}

.report-card:hover {
  border-color: var(--color-primary);
  background: var(--bg-card-active);
}

.report-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.report-card-icon {
  font-size: 20px;
}

.report-card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.report-card-hint {
  font-size: 12px;
  color: var(--text-dim);
  margin-left: auto;
}

/* ── 报告弹窗 ── */
.report-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.report-modal {
  background: var(--bg-admin-card);
  border: 1px solid var(--border-primary);
  border-radius: 14px;
  width: 90%;
  max-width: 680px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.report-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-primary);
}

.report-modal-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.report-modal-close {
  background: none;
  border: none;
  color: var(--text-dim);
  font-size: 18px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.15s;
}

.report-modal-close:hover {
  color: var(--text-primary);
  background: var(--bg-admin-input);
}

.report-modal-body {
  overflow-y: auto;
  padding: 16px 20px 20px;
}

/* ── 报告区（弹窗内复用） ── */

.report-block {
  margin-top: 10px;
  padding: 10px 12px;
  background: var(--bg-admin-input);
  border: 1px solid var(--border-admin-input);
  border-radius: 8px;
}

.block-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.block-text {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.6;
}

.liability-bars {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-bottom: 8px;
}

.party-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.party-name {
  font-size: 12px;
  color: var(--text-muted);
  width: 80px;
  flex-shrink: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.party-bar-wrap {
  flex: 1;
  height: 7px;
  background: var(--border-primary);
  border-radius: 4px;
  overflow: hidden;
}

.party-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease;
}

.party-pct {
  font-size: 12px;
  font-weight: 600;
  width: 36px;
  text-align: right;
  flex-shrink: 0;
}

.party-reason {
  font-size: 11px;
  color: #90a4ae;
  margin-top: 3px;
  line-height: 1.5;
}

.resort-note {
  font-size: 11px;
  color: var(--text-warning);
  margin-top: 6px;
  padding: 5px 8px;
  background: rgba(255, 152, 0, 0.08);
  border-radius: 4px;
}

.ref-item {
  margin-bottom: 6px;
  padding: 5px 8px;
  background: rgba(124, 77, 255, 0.06);
  border-left: 3px solid #7c4dff33;
  border-radius: 0 4px 4px 0;
}

.ref-item:last-child { margin-bottom: 0; }

.ref-title {
  font-size: 11px;
  font-weight: 500;
  color: #b39ddb;
  margin-bottom: 2px;
}

.ref-text {
  font-size: 11px;
  color: #90a4ae;
  line-height: 1.5;
}

/* ── 导出按钮 ── */
.btn-export-pdf {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  padding: 7px 14px;
  background: transparent;
  border: 1px solid var(--border-accent);
  color: var(--color-primary);
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-export-pdf:hover:not(:disabled) {
  background: var(--bg-card-active);
}

.btn-export-pdf:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ── 输入区 ── */
.input-area {
  padding: 14px 20px;
  background: var(--bg-admin-input-alt);
  border-top: 1px solid var(--border-primary);
}

.input-area.input-empty {
  background: transparent;
  border-top: none;
  padding: 16px 20px 0;
}

.input-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  max-width: 720px;
  margin: 0 auto;
}

.input-empty .input-row {
  max-width: 640px;
}

.input-empty .chat-input {
  border-radius: 24px;
  padding: 12px 18px;
}

.btn-video-upload {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--bg-admin-input);
  border: 1px solid var(--border-admin-input);
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s;
}

.btn-video-upload:hover { border-color: var(--color-primary); }

.btn-video-upload.hasVideo {
  border-color: var(--color-success);
  background: rgba(76, 175, 80, 0.1);
}

.upload-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-dim);
}

.chat-input {
  flex: 1;
  padding: 10px 14px;
  background: var(--bg-admin-input);
  border: 1px solid var(--border-admin-input);
  border-radius: 20px;
  color: var(--text-primary);
  font-size: 14px;
  font-family: inherit;
  resize: none;
  outline: none;
  overflow: hidden;
  line-height: 1.4;
}

.chat-input:focus { border-color: var(--color-admin-focus); }
.chat-input::placeholder { color: var(--text-dim); }

.btn-send {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--color-admin-focus);
  color: #fff;
  border: none;
  font-size: 18px;
  cursor: pointer;
  flex-shrink: 0;
  transition: opacity 0.2s;
}

.btn-send:hover:not(:disabled) { opacity: 0.85; }
.btn-send:disabled { opacity: 0.4; cursor: not-allowed; }

.sending-icon { animation: pulse 1s ease-in-out infinite; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.file-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  margin-left: 50px;
  max-width: 700px;
}

.file-name {
  font-size: 12px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-remove-file {
  background: none;
  border: none;
  color: var(--text-dim);
  cursor: pointer;
  font-size: 14px;
  padding: 0;
}

.btn-remove-file:hover { color: var(--text-danger); }

.scroll-bottom { height: 0; flex-shrink: 0; }
</style>
