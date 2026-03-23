from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from app.services.yolo_processor import YOLOProcessor
from app.services.result_callback import ResultCallback

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class TaskRequest(BaseModel):
    taskId: int
    videoUrl: str


@router.post("/task/receive")
async def receive_task(task: TaskRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_task, task.taskId, task.videoUrl)
    return {"status": "accepted", "taskId": task.taskId}


def process_task(task_id: int, video_url: str):
    processor = YOLOProcessor()
    callback = ResultCallback()
    try:
        callback.send_status(task_id, "PROCESSING")
        tracks = processor.process_video(video_url)
        callback.send_result(task_id, tracks)
    except Exception as e:
        logger.error("Task %d failed: %s", task_id, e)
        callback.send_error(task_id, str(e))
