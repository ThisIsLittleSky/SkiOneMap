import logging
import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# HSV color ranges for common clothing colors
COLOR_RANGES: Dict[str, List[Tuple[np.ndarray, np.ndarray]]] = {
    "红色": [
        (np.array([0, 70, 50]), np.array([10, 255, 255])),
        (np.array([170, 70, 50]), np.array([180, 255, 255])),
    ],
    "橙色": [
        (np.array([10, 70, 50]), np.array([25, 255, 255])),
    ],
    "黄色": [
        (np.array([25, 70, 50]), np.array([35, 255, 255])),
    ],
    "绿色": [
        (np.array([35, 70, 50]), np.array([85, 255, 255])),
    ],
    "蓝色": [
        (np.array([85, 70, 50]), np.array([130, 255, 255])),
    ],
    "紫色": [
        (np.array([130, 70, 50]), np.array([170, 255, 255])),
    ],
    "白色": [
        (np.array([0, 0, 180]), np.array([180, 50, 255])),
    ],
    "黑色": [
        (np.array([0, 0, 0]), np.array([180, 80, 60])),
    ],
    "灰色": [
        (np.array([0, 0, 60]), np.array([180, 50, 180])),
    ],
    "粉色": [
        (np.array([0, 20, 150]), np.array([10, 70, 255])),
        (np.array([170, 20, 150]), np.array([180, 70, 255])),
    ],
}

COLOR_NAME_TO_EN: Dict[str, str] = {
    "红色": "red", "橙色": "orange", "黄色": "yellow",
    "绿色": "green", "蓝色": "blue", "紫色": "purple",
    "白色": "white", "黑色": "black", "灰色": "gray", "粉色": "pink",
}

EN_TO_COLOR_NAME: Dict[str, str] = {v: k for k, v in COLOR_NAME_TO_EN.items()}


class ColorExtractor:
    """Extract dominant clothing color from a person cropped image."""

    def extract_dominant_color(self, image_or_path) -> Optional[str]:
        if isinstance(image_or_path, str):
            image = cv2.imread(image_or_path)
        else:
            image = image_or_path

        if image is None or image.size == 0:
            return None

        h, w = image.shape[:2]
        # Focus on the torso area (upper 60%, center 70%) to capture clothing
        y_start = int(h * 0.1)
        y_end = int(h * 0.6)
        x_start = int(w * 0.15)
        x_end = int(w * 0.85)
        torso = image[y_start:y_end, x_start:x_end]

        if torso.size == 0:
            torso = image

        hsv = cv2.cvtColor(torso, cv2.COLOR_BGR2HSV)
        total_pixels = hsv.shape[0] * hsv.shape[1]
        if total_pixels == 0:
            return None

        color_ratios: Dict[str, float] = {}
        for color_name, ranges in COLOR_RANGES.items():
            mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            for lower, upper in ranges:
                mask |= cv2.inRange(hsv, lower, upper)
            ratio = float(np.count_nonzero(mask)) / total_pixels
            color_ratios[color_name] = ratio

        if not color_ratios:
            return None

        dominant = max(color_ratios, key=color_ratios.get)
        ratio = color_ratios[dominant]

        if ratio < 0.08:
            return None

        en_name = COLOR_NAME_TO_EN.get(dominant, dominant)
        logger.info(f"Dominant color: {dominant}({en_name}), ratio={ratio:.2%}")
        return en_name

    def extract_color_distribution(self, image_or_path) -> Dict[str, float]:
        if isinstance(image_or_path, str):
            image = cv2.imread(image_or_path)
        else:
            image = image_or_path

        if image is None or image.size == 0:
            return {}

        h, w = image.shape[:2]
        y_start = int(h * 0.1)
        y_end = int(h * 0.6)
        x_start = int(w * 0.15)
        x_end = int(w * 0.85)
        torso = image[y_start:y_end, x_start:x_end]
        if torso.size == 0:
            torso = image

        hsv = cv2.cvtColor(torso, cv2.COLOR_BGR2HSV)
        total_pixels = hsv.shape[0] * hsv.shape[1]
        if total_pixels == 0:
            return {}

        distribution: Dict[str, float] = {}
        for color_name, ranges in COLOR_RANGES.items():
            mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            for lower, upper in ranges:
                mask |= cv2.inRange(hsv, lower, upper)
            ratio = float(np.count_nonzero(mask)) / total_pixels
            if ratio > 0.03:
                en_name = COLOR_NAME_TO_EN.get(color_name, color_name)
                distribution[en_name] = round(ratio, 4)

        return distribution

    def match_color(self, target_color: str, image_or_path) -> float:
        en_color = target_color.lower()
        cn_color = EN_TO_COLOR_NAME.get(en_color)
        if not cn_color:
            cn_color = target_color
            en_color = COLOR_NAME_TO_EN.get(cn_color)

        ranges = COLOR_RANGES.get(cn_color)
        if not ranges:
            return 0.0

        if isinstance(image_or_path, str):
            image = cv2.imread(image_or_path)
        else:
            image = image_or_path

        if image is None or image.size == 0:
            return 0.0

        h, w = image.shape[:2]
        y_start = int(h * 0.1)
        y_end = int(h * 0.6)
        x_start = int(w * 0.15)
        x_end = int(w * 0.85)
        torso = image[y_start:y_end, x_start:x_end]
        if torso.size == 0:
            torso = image

        hsv = cv2.cvtColor(torso, cv2.COLOR_BGR2HSV)
        total_pixels = hsv.shape[0] * hsv.shape[1]
        if total_pixels == 0:
            return 0.0

        mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for lower, upper in ranges:
            mask |= cv2.inRange(hsv, lower, upper)

        return float(np.count_nonzero(mask)) / total_pixels
