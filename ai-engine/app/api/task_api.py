from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from app.services.yolo_processor import YOLOProcessor
from app.services.behavior_detector import detect_all
from app.services.result_callback import ResultCallback
from app.services.rag_engine import RAGEngine
from app.services.video_annotator import VideoAnnotator

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
    rag_engine = RAGEngine()
    annotator = VideoAnnotator()
    try:
        callback.send_status(task_id, "PROCESSING")
        tracks = processor.process_video(video_url)
        alerts = detect_all(tracks)
        liability_suggestion = rag_engine.generate_liability_suggestion(alerts, tracks) if alerts else ""
        annotated_video_path = annotator.annotate_video(video_url, task_id, tracks, alerts)
        callback.send_result(
            task_id,
            tracks,
            alerts,
            liability_suggestion,
            annotated_video_path=annotated_video_path,
        )
    except Exception as e:
        logger.error("Task %d failed: %s", task_id, e)
        callback.send_error(task_id, str(e))
