import os
import logging
from typing import List, Dict, Any
from app.services.rag_engine import RAGEngine

logger = logging.getLogger(__name__)


class RoutePredictor:
    def __init__(self):
        self.rag_engine = RAGEngine()
    
    def predict_route(
        self, 
        current_camera: Dict[str, Any],
        all_cameras: List[Dict[str, Any]],
        match_info: Dict[str, Any]
    ) -> str:
        """基于摄像头位置和描述预测人员可能的移动路线"""
        logger.info(f"Predicting route from camera: {current_camera.get('name')}")
        
        camera_info = self._format_camera_info(current_camera, all_cameras)
        
        prompt = f"""你是一个滑雪场监控分析专家。根据以下信息，预测目标人员可能的移动路线。

当前检测位置：
- 摄像头名称：{current_camera.get('name', '未知')}
- 摄像头描述：{current_camera.get('description', '无描述')}
- 位置坐标：({current_camera.get('pos_x', 0)}, {current_camera.get('pos_y', 0)}, {current_camera.get('pos_z', 0)})

匹配信息：
- 置信度：{match_info.get('confidence', 0):.2f}
- 检测时间：第{match_info.get('frame', 0)}帧

周边摄像头信息：
{camera_info}

请分析：
1. 该人员最可能前往的3个位置（按概率排序）
2. 每个位置的理由
3. 建议重点监控的摄像头

请用简洁的中文回答，不超过200字。"""

        try:
            response = self.rag_engine.llm_client.chat.completions.create(
                model=self.rag_engine.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=300
            )
            
            route_prediction = response.choices[0].message.content.strip()
            logger.info(f"Route prediction completed: {route_prediction[:50]}...")
            return route_prediction
            
        except Exception as e:
            logger.error(f"Failed to predict route: {e}")
            return "路线预测失败"
    
    def _format_camera_info(self, current_camera: Dict[str, Any], all_cameras: List[Dict[str, Any]]) -> str:
        """格式化摄像头信息"""
        current_pos = (
            current_camera.get('pos_x', 0),
            current_camera.get('pos_y', 0),
            current_camera.get('pos_z', 0)
        )
        
        camera_list = []
        for cam in all_cameras:
            if cam.get('id') == current_camera.get('id'):
                continue
            
            cam_pos = (cam.get('pos_x', 0), cam.get('pos_y', 0), cam.get('pos_z', 0))
            distance = self._calculate_distance(current_pos, cam_pos)
            
            camera_list.append({
                'name': cam.get('name', '未知'),
                'description': cam.get('description', '无描述'),
                'distance': distance
            })
        
        camera_list.sort(key=lambda x: x['distance'])
        
        info_lines = []
        for i, cam in enumerate(camera_list[:5], 1):
            info_lines.append(
                f"{i}. {cam['name']} - {cam['description']} (距离: {cam['distance']:.1f}m)"
            )
        
        return "\n".join(info_lines) if info_lines else "无周边摄像头信息"
    
    def _calculate_distance(self, pos1: tuple, pos2: tuple) -> float:
        """计算两点间的欧氏距离"""
        import math
        return math.sqrt(
            (pos1[0] - pos2[0]) ** 2 +
            (pos1[1] - pos2[1]) ** 2 +
            (pos1[2] - pos2[2]) ** 2
        )
