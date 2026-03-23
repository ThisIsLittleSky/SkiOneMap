# 危险行为检测算法说明

> 模块路径：`ai-engine/app/services/behavior_detector.py`

---

## 一、概述

危险行为检测模块在 YOLO11 完成轨迹提取后运行，对每条轨迹（或轨迹对）进行规则计算，输出结构化预警列表。当前实现四类检测：

| 行为类型 | 枚举值 | 严重程度 |
|----------|--------|---------|
| 逆行 | `WRONG_WAY` | WARNING |
| 超速 | `OVERSPEED` | WARNING |
| 碰撞风险 | `COLLISION_RISK` | DANGER |
| 静止/疑似摔倒 | `STILL_DETECTED` | DANGER |

---

## 二、输入数据结构

YOLO11 输出的轨迹数据格式（每条轨迹）：

```json
{
  "trackId": 1,
  "className": "person",
  "points": [
    { "frame": 0, "x": 320.5, "y": 100.2, "width": 45.0, "height": 80.0, "confidence": 0.92 },
    { "frame": 1, "x": 321.0, "y": 103.8, "width": 45.1, "height": 80.2, "confidence": 0.91 },
    ...
  ]
}
```

- `x`, `y`：目标质心在视频帧中的像素坐标
- `frame`：帧索引（从 0 开始）
- 坐标系：原点在左上角，**y 轴向下为正**（符合图像坐标系）

---

## 三、算法详解

### 3.1 逆行检测（WRONG_WAY）

**假设前提：** 摄像头俯视拍摄，滑雪者正常下滑方向为 **y 坐标递增**（从画面上方滑向下方）。

**检测逻辑：**

```
对相邻帧 i-1 → i：
  dy = points[i].y - points[i-1].y

若 dy < -MIN_DISPLACEMENT（即向上移动且位移足够大）→ 逆向帧计数 +1
否则 → 计数归零

当连续逆向帧数 >= WRONG_WAY_FRAMES → 触发预警，计数归零
```

**参数：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `WRONG_WAY_FRAMES` | 8 帧 | 连续逆向帧数阈值 |
| `WRONG_WAY_MIN_DISPLACEMENT` | 3.0 px | 每帧最小位移，过滤抖动 |

**触发后行为：** 记录触发帧编号和位置，计数归零以避免同一段逆行重复触发。

---

### 3.2 超速检测（OVERSPEED）

**核心指标：** 相邻帧像素位移 = 目标质心移动距离（px/帧），代理速度。

**检测逻辑：**

```
对相邻帧 i-1 → i：
  speed = sqrt((x[i]-x[i-1])² + (y[i]-y[i-1])²)

若 speed > SPEED_THRESHOLD → 超速帧计数 +1，记录峰值速度
否则：
  若已累计超速帧数 >= SPEED_FRAMES → 触发预警
  计数归零
```

**参数：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `SPEED_THRESHOLD` | 40.0 px/帧 | 速度上限（依视频分辨率调整） |
| `SPEED_FRAMES` | 5 帧 | 连续超速帧数才触发，过滤瞬时噪声 |

**注意：** px/帧 与实际物理速度的换算需结合摄像头焦距、安装高度和帧率，MVP 阶段使用像素位移作为相对速度代理指标。

---

### 3.3 碰撞风险检测（COLLISION_RISK）

**检测对象：** 所有轨迹两两配对（复杂度 O(N²)，N 为同帧轨迹数）。

**检测逻辑：**

```
构建索引：trackId → {frame: point}

对每对 (trackA, trackB)，取共同帧集合：
  d = sqrt((xA-xB)² + (yA-yB)²)

若 d < COLLISION_DIST_THRESHOLD → 接近帧计数 +1
否则：
  若已累计接近帧数 >= COLLISION_APPROACH_FRAMES → 触发预警
  计数归零

预警位置 = 两轨迹质心中点
```

**参数：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `COLLISION_DIST_THRESHOLD` | 60.0 px | 危险距离阈值 |
| `COLLISION_APPROACH_FRAMES` | 3 帧 | 连续接近帧数阈值 |

**严重程度设为 DANGER**，因碰撞风险可能造成直接伤害，需立即干预。

---

### 3.4 静止检测（STILL_DETECTED）

**检测目标：** 滑雪者在雪道上长时间静止不动，可能是摔倒、受伤或失去意识。

**检测逻辑：**

```
对相邻帧 i-1 → i：
  d = sqrt((x[i]-x[i-1])² + (y[i]-y[i-1])²)

若 d < STILL_DIST_THRESHOLD → 静止帧计数 +1，记录起始点
否则：
  若已累计静止帧数 >= STILL_FRAMES → 触发预警
  计数归零
```

**参数：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `STILL_DIST_THRESHOLD` | 2.0 px | 视为静止的最大位移 |
| `STILL_FRAMES` | 30 帧 | 连续静止帧数（约 1 秒 @ 30fps） |

**严重程度设为 DANGER**，触发后建议立即派遣救援人员。

---

## 四、输出数据结构

每条预警的格式：

```json
{
  "alertType": "WRONG_WAY",
  "severity": "WARNING",
  "trackId": 2,
  "frame": 145,
  "positionX": 312.5,
  "positionY": 88.0,
  "description": "轨迹 2 检测到逆行：连续 8 帧沿坡面向上行进，触发帧 145，位置 (312, 88)"
}
```

`detect_all()` 函数汇总所有检测结果，返回 `List[Dict]`，传入后续 RAG 引擎和结果回调。

---

## 五、调用链路

```
task_consumer._process_task()
  ├── YOLOProcessor.process_video()   → tracks: List[Dict]
  ├── behavior_detector.detect_all()  → alerts: List[Dict]
  ├── RAGEngine.generate_liability_suggestion()  （有预警时）
  └── ResultCallback.send_result()    → 写入 Redis ai:results 队列
```

---

## 六、参数调优建议

| 场景 | 建议调整 |
|------|---------|
| 摄像头分辨率高（4K） | 适当提高 `SPEED_THRESHOLD`、`COLLISION_DIST_THRESHOLD` |
| 摄像头分辨率低（720p） | 降低上述阈值 |
| 帧率高（60fps） | 增大 `WRONG_WAY_FRAMES`、`STILL_FRAMES`、`SPEED_FRAMES` |
| 雪道宽，人员稀疏 | 降低 `COLLISION_DIST_THRESHOLD` 减少误报 |
| 人员密集区 | 降低 `COLLISION_APPROACH_FRAMES` 提高灵敏度 |
