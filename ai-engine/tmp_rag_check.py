from app.services.rag_engine import RAGEngine

engine = RAGEngine()
engine._init()
print({"initialized": engine._initialized, "has_index": engine.index is not None})
