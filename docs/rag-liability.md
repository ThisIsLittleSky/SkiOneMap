# RAG 定责建议流程说明

> 模块路径：`ai-engine/app/services/rag_engine.py`
> 知识库路径：`ai-engine/data/knowledge/`

---

## 一、概述

RAG（Retrieval-Augmented Generation）定责建议引擎在检测到危险行为后触发，通过向量检索匹配相关安全规范和历史案例，结合 LLM 生成结构化的定责分析报告。

**技术栈：**

| 组件 | 选型 | 说明 |
|------|------|------|
| 向量数据库 | ChromaDB | 本地持久化，无需独立服务 |
| 向量化模型 | text-embedding-3-small | OpenAI 嵌入模型 |
| 检索框架 | LlamaIndex 0.10+ | 管理文档加载、分块、索引、查询 |
| 生成模型 | gpt-4o-mini | 低成本、响应快，适合 MVP |
| 兜底策略 | 规则引擎 | 无 API Key 或 LLM 不可用时自动降级 |

---

## 二、知识库文档

知识库存放于 `ai-engine/data/knowledge/`，当前包含两个文档：

| 文件 | 内容 |
|------|------|
| `ski_safety_rules.md` | 滑雪场安全规范（通行规则、速度限制、违规分级、定责原则、救援流程） |
| `accident_cases.md` | 历史事故案例库（逆行、超速、碰撞、摔倒等典型案例及定责结论） |

后续可直接向 `data/knowledge/` 目录添加 `.md`、`.txt`、`.pdf` 文件扩充知识库，下次触发分析时 LlamaIndex 会自动重新向量化（ChromaDB 集合为空时重建）。

---

## 三、完整流程

```
危险行为检测结果 (alerts)
         │
         ▼
① 检查 OPENAI_API_KEY 是否有效
         │
    无效 ──→ 规则引擎兜底建议
         │
    有效 ▼
② RAGEngine._init()
   └── _build_index()
       ├── 读取 data/knowledge/ 下所有文档
       ├── LlamaIndex SimpleDirectoryReader 加载 & 分块
       ├── text-embedding-3-small 向量化
       └── 写入 ChromaDB（已有数据则跳过，直接加载）
         │
         ▼
③ 构建查询 Prompt
   ├── 列举所有检测到的危险行为（类型、严重程度、位置、描述）
   └── 附上轨迹概要（帧数、总位移、目标类别）
         │
         ▼
④ LlamaIndex VectorStoreIndex.as_query_engine()
   ├── similarity_top_k=4（检索最相关的 4 个文本块）
   ├── 向量化查询 Prompt
   ├── 在 ChromaDB 中检索相似文本块（安全规范条文 + 案例片段）
   └── 将检索到的上下文 + Prompt 拼接后发送给 gpt-4o-mini
         │
         ▼
⑤ LLM 生成定责建议文本
   ├── 各当事方违规行为与责任比例
   ├── 雪场管理方连带责任判断
   ├── 建议处理措施
   └── 后续风险防范建议
         │
         ▼
⑥ 结果写入 ResultCallback → Redis ai:results 队列
   └── Java 端解析后存入 tasks.result，通过 WebSocket 推送至前端
```

---

## 四、Prompt 构造示例

以检测到"逆行 + 碰撞风险"为例，实际发送给 LLM 的 Prompt：

```
以下是一起滑雪场视频监控分析结果，请根据滑雪场安全规范和历史事故案例，
对检测到的危险行为进行定责分析，给出责任方判断和建议处理措施。

【检测到的危险行为】
- 行为类型：WRONG_WAY，严重程度：WARNING，涉及轨迹ID：2，
  描述：轨迹 2 检测到逆行：连续 8 帧沿坡面向上行进，触发帧 145，位置 (312, 88)
- 行为类型：COLLISION_RISK，严重程度：DANGER，涉及轨迹ID：1，
  描述：轨迹 1 与轨迹 2 检测到碰撞风险：连续 4 帧距离低于 60px，触发帧 143，位置 (308, 92)

【轨迹概要】
轨迹ID 1：共 629 帧，总位移 8420.3px，类别 person
轨迹ID 2：共 512 帧，总位移 3201.7px，类别 person

请依据安全规范和案例库，分析：
1. 各轨迹（当事人）的违规行为及责任比例
2. 雪场管理方是否存在连带责任
3. 建议的处理措施（警告/责令离场/追责赔偿）
4. 后续风险防范建议
请以中文回答，结构清晰。
```

LlamaIndex 会在此 Prompt 基础上，自动前置从 ChromaDB 检索到的相关规范条文和案例片段作为上下文（Context），再一并发送给 LLM。

---

## 五、兜底规则引擎

当以下任一条件成立时，自动使用规则引擎代替 LLM：

- `OPENAI_API_KEY` 未配置或为默认占位值
- ChromaDB 索引构建失败（文档缺失、网络异常）
- LLM 调用抛出异常

规则引擎按预警类型输出固定模板建议：

| alertType | 建议模板 |
|-----------|---------|
| `WRONG_WAY` | 逆行方承担主要责任（70%~100%），建议责令离场并记录在案 |
| `OVERSPEED` | 超速方承担主要责任（60%~80%），建议当场警告并限速提醒 |
| `COLLISION_RISK` | 后方/超越方责任 ≥ 80%，建议立即调度巡逻人员处置 |
| `STILL_DETECTED` | 建议立即派遣救援人员，目标响应时间 ≤ 5 分钟 |

---

## 六、ChromaDB 索引管理

```
ai-engine/data/chroma/          ← 持久化目录（由 CHROMA_DB_PATH 配置）
  └── ski_knowledge/            ← ChromaDB 集合
      ├── chroma.sqlite3        ← 元数据
      └── ...                   ← 向量数据文件
```

**首次运行：** 集合为空，自动读取 `data/knowledge/` 所有文档，分块向量化后写入。

**后续运行：** 集合已有数据，直接加载索引，跳过向量化步骤，启动更快。

**更新知识库：** 删除 `data/chroma/` 目录后重启 AI 引擎，即可触发重新向量化。

---

## 七、环境变量配置

```properties
# ai-engine/.env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx   # 必填，留空则降级为规则引擎
CHROMA_DB_PATH=data/chroma           # ChromaDB 持久化路径
```

---

## 八、调用链路

```
task_consumer._process_task()
  ├── behavior_detector.detect_all()  → alerts (有预警才继续)
  └── RAGEngine.generate_liability_suggestion(alerts, tracks)
      ├── [有 Key] _init() → _build_index() → query_engine.query()
      └── [无 Key] _fallback_suggestion()
```

最终结果通过 `ResultCallback.send_result()` 的 `liabilitySuggestion` 字段返回，经 Redis → Java → WebSocket 推送到前端预警记录页面展示。
