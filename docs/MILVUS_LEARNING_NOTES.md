# Milvus 向量数据库学习笔记与项目实践指南

## 1. 简介与核心概念

### 1.1 什么是 Milvus？
Milvus 是一个高度可扩展的开源向量数据库，专门用于存储、索引和管理由深度神经网络（DNN）和其他机器学习模型生成的海量 embedding 向量。它在处理非结构化数据（如图像、视频、音频、自然语言文本）方面具有独特优势。

在我们的项目“基于双引擎架构与多模态大模型的工业视觉推训与分析平台”中，Milvus 扮演着**跨模态自然语言检索中枢**的角色。

### 1.2 核心概念
*   **Collection（集合）：** 类似于关系型数据库中的表（Table）。
*   **Entity（实体）：** 集合中的一条记录，相当于关系型数据库中的行（Row）。
*   **Field（字段）：** 实体中的属性，包括标量字段（如 ID、字符串、整数等）和向量字段（如 FloatVector）。
*   **Partition（分区）：** 集合可以分为多个分区，用于加速查询。
*   **Index（索引）：** 加速向量相似度搜索的结构。常见索引类型包括 `IVF_FLAT`、`HNSW` 等。
*   **Metric Type（距离度量）：** 计算向量相似度的方法，如欧氏距离（`L2`）、内积（`IP`）或余弦相似度（`COSINE`）。

## 2. 为什么项目需要 Milvus？

结合项目需求：“搭建自适应视频流处理与自然语言事件检索中枢”，Milvus 的作用是：
1.  **存储多模态结构化数据：** 将视觉模型（大模型/CLIP）提取的视频片段/图片特征向量（如 512 维或 768 维），以及截取视频元数据（时间戳、设备号、事件描述等）存入数据库。
2.  **支持自然语言查询：** 当用户输入“检索特定时间与人员的具体行为记录”时，先由文本大模型（如 DeepSeek）将其转化为文本向量，再到 Milvus 中进行相似度检索。
3.  **高并发与大规模：** 满足 24 小时视频流产生的海量特征的毫秒级检索需求。

## 3. Milvus 架构与部署基础

*   Milvus 采用云原生架构，主要包含：接入层（Proxy）、协调服务层（Coordinator Service）、工作节点层（Worker Node）和存储层（Storage）。
*   **本地开发：** 推荐使用 Docker Compose 部署 Milvus Standalone（单机版）进行开发测试。

---

## 4. Python 操作 Milvus 业务实战案例 (Demo)

以下示例模拟了项目中“**视频片段特征入库与自然语言检索**”的核心流程。

### 4.1 环境准备
安装 Milvus 的 Python 客户端 `pymilvus` 以及用于模拟向量生成的 numpy：

```bash
pip install pymilvus numpy
```

### 4.2 业务场景模拟代码
该脚本模拟了将切分的视频片段特征存入 Milvus，并根据文本查询向量检索出最相关的视频片段。

```python
import numpy as np
from pymilvus import (
    connections,
    utility,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
)

# -------------------------------------------------------------------------
# 1. 连接 Milvus 服务器
# -------------------------------------------------------------------------
print("1. Connecting to Milvus...")
connections.connect("default", host="localhost", port="19530")

# -------------------------------------------------------------------------
# 2. 定义 Collection Schema (集合结构)
# 根据项目需求，我们需要存储：视频ID、设备/工位名称、时间戳、以及视觉特征向量
# -------------------------------------------------------------------------
collection_name = "industrial_video_retrieval"
dim = 512  # 假设多模态大模型（如CLIP）输出的向量维度为 512

# 如果集合已存在则删除 (方便重复测试)
if utility.has_collection(collection_name):
    utility.drop_collection(collection_name)

print(f"2. Creating collection: {collection_name}")
fields = [
    FieldSchema(name="video_id", dtype=DataType.INT64, is_primary=True, auto_id=True, description="Primary key"),
    FieldSchema(name="camera_name", dtype=DataType.VARCHAR, max_length=100, description="Camera or Workstation name"),
    FieldSchema(name="timestamp", dtype=DataType.VARCHAR, max_length=50, description="Event timestamp"),
    # 向量字段必须指定维度
    FieldSchema(name="video_embedding", dtype=DataType.FLOAT_VECTOR, dim=dim, description="Visual feature vector")
]
schema = CollectionSchema(fields=fields, description="Collection for retrieving industrial video clips")
collection = Collection(name=collection_name, schema=schema)

# -------------------------------------------------------------------------
# 3. 模拟视频片段特征入库 (Insert)
# -------------------------------------------------------------------------
print("3. Inserting simulated video clips data...")
num_entities = 1000  # 模拟1000个截取的视频片段

# 模拟业务数据
camera_names = [f"Camera_Line_A_{i%5}" for i in range(num_entities)]
timestamps = [f"2026-03-27 10:{i%60:02d}:00" for i in range(num_entities)]
# 模拟深度学习模型输出的向量，这里用随机数代替
vectors = [[np.random.random() for _ in range(dim)] for _ in range(num_entities)]

entities = [
    camera_names,
    timestamps,
    vectors
]

insert_result = collection.insert(entities)
# 数据插入后需要 flush，确保数据落盘并可被检索
collection.flush()
print(f"   Inserted {insert_result.insert_count} entities.")

# -------------------------------------------------------------------------
# 4. 创建索引 (Index)
# 必须为向量字段创建索引才能进行高效检索
# -------------------------------------------------------------------------
print("4. Creating index for vector search...")
index_params = {
    "metric_type": "COSINE",  # 使用余弦相似度，常用于文本/图像特征对齐
    "index_type": "IVF_FLAT", # IVF_FLAT 是最常用的平衡索引类型
    "params": {"nlist": 1024} # nlist: 聚类中心的数量
}
collection.create_index(field_name="video_embedding", index_params=index_params)
print("   Index created successfully.")

# -------------------------------------------------------------------------
# 5. 加载数据到内存 (Load)
# 在进行搜索之前，必须将 collection 加载到内存中
# -------------------------------------------------------------------------
print("5. Loading collection to memory...")
collection.load()

# -------------------------------------------------------------------------
# 6. 模拟自然语言向量检索 (Search)
# 假设用户输入："检索A流水线的违规操作"，文本大模型（如DeepSeek）将其转为了查询向量
# -------------------------------------------------------------------------
print("6. Performing vector similarity search...")
search_params = {
    "metric_type": "COSINE",
    "params": {"nprobe": 10} # nprobe: 决定搜索多少个聚类簇，权衡精度和速度
}

# 模拟自然语言生成的查询向量
query_vector = [[np.random.random() for _ in range(dim)]]

# 搜索最相似的前 5 个视频片段
# 可以通过 expr 进行标量过滤，例如只查询今天的数据或特定摄像头的数据
results = collection.search(
    data=query_vector,
    anns_field="video_embedding",
    param=search_params,
    limit=5,
    expr=None, # 可以加入条件如: "camera_name == 'Camera_Line_A_1'"
    output_fields=["camera_name", "timestamp"] # 指定返回的标量字段
)

print("   Search Results (Top 5 matches):")
for hits in results:
    for hit in hits:
        print(f"   - Distance/Score: {hit.distance:.4f}, "
              f"Video ID: {hit.id}, "
              f"Camera: {hit.entity.get('camera_name')}, "
              f"Time: {hit.entity.get('timestamp')}")

# -------------------------------------------------------------------------
# 7. 释放内存
# -------------------------------------------------------------------------
print("7. Releasing collection...")
collection.release()
print("Done.")
```

## 5. 项目落地关键点提示

在将 Milvus 接入实际项目时，需要重点关注以下几个问题：

1.  **特征对齐：** 确保视频特征提取模型（如 CLIP 视觉端）和文本查询模型（如 CLIP 文本端或微调后的 DeepSeek）处于**同一特征语义空间**中，否则相似度计算（如 Cosine 距离）将失去意义。
2.  **标量过滤与混合查询：** 项目需要“追溯特定时间与人员”，这意味着我们不仅需要向量检索，还需要结合时间戳、人员ID等进行标量条件过滤（使用 `expr` 参数）。Milvus 对混合查询有很好的支持。
3.  **动态数据生命周期：** 24小时流处理产生的数据量极大，需要结合 Milvus 的 TTL（Time To Live）机制或定期清理策略，淘汰无价值的旧特征数据，节省存储成本。
4.  **向量维度评估：** 不同大模型输出的维度不同（如 512, 768, 1024）。在定义 Collection 时必须明确维度，并在模型端做好固定。
