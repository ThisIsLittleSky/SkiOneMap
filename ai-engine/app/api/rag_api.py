"""
RAG 知识库管理 API
提供文档上传、索引状态查询、索引重建接口
"""
import os
import json
import logging
import shutil
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "knowledge")
ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf"}

# 查询历史记录（内存存储，最多保留 100 条）
query_history: List[Dict[str, Any]] = []
MAX_HISTORY = 100


def _knowledge_dir() -> str:
    path = os.path.abspath(KNOWLEDGE_DIR)
    os.makedirs(path, exist_ok=True)
    return path


@router.post("/rag/upload")
async def upload_knowledge(file: UploadFile = File(...)):
    """上传知识库文档并向量化入库。"""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}，仅支持 {ALLOWED_EXTENSIONS}")

    kdir = _knowledge_dir()
    dest = os.path.join(kdir, file.filename)
    with open(dest, "wb") as f:
        content = await file.read()
        f.write(content)
    logger.info("Knowledge file uploaded: %s (%d bytes)", file.filename, len(content))

    # 触发增量向量化
    chunks = _rebuild_index()
    return {"filename": file.filename, "chunks": chunks, "status": "indexed"}


@router.post("/rag/rebuild")
async def rebuild_index():
    """重建全量向量索引。"""
    chunks = _rebuild_index()
    return {"status": "ok", "chunks": chunks}


@router.get("/rag/status")
async def rag_status():
    """返回知识库当前状态。"""
    kdir = _knowledge_dir()
    files = [f for f in os.listdir(kdir) if os.path.isfile(os.path.join(kdir, f))]
    
    use_embedding = os.getenv("USE_EMBEDDING", "true").lower() == "true"
    
    # 计算索引大小
    chroma_path = os.path.abspath(os.getenv("CHROMA_DB_PATH", "data/chroma"))
    index_size_mb = 0.0
    if os.path.exists(chroma_path):
        total_size = sum(
            os.path.getsize(os.path.join(dirpath, filename))
            for dirpath, _, filenames in os.walk(chroma_path)
            for filename in filenames
        )
        index_size_mb = total_size / (1024 * 1024)

    # 最近上传时间
    last_upload = None
    if files:
        file_times = [os.path.getmtime(os.path.join(kdir, f)) for f in files]
        last_upload = datetime.fromtimestamp(max(file_times)).isoformat()

    chunk_count = 0
    initialized = False
    
    if use_embedding:
        # Embedding 模式：检查 ChromaDB
        try:
            import chromadb
            client = chromadb.PersistentClient(path=chroma_path)
            collection = client.get_or_create_collection("ski_knowledge")
            chunk_count = collection.count()
            initialized = chunk_count > 0
        except Exception as e:
            logger.warning("ChromaDB status check failed: %s", e)
    else:
        # 无 Embedding 模式：检查文档是否加载
        from app.services.rag_engine import RAGEngine
        try:
            engine = RAGEngine()
            if engine._initialized and engine.documents:
                chunk_count = len(engine.documents)
                initialized = True
            elif len(files) > 0:
                # 有文档但未初始化，尝试初始化
                engine._init()
                if engine.documents:
                    chunk_count = len(engine.documents)
                    initialized = True
        except Exception as e:
            logger.warning("RAG engine status check failed: %s", e)

    llm_model = os.getenv("QWEN_LLM_MODEL", "qwen3-max-2026-01-23")
    embedding_model = os.getenv("QWEN_EMBEDDING_MODEL", "tongyi-embedding-vision-plus-2026-03-06")

    return {
        "initialized": initialized,
        "documents": len(files),
        "chunks": chunk_count,
        "indexSizeMB": round(index_size_mb, 2),
        "lastUpload": last_upload,
        "queryCount": len(query_history),
        "useEmbedding": use_embedding,
        "llmModel": llm_model,
        "embeddingModel": embedding_model if use_embedding else None,
    }


@router.get("/rag/documents")
async def list_documents():
    """列出所有知识库文档。"""
    kdir = _knowledge_dir()
    files = []
    for fname in os.listdir(kdir):
        fpath = os.path.join(kdir, fname)
        if os.path.isfile(fpath):
            stat = os.stat(fpath)
            files.append({
                "filename": fname,
                "size": stat.st_size,
                "uploadTime": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
    files.sort(key=lambda x: x["uploadTime"], reverse=True)
    return {"documents": files}


@router.delete("/rag/documents/{filename}")
async def delete_document(filename: str):
    """删除指定文档。"""
    kdir = _knowledge_dir()
    fpath = os.path.join(kdir, filename)
    if not os.path.isfile(fpath):
        raise HTTPException(status_code=404, detail="文档不存在")
    os.remove(fpath)
    logger.info("Document deleted: %s", filename)
    return {"status": "ok", "filename": filename}


@router.get("/rag/documents/{filename}/preview")
async def preview_document(filename: str):
    """预览文档内容（前 500 字符）。"""
    kdir = _knowledge_dir()
    fpath = os.path.join(kdir, filename)
    if not os.path.isfile(fpath):
        raise HTTPException(status_code=404, detail="文档不存在")
    
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read(500)
        return {"filename": filename, "preview": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取失败: {str(e)}")


class QueryTestRequest(BaseModel):
    query: str


@router.post("/rag/test")
async def test_query(req: QueryTestRequest):
    """查询测试：直接 RAG 检索 + LLM 回答，返回结构化结果。"""
    from app.services.rag_engine import RAGEngine
    
    start_time = time.time()
    engine = RAGEngine()
    
    try:
        engine._init()
        if not engine._initialized:
            raise HTTPException(status_code=500, detail="RAG 引擎未初始化，请先上传知识库文档")
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=f"知识库为空: {str(e)}")
    except Exception as e:
        logger.error("RAG initialization failed: %s", e)
        raise HTTPException(status_code=500, detail=f"RAG 引擎初始化失败: {str(e)}")
    
    try:
        result_str = engine.query_knowledge(req.query)
        elapsed = time.time() - start_time

        # 解析 JSON 结果
        try:
            structured = json.loads(result_str)
        except json.JSONDecodeError:
            structured = {
                "liability": {"parties": [], "resort_liability": "无"},
                "behavior_analysis": result_str,
                "references": [],
                "suggestion": ""
            }
        
        # 记录查询历史
        query_history.append({
            "query": req.query,
            "timestamp": datetime.now().isoformat(),
            "elapsed": round(elapsed, 2),
            "success": True,
        })
        if len(query_history) > MAX_HISTORY:
            query_history.pop(0)
        
        return {
            "query": req.query,
            "answer": structured,
            "elapsed": round(elapsed, 2),
        }
    except Exception as e:
        logger.error("Query test failed: %s", e)
        query_history.append({
            "query": req.query,
            "timestamp": datetime.now().isoformat(),
            "elapsed": 0,
            "success": False,
            "error": str(e),
        })
        if len(query_history) > MAX_HISTORY:
            query_history.pop(0)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/rag/history")
async def get_query_history(limit: int = Query(10, ge=1, le=100)):
    """获取最近的查询历史。"""
    return {"history": query_history[-limit:][::-1]}


@router.get("/rag/stats")
async def get_stats():
    """获取性能统计。"""
    if not query_history:
        return {
            "totalQueries": 0,
            "avgElapsed": 0,
            "maxElapsed": 0,
            "minElapsed": 0,
            "successRate": 0,
        }
    
    success_queries = [q for q in query_history if q.get("success")]
    elapsed_times = [q["elapsed"] for q in success_queries if "elapsed" in q]
    
    return {
        "totalQueries": len(query_history),
        "avgElapsed": round(sum(elapsed_times) / len(elapsed_times), 2) if elapsed_times else 0,
        "maxElapsed": round(max(elapsed_times), 2) if elapsed_times else 0,
        "minElapsed": round(min(elapsed_times), 2) if elapsed_times else 0,
        "successRate": round(len(success_queries) / len(query_history) * 100, 1),
    }


@router.delete("/rag/clear")
async def clear_knowledge():
    """清空知识库（删除所有文档和索引）。"""
    kdir = _knowledge_dir()
    for fname in os.listdir(kdir):
        fpath = os.path.join(kdir, fname)
        if os.path.isfile(fpath):
            os.remove(fpath)
    
    # 清空 ChromaDB
    chroma_path = os.path.abspath(os.getenv("CHROMA_DB_PATH", "data/chroma"))
    if os.path.exists(chroma_path):
        shutil.rmtree(chroma_path)
        os.makedirs(chroma_path, exist_ok=True)
    
    logger.info("Knowledge base cleared")
    return {"status": "ok", "message": "知识库已清空"}


class EmbeddingModeRequest(BaseModel):
    enabled: bool


@router.post("/rag/embedding-mode")
async def set_embedding_mode(req: EmbeddingModeRequest):
    """动态切换 Embedding 模式。"""
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    
    # 读取现有 .env 内容
    env_lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            env_lines = f.readlines()
    
    # 更新或添加 USE_EMBEDDING
    found = False
    new_value = "true" if req.enabled else "false"
    for i, line in enumerate(env_lines):
        if line.strip().startswith("USE_EMBEDDING="):
            env_lines[i] = f"USE_EMBEDDING={new_value}\n"
            found = True
            break
    
    if not found:
        env_lines.append(f"USE_EMBEDDING={new_value}\n")
    
    # 写回 .env
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(env_lines)
    
    # 更新当前进程环境变量
    os.environ["USE_EMBEDDING"] = new_value
    
    # 重置 RAG 引擎以应用新配置
    from app.services.rag_engine import RAGEngine
    try:
        engine = RAGEngine()
        engine._initialized = False
        engine._init()
    except Exception as e:
        logger.warning("Failed to reinitialize RAG engine: %s", e)
    
    logger.info("Embedding mode set to: %s", new_value)
    return {"status": "ok", "enabled": req.enabled, "message": f"Embedding 模式已{'开启' if req.enabled else '关闭'}"}


def _rebuild_index() -> int:
    """重建 ChromaDB 向量索引，返回 chunk 数量。"""
    from app.services.rag_engine import RAGEngine
    engine = RAGEngine()
    engine._initialized = False  # 强制重新构建
    try:
        engine._init()
        # 获取最新 chunk 数量
        import chromadb
        chroma_path = os.path.abspath(os.getenv("CHROMA_DB_PATH", "data/chroma"))
        client = chromadb.PersistentClient(path=chroma_path)
        collection = client.get_or_create_collection("ski_knowledge")
        return collection.count()
    except Exception as e:
        logger.error("Failed to rebuild RAG index: %s", e)
        raise HTTPException(status_code=500, detail=f"索引构建失败: {str(e)}")
