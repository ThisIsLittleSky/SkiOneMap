<template>
  <div class="page-body">
    <!-- 场地配置 -->
    <section class="section">
      <div class="section-header">
        <h3>场地配置（3D建模四角经纬度）</h3>
        <button class="btn-primary" @click="saveConfig" :disabled="configSaving">
          {{ configSaving ? '保存中...' : '保存配置' }}
        </button>
      </div>
      <div class="config-grid">
        <div class="config-item">
          <label>场地名称</label>
          <input v-model="config.sceneName" placeholder="场地名称" />
        </div>
        <div class="config-item">
          <label>天气城市编码</label>
          <input v-model="config.weatherCityCode" placeholder="如 101090301" />
        </div>
        <div class="coord-grid">
          <div class="coord-label">西北角（NW）</div>
          <input v-model.number="config.latNW" type="number" step="0.0001" placeholder="纬度" />
          <input v-model.number="config.lngNW" type="number" step="0.0001" placeholder="经度" />
          <div class="coord-label">东北角（NE）</div>
          <input v-model.number="config.latNE" type="number" step="0.0001" placeholder="纬度" />
          <input v-model.number="config.lngNE" type="number" step="0.0001" placeholder="经度" />
          <div class="coord-label">西南角（SW）</div>
          <input v-model.number="config.latSW" type="number" step="0.0001" placeholder="纬度" />
          <input v-model.number="config.lngSW" type="number" step="0.0001" placeholder="经度" />
          <div class="coord-label">东南角（SE）</div>
          <input v-model.number="config.latSE" type="number" step="0.0001" placeholder="纬度" />
          <input v-model.number="config.lngSE" type="number" step="0.0001" placeholder="经度" />
        </div>
      </div>
      <div v-if="configMsg" class="message" :class="configErr ? 'error' : 'success'">{{ configMsg }}</div>
    </section>

    <div class="divider"></div>

    <!-- 摄像头列表 -->
    <section class="section">
      <div class="section-header">
        <h3>摄像头管理</h3>
        <button class="btn-primary" @click="showAddForm = !showAddForm">
          {{ showAddForm ? '取消' : '+ 添加摄像头' }}
        </button>
      </div>

      <!-- 添加表单 -->
      <div v-if="showAddForm" class="add-form">
        <div class="form-row">
          <div class="form-item">
            <label>摄像头名称 *</label>
            <input v-model="newCam.name" placeholder="如：A区1号摄像头" />
          </div>
          <div class="form-item">
            <label>描述</label>
            <input v-model="newCam.description" placeholder="可选描述" />
          </div>
        </div>
        <div class="coord-hint">
          3D坐标参考范围：X / Z 约 <strong>-50 ~ 50</strong>（雪道平面水平方向），Y 约 <strong>0 ~ 30</strong>（地面以上高度）。建议从 X=0, Y=5, Z=0 开始，逐步调整至合适位置。
        </div>
        <div class="form-row">
          <div class="form-item">
            <label>3D场景 X（左右，-50~50）</label>
            <input v-model.number="newCam.posX" type="number" step="1" placeholder="-50 ~ 50" />
          </div>
          <div class="form-item">
            <label>3D场景 Y（高度，0~30）</label>
            <input v-model.number="newCam.posY" type="number" step="1" placeholder="0 ~ 30" />
          </div>
          <div class="form-item">
            <label>3D场景 Z（前后，-50~50）</label>
            <input v-model.number="newCam.posZ" type="number" step="1" placeholder="-50 ~ 50" />
          </div>
          <div class="form-item">
            <label>状态</label>
            <select v-model="newCam.status">
              <option value="ONLINE">在线</option>
              <option value="OFFLINE">离线</option>
            </select>
          </div>
        </div>
        <button class="btn-primary" @click="handleAdd" :disabled="!newCam.name || adding">
          {{ adding ? '添加中...' : '确认添加' }}
        </button>
        <div v-if="addMsg" class="message" :class="addErr ? 'error' : 'success'">{{ addMsg }}</div>
      </div>

      <p v-if="loading" class="tip">加载中...</p>
      <p v-else-if="cameras.length === 0" class="tip">暂无摄像头，请点击添加</p>
      <table v-else>
        <thead>
          <tr>
            <th>ID</th><th>名称</th><th>描述</th>
            <th>X</th><th>Y</th><th>Z</th>
            <th>状态</th><th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="cam in cameras" :key="cam.id">
            <td>{{ cam.id }}</td>
            <!-- 行内编辑 -->
            <template v-if="editId === cam.id">
              <td><input v-model="editForm.name" class="inline-input" /></td>
              <td><input v-model="editForm.description" class="inline-input" /></td>
              <td><input v-model.number="editForm.posX" type="number" step="0.1" class="inline-input num-input" /></td>
              <td><input v-model.number="editForm.posY" type="number" step="0.1" class="inline-input num-input" /></td>
              <td><input v-model.number="editForm.posZ" type="number" step="0.1" class="inline-input num-input" /></td>
              <td>
                <select v-model="editForm.status" class="inline-input">
                  <option value="ONLINE">在线</option>
                  <option value="OFFLINE">离线</option>
                </select>
              </td>
              <td class="actions-cell">
                <button class="btn-save" @click="handleEdit(cam.id)" :disabled="saving">{{ saving ? '保存中' : '保存' }}</button>
                <button class="btn-cancel" @click="editId = null">取消</button>
              </td>
            </template>
            <template v-else>
              <td>{{ cam.name }}</td>
              <td class="desc-cell">{{ cam.description }}</td>
              <td>{{ cam.posX }}</td>
              <td>{{ cam.posY }}</td>
              <td>{{ cam.posZ }}</td>
              <td>
                <span class="status-badge" :class="cam.status === 'ONLINE' ? 'online' : 'offline'">
                  {{ cam.status === 'ONLINE' ? '在线' : '离线' }}
                </span>
              </td>
              <td class="actions-cell">
                <button class="btn-upload" @click="openUpload(cam)">上传视频</button>
                <button class="btn-edit" @click="startEdit(cam)">编辑</button>
                <button class="btn-delete" @click="handleDelete(cam.id)">删除</button>
              </td>
            </template>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- 视频上传弹窗 -->
    <Teleport to="body">
      <div v-if="uploadTarget" class="overlay" @click.self="!uploading && !analyzing && closeUploadModal()">
        <div class="upload-modal">
          <div class="modal-header">
            <span>向【{{ uploadTarget.name }}】上传事故视频</span>
            <button class="btn-close" @click="closeUploadModal">×</button>
          </div>
          <div class="modal-body">
            <label class="file-label">
              <input type="file" accept="video/*" @change="handleFileChange" ref="fileInput" />
              {{ uploadFile ? uploadFile.name : '选择视频文件' }}
            </label>
            <div class="progress-bar" v-if="uploading">
              <div class="progress-fill" :style="{ width: uploadPct + '%' }"></div>
            </div>
            <div v-if="analyzing" class="analyzing-hint">
              <span class="analyzing-dot"></span> AI 分析中，请稍候...
            </div>
            <div v-if="uploadMsg2" class="message" :class="uploadErr2 ? 'error' : 'success'">{{ uploadMsg2 }}</div>
            <button class="btn-primary" @click="handleUpload" :disabled="!uploadFile || uploading || analyzing">
              {{ uploading ? `上传中 ${uploadPct}%` : analyzing ? '分析中...' : '上传并开始分析' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  getSceneConfig, saveSceneConfig, listCameras, addCamera, updateCamera, deleteCamera,
  uploadCameraVideo, getTaskStatus, type SceneConfig, type CameraInfo
} from '@/api'

const config = ref<SceneConfig>({
  sceneName: '崇礼滑雪场',
  latNW: null, lngNW: null, latNE: null, lngNE: null,
  latSW: null, lngSW: null, latSE: null, lngSE: null,
  weatherCityCode: '101090301',
})
const configSaving = ref(false)
const configMsg = ref('')
const configErr = ref(false)

const cameras = ref<CameraInfo[]>([])
const loading = ref(false)
const showAddForm = ref(false)
const adding = ref(false)
const addMsg = ref('')
const addErr = ref(false)

const newCam = ref({ name: '', description: '', posX: 0, posY: 0, posZ: 0, status: 'ONLINE' })

// 行内编辑状态
const editId = ref<number | null>(null)
const editForm = ref({ name: '', description: '', posX: 0, posY: 0, posZ: 0, status: 'ONLINE' })
const saving = ref(false)

function startEdit(cam: CameraInfo) {
  editId.value = cam.id
  editForm.value = { name: cam.name, description: cam.description, posX: cam.posX, posY: cam.posY, posZ: cam.posZ, status: cam.status }
}

async function handleEdit(id: number) {
  saving.value = true
  try {
    await updateCamera(id, editForm.value)
    editId.value = null
    await loadCameras()
  } catch { alert('保存失败') }
  finally { saving.value = false }
}

const uploadTarget = ref<CameraInfo | null>(null)
const uploadFile = ref<File | null>(null)
const uploading = ref(false)
const uploadPct = ref(0)
const uploadMsg2 = ref('')
const uploadErr2 = ref(false)
const fileInput = ref<HTMLInputElement>()

async function loadConfig() {
  try { const r = await getSceneConfig(); config.value = r.data } catch {}
}

async function saveConfig() {
  configSaving.value = true; configMsg.value = ''
  try {
    await saveSceneConfig(config.value)
    configMsg.value = '保存成功'; configErr.value = false
  } catch { configMsg.value = '保存失败'; configErr.value = true }
  finally { configSaving.value = false }
}

async function loadCameras() {
  loading.value = true
  try { const r = await listCameras(); cameras.value = r.data }
  catch {} finally { loading.value = false }
}

async function handleAdd() {
  adding.value = true; addMsg.value = ''
  try {
    await addCamera(newCam.value)
    addMsg.value = '添加成功'; addErr.value = false
    newCam.value = { name: '', description: '', posX: 0, posY: 0, posZ: 0, status: 'ONLINE' }
    showAddForm.value = false
    await loadCameras()
  } catch { addMsg.value = '添加失败'; addErr.value = true }
  finally { adding.value = false }
}

async function handleDelete(id: number) {
  if (!confirm('确认删除该摄像头？')) return
  await deleteCamera(id)
  await loadCameras()
}

function openUpload(cam: CameraInfo) {
  uploadTarget.value = cam
  uploadFile.value = null
  uploadMsg2.value = ''
  uploadErr2.value = false
  uploadPct.value = 0
}

function handleFileChange(e: Event) {
  const t = e.target as HTMLInputElement
  if (t.files?.length) { uploadFile.value = t.files[0]; uploadMsg2.value = '' }
}

function closeUploadModal() {
  if (uploading.value || analyzing.value) return
  uploadTarget.value = null
}

const analyzing = ref(false)

async function handleUpload() {
  if (!uploadFile.value || !uploadTarget.value) return
  uploading.value = true; uploadPct.value = 0; uploadMsg2.value = ''
  let taskId: number | null = null
  try {
    const r = await uploadCameraVideo(uploadTarget.value.id, uploadFile.value, p => { uploadPct.value = p })
    taskId = r.data.taskId
    uploadErr2.value = false
    uploadFile.value = null
    if (fileInput.value) fileInput.value.value = ''
  } catch (err: any) {
    uploadMsg2.value = `上传失败: ${err.response?.data?.error || err.message}`
    uploadErr2.value = true
    uploading.value = false
    return
  }
  uploading.value = false

  // 轮询任务状态
  analyzing.value = true
  uploadMsg2.value = `上传成功，正在分析（任务 #${taskId}）...`
  const DONE_STATES = ['DONE', 'COMPLETED', 'FAILED', 'ERROR']
  const poll = async () => {
    try {
      const s = await getTaskStatus(taskId!)
      const status = s.data.status
      if (DONE_STATES.includes(status)) {
        analyzing.value = false
        if (status === 'FAILED' || status === 'ERROR') {
          uploadMsg2.value = `分析失败（任务 #${taskId}）`
          uploadErr2.value = true
        } else {
          uploadMsg2.value = `分析完成（任务 #${taskId}）`
          uploadErr2.value = false
        }
      } else {
        setTimeout(poll, 3000)
      }
    } catch {
      analyzing.value = false
      uploadMsg2.value = `查询分析状态失败（任务 #${taskId}）`
      uploadErr2.value = true
    }
  }
  poll()
}

onMounted(() => { loadConfig(); loadCameras() })
</script>

<style scoped>
.page-body { padding: 24px 28px; max-width: 1100px; }
.section { margin-bottom: 8px; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
h3 { font-size: 15px; color: #90caf9; }
.divider { border: none; border-top: 1px solid #1e3a5f; margin: 24px 0; }

.config-grid { display: flex; flex-direction: column; gap: 12px; }
.config-item { display: flex; flex-direction: column; gap: 5px; max-width: 320px; }
.config-item label { font-size: 12px; color: #78909c; }
.config-item input { padding: 7px 12px; background: #0a1929; border: 1px solid #2a4a6a; border-radius: 4px; color: #e0e0e0; font-size: 13px; outline: none; }

.coord-grid {
  display: grid;
  grid-template-columns: 100px 1fr 1fr;
  gap: 8px;
  align-items: center;
  max-width: 500px;
}
.coord-grid input { padding: 7px 10px; background: #0a1929; border: 1px solid #2a4a6a; border-radius: 4px; color: #e0e0e0; font-size: 13px; outline: none; }
.coord-label { font-size: 12px; color: #546e7a; }

.add-form { background: #0d1f33; border: 1px solid #1e3a5f; border-radius: 8px; padding: 16px; margin-bottom: 16px; display: flex; flex-direction: column; gap: 12px; }
.form-row { display: flex; gap: 12px; flex-wrap: wrap; }
.form-item { display: flex; flex-direction: column; gap: 5px; flex: 1; min-width: 120px; }
.form-item label { font-size: 12px; color: #78909c; }
.form-item input, .form-item select { padding: 7px 10px; background: #0a1929; border: 1px solid #2a4a6a; border-radius: 4px; color: #e0e0e0; font-size: 13px; outline: none; }

.tip { color: #37474f; font-size: 14px; padding: 16px 0; }

table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid #1a2e44; }
th { background: #0d1f33; color: #78909c; font-weight: 600; }
tr:hover td { background: rgba(21,101,192,0.06); }
.desc-cell { max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #546e7a; }
.actions-cell { display: flex; gap: 8px; }

.status-badge { padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 500; }
.online { background: rgba(46,125,50,0.2); color: #81c784; }
.offline { background: rgba(96,125,139,0.2); color: #90a4ae; }

.btn-primary { padding: 7px 16px; background: #1565c0; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-upload { padding: 4px 10px; font-size: 12px; background: #0d47a1; color: #90caf9; border: 1px solid #1565c0; border-radius: 4px; cursor: pointer; }
.btn-edit { padding: 4px 10px; font-size: 12px; background: transparent; color: #80cbc4; border: 1px solid #00897b; border-radius: 4px; cursor: pointer; }
.btn-save { padding: 4px 10px; font-size: 12px; background: #1b5e20; color: #a5d6a7; border: 1px solid #2e7d32; border-radius: 4px; cursor: pointer; }
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-cancel { padding: 4px 10px; font-size: 12px; background: transparent; color: #78909c; border: 1px solid #37474f; border-radius: 4px; cursor: pointer; }
.btn-delete { padding: 4px 10px; font-size: 12px; background: transparent; color: #ef9a9a; border: 1px solid #c62828; border-radius: 4px; cursor: pointer; }

.inline-input {
  padding: 4px 6px;
  background: #0a1929;
  border: 1px solid #2a4a6a;
  border-radius: 3px;
  color: #e0e0e0;
  font-size: 12px;
  outline: none;
  width: 100%;
  min-width: 60px;
}
.inline-input:focus { border-color: #1976d2; }
.num-input { width: 60px; min-width: 50px; }

.coord-hint {
  font-size: 12px;
  color: #546e7a;
  background: #0a1929;
  border: 1px solid #1e3a5f;
  border-radius: 4px;
  padding: 8px 12px;
  line-height: 1.6;
}
.coord-hint strong { color: #00e5ff; }

.message { padding: 8px 14px; border-radius: 4px; font-size: 13px; }
.message.success { background: rgba(46,125,50,0.15); color: #81c784; border: 1px solid #2e7d32; }
.message.error { background: rgba(198,40,40,0.15); color: #ef9a9a; border: 1px solid #c62828; }

.overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 1000; display: flex; align-items: center; justify-content: center; }
.upload-modal { background: #0d1f33; border: 1px solid #1e3a5f; border-radius: 10px; width: 460px; overflow: hidden; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 18px; border-bottom: 1px solid #1e3a5f; font-size: 14px; color: #90caf9; }
.btn-close { background: none; border: none; color: #546e7a; font-size: 20px; cursor: pointer; }
.modal-body { padding: 18px; display: flex; flex-direction: column; gap: 12px; }
.file-label { display: inline-flex; align-items: center; padding: 7px 14px; background: #0a1929; border: 1px solid #2a4a6a; border-radius: 4px; font-size: 13px; color: #90caf9; cursor: pointer; }
.file-label input { display: none; }
.progress-bar { height: 6px; background: #1a2e44; border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: #42a5f5; transition: width 0.2s; }

.analyzing-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #00e5ff;
  padding: 4px 0;
}
.analyzing-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #00e5ff;
  animation: blink 1.2s ease-in-out infinite;
  flex-shrink: 0;
}
@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0.2; } }
</style>
