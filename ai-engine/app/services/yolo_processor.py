import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class YOLOProcessor:
    def __init__(self):
        self.model_path = os.getenv("YOLO_MODEL_PATH", "models/yolo11n.pt")
        self.model = None

    def _load_model(self):
        if self.model is None:
            from ultralytics import YOLO
            logger.info("Loading YOLO model from %s", self.model_path)
            self.model = YOLO(self.model_path)
            logger.info("YOLO model loaded successfully")

    def process_video(self, video_path: str) -> List[Dict[str, Any]]:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        self._load_model()
        logger.info("Processing video: %s", video_path)

        results = self.model.track(source=video_path, persist=True, stream=True)

        tracks: Dict[int, Dict[str, Any]] = {}
        frame_idx = 0

        for result in results:
            if result.boxes is not None and result.boxes.id is not None:
                boxes = result.boxes
                for i in range(len(boxes)):
                    track_id = int(boxes.id[i])
                    x_center = float(boxes.xywh[i][0])
                    y_center = float(boxes.xywh[i][1])
                    width = float(boxes.xywh[i][2])
                    height = float(boxes.xywh[i][3])
                    confidence = float(boxes.conf[i])
                    class_id = int(boxes.cls[i])

                    if track_id not in tracks:
                        tracks[track_id] = {
                            "trackId": track_id,
                            "className": self.model.names[class_id],
                            "points": []
                        }
                    tracks[track_id]["points"].append({
                        "frame": frame_idx,
                        "x": round(x_center, 2),
                        "y": round(y_center, 2),
                        "width": round(width, 2),
                        "height": round(height, 2),
                        "confidence": round(confidence, 4)
                    })
            frame_idx += 1

            if frame_idx % 100 == 0:
                logger.info("Processed %d frames, %d tracks detected", frame_idx, len(tracks))

        logger.info("Video processing complete: %d frames, %d tracks", frame_idx, len(tracks))
        return list(tracks.values())
