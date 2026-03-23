"""
RAG 知识库管理 API
提供文档上传、索引状态查询、索引重建接口
"""
import os
import logging
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "knowledge")
ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf"}


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

    try:
        import chromadb
        chroma_path = os.path.abspath(os.getenv("CHROMA_DB_PATH", "data/chroma"))
        client = chromadb.PersistentClient(path=chroma_path)
        collection = client.get_or_create_collection("ski_knowledge")
        chunk_count = collection.count()
        initialized = chunk_count > 0
    except Exception as e:
        logger.warning("ChromaDB status check failed: %s", e)
        chunk_count = 0
        initialized = False

    return {
        "initialized": initialized,
        "documents": len(files),
        "chunks": chunk_count,
    }


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
