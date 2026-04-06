import os
import logging
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
import torch
import torch.nn.functional as F

logger = logging.getLogger(__name__)


class PersonReIdentification:
    def __init__(self):
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.feature_dim = 512
        self.match_threshold = float(os.getenv("REID_MATCH_THRESHOLD", "0.6"))
        
    def _load_model(self):
        """加载ReID模型（使用简单的特征提取器）"""
        if self.model is None:
            try:
                from torchvision import models, transforms
                self.model = models.resnet50(pretrained=True)
                self.model.fc = torch.nn.Identity()
                self.model = self.model.to(self.device)
                self.model.eval()
                
                self.transform = transforms.Compose([
                    transforms.ToPILImage(),
                    transforms.Resize((256, 128)),
                    transforms.ToTensor(),
                    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
                ])
                logger.info("ReID model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load ReID model: {e}")
                raise
    
    def extract_feature(self, image_path: str) -> np.ndarray:
        """提取图像特征向量"""
        self._load_model()
        
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Failed to read image: {image_path}")
            return np.zeros(self.feature_dim)
        
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_tensor = self.transform(image_rgb).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            feature = self.model(image_tensor)
            feature = F.normalize(feature, p=2, dim=1)
        
        return feature.cpu().numpy().flatten()
    
    def compute_similarity(self, feature1: np.ndarray, feature2: np.ndarray) -> float:
        """计算两个特征向量的余弦相似度"""
        if feature1.size == 0 or feature2.size == 0:
            return 0.0
        
        similarity = np.dot(feature1, feature2) / (np.linalg.norm(feature1) * np.linalg.norm(feature2))
        return float(similarity)
    
    def match_person_in_video(
        self, 
        target_image_path: str, 
        video_path: str,
        tracks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """在视频中匹配目标人员"""
        logger.info(f"Matching person in video: {video_path}")
        
        target_feature = self.extract_feature(target_image_path)
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Failed to open video: {video_path}")
            return []
        
        matches = []
        
        for track in tracks:
            track_id = track.get("track_id")
            points = track.get("points", [])
            
            if not points:
                continue
            
            mid_idx = len(points) // 2
            mid_point = points[mid_idx]
            frame_num = mid_point.get("frame")
            bbox = mid_point.get("bbox")
            
            if not bbox or len(bbox) != 4:
                continue
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            
            if not ret:
                continue
            
            x1, y1, x2, y2 = map(int, bbox)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)
            
            cropped = frame[y1:y2, x1:x2]
            
            if cropped.size == 0:
                continue
            
            temp_path = f"/tmp/temp_track_{track_id}.jpg"
            cv2.imwrite(temp_path, cropped)
            
            track_feature = self.extract_feature(temp_path)
            similarity = self.compute_similarity(target_feature, track_feature)
            
            if similarity >= self.match_threshold:
                matches.append({
                    "track_id": track_id,
                    "frame": frame_num,
                    "confidence": similarity,
                    "bbox": bbox
                })
                logger.info(f"Match found: track_id={track_id}, confidence={similarity:.3f}")
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        cap.release()
        
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        
        return matches
