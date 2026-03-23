import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.task_api import router as task_router
from app.api.health import router as health_router
from app.api.rag_api import router as rag_router
from app.services.task_consumer import TaskConsumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

task_consumer = TaskConsumer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task_consumer.start()
    yield
    task_consumer.stop()


app = FastAPI(title="Ski Monitor AI Engine", version="0.1.0", lifespan=lifespan)

app.include_router(health_router, prefix="/ai")
app.include_router(task_router, prefix="/ai")
app.include_router(rag_router, prefix="/ai")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
