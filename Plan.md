# 滑雪场 AI 安全监控系统 — 开发文档 (MVP)

> 版本：v0.1.0 | 更新日期：2026-03-21 | 状态：规划中

---

## 一、项目背景

### 1.1 业务背景

随着滑雪运动的普及，滑雪场的安全管理需求日益突出。传统的人工巡检和事后回放存在以下痛点：

- **发现滞后**：事故发生后才能通过监控回放发现问题，实时性差
- **人工成本高**：需要专职人员长时间盯着监控画面，效率低且容易疲劳
- **事后定责难**：缺乏客观的行为轨迹数据支撑，责任判定主观性强
- **规则执行难**：逆行、危险驾驶等违规行为难以实时预警和记录

### 1.2 核心目标

本系统旨在构建一套**实时监控 + AI 行为识别 + 智能定责建议**的滑雪场安全监控平台，实现：

1. 滑雪者轨迹实时提取与可视化
2. 危险行为（逆行、失控碰撞等）的自动检测与预警
3. 基于知识库的智能事故定责建议生成
4. 2.5D 雪场监控大屏，管理人员实时掌握全场态势

### 1.3 MVP 范围界定

| 功能 | MVP 是否包含 |
|------|:-----------:|
| 视频上传与播放 | ✅ |
| YOLO 轨迹提取 | ✅ |
| 危险行为预警 | ✅ |
| WebSocket 实时推送 | ✅ |
| 2.5D 雪场大屏 | ✅ |
| RAG 定责建议 | ✅ |
| 完整用户权限系统 | ❌ (简化角色判断) |
| 知识库管理界面 | ❌ (手动上传文档) |
| 微服务注册中心 | ❌ (Docker Compose 同机部署) |

---

## 二、技术选型

### 2.1 技术栈总览

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Vue 3)                         │
│           雪场监控大屏 · 后台管理 · 用户界面                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│                     Java 后端 (Spring Boot 3)                 │
│         用户认证 · 视频管理 · 任务调度 · WebSocket           │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST / 任务下发
┌──────────────────────────▼──────────────────────────────────┐
│                   Python AI 引擎 (FastAPI)                    │
│              YOLO11 检测 · 轨迹提取 · LlamaIndex            │
└──────────────────────────┬──────────────────────────────────┘
                           │ 回调通知
┌──────────────────────────▼──────────────────────────────────┐
│                     Redis (消息队列 + 缓存)                   │
│                 任务缓冲 · 状态同步 · 发布订阅                │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 详细选型说明

#### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | 3.4+ | 核心框架，Composition API |
| Vite | 5.x | 构建工具，热更新快 |
| ECharts | 5.5+ | 2.5D 地图可视化 |
| Pinia | 2.x | 状态管理 |
| Axios | 1.6+ | HTTP 请求 |
| websocket | — | WebSocket 客户端 |

#### 主后端 (Java)

| 技术 | 版本 | 用途 |
|------|------|------|
| Spring Boot | 3.2+ | 核心框架 |
| Spring WebSocket | — | 实时通信 |
| Spring Data JPA | — | ORM 持久层 |
| MySQL | 8.0+ | 关系数据库 |
| Redis | 7.x | 消息队列与缓存 |
| MyBatis-Plus | 3.5+ | 增强 ORM（可选） |

#### AI 引擎 (Python)

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.110+ | 异步 API 服务 |
| YOLO11 | ultralytics 8.x+ | 目标检测与跟踪 |
| LlamaIndex | 0.10+ | RAG 检索框架 |
| ChromaDB | 0.4+ | 向量数据库（轻量，pip 安装） |
| OpenAI API | — | LLM 调用（可切换 Claude/本地模型） |
| Redis | — | Python 端消费消息队列 |

#### 基础设施

| 技术 | 用途 |
|------|------|
| Docker + Docker Compose | 服务容器化与编排 |
| Git | 版本控制 |

### 2.3 向量数据库选型说明

本项目选用 **ChromaDB**，原因如下：

- **零配置**：内置 SQLite 后端，无需单独安装服务进程
- **轻量级**：`pip install chromadb` 即可，依赖极小
- **LlamaIndex 原生支持**：无缝集成，减少集成成本
- **适合 MVP**：初期数据量小，完全够用，后续可平滑迁移到 Qdrant/Milvus

```bash
# 安装命令
pip install chromadb
```

---

## 三、系统架构

### 3.1 整体架构图

```
                                    ┌─────────────────┐
                                    │   Vue 3 大屏     │
                                    │  (ECharts 2.5D)  │
                                    └────────▲─────────┘
                                             │ WebSocket
                                             │
┌──────────┐    HTTP    ┌────────────────────┼────────────────────┐
│  用户端   │ ────────▶ │                    │                     │
│ (上传视频)│            │        Java Spring Boot 3              │
└──────────┘            │   ┌─────────┐  ┌─────────────┐          │
                         │   │  用户   │  │  WebSocket  │          │
                         │   │  权限   │  │   Server    │          │
                         │   └────┬────┘  └──────┬──────┘          │
                         │        │              │                  │
                         │   ┌────▼────┐   ┌────▼────┐             │
                         │   │  视频   │   │  任务    │             │
                         │   │  管理   │   │  状态    │             │
                         │   └────┬────┘   └────┬────┘             │
                         └────────┼────────────┼──────────────────┘
                                  │            │
                            ┌─────▼────────────▼─────┐
                            │       Redis            │
                            │   (消息队列 + 缓存)     │
                            └─────┬────────────┬─────┘
                                  │            │
                    ┌─────────────▼──┐   ┌─────▼─────────────┐
                    │  任务下发队列   │   │   回调通知队列      │
                    │  video:tasks   │   │  ai:results        │
                    └────────┬───────┘   └─────┬─────────────┘
                             │                  │
┌────────────────────────────▼──────────────────▼──────────────────┐
│                         Python AI 引擎                              │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐   │
│  │   FastAPI    │  │  YOLO11     │  │  LlamaIndex + ChromaDB │   │
│  │  任务接收     │  │  轨迹提取     │  │  RAG 定责建议生成       │   │
│  └──────────────┘  └──────────────┘  └────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

### 3.2 核心数据流

```
用户上传视频
     │
     ▼
① Java：存储视频文件，记录任务 → Redis 任务队列
     │
     ▼
② Python：消费任务 → YOLO 检测 → 轨迹坐标提取
     │
     ▼
③ Python：轨迹坐标 → LlamaIndex 检索知识库 → LLM 生成定责建议
     │
     ▼
④ Python：回调 Java（写入 Redis 结果队列）
     │
     ▼
⑤ Java：消费结果 → WebSocket 推送 → Vue 大屏展示
```

---

## 四、各模块职责

### 4.1 前端模块 (Vue 3)

| 模块 | 职责 |
|------|------|
| **监控大屏** | 2.5D 雪场地图，实时显示滑雪者轨迹、预警信息 |
| **视频播放** | 视频上传、播放、回放 |
| **后台管理** | 用户管理、视频管理、预警记录查询 |
| **WebSocket 客户端** | 接收实时预警推送并展示 |

### 4.2 Java 后端模块 (Spring Boot)

| 模块 | 职责 |
|------|------|
| **UserController** | 用户注册、登录、权限验证 |
| **VideoController** | 视频上传、存储、元信息管理 |
| **TaskController** | 任务创建、查询、状态管理 |
| **WebSocketHandler** | WebSocket 连接管理、消息推送 |
| **RedisPublisher** | 将任务下发至 Redis 队列 |
| **RedisSubscriber** | 消费 AI 回调结果 |

**核心接口设计**：

```
POST   /api/video/upload          # 上传视频
GET    /api/video/{id}             # 获取视频信息
POST   /api/task/create            # 创建分析任务
GET    /api/task/{id}/status       # 查询任务状态
GET    /api/task/{id}/result       # 获取分析结果
WS     /ws/alerts                  # WebSocket 预警推送
```

### 4.3 Python AI 引擎模块 (FastAPI)

| 模块 | 职责 |
|------|------|
| **TaskAPI** | 接收 Java 下发的任务 |
| **YOLOProcessor** | YOLO11 模型加载、视频帧处理、轨迹提取 |
| **RAGEngine** | LlamaIndex 向量检索、Prompt 构建、LLM 调用 |
| **ResultCallback** | 将分析结果回调至 Java |

**核心接口设计**：

```
POST   /ai/task/receive           # 接收分析任务
POST   /ai/callback/result         # 回调分析结果（内部）
GET    /ai/health                  # 健康检查
```

### 4.4 危险行为检测规则

| 行为类型 | 检测逻辑 |
|----------|----------|
| **逆行** | 轨迹方向与滑道主流方向相反，持续超过 N 帧 |
| **超速** | 轨迹速度超过阈值（可通过轨迹位移计算） |
| **碰撞风险** | 两轨迹在短时间内的欧氏距离小于安全阈值 |
| **静止检测** | 轨迹点长时间无位移，可能发生摔伤 |

---

## 五、开发阶段计划

### 阶段一：基础设施搭建（预计 3-5 天）

**目标**：完成项目脚手架、Docker Compose 编排、数据库设计

**任务清单**：

- [ ] 搭建 Vue 3 + Vite 项目结构，配置 TypeScript
- [ ] 搭建 Spring Boot 3 项目结构，配置 MySQL + Redis 连接
- [ ] 搭建 Python FastAPI 项目结构，配置依赖（YOLO、LlamaIndex、ChromaDB）
- [ ] 编写 Docker Compose 配置文件，统一编排所有服务
- [ ] 设计并创建 MySQL 数据库表（用户表、视频表、任务表、预警记录表）
- [ ] 编写 README.md 和开发环境配置说明

**交付物**：

- 三个服务可独立启动，并通过 Docker Compose 一键启动
- 数据库表结构文档

---

### 阶段二：核心链路开发（预计 7-10 天）

**目标**：实现视频上传 → AI 分析 → 结果回调的完整链路

**任务清单**：

- [x] Java：实现视频文件上传接口（本地存储，MVP 阶段）
- [x] Java：实现 Redis 任务队列下发逻辑
- [x] Python：实现 FastAPI 任务接收接口
- [x] Python：集成 YOLO11，实现视频帧处理与轨迹提取
- [x] Python：实现轨迹数据回调 Java 接口
- [x] Java：实现 Redis 结果消费与 WebSocket 推送
- [x] 前端：实现 WebSocket 客户端，接收预警消息

**交付物**：

- 端到端可运行的视频分析流程
- WebSocket 实时推送验证

---

### 阶段三：AI 能力增强（预计 5-7 天）

**目标**：实现危险行为检测规则和 RAG 定责建议

**任务清单**：

- [x] 实现逆行检测算法
- [x] 实现碰撞风险检测算法
- [x] 实现超速检测算法
- [x] 准备知识库文档（滑雪场安全规范、事故案例等）
- [x] 集成 ChromaDB，向量化了知识库文档
- [x] 实现 LlamaIndex RAG 流程，生成定责建议
- [x] 完善预警推送内容（包含定责建议）

**交付物**：

- 危险行为实时预警功能
- 事故定责建议报告生成

---

### 阶段四：前端大屏开发（预计 5-7 天）

**目标**：完成 2.5D 雪场监控大屏和后台管理界面

**任务清单**：

- [ ] 设计 2.5D 雪场地图布局（使用 ECharts）
- [ ] 实现滑雪者轨迹实时绘制
- [ ] 实现预警信息弹窗与历史记录
- [ ] 实现视频播放与回放功能
- [ ] 实现后台管理界面（视频列表、预警记录）

**交付物**：

- 完整的监控大屏界面
- 后台管理界面

---

### 阶段五：测试与优化（预计 3-5 天）

**目标**：功能测试、性能优化、部署文档完善

**任务清单**：

- [ ] 编写单元测试（各模块核心逻辑）
- [ ] 编写集成测试（核心链路）
- [ ] 接口测试（见章节六）
- [ ] YOLO 模型推理性能优化（GPU 加速评估）
- [ ] 完善部署文档
- [ ] MVP 版本发布

---

## 六、接口测试

### 6.1 接口测试计划

#### Java 后端接口测试

| 接口 | 方法 | 测试用例 |
|------|------|----------|
| `/api/video/upload` | POST | 上传视频文件，验证返回视频 ID |
| `/api/video/{id}` | GET | 查询视频信息，验证返回正确元数据 |
| `/api/task/create` | POST | 创建任务，验证返回任务 ID |
| `/api/task/{id}/status` | GET | 查询任务状态，验证状态流转 |
| `/api/task/{id}/result` | GET | 查询任务结果，验证返回完整结果 |

**测试命令示例**（使用 curl）：

```bash
# 上传视频
curl -X POST http://localhost:8080/api/video/upload \
  -F "file=@/path/to/video.mp4"

# 创建分析任务
curl -X POST http://localhost:8080/api/task/create \
  -H "Content-Type: application/json" \
  -d '{"videoId": 1}'

# 查询任务状态
curl http://localhost:8080/api/task/1/status

# 查询任务结果
curl http://localhost:8080/api/task/1/result
```

#### Python AI 引擎接口测试

| 接口 | 方法 | 测试用例 |
|------|------|----------|
| `/ai/task/receive` | POST | 模拟任务下发，验证 YOLO 处理 |
| `/ai/health` | GET | 健康检查，验证服务存活 |

**测试命令示例**：

```bash
# 健康检查
curl http://localhost:8000/ai/health

# 模拟接收任务
curl -X POST http://localhost:8000/ai/task/receive \
  -H "Content-Type: application/json" \
  -d '{"taskId": "123", "videoUrl": "/videos/1.mp4"}'
```

#### WebSocket 接口测试

```bash
# 使用 websocat 测试 WebSocket 连接
websocat ws://localhost:8080/ws/alerts

# 连接后等待接收预警消息
```

### 6.2 接口测试报告模板

| 测试编号 | 接口 | 测试用例 | 预期结果 | 实际结果 | 状态 |
|----------|------|----------|----------|----------|------|
| TC-001 | `/api/video/upload` | 上传正常视频 | 返回视频 ID | — | 待测 |
| TC-002 | `/api/video/upload` | 上传非法格式 | 返回 400 错误 | — | 待测 |
| TC-003 | `/api/task/create` | 正常创建任务 | 返回任务 ID，状态为 PENDING | — | 待测 |
| TC-004 | `/api/task/create` | 视频不存在 | 返回 404 错误 | — | 待测 |
| ... | ... | ... | ... | ... | ... |

---

## 七、附录

### 7.1 数据库表设计（初稿）

```sql
-- 用户表
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'USER',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 视频表
CREATE TABLE videos (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    filepath VARCHAR(500) NOT NULL,
    duration INT,
    status VARCHAR(20) DEFAULT 'UPLOADED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 任务表
CREATE TABLE tasks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    video_id BIGINT NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',
    result TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(id)
);

-- 预警记录表
CREATE TABLE alerts (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_id BIGINT NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'WARNING',
    description TEXT,
    position_x FLOAT,
    position_y FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

### 7.2 环境变量配置

**Java (.env)**

```properties
SPRING_DATASOURCE_URL=jdbc:mysql://mysql:3306/ski_db
SPRING_DATASOURCE_USERNAME=root
SPRING_DATASOURCE_PASSWORD=your_password
REDIS_HOST=redis
REDIS_PORT=6379
VIDEO_STORAGE_PATH=/data/videos
```

**Python (.env)**

```properties
OPENAI_API_KEY=your_openai_api_key
CHROMA_DB_PATH=/data/chroma
REDIS_HOST=redis
REDIS_PORT=6379
YOLO_MODEL_PATH=/models/yolo11n.pt
```

### 7.3 参考资料

- [Vue 3 官方文档](https://vuejs.org/)
- [Spring Boot 3 官方文档](https://spring.io/projects/spring-boot)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Ultralytics YOLO11](https://docs.ultralytics.com/)
- [LlamaIndex 官方文档](https://docs.llamaindex.ai/)
- [ChromaDB 官方文档](https://docs.trychroma.com/)
- [ECharts 官方文档](https://echarts.apache.org/)

---

*文档版本：v0.1.0 | 如有更新请同步修改此文档*
