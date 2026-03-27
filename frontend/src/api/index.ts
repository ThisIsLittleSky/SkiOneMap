import axios from 'axios'

const TOKEN_KEY = 'ski_admin_token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function removeToken() {
  localStorage.removeItem(TOKEN_KEY)
}

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' }
})

// 每次请求自动带上 token
apiClient.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers['X-Auth-Token'] = token
  return config
})

// 登录认证接口
export function login(username: string, password: string) {
  return apiClient.post<{ token: string; username: string }>('/auth/login', { username, password })
}

export function verifyToken() {
  return apiClient.get<{ username: string; valid: boolean }>('/auth/verify')
}

export function logout() {
  return apiClient.post('/auth/logout')
}


// RAG 知识库接口（直接调 AI 引擎，走 /ai 代理）
const aiClient = axios.create({
  baseURL: '/ai',
  timeout: 120000,
})

export function uploadKnowledgeFile(file: File, onProgress?: (p: number) => void) {
  const form = new FormData()
  form.append('file', file)
  return aiClient.post<{ filename: string; chunks: number; status: string }>(
    '/rag/upload',
    form,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (e.total && onProgress) onProgress(Math.round((e.loaded * 100) / e.total))
      },
    }
  )
}

export function getRagStatus() {
  return aiClient.get<{ initialized: boolean; chunks: number; documents: number }>(
    '/rag/status'
  )
}

export function rebuildRagIndex() {
  return aiClient.post<{ status: string; chunks: number }>('/rag/rebuild')
}


export interface VideoInfo {
  id: number
  userId: number
  filename: string
  filepath: string
  duration: number | null
  status: string
  createdAt: string
}

export interface TaskInfo {
  taskId: number
  status: string
  result?: string
}

export function uploadVideo(file: File, onProgress?: (percent: number) => void) {
  const formData = new FormData()
  formData.append('file', file)
  return apiClient.post<{ id: number; filename: string; status: string }>('/video/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000,
    onUploadProgress: (e) => {
      if (e.total && onProgress) {
        onProgress(Math.round((e.loaded * 100) / e.total))
      }
    }
  })
}

export function getVideo(id: number) {
  return apiClient.get<VideoInfo>(`/video/${id}`)
}

export function listVideos() {
  return apiClient.get<VideoInfo[]>('/video/list')
}

export function createTask(videoId: number) {
  return apiClient.post<TaskInfo>('/task/create', { videoId })
}

export function getTaskStatus(taskId: number) {
  return apiClient.get<TaskInfo>(`/task/${taskId}/status`)
}

export function getTaskResult(taskId: number) {
  return apiClient.get<TaskInfo>(`/task/${taskId}/result`)
}

export interface TrackSummary {
  taskId: number
  status: string
  trackCount: number
  totalFrames: number
  liabilitySuggestion: string
  annotatedVideoAvailable: boolean
  annotatedVideoUrl: string
  alerts: Array<{
    id: number
    taskId: number
    alertType: string
    severity: string
    description: string
    positionX: number
    positionY: number
    createdAt: string
  }>
}

export function getTaskTracks(taskId: number) {
  return apiClient.get<TrackSummary>(`/task/${taskId}/tracks`)
}

export function listTasks() {
  return apiClient.get<Array<{ id: number; videoId: number; status: string; createdAt: string }>>('/task/list')
}

export function listAlerts() {
  return apiClient.get<TrackSummary['alerts']>('/alert/list')
}

// ── 场地配置 & 摄像头 ──────────────────────────────────────────

export interface SceneConfig {
  id?: number
  sceneName: string
  latNW: number | null; lngNW: number | null
  latNE: number | null; lngNE: number | null
  latSW: number | null; lngSW: number | null
  latSE: number | null; lngSE: number | null
  weatherCityCode: string
}

export interface CameraInfo {
  id: number
  name: string
  description: string
  posX: number
  posY: number
  posZ: number
  status: string
  createdAt: string
}

export function getSceneConfig() {
  return apiClient.get<SceneConfig>('/scene/config')
}

export function saveSceneConfig(cfg: SceneConfig) {
  return apiClient.put<SceneConfig>('/scene/config', cfg)
}

export function listCameras() {
  return apiClient.get<CameraInfo[]>('/scene/cameras')
}

export function addCamera(camera: Omit<CameraInfo, 'id' | 'createdAt'>) {
  return apiClient.post<CameraInfo>('/scene/cameras', camera)
}

export function updateCamera(id: number, camera: Partial<CameraInfo>) {
  return apiClient.put<CameraInfo>(`/scene/cameras/${id}`, camera)
}

export function deleteCamera(id: number) {
  return apiClient.delete(`/scene/cameras/${id}`)
}

export function uploadCameraVideo(cameraId: number, file: File, onProgress?: (p: number) => void) {
  const form = new FormData()
  form.append('file', file)
  return apiClient.post<{ videoId: number; taskId: number; cameraId: number; cameraName: string; status: string }>(
    `/scene/cameras/${cameraId}/upload`, form,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000,
      onUploadProgress: (e) => { if (e.total && onProgress) onProgress(Math.round(e.loaded * 100 / e.total)) }
    }
  )
}
