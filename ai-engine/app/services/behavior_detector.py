"""
危险行为检测模块
检测逆行、超速、碰撞风险、静止（摔倒）四类危险行为
"""
import math
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# ── 可调参数 ──────────────────────────────────────────────────────────────────
# 逆行：主流方向（y 递增 = 从上往下滑），连续多少帧逆向才触发
WRONG_WAY_FRAMES = 8          # 连续逆向帧数阈值
WRONG_WAY_MIN_DISPLACEMENT = 3.0  # 每帧最小位移（像素），过小不计

# 超速：相邻帧位移阈值（像素/帧），超过即预警
SPEED_THRESHOLD = 40.0        # 正常阈值；视频分辨率不同可调整
SPEED_FRAMES = 5              # 连续超速帧数才触发

# 碰撞风险：两轨迹质心欧氏距离 < 阈值 && 相向运动
COLLISION_DIST_THRESHOLD = 60.0   # 像素距离
COLLISION_APPROACH_FRAMES = 3     # 连续接近帧数

# 静止（摔倒）：轨迹位移连续 N 帧 < 阈值
STILL_DIST_THRESHOLD = 2.0    # 几乎不动
STILL_FRAMES = 30             # 连续静止帧数（约 1 秒 @ 30fps）
# ─────────────────────────────────────────────────────────────────────────────


def _dist(p1: Dict, p2: Dict) -> float:
    return math.sqrt((p1["x"] - p2["x"]) ** 2 + (p1["y"] - p2["y"]) ** 2)


def _dy(p1: Dict, p2: Dict) -> float:
    """p2 相对 p1 的 y 轴位移（正值 = 向下滑，符合主流方向）"""
    return p2["y"] - p1["y"]


def detect_wrong_way(track: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    逆行检测：y 轴位移持续为负（向上），且位移足够大。

    算法：
      滑行主流方向为 y 增大（摄像头俯视，滑雪者从上往下）。
      对每对相邻帧计算 dy = y[i+1] - y[i]；
      若 dy < -WRONG_WAY_MIN_DISPLACEMENT，则记为逆向帧；
      连续 WRONG_WAY_FRAMES 帧逆向即触发一次预警，记录触发点。
    """
    points = track["points"]
    alerts = []
    consecutive = 0
    triggered_frames = set()

    for i in range(1, len(points)):
        dy = _dy(points[i - 1], points[i])
        if dy < -WRONG_WAY_MIN_DISPLACEMENT:
            consecutive += 1
        else:
            consecutive = 0

        if consecutive >= WRONG_WAY_FRAMES:
            trigger_frame = points[i]["frame"]
            if trigger_frame not in triggered_frames:
                triggered_frames.add(trigger_frame)
                alerts.append({
                    "alertType": "WRONG_WAY",
                    "severity": "WARNING",
                    "trackId": track["trackId"],
                    "frame": trigger_frame,
                    "positionX": round(points[i]["x"], 2),
                    "positionY": round(points[i]["y"], 2),
                    "description": (
                        f"轨迹 {track['trackId']} 检测到逆行："
                        f"连续 {consecutive} 帧沿坡面向上行进，"
                        f"触发帧 {trigger_frame}，"
                        f"位置 ({points[i]['x']:.0f}, {points[i]['y']:.0f})"
                    )
                })
                consecutive = 0  # 重置，避免重复计入同一段逆行

    return alerts


def detect_overspeed(track: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    超速检测：相邻帧像素位移超过阈值，连续 N 帧触发。

    算法：
      speed[i] = dist(points[i], points[i-1])（像素/帧）；
      连续 SPEED_FRAMES 帧 speed > SPEED_THRESHOLD 即触发预警。
      记录该段最大速度。
    """
    points = track["points"]
    alerts = []
    consecutive = 0
    max_speed = 0.0
    start_frame = 0

    for i in range(1, len(points)):
        speed = _dist(points[i - 1], points[i])
        if speed > SPEED_THRESHOLD:
            if consecutive == 0:
                start_frame = points[i]["frame"]
            consecutive += 1
            max_speed = max(max_speed, speed)
        else:
            if consecutive >= SPEED_FRAMES:
                alerts.append({
                    "alertType": "OVERSPEED",
                    "severity": "WARNING",
                    "trackId": track["trackId"],
                    "frame": start_frame,
                    "positionX": round(points[i - 1]["x"], 2),
                    "positionY": round(points[i - 1]["y"], 2),
                    "description": (
                        f"轨迹 {track['trackId']} 检测到超速："
                        f"连续 {consecutive} 帧速度超阈值，"
                        f"峰值速度 {max_speed:.1f} px/帧，"
                        f"起始帧 {start_frame}"
                    )
                })
            consecutive = 0
            max_speed = 0.0

    # 末尾段处理
    if consecutive >= SPEED_FRAMES:
        alerts.append({
            "alertType": "OVERSPEED",
            "severity": "WARNING",
            "trackId": track["trackId"],
            "frame": start_frame,
            "positionX": round(points[-1]["x"], 2),
            "positionY": round(points[-1]["y"], 2),
            "description": (
                f"轨迹 {track['trackId']} 检测到超速："
                f"连续 {consecutive} 帧速度超阈值，"
                f"峰值速度 {max_speed:.1f} px/帧，"
                f"起始帧 {start_frame}"
            )
        })

    return alerts


def detect_collision_risk(tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    碰撞风险检测：两轨迹在同一帧距离 < 阈值，且连续 N 帧，触发预警。

    算法：
      构建 frame→points 索引；
      对每对 (trackA, trackB)，逐帧计算欧氏距离；
      若距离 < COLLISION_DIST_THRESHOLD 且连续 COLLISION_APPROACH_FRAMES 帧，触发。
    """
    if len(tracks) < 2:
        return []

    # 构建 trackId → {frame: point} 映射
    frame_maps: Dict[int, Dict[int, Dict]] = {}
    for track in tracks:
        tid = track["trackId"]
        frame_maps[tid] = {p["frame"]: p for p in track["points"]}

    alerts = []
    track_ids = [t["trackId"] for t in tracks]

    for i in range(len(track_ids)):
        for j in range(i + 1, len(track_ids)):
            tid_a, tid_b = track_ids[i], track_ids[j]
            common_frames = sorted(
                set(frame_maps[tid_a].keys()) & set(frame_maps[tid_b].keys())
            )
            consecutive = 0
            trigger_frame = None
            trigger_pa = trigger_pb = None

            for frame in common_frames:
                pa = frame_maps[tid_a][frame]
                pb = frame_maps[tid_b][frame]
                d = _dist(pa, pb)
                if d < COLLISION_DIST_THRESHOLD:
                    consecutive += 1
                    if consecutive == 1:
                        trigger_frame = frame
                        trigger_pa, trigger_pb = pa, pb
                else:
                    if consecutive >= COLLISION_APPROACH_FRAMES:
                        mid_x = round((trigger_pa["x"] + trigger_pb["x"]) / 2, 2)
                        mid_y = round((trigger_pa["y"] + trigger_pb["y"]) / 2, 2)
                        alerts.append({
                            "alertType": "COLLISION_RISK",
                            "severity": "DANGER",
                            "trackId": tid_a,
                            "frame": trigger_frame,
                            "positionX": mid_x,
                            "positionY": mid_y,
                            "description": (
                                f"轨迹 {tid_a} 与轨迹 {tid_b} 检测到碰撞风险："
                                f"连续 {consecutive} 帧距离低于 {COLLISION_DIST_THRESHOLD:.0f}px，"
                                f"最近距离约 {d:.1f}px，"
                                f"触发帧 {trigger_frame}，"
                                f"位置 ({mid_x}, {mid_y})"
                            )
                        })
                    consecutive = 0

            # 末尾段
            if consecutive >= COLLISION_APPROACH_FRAMES and trigger_pa and trigger_pb:
                mid_x = round((trigger_pa["x"] + trigger_pb["x"]) / 2, 2)
                mid_y = round((trigger_pa["y"] + trigger_pb["y"]) / 2, 2)
                alerts.append({
                    "alertType": "COLLISION_RISK",
                    "severity": "DANGER",
                    "trackId": tid_a,
                    "frame": trigger_frame,
                    "positionX": mid_x,
                    "positionY": mid_y,
                    "description": (
                        f"轨迹 {tid_a} 与轨迹 {tid_b} 检测到碰撞风险："
                        f"连续 {consecutive} 帧距离低于 {COLLISION_DIST_THRESHOLD:.0f}px，"
                        f"触发帧 {trigger_frame}，"
                        f"位置 ({mid_x}, {mid_y})"
                    )
                })

    return alerts


def detect_still(track: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    静止检测（摔倒/受伤）：轨迹连续 N 帧位移极小，可能摔倒或失去意识。

    算法：
      对每对相邻帧计算位移；
      若 dist < STILL_DIST_THRESHOLD，则记为静止帧；
      连续 STILL_FRAMES 帧触发一次预警。
    """
    points = track["points"]
    alerts = []
    consecutive = 0
    still_start = None

    for i in range(1, len(points)):
        d = _dist(points[i - 1], points[i])
        if d < STILL_DIST_THRESHOLD:
            consecutive += 1
            if consecutive == 1:
                still_start = points[i - 1]
        else:
            if consecutive >= STILL_FRAMES:
                alerts.append({
                    "alertType": "STILL_DETECTED",
                    "severity": "DANGER",
                    "trackId": track["trackId"],
                    "frame": still_start["frame"],
                    "positionX": round(still_start["x"], 2),
                    "positionY": round(still_start["y"], 2),
                    "description": (
                        f"轨迹 {track['trackId']} 检测到长时间静止（疑似摔倒）："
                        f"连续 {consecutive} 帧位移低于 {STILL_DIST_THRESHOLD}px，"
                        f"起始帧 {still_start['frame']}，"
                        f"位置 ({still_start['x']:.0f}, {still_start['y']:.0f})"
                    )
                })
            consecutive = 0
            still_start = None

    if consecutive >= STILL_FRAMES and still_start:
        alerts.append({
            "alertType": "STILL_DETECTED",
            "severity": "DANGER",
            "trackId": track["trackId"],
            "frame": still_start["frame"],
            "positionX": round(still_start["x"], 2),
            "positionY": round(still_start["y"], 2),
            "description": (
                f"轨迹 {track['trackId']} 检测到长时间静止（疑似摔倒）："
                f"连续 {consecutive} 帧位移低于 {STILL_DIST_THRESHOLD}px，"
                f"起始帧 {still_start['frame']}，"
                f"位置 ({still_start['x']:.0f}, {still_start['y']:.0f})"
            )
        })

    return alerts


def detect_all(tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """对所有轨迹运行全部危险行为检测，返回合并的预警列表。"""
    all_alerts = []

    for track in tracks:
        if len(track["points"]) < 2:
            continue
        all_alerts.extend(detect_wrong_way(track))
        all_alerts.extend(detect_overspeed(track))
        all_alerts.extend(detect_still(track))

    all_alerts.extend(detect_collision_risk(tracks))

    logger.info("Behavior detection complete: %d alerts from %d tracks",
                len(all_alerts), len(tracks))
    return all_alerts
