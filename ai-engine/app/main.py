import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.task_api import router as task_router
from app.api.health import router as health_router
from app.api.rag_api import router as rag_router
from app.api.tracking_api import router as tracking_router
from app.services.task_consumer import TaskConsumer

# 加载 .env 环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

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
app.include_router(tracking_router, prefix="/ai")

persons_dir = Path(os.getenv("TRACKING_PERSONS_DIR", "data/tracking/persons"))
persons_dir.mkdir(parents=True, exist_ok=True)
app.mount("/ai/tracking/persons", StaticFiles(directory=str(persons_dir)), name="tracking_persons")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
