"""
RAG 定责建议引擎
使用 LlamaIndex + ChromaDB 向量检索 + 阿里千问兼容接口生成定责建议
"""
import os
import logging
from typing import List, Dict, Any

from openai import OpenAI

logger = logging.getLogger(__name__)

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "knowledge")


class QwenCompatibleEmbedding:
    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def get_text_embedding(self, text: str) -> List[float]:
        response = self.client.embeddings.create(model=self.model, input=text)
        return response.data[0].embedding

    def get_query_embedding(self, query: str) -> List[float]:
        return self.get_text_embedding(query)

    def get_text_embedding_batch(self, texts: List[str], **kwargs) -> List[List[float]]:
        response = self.client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]


class RAGEngine:
    def __init__(self):
        self.chroma_path = os.getenv("CHROMA_DB_PATH", "data/chroma")
        self.qwen_api_key = os.getenv("QWEN_API_KEY", "")
        self.qwen_base_url = os.getenv(
            "QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.llm_model = os.getenv("QWEN_LLM_MODEL", "qwen3-max-2026-01-23")
        self.embedding_model = os.getenv("QWEN_EMBEDDING_MODEL", "qwen3-vl-embedding")
        self.index = None
        self._initialized = False

    def _init(self):
        if self._initialized:
            return
        try:
            self._build_index()
            self._initialized = True
        except Exception as e:
            logger.error("RAG engine initialization failed: %s", e)
            self._initialized = False

    def _build_index(self):
        """加载知识库文档，构建或加载 ChromaDB 向量索引。"""
        from llama_index.core import (
            VectorStoreIndex,
            SimpleDirectoryReader,
            StorageContext,
            Settings,
        )
        from llama_index.vector_stores.chroma import ChromaVectorStore
        from llama_index.llms.openai import OpenAI as LlamaOpenAI
        import chromadb

        knowledge_dir = os.path.abspath(KNOWLEDGE_DIR)
        if not os.path.isdir(knowledge_dir) or not os.listdir(knowledge_dir):
            raise FileNotFoundError(f"Knowledge directory empty or missing: {knowledge_dir}")

        # 通过 OpenAI 兼容接口接入阿里千问
        Settings.llm = LlamaOpenAI(
            model=self.llm_model,
            api_key=self.qwen_api_key,
            api_base=self.qwen_base_url,
            temperature=0.2,
        )
        Settings.embed_model = QwenCompatibleEmbedding(
            model=self.embedding_model,
            api_key=self.qwen_api_key,
            base_url=self.qwen_base_url,
        )

        # 初始化 ChromaDB
        chroma_path = os.path.abspath(self.chroma_path)
        os.makedirs(chroma_path, exist_ok=True)
        chroma_client = chromadb.PersistentClient(path=chroma_path)
        chroma_collection = chroma_client.get_or_create_collection("ski_knowledge")

        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # 如果集合已有数据则直接加载，否则重新向量化
        if chroma_collection.count() > 0:
            logger.info("Loading existing ChromaDB index (%d chunks)", chroma_collection.count())
            self.index = VectorStoreIndex.from_vector_store(
                vector_store, storage_context=storage_context
            )
        else:
            logger.info("Building new index from knowledge directory: %s", knowledge_dir)
            documents = SimpleDirectoryReader(knowledge_dir).load_data()
            logger.info("Loaded %d documents, vectorizing...", len(documents))
            self.index = VectorStoreIndex.from_documents(
                documents, storage_context=storage_context
            )
            logger.info("Index built with %d chunks", chroma_collection.count())

    def generate_liability_suggestion(
        self, alerts: List[Dict[str, Any]], tracks: List[Dict[str, Any]]
    ) -> str:
        """
        基于检测到的预警事件和轨迹数据，通过 RAG 生成定责建议。

        参数:
            alerts: 危险行为检测结果列表
            tracks: 所有轨迹数据

        返回:
            str: LLM 生成的定责建议文本
        """
        if not self.qwen_api_key or self.qwen_api_key == "your_qwen_api_key":
            return self._fallback_suggestion(alerts)

        self._init()
        if not self._initialized or self.index is None:
            logger.warning("RAG index not available, using fallback")
            return self._fallback_suggestion(alerts)

        try:
            query_engine = self.index.as_query_engine(similarity_top_k=4)
            prompt = self._build_prompt(alerts, tracks)
            response = query_engine.query(prompt)
            result = str(response).strip()
            logger.info("RAG generated liability suggestion (%d chars)", len(result))
            return result
        except Exception as e:
            logger.error("RAG query failed: %s", e)
            return self._fallback_suggestion(alerts)

    def _build_prompt(
        self, alerts: List[Dict[str, Any]], tracks: List[Dict[str, Any]]
    ) -> str:
        """构建 RAG 查询 prompt。"""
        alert_lines = []
        for a in alerts:
            alert_lines.append(
                f"- 行为类型：{a['alertType']}，严重程度：{a['severity']}，"
                f"涉及轨迹ID：{a.get('trackId', '未知')}，"
                f"描述：{a.get('description', '')}"
            )

        track_summary = []
        for t in tracks:
            pts = t["points"]
            if len(pts) >= 2:
                total_dist = sum(
                    ((pts[i]["x"] - pts[i-1]["x"])**2 + (pts[i]["y"] - pts[i-1]["y"])**2) ** 0.5
                    for i in range(1, len(pts))
                )
                track_summary.append(
                    f"轨迹ID {t['trackId']}：共 {len(pts)} 帧，"
                    f"总位移 {total_dist:.1f}px，类别 {t['className']}"
                )

        prompt = (
            "以下是一起滑雪场视频监控分析结果，请根据滑雪场安全规范和历史事故案例，"
            "对检测到的危险行为进行定责分析，给出责任方判断和建议处理措施。\n\n"
            "【检测到的危险行为】\n"
            + "\n".join(alert_lines) + "\n\n"
            "【轨迹概要】\n"
            + "\n".join(track_summary) + "\n\n"
            "请依据安全规范和案例库，分析：\n"
            "1. 各轨迹（当事人）的违规行为及责任比例\n"
            "2. 雪场管理方是否存在连带责任\n"
            "3. 建议的处理措施（警告/责令离场/追责赔偿）\n"
            "4. 后续风险防范建议\n"
            "请以中文回答，结构清晰。"
        )
        return prompt

    def _fallback_suggestion(self, alerts: List[Dict[str, Any]]) -> str:
        """无 LLM 时基于规则的简单定责建议。"""
        if not alerts:
            return "未检测到危险行为，无需定责分析。"

        lines = ["【规则定责建议（无 LLM，基于规则引擎）】\n"]
        for alert in alerts:
            alert_type = alert.get("alertType", "")
            track_id = alert.get("trackId", "未知")

            if alert_type == "WRONG_WAY":
                lines.append(
                    f"• 轨迹 {track_id} — 逆行违规：依据规范第三章3.1条，"
                    "逆行方承担主要责任（70%~100%），建议责令离场并记录在案。"
                )
            elif alert_type == "OVERSPEED":
                lines.append(
                    f"• 轨迹 {track_id} — 超速违规：依据规范第三章3.2条，"
                    "超速方对事故承担主要责任（60%~80%），建议当场警告并限速提醒。"
                )
            elif alert_type == "COLLISION_RISK":
                lines.append(
                    f"• 轨迹 {track_id} — 碰撞风险：依据规范第三章3.3条，"
                    "双方须保持安全间距，若发生碰撞后方/超越方责任 ≥ 80%，"
                    "建议立即干预，调度巡逻人员处置。"
                )
            elif alert_type == "STILL_DETECTED":
                lines.append(
                    f"• 轨迹 {track_id} — 静止预警（疑似摔倒）：依据规范第五章救援流程，"
                    "建议立即派遣救援人员前往确认伤情，目标响应时间 ≤ 5 分钟。"
                )

        lines.append("\n以上建议基于规则引擎，最终定责以现场调查和完整证据为准。")
        return "\n".join(lines)
