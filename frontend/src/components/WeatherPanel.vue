<template>
  <div class="weather-widget">
    <template v-if="weather">
      <span class="weather-icon">{{ weatherIcon(today.type) }}</span>
      <span class="temp-now">{{ weather.wendu }}°</span>
      <span class="weather-type">{{ today.type }}</span>
      <span class="temp-range">{{ todayLow }}~{{ todayHigh }}</span>
      <span class="weather-wind">{{ today.fx }} {{ today.fl }}</span>
    </template>
    <template v-else>
      <span class="loading">获取天气...</span>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const props = defineProps<{ cityCode?: string }>()
const weather = ref<any>(null)
const today = ref<any>({})

const todayHigh = computed(() => today.value.high?.replace('高温 ', '') || '--')
const todayLow = computed(() => today.value.low?.replace('低温 ', '') || '--')

const ICON_MAP: Record<string, string> = {
  '晴': '☀️', '多云': '⛅', '阴': '☁️', '小雨': '🌧️', '中雨': '🌧️',
  '大雨': '⛈️', '暴雨': '⛈️', '小雪': '🌨️', '中雪': '❄️',
  '大雪': '❄️', '暴雪': '❄️', '雨夹雪': '🌨️', '雾': '🌫️', '霾': '🌫️',
}

function weatherIcon(type: string): string {
  for (const [k, v] of Object.entries(ICON_MAP)) {
    if (type?.includes(k)) return v
  }
  return '🌤️'
}

async function fetchWeather() {
  const code = props.cityCode || '101090301'
  try {
    const res = await axios.get(`/weather/api/weather/city/${code}`, { timeout: 8000 })
    if (res.data.status === 200) {
      weather.value = res.data.data
      today.value = res.data.data.forecast?.[0] || {}
    }
  } catch {}
}

onMounted(fetchWeather)
</script>

<style scoped>
.weather-widget {
  display: flex;
  align-items: center;
  gap: 8px;
}

.weather-icon { font-size: 22px; line-height: 1; }
.temp-now { font-size: 22px; font-weight: 700; color: #e3f2fd; line-height: 1; }
.weather-type { font-size: 12px; color: #90caf9; }
.temp-range { font-size: 11px; color: #546e7a; }
.weather-wind { font-size: 11px; color: #546e7a; }
.loading { font-size: 12px; color: #37474f; }
</style>
