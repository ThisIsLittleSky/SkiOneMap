<template>
  <div class="liability-display">
    <template v-if="structured">
      <!-- 责任占比 -->
      <div v-if="structured.liability.parties.length > 0" class="ld-section">
        <div class="ld-section-title">责任占比</div>
        <div class="ld-bars">
          <div v-for="(p, i) in structured.liability.parties" :key="i" class="ld-party-row">
            <span class="ld-party-name">{{ p.name }}</span>
            <div class="ld-bar-wrap">
              <div class="ld-bar" :style="{ width: p.percentage + '%', background: colors[i % colors.length] }"></div>
            </div>
            <span class="ld-pct" :style="{ color: colors[i % colors.length] }">{{ p.percentage }}%</span>
          </div>
        </div>
        <div v-for="(p, i) in structured.liability.parties" :key="'r'+i" class="ld-reason">
          <strong>{{ p.name }}：</strong>{{ p.reason }}
        </div>
        <div v-if="structured.liability.resort_liability && structured.liability.resort_liability !== '无'" class="ld-resort">
          <strong>雪场连带责任：</strong>{{ structured.liability.resort_liability }}
        </div>
      </div>

      <!-- 行为分析 -->
      <div v-if="structured.behavior_analysis" class="ld-section">
        <div class="ld-section-title">行为分析</div>
        <div class="ld-text">{{ structured.behavior_analysis }}</div>
      </div>

      <!-- 参考文献 -->
      <div v-if="structured.references.length > 0" class="ld-section">
        <div class="ld-section-title">参考文献</div>
        <div v-for="(ref, i) in structured.references" :key="i" class="ld-ref">
          <div class="ld-ref-title">{{ ref.title }}</div>
          <div class="ld-ref-content">{{ ref.content }}</div>
        </div>
      </div>

      <!-- 处理建议 -->
      <div v-if="structured.suggestion" class="ld-section">
        <div class="ld-section-title">处理建议</div>
        <div class="ld-text">{{ structured.suggestion }}</div>
      </div>
    </template>
    <template v-else>
      <pre class="ld-fallback">{{ text }}</pre>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { LiabilityResult } from '@/api'

const props = defineProps<{
  text: string
}>()

const colors = ['#00e5ff', '#ff6b35', '#7c4dff', '#ff9800', '#4caf50']

const structured = computed<LiabilityResult | null>(() => {
  if (!props.text) return null
  try {
    const parsed = JSON.parse(props.text)
    if (parsed && parsed.liability) return parsed as LiabilityResult
  } catch {
    // not JSON, fallback to plain text
  }
  return null
})
</script>

<style scoped>
.ld-section {
  margin-top: 8px;
  padding: 8px 10px;
  background: rgba(13, 31, 51, 0.6);
  border: 1px solid #1e3a5f;
  border-radius: 4px;
}

.ld-section-title {
  font-size: 11px;
  font-weight: 600;
  color: #90caf9;
  margin-bottom: 6px;
  padding-bottom: 3px;
  border-bottom: 1px solid #1e3a5f33;
}

.ld-text {
  font-size: 12px;
  color: #b0bec5;
  line-height: 1.6;
}

.ld-bars {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 6px;
}

.ld-party-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.ld-party-name {
  font-size: 11px;
  color: #78909c;
  width: 70px;
  flex-shrink: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ld-bar-wrap {
  flex: 1;
  height: 6px;
  background: #1e3a5f;
  border-radius: 3px;
  overflow: hidden;
}

.ld-bar {
  height: 100%;
  border-radius: 3px;
  transition: width 0.8s ease;
}

.ld-pct {
  font-size: 12px;
  font-weight: 600;
  width: 36px;
  text-align: right;
  flex-shrink: 0;
}

.ld-reason {
  font-size: 11px;
  color: #90a4ae;
  margin-top: 3px;
  line-height: 1.4;
}

.ld-resort {
  font-size: 11px;
  color: #ffb74d;
  margin-top: 4px;
  padding: 4px 6px;
  background: rgba(255, 152, 0, 0.06);
  border-radius: 3px;
}

.ld-ref {
  margin-bottom: 6px;
  padding: 4px 6px;
  background: rgba(124, 77, 255, 0.05);
  border-left: 2px solid #7c4dff33;
  border-radius: 0 3px 3px 0;
}

.ld-ref:last-child { margin-bottom: 0; }

.ld-ref-title {
  font-size: 11px;
  font-weight: 500;
  color: #b39ddb;
  margin-bottom: 2px;
}

.ld-ref-content {
  font-size: 11px;
  color: #90a4ae;
  line-height: 1.4;
}

.ld-fallback {
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'Microsoft YaHei', sans-serif;
  font-size: 12px;
  line-height: 1.7;
  color: #b0bec5;
  margin: 0;
}
</style>
