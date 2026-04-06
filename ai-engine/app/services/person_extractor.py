import os
import logging
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
import requests

from app.services.color_extractor import ColorExtractor

logger = logging.getLogger(__name__)


class PersonExtractor:
    def __init__(self):
        self.output_dir = Path(os.getenv("TRACKING_PERSONS_DIR", "data/tracking/persons"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8080")
        self.color_extractor = ColorExtractor()
        
    def extract_persons_from_video(self, video_id: int, video_path: str, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从视频轨迹中提取每个人的图像"""
        logger.info(f"Extracting persons from video {video_id}, tracks count: {len(tracks)}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Failed to open video: {video_path}")
            return []
        
        persons = []
        
        for track in tracks:
            track_id = track.get("trackId") or track.get("track_id")
            points = track.get("points", [])
            
            if not points:
                continue
            
            mid_idx = len(points) // 2
            mid_point = points[mid_idx]
            frame_num = mid_point.get("frame")
            
            x_center = mid_point.get("x")
            y_center = mid_point.get("y")
            width = mid_point.get("width")
            height = mid_point.get("height")
            
            if x_center is None or y_center is None or width is None or height is None:
                continue
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            
            if not ret:
                logger.warning(f"Failed to read frame {frame_num} for track {track_id}")
                continue
            
            x1 = int(x_center - width / 2)
            y1 = int(y_center - height / 2)
            x2 = int(x_center + width / 2)
            y2 = int(y_center + height / 2)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)
            
            cropped = frame[y1:y2, x1:x2]
            
            if cropped.size == 0:
                continue
            
            image_filename = f"video_{video_id}_track_{track_id}.jpg"
            image_path = self.output_dir / image_filename
            cv2.imwrite(str(image_path), cropped)
            
            dominant_color = self.color_extractor.extract_dominant_color(cropped)
            color_distribution = self.color_extractor.extract_color_distribution(cropped)
            
            person_data = {
                "video_id": video_id,
                "track_id": track_id,
                "cropped_image_path": f"/ai/tracking/persons/{image_filename}",
                "first_frame": points[0].get("frame"),
                "last_frame": points[-1].get("frame"),
                "frame_count": len(points),
                "dominant_color": dominant_color,
                "color_distribution": str(color_distribution) if color_distribution else None
            }
            
            persons.append(person_data)
            logger.info(f"Extracted person: track_id={track_id}, frames={len(points)}")
        
        cap.release()
        
        self._save_persons_to_db(persons)
        
        return persons
    
    def _save_persons_to_db(self, persons: List[Dict[str, Any]]):
        """保存人员信息到数据库"""
        try:
            url = f"{self.backend_url}/api/tracking/persons/batch"
            response = requests.post(url, json=persons, timeout=30)
            response.raise_for_status()
            logger.info(f"Saved {len(persons)} persons to database")
        except Exception as e:
            logger.error(f"Failed to save persons to database: {e}")
