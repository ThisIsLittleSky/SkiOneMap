<template>
  <div class="sos-view">
    <div class="header">
      <h2 class="title">事故救援 (SOS) 记录管理</h2>
      <div class="actions">
        <button class="btn btn-primary" @click="fetchSosList">
          <span class="icon">↻</span> 刷新列表
        </button>
      </div>
    </div>

    <div class="content">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else-if="sosList.length === 0" class="empty">暂无事故求救记录</div>
      
      <table v-else class="sos-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>发生时间</th>
            <th>模式</th>
            <th>位置(经度, 纬度)</th>
            <th>设备信息</th>
            <th>处理状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="sos in sosList" :key="sos.id" :class="{ 'row-unhandled': sos.status === 0 }">
            <td>{{ sos.id }}</td>
            <td>{{ formatTime(sos.timestamp) }}</td>
            <td>
              <span :class="['mode-badge', sos.mode === 'sentinel' ? 'mode-sentinel' : 'mode-normal']">
                {{ sos.mode === 'sentinel' ? '哨兵模式' : '普通模式' }}
              </span>
            </td>
            <td class="location">
              {{ sos.longitude ? sos.longitude.toFixed(6) : '未知' }}, 
              {{ sos.latitude ? sos.latitude.toFixed(6) : '未知' }}
            </td>
            <td class="device-cell" :title="sos.device">{{ truncate(sos.device, 20) }}</td>
            <td>
              <span :class="['status-badge', sos.status === 1 ? 'status-handled' : 'status-pending']">
                {{ sos.status === 1 ? '已处理' : '待处理' }}
              </span>
            </td>
            <td>
              <button 
                v-if="sos.status === 0"
                class="btn btn-action" 
                @click="markAsHandled(sos.id)"
              >
                标记已处理
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// 定义接口模型
interface SosRecord {
  id: number
  timestamp: number
  latitude: number
  longitude: number
  mode: string
  device: string
  status: number
}

const sosList = ref<SosRecord[]>([])
const loading = ref(true)
const error = ref('')

// TODO: 等后端完善了 GET /api/sos 列表接口和 PUT /api/sos/{id}/status 接口后，替换这里的 mock 数据
// 目前由于您只让我加了前台路由，我先写一套带模拟数据的 UI，方便您查看效果
const fetchSosList = async () => {
  loading.value = true
  error.value = ''
  
  try {
    // 模拟网络请求延迟
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 模拟数据
    sosList.value = [
      {
        id: 1,
        timestamp: Date.now() - 1000 * 60 * 5,
        latitude: 39.9042,
        longitude: 116.4074,
        mode: 'sentinel',
        device: 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)...',
        status: 0
      },
      {
        id: 2,
        timestamp: Date.now() - 1000 * 60 * 60 * 2,
        latitude: 39.9011,
        longitude: 116.4022,
        mode: 'normal',
        device: 'Mozilla/5.0 (Linux; Android 13; SM-G991B)...',
        status: 1
      }
    ]
  } catch (err: any) {
    error.value = err.message || '获取记录失败'
  } finally {
    loading.value = false
  }
}

const markAsHandled = async (id: number) => {
  if (!confirm('确认已处理该求救信号？')) return
  
  try {
    // 模拟标记已处理请求
    await new Promise(resolve => setTimeout(resolve, 300))
    const item = sosList.value.find(s => s.id === id)
    if (item) {
      item.status = 1
    }
  } catch (err: any) {
    alert('操作失败: ' + err.message)
  }
}

const formatTime = (ts: number) => {
  if (!ts) return '未知'
  return new Date(ts).toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  })
}

const truncate = (str: string, len: number) => {
  if (!str) return '未知'
  return str.length > len ? str.substring(0, len) + '...' : str
}

onMounted(() => {
  fetchSosList()
})
</script>

<style scoped>
.sos-view {
  padding: 24px;
  color: #e3f2fd;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.title {
  font-size: 20px;
  font-weight: 600;
  color: #fff;
  margin: 0;
}

.content {
  flex: 1;
  background: #112233;
  border-radius: 8px;
  border: 1px solid #1e3a5f;
  padding: 20px;
  overflow-y: auto;
}

.loading, .error, .empty {
  text-align: center;
  padding: 40px;
  color: #90a4ae;
}

.error { color: #ef5350; }

.sos-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.sos-table th {
  padding: 12px 16px;
  color: #90caf9;
  font-weight: 500;
  font-size: 14px;
  border-bottom: 1px solid #1e3a5f;
  background: rgba(30, 58, 95, 0.3);
}

.sos-table td {
  padding: 16px;
  font-size: 14px;
  border-bottom: 1px solid #1e3a5f;
  color: #e0e0e0;
}

.row-unhandled {
  background: rgba(244, 67, 54, 0.05);
}

.device-cell {
  color: #90a4ae;
  font-size: 12px;
}

.mode-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.mode-sentinel { background: rgba(255, 152, 0, 0.2); color: #ff9800; border: 1px solid rgba(255, 152, 0, 0.5); }
.mode-normal { background: rgba(33, 150, 243, 0.2); color: #2196f3; border: 1px solid rgba(33, 150, 243, 0.5); }

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-pending { background: #f44336; color: white; }
.status-handled { background: #4caf50; color: white; }

.btn {
  padding: 6px 12px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.btn-primary { background: #1976d2; color: white; }
.btn-primary:hover { background: #1565c0; }

.btn-action { background: #ef5350; color: white; }
.btn-action:hover { background: #d32f2f; }
</style>
