from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import os
import json
import requests
import cv2
import subprocess
import shutil

from app.services.person_extractor import PersonExtractor
from app.services.person_reidentification import PersonReIdentification
from app.services.appearance_analyzer import AppearanceAnalyzer
from app.services.route_predictor import RoutePredictor
from app.services.yolo_processor import YOLOProcessor
from app.services.color_extractor import ColorExtractor

logger = logging.getLogger(__name__)

router = APIRouter()


class ExtractPersonsRequest(BaseModel):
    video_id: int


class MatchPersonRequest(BaseModel):
    task_id: int


class TrackingExecuteRequest(BaseModel):
    task_id: int


class ColorSearchRequest(BaseModel):
    target_color: str
    camera_ids: List[int]
    min_color_ratio: float = 0.10


@router.post("/tracking/extract-persons")
async def extract_persons(request: ExtractPersonsRequest):
    """从视频中提取所有人员"""
    try:
        video_id = request.video_id
        backend_url = os.getenv("BACKEND_URL", "http://localhost:8080")
        
        video_response = requests.get(f"{backend_url}/api/video/{video_id}")
        video_response.raise_for_status()
        video_data = video_response.json()
        video_path = video_data.get("filepath")
        
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Video file not found")
        
        task_response = requests.get(f"{backend_url}/api/task/list")
        tasks = task_response.json()
        
        task = None
        for t in tasks:
            if t.get("videoId") == video_id and t.get("status") == "COMPLETED":
                task = t
                break
        
        tracks = []
        if task and task.get("result"):
            result_raw = task.get("result", "{}")
            if isinstance(result_raw, str):
                result = json.loads(result_raw)
            else:
                result = result_raw
            if isinstance(result, dict):
                tracks = result.get("tracks", [])
            else:
                logger.warning(f"Expected dict for task result, got {type(result).__name__}")
        
        if not tracks:
            logger.info(f"No tracks in task result, running YOLO for video {video_id}")
            processor = YOLOProcessor()
            tracks = processor.process_video(video_path)
        
        extractor = PersonExtractor()
        persons = extractor.extract_persons_from_video(video_id, video_path, tracks)
        
        return {"status": "success", "persons": persons, "count": len(persons)}
        
    except Exception as e:
        import traceback
        logger.error(f"Failed to extract persons: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tracking/execute")
async def execute_tracking(request: TrackingExecuteRequest):
    """执行追踪任务"""
    try:
        task_id = request.task_id
        backend_url = os.getenv("BACKEND_URL", "http://localhost:8080")
        
        task_response = requests.get(f"{backend_url}/api/tracking/internal/task/{task_id}")
        task_response.raise_for_status()
        task_data = task_response.json()
        logger.info(f"Task data type={type(task_data).__name__}, value={task_data}")
        
        if isinstance(task_data, str):
            task_data = json.loads(task_data)
        
        video_id = task_data.get("videoId")
        target_track_id = task_data.get("targetTrackId")
        camera_ids = task_data.get("cameraIds", [])
        
        video_response = requests.get(f"{backend_url}/api/video/{video_id}")
        video_response.raise_for_status()
        video_data = video_response.json()
        logger.info(f"Video data type={type(video_data).__name__}")
        
        if isinstance(video_data, str):
            video_data = json.loads(video_data)
        video_path = video_data.get("filepath")
        
        target_person_response = requests.get(
            f"{backend_url}/api/tracking/persons/{video_id}/{target_track_id}"
        )
        target_person_response.raise_for_status()
        target_person = target_person_response.json()
        logger.info(f"Target person type={type(target_person).__name__}, value={target_person}")
        
        if isinstance(target_person, str):
            target_person = json.loads(target_person)
        target_image_url_path = target_person.get("croppedImagePath")
        
        if not target_image_url_path:
            raise HTTPException(status_code=404, detail="Target person image path not found")
        
        # Convert URL path to file system path
        persons_dir = os.getenv("TRACKING_PERSONS_DIR", "data/tracking/persons")
        if not os.path.isabs(persons_dir):
            # Make it absolute relative to the ai-engine directory (3 levels up from this file)
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            persons_dir = os.path.join(base_dir, persons_dir)
        
        image_filename = os.path.basename(target_image_url_path)
        target_image_path = os.path.join(persons_dir, image_filename)
        
        if not os.path.exists(target_image_path):
            raise HTTPException(status_code=404, detail=f"Target person image not found: {target_image_path}")
        
        reid = PersonReIdentification()
        appearance_analyzer = AppearanceAnalyzer()
        route_predictor = RoutePredictor()
        processor = YOLOProcessor()
        
        cameras_response = requests.get(f"{backend_url}/api/tracking/cameras")
        cameras_response.raise_for_status()
        all_cameras = cameras_response.json()
        logger.info(f"Cameras type={type(all_cameras).__name__}, count={len(all_cameras) if isinstance(all_cameras, list) else 'N/A'}")
        
        if isinstance(all_cameras, str):
            all_cameras = json.loads(all_cameras)
        
        results = []
        
        for camera_id in camera_ids:
            camera = next((c for c in all_cameras if c.get("id") == camera_id), None)
            if not camera:
                continue
            
            videos_response = requests.get(f"{backend_url}/api/video/search", params={"cameraId": camera_id})
            videos_response.raise_for_status()
            camera_videos = videos_response.json()
            logger.info(f"Camera videos type={type(camera_videos).__name__} for camera {camera_id}")
            
            if not isinstance(camera_videos, list):
                logger.warning(f"Expected list of videos, got {type(camera_videos).__name__}: {camera_videos}")
                continue
            
            for video in camera_videos:
                cam_video_path = video.get("filepath")
                if not cam_video_path or not os.path.exists(cam_video_path):
                    continue
                
                tracks = processor.process_video(cam_video_path)
                
                matches = reid.match_person_in_video(target_image_path, cam_video_path, tracks)
                
                for match in matches:
                    appearance = appearance_analyzer.analyze_appearance(
                        target_image_path, match
                    )
                    
                    predicted_route = route_predictor.predict_route(
                        camera, all_cameras, match
                    )
                    
                    result = {
                        "tracking_task_id": task_id,
                        "camera_id": camera_id,
                        "video_id": video.get("id"),
                        "found_at_frame": match.get("frame"),
                        "confidence": match.get("confidence"),
                        "appearance_features": appearance,
                        "predicted_route": predicted_route
                    }
                    
                    results.append(result)
        
        save_response = requests.post(
            f"{backend_url}/api/tracking/results/batch",
            json={"task_id": task_id, "results": results}
        )
        save_response.raise_for_status()
        
        update_response = requests.put(
            f"{backend_url}/api/tracking/tasks/{task_id}/status",
            json={"status": "COMPLETED"}
        )
        
        return {"status": "success", "task_id": task_id, "matches": len(results)}
        
    except Exception as e:
        import traceback
        logger.error(f"Failed to execute tracking: {e}\n{traceback.format_exc()}")
        
        try:
            backend_url = os.getenv("BACKEND_URL", "http://localhost:8080")
            requests.put(
                f"{backend_url}/api/tracking/tasks/{request.task_id}/status",
                json={"status": "FAILED"}
            )
        except:
            pass
        
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tracking/search-by-color")
async def search_by_color(request: ColorSearchRequest):
    """根据衣服颜色搜索所有匹配的滑雪者，返回截图和视频片段信息供用户选择"""
    try:
        target_color = request.target_color.lower()
        camera_ids = request.camera_ids
        min_ratio = request.min_color_ratio
        backend_url = os.getenv("BACKEND_URL", "http://localhost:8080")
        
        color_extractor = ColorExtractor()
        persons_dir = os.getenv("TRACKING_PERSONS_DIR", "data/tracking/persons")
        if not os.path.isabs(persons_dir):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            persons_dir = os.path.join(base_dir, persons_dir)
        
        matches = []
        
        for camera_id in camera_ids:
            videos_response = requests.get(
                f"{backend_url}/api/video/search", params={"cameraId": camera_id}
            )
            videos_response.raise_for_status()
            camera_videos = videos_response.json()
            
            if not isinstance(camera_videos, list):
                continue
            
            for video in camera_videos:
                video_id = video.get("id")
                cam_video_path = video.get("filepath")
                if not cam_video_path or not os.path.exists(cam_video_path):
                    continue
                
                try:
                    persons_response = requests.get(
                        f"{backend_url}/api/tracking/persons/{video_id}",
                        params={"extract": "false"}
                    )
                    persons_response.raise_for_status()
                    persons = persons_response.json()
                except Exception as e:
                    logger.warning(f"Failed to fetch persons for video {video_id}: {e}")
                    continue
                
                if not persons:
                    continue
                
                for person in persons:
                    image_url_path = person.get("croppedImagePath")
                    if not image_url_path:
                        continue
                    
                    image_filename = os.path.basename(image_url_path)
                    image_path = os.path.join(persons_dir, image_filename)
                    
                    if not os.path.exists(image_path):
                        continue
                    
                    color_ratio = color_extractor.match_color(target_color, image_path)
                    
                    if color_ratio >= min_ratio:
                        first_frame = person.get("firstFrame", 0)
                        last_frame = person.get("lastFrame", 0)
                        
                        clip_filename = f"clip_v{video_id}_t{person.get('trackId')}_{target_color}.mp4"
                        clip_path = os.path.join(persons_dir, clip_filename)
                        
                        _extract_video_clip(
                            cam_video_path, clip_path, first_frame, last_frame
                        )
                        
                        matches.append({
                            "person_id": person.get("id"),
                            "video_id": video_id,
                            "camera_id": camera_id,
                            "track_id": person.get("trackId"),
                            "cropped_image_path": image_url_path,
                            "clip_path": f"/ai/tracking/persons/{clip_filename}" if os.path.exists(clip_path) else None,
                            "color_ratio": round(color_ratio, 4),
                            "dominant_color": person.get("dominantColor"),
                            "first_frame": first_frame,
                            "last_frame": last_frame,
                            "frame_count": person.get("frameCount", 0),
                        })
        
        matches.sort(key=lambda x: x["color_ratio"], reverse=True)
        
        return {
            "status": "success",
            "target_color": target_color,
            "matches": matches,
            "count": len(matches),
        }
    
    except Exception as e:
        import traceback
        logger.error(f"Failed to search by color: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


def _extract_video_clip(
    video_path: str, output_path: str, start_frame: int, end_frame: int
):
    """Extract a short video clip from the source video."""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return
        
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        pad_frames = int(fps)
        clip_start = max(0, start_frame - pad_frames)
        clip_end = end_frame + pad_frames
        
        temp_output_path = output_path
        final_output_path = output_path
        ffmpeg_path = shutil.which(os.getenv("FFMPEG_BIN", "ffmpeg"))
        if ffmpeg_path:
            base, ext = os.path.splitext(output_path)
            temp_output_path = f"{base}.raw{ext}"

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(temp_output_path, fourcc, fps, (width, height))
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, clip_start)
        frame_idx = clip_start
        
        while frame_idx <= clip_end:
            ret, frame = cap.read()
            if not ret:
                break
            writer.write(frame)
            frame_idx += 1
        
        writer.release()
        cap.release()

        if ffmpeg_path and os.path.exists(temp_output_path):
            cmd = [
                ffmpeg_path,
                "-y",
                "-i",
                temp_output_path,
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                "-an",
                final_output_path,
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            if temp_output_path != final_output_path and os.path.exists(temp_output_path):
                os.remove(temp_output_path)
    except Exception as e:
        logger.error(f"Failed to extract video clip: {e}")
