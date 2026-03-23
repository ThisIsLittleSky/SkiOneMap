import os
import json
import threading
import redis
from app.services.yolo_processor import YOLOProcessor
from app.services.behavior_detector import detect_all
from app.services.rag_engine import RAGEngine
from app.services.result_callback import ResultCallback

import logging

logger = logging.getLogger(__name__)


class TaskConsumer:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DATABASE", 9)),
            decode_responses=True
        )
        self.task_queue = "video:tasks"
        self.running = False
        self.processor = YOLOProcessor()
        self.rag_engine = RAGEngine()
        self.callback = ResultCallback()

    def start(self):
        self.running = True
        thread = threading.Thread(target=self._poll_loop, daemon=True)
        thread.start()
        logger.info("Task consumer started, polling queue: %s", self.task_queue)

    def stop(self):
        self.running = False
        logger.info("Task consumer stopped")

    def _poll_loop(self):
        while self.running:
            try:
                message = self.redis_client.blpop(self.task_queue, timeout=5)
                if message is not None:
                    _, raw = message
                    task_data = json.loads(raw)
                    task_id = task_data["taskId"]
                    video_path = task_data.get("videoPath", "")
                    logger.info("Received task %d for video: %s", task_id, video_path)
                    self._process_task(task_id, video_path)
            except json.JSONDecodeError as e:
                logger.error("Invalid task message: %s", e)
            except Exception as e:
                logger.error("Error in task consumer: %s", e)
                if self.running:
                    import time
                    time.sleep(2)

    def _process_task(self, task_id: int, video_path: str):
        try:
            self.callback.send_status(task_id, "PROCESSING")

            # 1. YOLO 轨迹提取
            tracks = self.processor.process_video(video_path)
            logger.info("Task %d: extracted %d tracks", task_id, len(tracks))

            # 2. 危险行为检测
            alerts = detect_all(tracks)
            logger.info("Task %d: detected %d alerts", task_id, len(alerts))

            # 3. RAG 定责建议（有预警时才调用）
            liability_suggestion = ""
            if alerts:
                logger.info("Task %d: generating liability suggestion via RAG...", task_id)
                liability_suggestion = self.rag_engine.generate_liability_suggestion(
                    alerts, tracks
                )

            # 4. 回调结果
            self.callback.send_result(task_id, tracks, alerts, liability_suggestion)
            logger.info("Task %d completed: %d tracks, %d alerts", task_id, len(tracks), len(alerts))

        except Exception as e:
            logger.error("Task %d failed: %s", task_id, e, exc_info=True)
            self.callback.send_error(task_id, str(e))
