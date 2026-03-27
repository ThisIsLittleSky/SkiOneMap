import os
import logging
import shutil
import subprocess
from collections import defaultdict
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class VideoAnnotator:
    def __init__(self):
        self.output_root = os.getenv("ANNOTATED_VIDEO_PATH", os.path.join("data", "annotated"))
        self.alert_hold_frames = int(os.getenv("ANNOTATED_ALERT_HOLD_FRAMES", 18))
        self.trajectory_length = int(os.getenv("ANNOTATED_TRAJECTORY_LENGTH", 20))
        self.ffmpeg_path = shutil.which(os.getenv("FFMPEG_BIN", "ffmpeg"))

    def annotate_video(
        self,
        video_path: str,
        task_id: int,
        tracks: List[Dict[str, Any]],
        alerts: List[Dict[str, Any]],
    ) -> str:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        capture = cv2.VideoCapture(video_path)
        if not capture.isOpened():
            raise RuntimeError(f"Failed to open video: {video_path}")

        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0) or 25.0
        if width <= 0 or height <= 0:
            capture.release()
            raise RuntimeError(f"Invalid video size: {video_path}")

        output_path = self._build_output_path(video_path, task_id)
        temp_output_path = self._build_temp_output_path(output_path)
        writer = cv2.VideoWriter(
            temp_output_path,
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (width, height),
        )
        if not writer.isOpened():
            capture.release()
            raise RuntimeError(f"Failed to create annotated video: {temp_output_path}")

        points_by_frame, history_by_track = self._build_track_indexes(tracks)
        alerts_by_frame = self._build_alert_index(alerts)
        alert_counts = self._count_alert_types(alerts)

        frame_idx = 0
        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break

                overlay = frame.copy()
                self._draw_header(
                    overlay,
                    task_id,
                    frame_idx,
                    len(tracks),
                    len(alerts),
                    alert_counts,
                )

                for item in points_by_frame.get(frame_idx, []):
                    color = self._track_color(item["trackId"])
                    self._draw_track_box(overlay, item, color)
                    self._draw_track_path(
                        overlay,
                        history_by_track.get(item["trackId"], []),
                        frame_idx,
                        color,
                    )

                active_alerts = alerts_by_frame.get(frame_idx, [])
                for index, alert in enumerate(active_alerts):
                    self._draw_alert_marker(overlay, alert, index, width)

                frame = cv2.addWeighted(overlay, 0.96, frame, 0.04, 0)
                writer.write(frame)
                frame_idx += 1
        finally:
            capture.release()
            writer.release()

        self._transcode_to_browser_video(temp_output_path, output_path)
        logger.info("Annotated video generated for task %d: %s", task_id, output_path)
        return output_path

    def _build_output_path(self, video_path: str, task_id: int) -> str:
        output_dir = os.path.abspath(self.output_root)
        os.makedirs(output_dir, exist_ok=True)

        base_name = os.path.splitext(os.path.basename(video_path))[0]
        return os.path.join(output_dir, f"{base_name}_task{task_id}_annotated.mp4")

    def _build_temp_output_path(self, output_path: str) -> str:
        root, ext = os.path.splitext(output_path)
        return f"{root}_render{ext}"

    def _transcode_to_browser_video(self, temp_output_path: str, output_path: str):
        if not self.ffmpeg_path:
            raise RuntimeError("ffmpeg not found; cannot transcode annotated video to browser-compatible H.264")

        command = [
            self.ffmpeg_path,
            "-y",
            "-i",
            temp_output_path,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "-an",
            output_path,
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            raise RuntimeError(f"Failed to transcode annotated video: {stderr}") from exc
        finally:
            if os.path.exists(temp_output_path):
                os.remove(temp_output_path)

    def _build_track_indexes(
        self, tracks: List[Dict[str, Any]]
    ) -> Tuple[Dict[int, List[Dict[str, Any]]], Dict[int, List[Dict[str, Any]]]]:
        points_by_frame: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        history_by_track: Dict[int, List[Dict[str, Any]]] = {}

        for track in tracks:
            track_id = track["trackId"]
            points = sorted(track.get("points", []), key=lambda p: p["frame"])
            history_by_track[track_id] = points
            for point in points:
                points_by_frame[point["frame"]].append(
                    {
                        "trackId": track_id,
                        "className": track.get("className", "person"),
                        **point,
                    }
                )

        return points_by_frame, history_by_track

    def _build_alert_index(self, alerts: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
        alerts_by_frame: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for alert in alerts:
            start_frame = int(alert.get("frame", 0))
            for frame in range(start_frame, start_frame + self.alert_hold_frames):
                alerts_by_frame[frame].append(alert)
        return alerts_by_frame

    def _count_alert_types(self, alerts: List[Dict[str, Any]]) -> Dict[str, int]:
        counts: Dict[str, int] = defaultdict(int)
        for alert in alerts:
            counts[alert.get("alertType", "UNKNOWN")] += 1
        return dict(counts)

    def _draw_header(
        self,
        frame: np.ndarray,
        task_id: int,
        frame_idx: int,
        track_count: int,
        alert_count: int,
        alert_counts: Dict[str, int],
    ):
        cv2.rectangle(frame, (16, 16), (520, 110), (12, 28, 45), -1)
        cv2.rectangle(frame, (16, 16), (520, 110), (70, 130, 190), 2)
        cv2.putText(frame, f"Ski AI Task #{task_id}", (30, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (240, 245, 255), 2)
        cv2.putText(frame, f"Frame: {frame_idx}", (30, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (160, 215, 255), 2)
        cv2.putText(frame, f"Tracks: {track_count}  Alerts: {alert_count}", (200, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (160, 215, 255), 2)

        if alert_counts:
            summary = " | ".join(f"{self._alert_label(k)}:{v}" for k, v in sorted(alert_counts.items()))
            cv2.putText(frame, summary[:54], (30, 98), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 210, 130), 1)

    def _draw_track_box(self, frame: np.ndarray, item: Dict[str, Any], color: Tuple[int, int, int]):
        half_w = max(int(item.get("width", 0) / 2), 12)
        half_h = max(int(item.get("height", 0) / 2), 18)
        x = int(item["x"])
        y = int(item["y"])
        x1, y1 = max(0, x - half_w), max(0, y - half_h)
        x2, y2 = x + half_w, y + half_h

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"#{item['trackId']} {item.get('className', 'person')}"
        self._put_text_box(frame, label, (x1, max(24, y1 - 10)), color)

    def _draw_track_path(
        self,
        frame: np.ndarray,
        history: List[Dict[str, Any]],
        frame_idx: int,
        color: Tuple[int, int, int],
    ):
        recent = [p for p in history if p["frame"] <= frame_idx][-self.trajectory_length:]
        if len(recent) < 2:
            return

        for i in range(1, len(recent)):
            p1 = (int(recent[i - 1]["x"]), int(recent[i - 1]["y"]))
            p2 = (int(recent[i]["x"]), int(recent[i]["y"]))
            cv2.line(frame, p1, p2, color, 2)

        p1 = (int(recent[-2]["x"]), int(recent[-2]["y"]))
        p2 = (int(recent[-1]["x"]), int(recent[-1]["y"]))
        cv2.arrowedLine(frame, p1, p2, color, 2, tipLength=0.28)

    def _draw_alert_marker(
        self,
        frame: np.ndarray,
        alert: Dict[str, Any],
        index: int,
        frame_width: int,
    ):
        x = int(alert.get("positionX", 0))
        y = int(alert.get("positionY", 0))
        severity = alert.get("severity", "WARNING")
        label = self._alert_label(alert.get("alertType", "UNKNOWN"))
        color = (48, 65, 255) if severity == "DANGER" else (0, 180, 255)

        cv2.circle(frame, (x, y), 12, color, 2)
        cv2.circle(frame, (x, y), 4, color, -1)
        self._put_text_box(frame, label, (x + 16, max(24, y - 12)), color)

        notice_x = max(frame_width - 340, 16)
        notice_y = 36 + index * 30
        self._put_text_box(frame, f"{label} @ F{alert.get('frame', 0)}", (notice_x, notice_y), color)

    def _put_text_box(
        self,
        frame: np.ndarray,
        text: str,
        position: Tuple[int, int],
        color: Tuple[int, int, int],
    ):
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.5
        thickness = 1
        (text_w, text_h), _ = cv2.getTextSize(text, font, scale, thickness)
        x, y = position
        cv2.rectangle(frame, (x - 4, y - text_h - 8), (x + text_w + 6, y + 4), (8, 18, 28), -1)
        cv2.rectangle(frame, (x - 4, y - text_h - 8), (x + text_w + 6, y + 4), color, 1)
        cv2.putText(frame, text, (x, y - 4), font, scale, (245, 245, 245), thickness, cv2.LINE_AA)

    def _track_color(self, track_id: int) -> Tuple[int, int, int]:
        palette = [
            (79, 195, 247),
            (255, 183, 77),
            (129, 199, 132),
            (240, 98, 146),
            (186, 104, 200),
            (255, 241, 118),
        ]
        return palette[track_id % len(palette)]

    def _alert_label(self, alert_type: str) -> str:
        return {
            "WRONG_WAY": "Wrong Way",
            "OVERSPEED": "Overspeed",
            "COLLISION_RISK": "Collision Risk",
            "STILL_DETECTED": "Fall Risk",
        }.get(alert_type, alert_type.replace("_", " ").title())
