<template>
  <div ref="chartEl" class="ski-map-chart"></div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

export interface AlertPoint {
  positionX: number
  positionY: number
  alertType: string
  severity: string
}

const props = withDefaults(defineProps<{
  alertPoints?: AlertPoint[]
}>(), {
  alertPoints: () => [],
})

const chartEl = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

// 2.5D 等角投影转换
// 将地图坐标 (col, row) 映射到屏幕坐标
const TILE_W = 64  // 菱形宽度
const TILE_H = 32  // 菱形高度

function toScreen(col: number, row: number, elevation = 0): [number, number] {
  const x = (col - row) * (TILE_W / 2)
  const y = (col + row) * (TILE_H / 2) - elevation * 20
  return [x, y]
}

// 雪场地图数据：每个格子 [col, row, elevation, type]
// type: 0=雪坡, 1=树木, 2=山顶, 3=缆车站, 4=滑道
const COLS = 12
const ROWS = 14

// 定义地形高程（模拟山坡）
function getElevation(col: number, row: number): number {
  // 山顶在左上角，向右下逐渐降低
  const distFromTop = (col + row) / (COLS + ROWS)
  return Math.max(0, Math.round((1 - distFromTop) * 5))
}

// 定义地物类型
function getTileType(col: number, row: number): number {
  // 缆车站：左上角 和 右下角
  if (col === 1 && row === 1) return 3  // 山顶缆车站
  if (col === 10 && row === 12) return 3 // 山脚缆车站
  // 树木区域：两侧边缘
  if (col <= 1 || col >= 11) return 1
  if (row <= 0 || row >= 13) return 1
  // 滑道：中间区域斜线
  if (Math.abs(col - row) <= 1 && col >= 2 && col <= 9) return 4
  return 0 // 默认雪坡
}

// 各类型颜色配置
const TILE_COLORS: Record<number, { top: string; left: string; right: string }> = {
  0: { top: '#ddeeff', left: '#aaccee', right: '#99bbdd' },   // 雪坡
  1: { top: '#2d5a27', left: '#1a3a17', right: '#153010' },   // 树木
  2: { top: '#eef4ff', left: '#ccddef', right: '#bbccde' },   // 山顶
  3: { top: '#ffcc44', left: '#cc9922', right: '#aa7711' },   // 缆车站
  4: { top: '#c8e6ff', left: '#90bfe0', right: '#70a0cc' },   // 滑道
}

function buildTiles() {
  const tiles: Array<{
    col: number; row: number; elev: number; type: number
    sx: number; sy: number
  }> = []

  for (let row = 0; row < ROWS; row++) {
    for (let col = 0; col < COLS; col++) {
      const elev = getElevation(col, row)
      const type = getTileType(col, row)
      const [sx, sy] = toScreen(col, row, elev)
      tiles.push({ col, row, elev, type, sx, sy })
    }
  }
  // 按绘制顺序排序（远到近）
  tiles.sort((a, b) => (a.col + a.row) - (b.col + b.row))
  return tiles
}

// 将 positionX/Y (0-1 归一化) 映射到等角坐标
function alertToScreen(px: number, py: number): [number, number] {
  const col = Math.round(px * (COLS - 1))
  const row = Math.round(py * (ROWS - 1))
  const elev = getElevation(col, row)
  const [sx, sy] = toScreen(col, row, elev)
  return [sx, sy]
}

// 用 ECharts custom series 的 renderItem 绘制等角菱形
function buildOption(alertPts: AlertPoint[] = []): echarts.EChartsOption {
  const tiles = buildTiles()

  // 计算画布范围
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
  tiles.forEach(t => {
    minX = Math.min(minX, t.sx - TILE_W / 2)
    maxX = Math.max(maxX, t.sx + TILE_W / 2)
    minY = Math.min(minY, t.sy - TILE_H / 2 - t.elev * 20)
    maxY = Math.max(maxY, t.sy + TILE_H / 2)
  })

  const padding = 40
  const viewW = maxX - minX + padding * 2
  const viewH = maxY - minY + padding * 2
  const offsetX = -minX + padding
  const offsetY = -minY + padding

  const data = tiles.map(t => ({
    value: [t.sx + offsetX, t.sy + offsetY, t.elev, t.type, t.col, t.row],
    col: t.col,
    row: t.row,
  }))

  return {
    backgroundColor: 'transparent',
    grid: { left: 0, right: 0, top: 0, bottom: 0, containLabel: false },
    xAxis: {
      type: 'value',
      min: 0, max: viewW,
      show: false,
    },
    yAxis: {
      type: 'value',
      min: 0, max: viewH,
      inverse: true,
      show: false,
    },
    series: [
      {
        type: 'custom',
        coordinateSystem: 'cartesian2d',
        data,
        renderItem(_params, api) {
          const sx = api.value(0) as number
          const sy = api.value(1) as number
          const elev = api.value(2) as number
          const type = api.value(3) as number
          const colors = TILE_COLORS[type] ?? TILE_COLORS[0]

          const hw = TILE_W / 2
          const hh = TILE_H / 2
          const ew = elev * 20  // 立面高度

          // 顶面菱形 4 点
          const top = api.coord([sx, sy - hh - ew])
          const right = api.coord([sx + hw, sy - ew])
          const bottom = api.coord([sx, sy + hh - ew])
          const left = api.coord([sx - hw, sy - ew])

          // 左侧面（梯形）
          const leftFaceBottomL = api.coord([sx - hw, sy - ew + ew + hh])
          const leftFaceBottomR = api.coord([sx, sy - ew + ew + hh])

          // 右侧面（梯形）
          const rightFaceBottomL = api.coord([sx, sy - ew + ew + hh])
          const rightFaceBottomR = api.coord([sx + hw, sy - ew + ew + hh])

          const children: echarts.CustomSeriesRenderItemReturn[] = []

          // 只在有高度时绘制立面
          if (ew > 0) {
            // 左立面
            children.push({
              type: 'polygon',
              shape: {
                points: [left, bottom, leftFaceBottomR, leftFaceBottomL],
              },
              style: { fill: colors.left, stroke: 'rgba(255,255,255,0.08)', lineWidth: 0.5 },
              z2: 10,
            } as any)
            // 右立面
            children.push({
              type: 'polygon',
              shape: {
                points: [bottom, right, rightFaceBottomR, rightFaceBottomL],
              },
              style: { fill: colors.right, stroke: 'rgba(255,255,255,0.08)', lineWidth: 0.5 },
              z2: 10,
            } as any)
          }

          // 顶面
          children.push({
            type: 'polygon',
            shape: { points: [top, right, bottom, left] },
            style: {
              fill: colors.top,
              stroke: 'rgba(255,255,255,0.15)',
              lineWidth: 0.5,
            },
            z2: 20,
          } as any)

          // 树木标记
          if (type === 1) {
            const cx = api.coord([sx, sy - hh - ew - 10])
            children.push({
              type: 'path',
              shape: {
                pathData: 'M0,-12 L6,0 L3,0 L3,6 L-3,6 L-3,0 L-6,0 Z',
                x: cx[0],
                y: cx[1],
                width: 12, height: 18,
                layout: 'cover',
              },
              style: { fill: '#3a7a30', stroke: 'none' },
              z2: 30,
            } as any)
          }

          // 缆车站标记
          if (type === 3) {
            const cx = api.coord([sx, sy - hh - ew - 8])
            children.push({
              type: 'rect',
              shape: { x: cx[0] - 8, y: cx[1] - 6, width: 16, height: 12, r: 2 },
              style: { fill: '#ff9800', stroke: '#fff', lineWidth: 1 },
              z2: 30,
            } as any)
            children.push({
              type: 'text',
              style: {
                x: cx[0], y: cx[1],
                text: 'S',
                fill: '#fff',
                fontSize: 9,
                fontWeight: 'bold',
                textAlign: 'center',
                textVerticalAlign: 'middle',
              },
              z2: 31,
            } as any)
          }

          return {
            type: 'group',
            children,
          } as echarts.CustomSeriesRenderItemReturn
        },
      },
      // 预警点散点系列
      {
        type: 'scatter',
        coordinateSystem: 'cartesian2d',
        data: alertPts.map(a => {
          const [sx, sy] = alertToScreen(
            Math.min(1, Math.max(0, a.positionX / 100)),
            Math.min(1, Math.max(0, a.positionY / 100)),
          )
          return {
            value: [sx + offsetX, sy + offsetY],
            alertType: a.alertType,
            severity: a.severity,
          }
        }),
        symbolSize: 14,
        itemStyle: {
          color: (p: any) => p.data.severity === 'DANGER' ? '#f44336' : '#ff9800',
          borderColor: '#fff',
          borderWidth: 1.5,
          opacity: 0.9,
        },
        label: {
          show: true,
          formatter: (p: any) => p.data.alertType?.charAt(0) ?? '!',
          color: '#fff',
          fontSize: 8,
          fontWeight: 'bold',
        },
        zlevel: 1,
        z: 50,
      },
    ],
  }
}

onMounted(() => {
  if (!chartEl.value) return
  chart = echarts.init(chartEl.value, undefined, { renderer: 'canvas' })
  chart.setOption(buildOption(props.alertPoints))

  const ro = new ResizeObserver(() => chart?.resize())
  ro.observe(chartEl.value)
  ;(chartEl.value as any).__ro = ro
})

watch(() => props.alertPoints, (pts) => {
  chart?.setOption(buildOption(pts), { notMerge: false })
}, { deep: true })

onUnmounted(() => {
  if (chartEl.value) {
    const ro = (chartEl.value as any).__ro as ResizeObserver | undefined
    ro?.disconnect()
  }
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.ski-map-chart {
  width: 100%;
  height: 100%;
}
</style>
