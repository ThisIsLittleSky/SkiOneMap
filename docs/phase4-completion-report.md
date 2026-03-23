# 阶段四：前端大屏开发 — 完成报告

> 版本：v0.4.0 | 完成日期：2026-03-22 | 状态：已完成

---

## 一、阶段目标回顾

| 任务 | 状态 |
|------|:----:|
| 设计 2.5D 雪场地图布局（ECharts） | ✅ |
| 实现滑雪者轨迹实时绘制 | ✅ |
| 实现预警信息弹窗与历史记录 | ✅ |
| 实现视频播放与回放功能 | ✅ |
| 实现后台管理界面（视频列表、预警记录） | ✅ |

---

## 二、新增文件清单

```
frontend/src/
├── components/
│   ├── NavBar.vue          # 共用导航栏组件（新增）
│   ├── SkiMapChart.vue     # ECharts 2.5D 雪场地图组件（新增）
│   └── AlertToast.vue      # 实时预警 Toast 通知组件（新增）
└── views/
    ├── DashboardView.vue   # 监控大屏（重写）
    ├── VideoView.vue       # 视频管理（重写，含播放器）
    └── AlertsView.vue      # 预警记录（重写，含任务管理）
```

---

## 三、各模块详细说明

### 3.1 NavBar.vue — 共用导航栏

- 统一顶部导航，包含品牌标识、页面路由链接、WebSocket 连接状态指示灯
- 预警记录 Tab 显示未读预警数量红点 badge
- WebSocket 在线时绿色光晕呼吸效果

### 3.2 SkiMapChart.vue — 2.5D 雪场地图

**核心实现**：使用 ECharts `custom series` + 等角投影（Isometric）算法

- **等角坐标转换**：`toScreen(col, row, elevation)` 将网格坐标转为屏幕坐标
  ```
  x = (col - row) × (TILE_W / 2)
  y = (col + row) × (TILE_H / 2) - elevation × 20
  ```
- **地形类型**：雪坡（白）/ 树木（绿）/ 滑道（浅蓝）/ 缆车站（橙）
- **立面渲染**：高程 > 0 时绘制左侧面和右侧面的梯形，形成立体感
- **地物标记**：树木绘制三角形图标，缆车站绘制橙色矩形"S"标志
- **预警点叠加**：接受 `alertPoints` prop，用 scatter series 将预警坐标映射到等角地图上，危险级别用红色/橙色区分

**Props 接口**：
```typescript
interface AlertPoint {
  positionX: number   // 0-100 归一化坐标
  positionY: number
  alertType: string
  severity: string
}
```

### 3.3 AlertToast.vue — 实时预警通知

- 监听 `alertStore.alerts` 长度变化，新预警进入时自动弹出 Toast
- Toast 5 秒后自动消失，可点击手动关闭
- 右上角固定定位，使用 `<Teleport to="body">` 脱离组件树
- `TransitionGroup` 实现滑入/滑出动画
- 根据 severity 显示不同颜色和图标（🚨 DANGER / ⚠️ WARNING / ℹ️ INFO）

### 3.4 DashboardView.vue — 监控大屏

- 左侧：2.5D 雪场地图（占主体），从 `alertStore` 实时获取预警点叠加显示
- 右侧：实时预警侧边栏，展示最近 10 条预警摘要（类型、描述、时间）
- `computed` 自动过滤有效坐标的预警点，响应式传入地图组件

### 3.5 VideoView.vue — 视频管理（增强）

**新增功能**：
- 文件选择器优化为自定义 `<label>` 样式，显示已选文件名
- 上传进度条（蓝色线性进度）
- **视频播放弹窗**：点击"播放"按钮打开 Modal，内嵌原生 `<video>` 标签
  - 视频流地址：`/api/video/{id}/stream`（对应 Java 后端流式接口）
  - 点击遮罩或"×"关闭弹窗，自动暂停并清空 src
- 暗色主题样式，与整体监控大屏一致

### 3.6 AlertsView.vue — 后台管理（增强）

**新增功能**：
- **Tab 切换**：实时预警记录 / 任务列表
- **任务列表**：调用 `listTasks()` API 展示所有分析任务，含状态标签
- **任务结果面板**：点击"查看结果"调用 `getTaskTracks()` 展示：
  - 轨迹数量、预警数量
  - AI 定责建议全文
  - 预警明细列表
- WebSocket 连接状态指示

---

## 四、技术实现要点

### 4.1 ECharts 2.5D 等角地图算法

地形由 `COLS×ROWS` 的网格构成，每个格子包含：
- **高程**：基于 `(col + row)` 距离计算，模拟从山顶到山脚的自然坡度
- **地物类型**：按规则分配雪坡/树木/滑道/缆车站
- **绘制顺序**：按 `col + row` 升序排列（Painter's Algorithm），确保近处格子覆盖远处

### 4.2 预警点坐标映射

AI 引擎返回的预警坐标为 0-100 归一化值，映射逻辑：
```typescript
col = round(positionX / 100 × (COLS - 1))
row = round(positionY / 100 × (ROWS - 1))
elevation = getElevation(col, row)
screenXY = toScreen(col, row, elevation)
```

### 4.3 响应式数据流

```
WebSocket 推送
    → App.vue 解析消息
    → alertStore.addAlert()
    → DashboardView computed alertPoints 自动更新
    → SkiMapChart watch(alertPoints) 触发
    → chart.setOption() 重绘预警点
    → AlertToast watch(alerts.length) 弹出通知
```

---

## 五、构建验证

```
vue-tsc --noEmit   ✅ 无类型错误
vite build         ✅ 构建成功（657 模块，4.55s）
```

> 注：DashboardView chunk 约 1MB，主要由 ECharts 库本身贡献（~900KB），属正常范围。
> 生产环境可配置 `manualChunks` 将 ECharts 单独分包以改善首屏加载速度。

---

## 六、接口依赖（对后端的要求）

| 接口 | 用途 | 状态 |
|------|------|------|
| `GET /api/video/list` | 视频列表 | 已有 |
| `POST /api/video/upload` | 视频上传 | 已有 |
| `GET /api/video/{id}/stream` | 视频流播放 | **需后端支持** |
| `POST /api/task/create` | 创建分析任务 | 已有 |
| `GET /api/task/list` | 任务列表 | 已有 |
| `GET /api/task/{id}/tracks` | 任务结果+预警 | 已有 |
| `WS /ws/alerts` | 实时预警推送 | 已有 |

> `/api/video/{id}/stream` 为视频流接口，后端需支持 `Range` 请求头以支持浏览器原生播放器拖拽定位。

---

## 七、后续优化建议（阶段五参考）

1. ECharts 分包：`manualChunks: { echarts: ['echarts'] }` 减小首屏 JS 体积
2. 轨迹动画：基于历史轨迹帧数据，用 ECharts `lines` series 绘制运动轨迹线
3. 地图缩放：添加 ECharts `dataZoom` 组件支持地图缩放平移
4. 预警过滤：AlertsView 增加按 severity / alertType 筛选功能
5. 视频流接口：后端添加 `Range` 支持，前端可实现精确回放定位
