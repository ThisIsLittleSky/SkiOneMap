<template>
  <div class="panel">
    <div class="panel-title">
      <span class="title-icon">⚖</span> 事故智能定责
      <span class="live-badge">LIVE</span>
    </div>
    <div class="panel-body">
      <div v-if="items.length === 0" class="empty">
        <div class="empty-icon">📋</div>
        <div>暂无定责记录</div>
      </div>
      <div v-for="item in items" :key="item.taskId" class="liability-item">
        <div class="item-header">
          <span class="task-id">
            <span class="task-hash">#</span>{{ item.taskId }}
          </span>
          <span class="item-status" :class="item.status">{{ item.statusText }}</span>
          <span class="item-time">{{ item.time }}</span>
        </div>

        <!-- 责任比例可视化 -->
        <div v-if="item.parties.length > 0" class="liability-bars">
          <div v-for="p in item.parties" :key="p.name" class="party-row">
            <span class="party-name">{{ p.name }}</span>
            <div class="party-bar-wrap">
              <div
                class="party-bar"
                :style="{ width: p.pct + '%', background: p.color }"
              ></div>
            </div>
            <span class="party-pct" :style="{ color: p.color }">{{ p.pct }}%</span>
          </div>
        </div>

        <!-- 法律条文依据 -->
        <div v-if="item.legalRefs.length > 0" class="legal-refs">
          <span v-for="ref in item.legalRefs" :key="ref" class="legal-tag">§ {{ ref }}</span>
        </div>

        <!-- 全文摘要 -->
        <div class="item-summary">{{ item.summary }}</div>

        <!-- 预警类型标签 -->
        <div v-if="item.alertTypes.length > 0" class="item-alerts">
          <span class="alert-tag" v-for="t in item.alertTypes" :key="t">{{ t }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAlertStore } from '@/stores/alertStore'

const alertStore = useAlertStore()

const PARTY_COLORS = ['#00e5ff', '#ff6b35', '#7c4dff', '#ff9800', '#4caf50']

function parseLiability(text: string) {
  const parties: { name: string; pct: number; color: string }[] = []
  const legalRefs: string[] = []

  if (!text) return { parties, legalRefs }

  // 匹配 "XX方：30%" 或 "甲方承担70%"
  const pctRegex = /([^，,。\s：:]{1,8})[方责任][\s：:]*(\d+)%/g
  let m: RegExpExecArray | null
  let colorIdx = 0
  while ((m = pctRegex.exec(text)) !== null) {
    parties.push({ name: m[1], pct: parseInt(m[2]), color: PARTY_COLORS[colorIdx++ % PARTY_COLORS.length] })
  }

  // 匹配法律条文：《xxx》第x条 或 第xx条第x款
  const lawRegex = /《[^》]{1,30}》[^，,。]*?第[\d一二三四五六七八九十百]+条(?:第[\d一二三四五六七八九十百]+款)?/g
  while ((m = lawRegex.exec(text)) !== null) {
    if (legalRefs.length < 3) legalRefs.push(m[0].slice(0, 20))
  }

  // 也匹配简单的 第xx条
  if (legalRefs.length === 0) {
    const simpleRegex = /第[\d一二三四五六七八九十百]{1,4}条(?:第[\d一二三四五六七八九十百]+款)?/g
    while ((m = simpleRegex.exec(text)) !== null) {
      if (legalRefs.length < 3) legalRefs.push(m[0])
    }
  }

  return { parties, legalRefs }
}

interface LiabilityItem {
  taskId: number
  time: string
  summary: string
  status: string
  statusText: string
  parties: { name: string; pct: number; color: string }[]
  legalRefs: string[]
  alertTypes: string[]
}

const items = computed<LiabilityItem[]>(() => {
  return alertStore.alerts
    .filter(a => a.liabilitySuggestion || a.rawStatus === 'COMPLETED')
    .slice(0, 5)
    .map(a => {
      const text = a.liabilitySuggestion || ''
      const { parties, legalRefs } = parseLiability(text)
      const statusMap: Record<string, string> = {
        COMPLETED: '已定责', PROCESSING: '分析中', FAILED: '失败', PENDING: '待处理'
      }
      return {
        taskId: a.taskId,
        time: a.createdAt,
        summary: text.slice(0, 56) + (text.length > 56 ? '...' : ''),
        status: (a.rawStatus || 'info').toLowerCase(),
        statusText: statusMap[a.rawStatus || ''] || '处理中',
        parties,
        legalRefs,
        alertTypes: [...new Set((a.subAlerts || []).map(s => s.alertType))].slice(0, 3),
      }
    })
})
</script>

<style scoped>
.panel { height: 100%; display: flex; flex-direction: column; }

.panel-title {
  font-size: 12px;
  font-weight: 600;
  color: #00e5ff;
  letter-spacing: 1px;
  padding-bottom: 8px;
  border-bottom: 1px solid #1e3a5f33;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 5px;
}
.title-icon { font-style: normal; }
.live-badge {
  margin-left: auto;
  font-size: 9px;
  padding: 1px 5px;
  background: rgba(244, 67, 54, 0.2);
  color: #ef9a9a;
  border: 1px solid #c6282844;
  border-radius: 10px;
  animation: blink 2s infinite;
}
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

.panel-body { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }

.empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 12px;
  color: #37474f;
}
.empty-icon { font-size: 24px; opacity: 0.4; }

.liability-item {
  background: rgba(0, 229, 255, 0.03);
  border: 1px solid #1e3a5f;
  border-radius: 6px;
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  transition: border-color 0.2s;
}
.liability-item:hover { border-color: #00e5ff33; }

.item-header {
  display: flex;
  align-items: center;
  gap: 6px;
}
.task-id { font-size: 12px; color: #00e5ff; font-weight: 700; }
.task-hash { color: #0097a7; font-size: 10px; }

.item-status {
  font-size: 9px;
  padding: 1px 6px;
  border-radius: 10px;
}
.item-status.completed { background: rgba(0,229,255,0.12); color: #00e5ff; }
.item-status.processing { background: rgba(255,152,0,0.12); color: #ffb74d; }
.item-status.failed { background: rgba(244,67,54,0.12); color: #ef9a9a; }

.item-time { font-size: 10px; color: #37474f; margin-left: auto; }

/* 责任比例 */
.liability-bars {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.party-row {
  display: flex;
  align-items: center;
  gap: 5px;
}
.party-name { font-size: 10px; color: #78909c; width: 36px; flex-shrink: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.party-bar-wrap { flex: 1; height: 5px; background: #1e3a5f; border-radius: 3px; overflow: hidden; }
.party-bar { height: 100%; border-radius: 3px; transition: width 1s ease; }
.party-pct { font-size: 11px; font-weight: 600; width: 30px; text-align: right; flex-shrink: 0; }

/* 法律条文 */
.legal-refs { display: flex; gap: 4px; flex-wrap: wrap; }
.legal-tag {
  font-size: 9px;
  padding: 1px 6px;
  background: rgba(124, 77, 255, 0.12);
  color: #b39ddb;
  border: 1px solid #7c4dff33;
  border-radius: 10px;
  white-space: nowrap;
  overflow: hidden;
  max-width: 100%;
  text-overflow: ellipsis;
}

.item-summary { font-size: 11px; color: #78909c; line-height: 1.5; }

.item-alerts { display: flex; gap: 4px; flex-wrap: wrap; }
.alert-tag {
  font-size: 10px;
  padding: 1px 6px;
  background: rgba(244, 67, 54, 0.12);
  color: #ef9a9a;
  border-radius: 10px;
  border: 1px solid #c6282833;
}
</style>
