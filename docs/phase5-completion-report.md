# 阶段五：测试与优化 — 完成报告

> 版本：v0.5.0 | 完成日期：2026-03-22 | 状态：已完成

---

## 一、阶段目标回顾

| 任务 | 状态 |
|------|:----:|
| 编写单元测试（各模块核心逻辑） | ✅ |
| 编写集成测试（核心链路） | ✅ |
| 接口测试（Controller MockMvc） | ✅ |
| video stream 接口补充（Range 支持） | ✅ |
| 前端 ECharts 分包优化 | ✅ |
| MVP 版本发布准备文档 | ✅ |

---

## 二、新增/修改文件清单

```
backend/src/test/java/com/ski/monitor/
├── service/
│   ├── VideoServiceTest.java           # VideoService 单元测试（新增）
│   ├── TaskServiceTest.java            # TaskService 单元测试（新增）
│   └── RedisSubscriberServiceTest.java # Redis 消费 + WebSocket 推送测试（新增）
└── controller/
    ├── VideoControllerTest.java        # VideoController MockMvc 集成测试（新增）
    └── TaskControllerTest.java         # TaskController MockMvc 集成测试（新增）

backend/src/main/java/com/ski/monitor/controller/
├── VideoController.java                # 新增 /{id}/stream 视频流接口（修改）
└── RangeResource.java                  # HTTP Range 资源辅助类（新增）

ai-engine/
├── tests/
│   ├── test_behavior_detector.py       # 四类危险行为检测算法单元测试（新增）
│   └── test_rag_engine.py              # RAG fallback 定责建议单元测试（新增）
└── pytest.ini                          # pytest 配置文件（新增）

frontend/
└── vite.config.ts                      # 新增 manualChunks 分包配置（修改）
```

---

## 三、测试说明

### 3.1 Java 测试

#### 如何运行

```bash
cd backend
mvn test
```

#### VideoServiceTest（5 个用例）

| 测试方法 | 验证内容 |
|----------|---------|
| `uploadVideo_savesFileAndReturnsVideo` | 上传视频文件保存到磁盘并返回正确实体 |
| `uploadVideo_handlesFileWithoutExtension` | 无后缀文件名默认使用 `.mp4` |
| `getById_returnsVideo_whenExists` | 按 ID 查询存在的视频返回实体 |
| `getById_returnsNull_whenNotExists` | 按 ID 查询不存在时返回 null |
| `listAll_returnsAllVideos` | listAll 返回所有视频列表 |

#### TaskServiceTest（6 个用例）

| 测试方法 | 验证内容 |
|----------|---------|
| `createTask_dispatchesToRedisAndSaves` | 创建任务后推送到 Redis 队列，消息包含 taskId/videoId，视频状态变为 PROCESSING |
| `createTask_throwsWhenVideoNotFound` | 视频不存在时抛出 IllegalArgumentException |
| `updateStatus_changesTaskStatus` | 更新任务状态正确写入 |
| `updateStatus_returnsNull_whenTaskNotFound` | 任务不存在时返回 null |
| `updateResult_setsResultAndUpdatesVideoStatus` | 任务完成时视频状态变为 ANALYZED |
| `updateResult_setsVideoToFailed_whenTaskFailed` | 任务失败时视频状态变为 FAILED |

#### RedisSubscriberServiceTest（6 个用例）

| 测试方法 | 验证内容 |
|----------|---------|
| `consumeResults_doesNothing_whenQueueEmpty` | 队列为空时无副作用 |
| `consumeResults_handlesCompletedTask_savesAlertsAndBroadcasts` | COMPLETED 消息：保存 2 条 Alert，广播一次 WS |
| `consumeResults_handlesFailedTask_broadcastsAndUpdates` | FAILED 消息：更新任务状态并广播 |
| `consumeResults_handlesProcessingStatus_updatesTaskOnly` | PROCESSING 消息：只更新状态 |
| `consumeResults_handlesCompletedWithNoAlerts` | 无 alerts 数组时不调用 alertRepository |
| `consumeResults_handlesMalformedJson_doesNotThrow` | 非法 JSON 消息被 catch 吞掉，不抛出异常 |

#### VideoControllerTest（5 个用例）

| 测试方法 | HTTP 验证 |
|----------|---------|
| `upload_returnsVideoId_onSuccess` | POST /upload → 200, `{id, filename, status}` |
| `upload_returns500_whenIOException` | IOException → 500, `{error}` |
| `getVideo_returnsVideo_whenExists` | GET /{id} → 200, 视频 JSON |
| `getVideo_returns404_whenNotFound` | GET /{id} 不存在 → 404 |
| `listAll_returnsVideoList` | GET /list → 200, 数组长度=2 |

#### TaskControllerTest（8 个用例）

| 测试方法 | HTTP 验证 |
|----------|---------|
| `createTask_returnsTaskId_onSuccess` | POST /create → 200, `{taskId, status}` |
| `createTask_returns400_whenVideoIdMissing` | 缺 videoId → 400 |
| `createTask_returns404_whenVideoNotFound` | 视频不存在 → 404 |
| `getStatus_returnsTaskStatus` | GET /{id}/status → 200 |
| `getStatus_returns404_whenNotFound` | 任务不存在 → 404 |
| `getResult_returnsResult_whenCompleted` | GET /{id}/result → 200 |
| `getTracks_returnsTracksAndAlerts_whenCompleted` | GET /{id}/tracks → trackCount, liabilitySuggestion, alerts |
| `getTracks_returnsPendingStatus_whenNotCompleted` | 未完成任务 → status=PROCESSING |
| `listTasks_returnsAllTasks` | GET /list → 200, 数组长度=2 |

---

### 3.2 Python 测试

#### 如何运行

```bash
cd ai-engine
# 需要先激活环境（conda 或 venv）
pytest
# 或指定详细输出
pytest -v
```

> **注意**：Python 测试无需启动任何外部服务（Redis/MySQL/YOLO），所有用例只测试纯逻辑。

#### test_behavior_detector.py（21 个用例）

| 类 | 测试内容 |
|----|---------|
| `TestDetectWrongWay`（6个） | 正常下滑无预警；逆行帧数达标触发；帧数不足不触发；位移过小不触发；描述包含轨迹ID；单点轨迹安全 |
| `TestDetectOverspeed`（5个） | 正常速度无预警；超速帧数达标触发；帧数不足不触发；末尾超速段也触发；描述包含速度信息 |
| `TestDetectCollisionRisk`（5个） | 单轨迹无预警；轨迹相距很远不触发；距离够近帧数达标触发；帧数不足不触发；多轨迹对只有近距离对触发 |
| `TestDetectStill`（5个） | 移动中无预警；静止帧数达标触发；帧数不足不触发；末尾静止段触发；描述包含轨迹ID |
| `TestDetectAll`（4个） | 正常轨迹无预警；综合多类型预警合并；单点轨迹跳过；碰撞风险被检测 |

#### test_rag_engine.py（11 个用例）

| 类 | 测试内容 |
|----|---------|
| `TestFallbackSuggestion`（8个） | 空预警返回无需定责；四类预警各有对应规则文本；多预警全部出现；返回值是非空字符串；未知类型不崩溃 |
| `TestGenerateLiabilitySuggestion`（3个） | 无 API key 走 fallback；占位符 key 走 fallback；空预警返回无需定责 |
| `TestBuildPrompt`（3个） | prompt 包含预警类型和描述；包含轨迹摘要和位移；内容为中文 |

---

## 四、新增接口：视频流播放

### `GET /api/video/{id}/stream`

支持 HTTP Range 请求，使浏览器原生 `<video>` 标签能够：
- 直接播放视频（无需下载完整文件）
- 拖拽进度条跳转（通过 Range 字节寻址）

**响应示例（完整请求）**：
```
HTTP/1.1 200 OK
Content-Type: video/mp4
Content-Length: 52428800
Accept-Ranges: bytes
```

**响应示例（Range 请求）**：
```
HTTP/1.1 206 Partial Content
Content-Type: video/mp4
Content-Range: bytes 0-1048575/52428800
Content-Length: 1048576
Accept-Ranges: bytes
```

实现类：
- `VideoController.streamVideo()` — 解析 Range 头，返回对应字节段
- `RangeResource` — 继承 Spring `AbstractResource`，从文件指定偏移量读取有限字节

---

## 五、前端构建优化

### ECharts 分包结果对比

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| DashboardView chunk | 1,040 KB | **5.24 KB** |
| ECharts chunk | 混入 DashboardView | 独立 1,035 KB（缓存复用） |
| 首屏 JS（不含 ECharts） | 合并 1040 KB | **约 115 KB** |

**优化原理**：将 ECharts 分离为独立 chunk，浏览器会将其单独缓存。用户首次访问后，后续刷新或路由跳转不再重新下载 ECharts，有效减少重复传输。

**配置**（`vite.config.ts`）：
```typescript
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        echarts: ['echarts'],
        vue: ['vue', 'vue-router', 'pinia'],
        axios: ['axios'],
      }
    }
  }
}
```

---

## 六、接口测试命令（手动执行）

以下命令可在服务全部启动后（`docker-compose up`）使用 curl 验证核心链路：

```bash
# 1. 健康检查
curl http://localhost:8000/ai/health

# 2. 上传视频
curl -X POST http://localhost:8080/api/video/upload \
  -F "file=@/path/to/ski.mp4"
# 预期: {"id":1,"filename":"ski.mp4","status":"UPLOADED"}

# 3. 创建分析任务
curl -X POST http://localhost:8080/api/task/create \
  -H "Content-Type: application/json" \
  -d '{"videoId": 1}'
# 预期: {"taskId":1,"status":"PENDING"}

# 4. 查询任务状态
curl http://localhost:8080/api/task/1/status
# 预期: {"taskId":1,"status":"PROCESSING"} 或 "COMPLETED"

# 5. 查询任务结果
curl http://localhost:8080/api/task/1/result

# 6. 查询轨迹 + 预警详情
curl http://localhost:8080/api/task/1/tracks

# 7. 视频流播放（支持 Range）
curl -H "Range: bytes=0-1048575" \
  http://localhost:8080/api/video/1/stream -I
# 预期: HTTP/1.1 206 Partial Content
```

---

## 七、MVP 版本状态

| 模块 | 状态 | 备注 |
|------|:----:|------|
| 视频上传 | ✅ | 本地存储 |
| Redis 任务队列 | ✅ | |
| YOLO11 轨迹提取 | ✅ | |
| 危险行为检测 | ✅ | 逆行/超速/碰撞/静止 |
| RAG 定责建议 | ✅ | 有 API Key 走 LLM，否则规则 fallback |
| WebSocket 实时推送 | ✅ | |
| 2.5D 监控大屏 | ✅ | ECharts 等角投影 |
| 视频播放（含 Range） | ✅ | |
| 后台管理界面 | ✅ | |
| 单元测试 | ✅ | Java 25个 + Python 32个 |
| Docker Compose 部署 | ✅ | 已有 |
