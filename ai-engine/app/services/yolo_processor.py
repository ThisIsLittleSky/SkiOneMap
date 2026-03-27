import os
import logging
import math
from typing import List, Dict, Any
import cv2

logger = logging.getLogger(__name__)


class YOLOProcessor:
    def __init__(self):
        self.model_path = os.getenv("YOLO_MODEL_PATH", "models/yolo11n.pt")
        self.tracker_config = self._resolve_tracker_config()
        self.conf_threshold = float(os.getenv("YOLO_CONF_THRESHOLD", "0.2"))
        self.iou_threshold = float(os.getenv("YOLO_IOU_THRESHOLD", "0.5"))
        self.min_track_frames = int(os.getenv("YOLO_MIN_TRACK_FRAMES", "8"))
        self.merge_gap_frames = int(os.getenv("YOLO_MERGE_GAP_FRAMES", "12"))
        self.merge_distance_threshold = float(os.getenv("YOLO_MERGE_DISTANCE_THRESHOLD", "120"))
        self.merge_direction_threshold = float(os.getenv("YOLO_MERGE_DIRECTION_THRESHOLD", "0.2"))
        self.slope_roi = self._parse_roi_polygon(
            os.getenv(
                "YOLO_SLOPE_ROI",
                "0.08,0.08;0.92,0.08;0.99,0.98;0.01,0.98",
            )
        )
        self.slope_roi_keep_ratio = float(os.getenv("YOLO_SLOPE_ROI_KEEP_RATIO", "0.55"))
        self.target_classes = self._parse_target_classes(
            os.getenv("YOLO_TARGET_CLASSES", "0")
        )
        self.model = None

    def _load_model(self):
        if self.model is None:
            from ultralytics import YOLO
            logger.info("Loading YOLO model from %s", self.model_path)
            self.model = YOLO(self.model_path)
            logger.info("YOLO model loaded successfully")

    def _resolve_tracker_config(self) -> str:
        tracker_config = os.getenv(
            "YOLO_TRACKER_CONFIG",
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "config",
                "trackers",
                "ski_bytetrack.yaml",
            ),
        )
        tracker_config = os.path.abspath(tracker_config)
        if os.path.exists(tracker_config):
            return tracker_config

        logger.warning(
            "Tracker config not found at %s, falling back to built-in bytetrack.yaml",
            tracker_config,
        )
        return "bytetrack.yaml"

    def _parse_target_classes(self, raw_value: str) -> List[int] | None:
        if not raw_value or not raw_value.strip():
            return None
        return [int(value.strip()) for value in raw_value.split(",") if value.strip()]

    def _parse_roi_polygon(self, raw_value: str) -> List[tuple[float, float]] | None:
        if not raw_value or not raw_value.strip():
            return None

        points: List[tuple[float, float]] = []
        for item in raw_value.split(";"):
            item = item.strip()
            if not item:
                continue
            x_str, y_str = item.split(",", maxsplit=1)
            points.append((float(x_str), float(y_str)))

        return points if len(points) >= 3 else None

    def _build_track_kwargs(self) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {
            "persist": True,
            "stream": True,
            "tracker": self.tracker_config,
            "conf": self.conf_threshold,
            "iou": self.iou_threshold,
            "verbose": False,
        }
        if self.target_classes is not None:
            kwargs["classes"] = self.target_classes
        return kwargs

    def _filter_tracks(self, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        filtered_tracks = [
            track for track in tracks if len(track.get("points", [])) >= self.min_track_frames
        ]
        removed_count = len(tracks) - len(filtered_tracks)
        if removed_count > 0:
            logger.info(
                "Filtered %d short tracks below %d frames",
                removed_count,
                self.min_track_frames,
            )
        return filtered_tracks

    def _read_video_size(self, video_path: str) -> tuple[int, int]:
        capture = cv2.VideoCapture(video_path)
        try:
            width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
            height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
            return width, height
        finally:
            capture.release()

    def _scale_roi_polygon(
        self,
        frame_width: int,
        frame_height: int,
    ) -> List[tuple[float, float]] | None:
        if not self.slope_roi or frame_width <= 0 or frame_height <= 0:
            return None

        return [
            (x * frame_width, y * frame_height)
            for x, y in self.slope_roi
        ]

    def _point_in_polygon(
        self,
        x: float,
        y: float,
        polygon: List[tuple[float, float]] | None,
    ) -> bool:
        if not polygon:
            return True

        inside = False
        point_count = len(polygon)
        for index in range(point_count):
            x1, y1 = polygon[index]
            x2, y2 = polygon[(index + 1) % point_count]
            intersects = ((y1 > y) != (y2 > y)) and (
                x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-9) + x1
            )
            if intersects:
                inside = not inside
        return inside

    def _filter_tracks_by_roi(
        self,
        tracks: List[Dict[str, Any]],
        roi_polygon: List[tuple[float, float]] | None,
    ) -> List[Dict[str, Any]]:
        if not roi_polygon:
            return tracks

        kept_tracks: List[Dict[str, Any]] = []
        removed_count = 0
        for track in tracks:
            points = track.get("points", [])
            if not points:
                continue

            inside_count = sum(
                1
                for point in points
                if self._point_in_polygon(point["x"], point["y"], roi_polygon)
            )
            inside_ratio = inside_count / len(points)
            if inside_ratio >= self.slope_roi_keep_ratio:
                kept_tracks.append(track)
            else:
                removed_count += 1

        if removed_count > 0:
            logger.info(
                "Filtered %d tracks outside slope ROI (keep ratio %.2f)",
                removed_count,
                self.slope_roi_keep_ratio,
            )
        return kept_tracks

    def _track_frame_range(self, track: Dict[str, Any]) -> tuple[int, int]:
        points = track.get("points", [])
        return points[0]["frame"], points[-1]["frame"]

    def _avg_box_size(self, point_a: Dict[str, Any], point_b: Dict[str, Any]) -> float:
        width = (point_a.get("width", 0.0) + point_b.get("width", 0.0)) / 2
        height = (point_a.get("height", 0.0) + point_b.get("height", 0.0)) / 2
        return math.sqrt(width * width + height * height)

    def _distance(self, point_a: Dict[str, Any], point_b: Dict[str, Any]) -> float:
        return math.sqrt(
            (point_a["x"] - point_b["x"]) ** 2 +
            (point_a["y"] - point_b["y"]) ** 2
        )

    def _estimate_motion_vector(self, points: List[Dict[str, Any]], from_tail: bool) -> tuple[float, float] | None:
        if len(points) < 2:
            return None

        window = points[-3:] if from_tail else points[:3]
        dx = 0.0
        dy = 0.0
        count = 0
        for index in range(1, len(window)):
            dx += window[index]["x"] - window[index - 1]["x"]
            dy += window[index]["y"] - window[index - 1]["y"]
            count += 1
        if count == 0:
            return None
        return dx / count, dy / count

    def _predict_next_point(
        self,
        last_point: Dict[str, Any],
        velocity: tuple[float, float] | None,
        gap_frames: int,
    ) -> Dict[str, Any]:
        if velocity is None:
            return last_point
        vx, vy = velocity
        return {
            **last_point,
            "x": last_point["x"] + vx * gap_frames,
            "y": last_point["y"] + vy * gap_frames,
        }

    def _direction_similarity(
        self,
        track_a: Dict[str, Any],
        track_b: Dict[str, Any],
    ) -> float:
        vector_a = self._estimate_motion_vector(track_a["points"], from_tail=True)
        vector_b = self._estimate_motion_vector(track_b["points"], from_tail=False)
        if vector_a is None or vector_b is None:
            return 1.0

        ax, ay = vector_a
        bx, by = vector_b
        norm_a = math.sqrt(ax * ax + ay * ay)
        norm_b = math.sqrt(bx * bx + by * by)
        if norm_a == 0 or norm_b == 0:
            return 1.0
        return (ax * bx + ay * by) / (norm_a * norm_b)

    def _can_merge_tracks(
        self,
        track_a: Dict[str, Any],
        track_b: Dict[str, Any],
    ) -> tuple[bool, float]:
        if track_a.get("className") != track_b.get("className"):
            return False, float("inf")

        _, end_frame = self._track_frame_range(track_a)
        start_frame, _ = self._track_frame_range(track_b)
        gap_frames = start_frame - end_frame
        if gap_frames <= 0 or gap_frames > self.merge_gap_frames:
            return False, float("inf")

        end_point = track_a["points"][-1]
        start_point = track_b["points"][0]
        predicted_point = self._predict_next_point(
            end_point,
            self._estimate_motion_vector(track_a["points"], from_tail=True),
            gap_frames,
        )
        distance = self._distance(predicted_point, start_point)
        adaptive_threshold = max(
            self.merge_distance_threshold,
            self._avg_box_size(end_point, start_point) * 1.5,
        )
        if distance > adaptive_threshold:
            return False, distance

        direction_similarity = self._direction_similarity(track_a, track_b)
        if direction_similarity < self.merge_direction_threshold:
            return False, distance

        return True, distance

    def _merge_track_pair(
        self,
        track_a: Dict[str, Any],
        track_b: Dict[str, Any],
    ) -> Dict[str, Any]:
        merged_points = sorted(
            [*track_a["points"], *track_b["points"]],
            key=lambda point: point["frame"],
        )
        return {
            **track_a,
            "points": merged_points,
        }

    def _merge_broken_tracks(self, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(tracks) < 2:
            return tracks

        working_tracks = [
            {
                **track,
                "points": sorted(track.get("points", []), key=lambda point: point["frame"]),
            }
            for track in tracks
        ]
        working_tracks.sort(key=lambda track: self._track_frame_range(track)[0])

        merged_any = True
        while merged_any:
            merged_any = False
            next_tracks: List[Dict[str, Any]] = []
            used_indices: set[int] = set()

            for index, track in enumerate(working_tracks):
                if index in used_indices:
                    continue

                best_index = None
                best_distance = float("inf")
                for candidate_index in range(index + 1, len(working_tracks)):
                    if candidate_index in used_indices:
                        continue
                    can_merge, distance = self._can_merge_tracks(track, working_tracks[candidate_index])
                    if can_merge and distance < best_distance:
                        best_index = candidate_index
                        best_distance = distance

                if best_index is not None:
                    track = self._merge_track_pair(track, working_tracks[best_index])
                    used_indices.add(best_index)
                    merged_any = True

                next_tracks.append(track)

            working_tracks = sorted(
                next_tracks,
                key=lambda track: self._track_frame_range(track)[0],
            )

        merged_count = len(tracks) - len(working_tracks)
        if merged_count > 0:
            logger.info("Merged %d broken track segments", merged_count)
        return working_tracks

    def process_video(self, video_path: str) -> List[Dict[str, Any]]:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        self._load_model()
        logger.info("Processing video: %s", video_path)
        frame_width, frame_height = self._read_video_size(video_path)
        roi_polygon = self._scale_roi_polygon(frame_width, frame_height)

        results = self.model.track(source=video_path, **self._build_track_kwargs())

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

        merged_tracks = self._merge_broken_tracks(list(tracks.values()))
        roi_filtered_tracks = self._filter_tracks_by_roi(merged_tracks, roi_polygon)
        filtered_tracks = self._filter_tracks(roi_filtered_tracks)
        logger.info(
            "Video processing complete: %d frames, %d raw tracks, %d merged tracks, %d ROI tracks, %d retained tracks",
            frame_idx,
            len(tracks),
            len(merged_tracks),
            len(roi_filtered_tracks),
            len(filtered_tracks),
        )
        return filtered_tracks
