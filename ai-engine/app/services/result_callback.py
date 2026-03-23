import os
import json
import redis
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ResultCallback:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DATABASE", 9)),
            decode_responses=True
        )
        self.result_queue = "ai:results"

    def send_status(self, task_id: int, status: str):
        result = {"taskId": task_id, "status": status}
        self.redis_client.rpush(self.result_queue, json.dumps(result))
        logger.info("Sent status update for task %d: %s", task_id, status)

    def send_result(
        self,
        task_id: int,
        tracks: List[Dict[str, Any]],
        alerts: List[Dict[str, Any]] = None,
        liability_suggestion: str = ""
    ):
        if alerts is None:
            alerts = []
        total_frames = 0
        if tracks:
            all_frames = [p["frame"] for t in tracks for p in t["points"]]
            total_frames = max(all_frames) + 1 if all_frames else 0

        result = {
            "taskId": task_id,
            "status": "COMPLETED",
            "tracks": tracks,
            "trackCount": len(tracks),
            "totalFrames": total_frames,
            "alerts": alerts,
            "alertCount": len(alerts),
            "liabilitySuggestion": liability_suggestion,
        }
        self.redis_client.rpush(self.result_queue, json.dumps(result))
        logger.info(
            "Sent completed result for task %d: %d tracks, %d alerts",
            task_id, len(tracks), len(alerts)
        )

    def send_error(self, task_id: int, error: str):
        result = {"taskId": task_id, "status": "FAILED", "error": error}
        self.redis_client.rpush(self.result_queue, json.dumps(result))
        logger.warning("Sent error for task %d: %s", task_id, error)
