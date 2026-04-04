"""
RAG 定责建议引擎
使用 LlamaIndex + ChromaDB 向量检索 + 阿里千问兼容接口生成定责建议
支持无 embedding 模式（直接用 LLM 处理文档）
"""
import os
import re
import json
import logging
from typing import List, Dict, Any, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "knowledge")


class RAGEngine:
    def __init__(self):
        self.chroma_path = os.getenv("CHROMA_DB_PATH", "data/chroma")
        self.qwen_api_key = os.getenv("QWEN_API_KEY", "")
        self.qwen_base_url = os.getenv(
            "QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.llm_model = os.getenv("QWEN_LLM_MODEL", "qwen3-max-2026-01-23")
        self.embedding_model = os.getenv("QWEN_EMBEDDING_MODEL", "text-embedding-v3")
        # DashScope SDK 需要通过环境变量或参数获取 API Key
        if self.qwen_api_key:
            os.environ["DASHSCOPE_API_KEY"] = self.qwen_api_key
        # 是否使用 embedding 向量检索，默认开启
        self.use_embedding = os.getenv("USE_EMBEDDING", "true").lower() == "true"
        self.index = None
        self.documents = []  # 直接加载的文档内容
        self._initialized = False
        # 启动时自动初始化
        try:
            self._init()
        except Exception as e:
            logger.warning("Failed to auto-initialize RAG engine: %s", e)

    def _init(self):
        if self._initialized:
            return
        if self.use_embedding:
            self._build_index()
        else:
            self._load_documents_simple()
        self._initialized = True

    def _load_documents_simple(self):
        """不使用 embedding，直接加载文档内容用于 LLM 处理"""
        from llama_index.core import SimpleDirectoryReader
        
        knowledge_dir = os.path.abspath(KNOWLEDGE_DIR)
        if not os.path.isdir(knowledge_dir) or not os.listdir(knowledge_dir):
            raise FileNotFoundError(f"Knowledge directory empty or missing: {knowledge_dir}")
        
        logger.info("Loading knowledge documents (no embedding mode): %s", knowledge_dir)
        documents = SimpleDirectoryReader(knowledge_dir).load_data()
        
        # 简单分块，每块约 1000 字符
        self.documents = []
        for doc in documents:
            text = doc.text
            # 按段落分割
            chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
            self.documents.extend(chunks)
        
        logger.info("Loaded %d document chunks (no vectorization)", len(self.documents))

    def _get_relevant_chunks(self, keywords: List[str], top_k: int = 4) -> List[str]:
        """基于关键词匹配获取相关文档块"""
        if not self.documents:
            return []
        
        scores = []
        for chunk in self.documents:
            chunk_lower = chunk.lower()
            score = sum(1 for kw in keywords if kw.lower() in chunk_lower)
            if score > 0:
                scores.append((score, chunk))
        
        # 按分数排序，取前 top_k
        scores.sort(key=lambda x: -x[0])
        return [chunk for _, chunk in scores[:top_k]]

    def _build_index(self):
        """使用 embedding 向量检索模式"""
        from http import HTTPStatus
        from llama_index.core import (
            VectorStoreIndex,
            SimpleDirectoryReader,
            StorageContext,
            Settings,
        )
        from llama_index.core.embeddings import BaseEmbedding
        from llama_index.vector_stores.chroma import ChromaVectorStore
        from llama_index.llms.openai import OpenAI as LlamaOpenAI
        import dashscope
        import chromadb

        knowledge_dir = os.path.abspath(KNOWLEDGE_DIR)
        if not os.path.isdir(knowledge_dir) or not os.listdir(knowledge_dir):
            raise FileNotFoundError(f"Knowledge directory empty or missing: {knowledge_dir}")

        Settings.llm = LlamaOpenAI(
            model=self.llm_model,
            api_key=self.qwen_api_key,
            api_base=self.qwen_base_url,
            temperature=0.2,
        )

        embed_model = self.embedding_model
        embed_api_key = self.qwen_api_key

        class SafeDashScopeEmbedding(BaseEmbedding):
            """DashScope embedding with proper error handling."""

            def _call_embedding(self, texts):
                if isinstance(texts, str):
                    texts = [texts]
                resp = dashscope.TextEmbedding.call(
                    model=embed_model, input=texts, api_key=embed_api_key
                )
                if resp.status_code != HTTPStatus.OK:
                    raise RuntimeError(
                        f"DashScope embedding failed: code={resp.status_code}, "
                        f"message={resp.message}"
                    )
                results = [None] * len(texts)
                for emb in resp.output["embeddings"]:
                    results[emb["text_index"]] = emb["embedding"]
                return results

            def _get_text_embedding(self, text: str):
                return self._call_embedding(text)[0]

            def _get_query_embedding(self, query: str):
                return self._call_embedding(query)[0]

            def _get_text_embeddings(self, texts):
                return self._call_embedding(texts)

            async def _aget_query_embedding(self, query: str):
                return self._get_query_embedding(query)

        Settings.embed_model = SafeDashScopeEmbedding(
            model_name=self.embedding_model,
        )

        chroma_path = os.path.abspath(self.chroma_path)
        os.makedirs(chroma_path, exist_ok=True)
        chroma_client = chromadb.PersistentClient(path=chroma_path)
        chroma_collection = chroma_client.get_or_create_collection("ski_knowledge")

        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

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

    # 结构化 JSON 输出格式要求（视频分析路径与查询测试路径共用）
    STRUCTURED_OUTPUT_INSTRUCTION = """请严格按照以下JSON格式输出，不要输出任何其他内容：
{
  "liability": {
    "parties": [
      {"name": "当事人名称", "percentage": 责任百分比数字, "reason": "责任原因"}
    ],
    "resort_liability": "雪场管理方连带责任说明，无则填'无'"
  },
  "behavior_analysis": "详细的行为分析描述",
  "references": [
    {"title": "法规/条文标题", "content": "相关条文摘要"}
  ],
  "suggestion": "处理措施建议"
}"""

    def generate_liability_suggestion(
        self, alerts: List[Dict[str, Any]], tracks: List[Dict[str, Any]]
    ) -> str:
        """
        视频分析路径：基于检测到的预警事件和轨迹数据，通过 RAG 生成结构化定责建议。
        返回 JSON 字符串。
        """
        if not self.qwen_api_key or self.qwen_api_key == "your_qwen_api_key":
            return self._fallback_suggestion(alerts)

        self._init()
        if not self._initialized:
            logger.warning("RAG not initialized, using fallback")
            return self._fallback_suggestion(alerts)

        try:
            if self.use_embedding and self.index:
                query_engine = self.index.as_query_engine(similarity_top_k=4)
                prompt = self._build_video_prompt(alerts, tracks)
                response = query_engine.query(prompt)
                result = str(response).strip()
            else:
                result = self._generate_video_with_llm_direct(alerts, tracks)

            result = self._extract_json(result)
            logger.info("RAG generated liability suggestion (%d chars)", len(result))
            return result
        except Exception as e:
            logger.error("RAG query failed: %s", e)
            return self._fallback_suggestion(alerts)

    def query_knowledge(self, question: str) -> str:
        """
        查询测试路径：直接根据用户问题进行 RAG 检索 + LLM 回答。
        不需要视频分析数据，返回结构化 JSON 字符串。
        """
        if not self.qwen_api_key or self.qwen_api_key == "your_qwen_api_key":
            return json.dumps({
                "liability": {"parties": [], "resort_liability": "无"},
                "behavior_analysis": "未配置 LLM API Key，无法生成分析。",
                "references": [],
                "suggestion": "请先配置有效的 API Key。"
            }, ensure_ascii=False)

        self._init()
        if not self._initialized:
            return json.dumps({
                "liability": {"parties": [], "resort_liability": "无"},
                "behavior_analysis": "RAG 引擎未初始化，请先上传知识库文档。",
                "references": [],
                "suggestion": ""
            }, ensure_ascii=False)

        try:
            if self.use_embedding and self.index:
                query_engine = self.index.as_query_engine(similarity_top_k=4)
                prompt = self._build_query_prompt(question)
                response = query_engine.query(prompt)
                result = str(response).strip()
            else:
                result = self._generate_query_with_llm_direct(question)

            result = self._extract_json(result)
            logger.info("RAG query_knowledge result (%d chars)", len(result))
            return result
        except Exception as e:
            logger.error("RAG query_knowledge failed: %s", e)
            return json.dumps({
                "liability": {"parties": [], "resort_liability": "无"},
                "behavior_analysis": f"查询失败: {str(e)}",
                "references": [],
                "suggestion": ""
            }, ensure_ascii=False)

    def _extract_json(self, text: str) -> str:
        """从 LLM 输出中提取 JSON 字符串，处理可能的 markdown 代码块包裹"""
        cleaned = text.strip()
        # 去除 markdown 代码块
        md_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', cleaned, re.DOTALL)
        if md_match:
            cleaned = md_match.group(1).strip()
        # 尝试提取第一个 JSON 对象
        brace_start = cleaned.find('{')
        if brace_start >= 0:
            depth = 0
            for i in range(brace_start, len(cleaned)):
                if cleaned[i] == '{':
                    depth += 1
                elif cleaned[i] == '}':
                    depth -= 1
                    if depth == 0:
                        candidate = cleaned[brace_start:i+1]
                        try:
                            json.loads(candidate)
                            return candidate
                        except json.JSONDecodeError:
                            break
        return text

    def _generate_video_with_llm_direct(
        self, alerts: List[Dict[str, Any]], tracks: List[Dict[str, Any]]
    ) -> str:
        """视频分析路径：不使用 embedding，直接用 LLM 处理"""
        keywords = []
        for alert in alerts:
            keywords.append(alert.get("alertType", ""))
            keywords.append(alert.get("description", ""))

        relevant_docs = self._get_relevant_chunks(keywords, top_k=4)
        knowledge_context = "\n\n".join(relevant_docs) if relevant_docs else "（知识库为空）"

        prompt = self._build_video_prompt_with_knowledge(alerts, tracks, knowledge_context)

        client = OpenAI(api_key=self.qwen_api_key, base_url=self.qwen_base_url)
        response = client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": "你是一个专业的滑雪场安全管理专家，正在分析一段视频中的实际事故。请根据法律法规和安全规范进行事故定责分析，严格以JSON格式输出。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()

    def _generate_query_with_llm_direct(self, question: str) -> str:
        """查询测试路径：不使用 embedding，直接用 LLM 处理"""
        keywords = question.split()
        if not keywords:
            keywords = [question]

        relevant_docs = self._get_relevant_chunks(keywords, top_k=4)
        knowledge_context = "\n\n".join(relevant_docs) if relevant_docs else "（知识库为空）"

        prompt = self._build_query_prompt_with_knowledge(question, knowledge_context)

        client = OpenAI(api_key=self.qwen_api_key, base_url=self.qwen_base_url)
        response = client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": "你是一个专业的滑雪场安全管理专家，正在回答一个关于滑雪安全的法律咨询问题。请根据知识库内容和法律法规进行分析，严格以JSON格式输出。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()

    def _build_alert_and_track_text(
        self, alerts: List[Dict[str, Any]], tracks: List[Dict[str, Any]]
    ) -> tuple:
        """构建预警行为和轨迹概要的文本"""
        alert_lines = []
        for a in alerts:
            alert_lines.append(
                f"- 行为类型：{a['alertType']}，严重程度：{a['severity']}，"
                f"涉及轨迹ID：{a.get('trackId', '未知')}，描述：{a.get('description', '')}"
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
                    f"轨迹ID {t['trackId']}：共 {len(pts)} 帧，总位移 {total_dist:.1f}px，类别 {t['className']}"
                )

        return "\n".join(alert_lines), "\n".join(track_summary)

    def _build_video_prompt_with_knowledge(
        self, alerts: List[Dict[str, Any]], tracks: List[Dict[str, Any]], knowledge_context: str
    ) -> str:
        """视频分析路径：带知识库内容的 prompt"""
        alert_text, track_text = self._build_alert_and_track_text(alerts, tracks)

        return f"""【参考知识库/案例】
{knowledge_context}

【视频分析检测到的危险行为】
{alert_text}

【轨迹概要】
{track_text}

请根据上述视频分析结果和知识库内容，对检测到的危险行为进行定责分析。

{self.STRUCTURED_OUTPUT_INSTRUCTION}"""

    def _build_video_prompt(
        self, alerts: List[Dict[str, Any]], tracks: List[Dict[str, Any]]
    ) -> str:
        """视频分析路径：向量检索查询 prompt"""
        alert_text, track_text = self._build_alert_and_track_text(alerts, tracks)

        return f"""以下是一起滑雪场视频监控分析结果，请根据滑雪场安全规范和历史事故案例，对检测到的危险行为进行定责分析。

【检测到的危险行为】
{alert_text}

【轨迹概要】
{track_text}

{self.STRUCTURED_OUTPUT_INSTRUCTION}"""

    def _build_query_prompt_with_knowledge(self, question: str, knowledge_context: str) -> str:
        """查询测试路径：带知识库内容的 prompt"""
        return f"""【参考知识库/案例】
{knowledge_context}

【用户咨询问题】
{question}

请根据知识库内容回答上述问题，给出定责分析参考。

{self.STRUCTURED_OUTPUT_INSTRUCTION}"""

    def _build_query_prompt(self, question: str) -> str:
        """查询测试路径：向量检索查询 prompt"""
        return f"""用户咨询以下滑雪安全问题，请根据滑雪场安全规范和法律法规进行分析回答。

【用户咨询问题】
{question}

{self.STRUCTURED_OUTPUT_INSTRUCTION}"""

    def _fallback_suggestion(self, alerts: List[Dict[str, Any]]) -> str:
        """无 LLM 时基于规则的简单定责建议，返回结构化 JSON 字符串"""
        if not alerts:
            return json.dumps({
                "liability": {"parties": [], "resort_liability": "无"},
                "behavior_analysis": "未检测到危险行为，无需定责分析。",
                "references": [],
                "suggestion": "无需处理。"
            }, ensure_ascii=False)

        parties = []
        references = []
        analysis_lines = []

        ALERT_RULES = {
            "WRONG_WAY": {
                "pct": 85,
                "analysis": "逆行违规",
                "ref_title": "规范第三章3.1条",
                "ref_content": "逆行方承担主要责任（70%~100%），建议责令离场并记录在案。",
                "suggestion": "责令离场并记录在案",
            },
            "OVERSPEED": {
                "pct": 70,
                "analysis": "超速违规",
                "ref_title": "规范第三章3.2条",
                "ref_content": "超速方对事故承担主要责任（60%~80%），建议当场警告并限速提醒。",
                "suggestion": "当场警告并限速提醒",
            },
            "COLLISION_RISK": {
                "pct": 80,
                "analysis": "碰撞风险",
                "ref_title": "规范第三章3.3条",
                "ref_content": "双方须保持安全间距，若发生碰撞后方/超越方责任≥80%。",
                "suggestion": "立即干预，调度巡逻人员处置",
            },
            "STILL_DETECTED": {
                "pct": 0,
                "analysis": "静止预警（疑似摔倒）",
                "ref_title": "规范第五章救援流程",
                "ref_content": "建议立即派遣救援人员前往确认伤情，目标响应时间≤5分钟。",
                "suggestion": "立即派遣救援人员确认伤情",
            },
        }

        suggestions = []
        for alert in alerts:
            alert_type = alert.get("alertType", "")
            track_id = alert.get("trackId", "未知")
            rule = ALERT_RULES.get(alert_type)
            if rule:
                if rule["pct"] > 0:
                    parties.append({
                        "name": f"轨迹{track_id}",
                        "percentage": rule["pct"],
                        "reason": rule["analysis"]
                    })
                analysis_lines.append(f"轨迹{track_id}：{rule['analysis']}")
                references.append({"title": rule["ref_title"], "content": rule["ref_content"]})
                suggestions.append(rule["suggestion"])

        result = {
            "liability": {
                "parties": parties,
                "resort_liability": "以现场调查和完整证据为准"
            },
            "behavior_analysis": "；".join(analysis_lines) if analysis_lines else "无",
            "references": references,
            "suggestion": "；".join(suggestions) if suggestions else "无需处理"
        }
        return json.dumps(result, ensure_ascii=False)
