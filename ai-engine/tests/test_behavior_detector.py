"""
behavior_detector 单元测试
覆盖逆行、超速、碰撞风险、静止四类危险行为检测算法
"""
import pytest
from app.services.behavior_detector import (
    detect_wrong_way,
    detect_overspeed,
    detect_collision_risk,
    detect_still,
    detect_all,
    WRONG_WAY_FRAMES,
    WRONG_WAY_MIN_DISPLACEMENT,
    SPEED_THRESHOLD,
    SPEED_FRAMES,
    COLLISION_DIST_THRESHOLD,
    COLLISION_APPROACH_FRAMES,
    STILL_DIST_THRESHOLD,
    STILL_FRAMES,
)


# ── 工具函数 ─────────────────────────────────────────────────────────────────

def make_track(track_id: int, points: list) -> dict:
    return {"trackId": track_id, "className": "person", "points": points}


def make_points_going_down(n: int, start_y=100, dy=10, start_x=50) -> list:
    """生成 n 个正常向下滑动的帧点（y 递增）。"""
    return [{"frame": i, "x": start_x, "y": start_y + i * dy} for i in range(n)]


def make_points_going_up(n: int, start_y=500, dy=10, start_x=50) -> list:
    """生成 n 个逆行（向上）的帧点（y 递减）。"""
    return [{"frame": i, "x": start_x, "y": start_y - i * dy} for i in range(n)]


def make_points_fast(n: int, speed=60.0) -> list:
    """生成 n 个超速帧点（相邻帧位移 = speed）。"""
    return [{"frame": i, "x": i * speed, "y": 0} for i in range(n)]


def make_points_still(n: int) -> list:
    """生成 n 个静止帧点（几乎不动）。"""
    return [{"frame": i, "x": 100.0, "y": 200.0} for i in range(n)]


# ── 逆行检测 ─────────────────────────────────────────────────────────────────

class TestDetectWrongWay:

    def test_no_alerts_when_going_down(self):
        track = make_track(1, make_points_going_down(20))
        alerts = detect_wrong_way(track)
        assert alerts == []

    def test_detects_wrong_way_with_enough_frames(self):
        # 连续逆行帧数 > WRONG_WAY_FRAMES
        points = make_points_going_up(WRONG_WAY_FRAMES + 5)
        track = make_track(1, points)
        alerts = detect_wrong_way(track)
        assert len(alerts) >= 1
        assert alerts[0]["alertType"] == "WRONG_WAY"
        assert alerts[0]["severity"] == "WARNING"
        assert alerts[0]["trackId"] == 1

    def test_no_alert_below_frame_threshold(self):
        # 逆行帧数不足 WRONG_WAY_FRAMES
        points = make_points_going_up(WRONG_WAY_FRAMES - 1)
        track = make_track(1, points)
        alerts = detect_wrong_way(track)
        assert alerts == []

    def test_no_alert_when_displacement_too_small(self):
        # y 减少但位移小于 WRONG_WAY_MIN_DISPLACEMENT
        points = [{"frame": i, "x": 50, "y": 500 - i * 0.5} for i in range(30)]
        track = make_track(1, points)
        alerts = detect_wrong_way(track)
        assert alerts == []

    def test_description_contains_track_id(self):
        points = make_points_going_up(WRONG_WAY_FRAMES + 2)
        track = make_track(42, points)
        alerts = detect_wrong_way(track)
        assert any("42" in a["description"] for a in alerts)

    def test_single_point_track_returns_no_alerts(self):
        track = make_track(1, [{"frame": 0, "x": 50, "y": 100}])
        alerts = detect_wrong_way(track)
        assert alerts == []


# ── 超速检测 ─────────────────────────────────────────────────────────────────

class TestDetectOverspeed:

    def test_no_alerts_when_normal_speed(self):
        # 位移远低于 SPEED_THRESHOLD
        points = [{"frame": i, "x": i * 5.0, "y": 0} for i in range(20)]
        track = make_track(1, points)
        alerts = detect_overspeed(track)
        assert alerts == []

    def test_detects_overspeed_with_enough_frames(self):
        points = make_points_fast(SPEED_FRAMES + 5, speed=SPEED_THRESHOLD + 10)
        track = make_track(1, points)
        alerts = detect_overspeed(track)
        assert len(alerts) >= 1
        assert alerts[0]["alertType"] == "OVERSPEED"
        assert alerts[0]["severity"] == "WARNING"

    def test_no_alert_below_frame_threshold(self):
        # 超速但帧数不足
        points = make_points_fast(SPEED_FRAMES - 1, speed=SPEED_THRESHOLD + 10)
        track = make_track(1, points)
        alerts = detect_overspeed(track)
        assert alerts == []

    def test_handles_trailing_overspeed_segment(self):
        # 末尾段超速也能检测到
        normal = [{"frame": i, "x": i * 2.0, "y": 0} for i in range(5)]
        fast = [{"frame": 5 + i, "x": 10 + i * (SPEED_THRESHOLD + 20), "y": 0} for i in range(SPEED_FRAMES + 3)]
        track = make_track(1, normal + fast)
        alerts = detect_overspeed(track)
        assert len(alerts) >= 1

    def test_description_mentions_speed(self):
        points = make_points_fast(SPEED_FRAMES + 5, speed=SPEED_THRESHOLD + 15)
        track = make_track(1, points)
        alerts = detect_overspeed(track)
        assert any("速度" in a["description"] or "px" in a["description"] for a in alerts)


# ── 碰撞风险检测 ─────────────────────────────────────────────────────────────

class TestDetectCollisionRisk:

    def test_no_alerts_with_single_track(self):
        tracks = [make_track(1, make_points_going_down(10))]
        alerts = detect_collision_risk(tracks)
        assert alerts == []

    def test_no_alerts_when_tracks_far_apart(self):
        points_a = [{"frame": i, "x": 0, "y": i * 10} for i in range(20)]
        points_b = [{"frame": i, "x": 1000, "y": i * 10} for i in range(20)]
        tracks = [make_track(1, points_a), make_track(2, points_b)]
        alerts = detect_collision_risk(tracks)
        assert alerts == []

    def test_detects_collision_when_close_enough(self):
        # 两轨迹距离 < COLLISION_DIST_THRESHOLD，持续足够帧
        close_dist = COLLISION_DIST_THRESHOLD / 2
        points_a = [{"frame": i, "x": 0, "y": i * 10} for i in range(COLLISION_APPROACH_FRAMES + 5)]
        points_b = [{"frame": i, "x": close_dist, "y": i * 10} for i in range(COLLISION_APPROACH_FRAMES + 5)]
        tracks = [make_track(1, points_a), make_track(2, points_b)]
        alerts = detect_collision_risk(tracks)
        assert len(alerts) >= 1
        assert alerts[0]["alertType"] == "COLLISION_RISK"
        assert alerts[0]["severity"] == "DANGER"

    def test_no_alert_when_close_but_too_few_frames(self):
        close_dist = COLLISION_DIST_THRESHOLD / 2
        n = COLLISION_APPROACH_FRAMES - 1
        points_a = [{"frame": i, "x": 0, "y": i * 10} for i in range(n)]
        points_b = [{"frame": i, "x": close_dist, "y": i * 10} for i in range(n)]
        tracks = [make_track(1, points_a), make_track(2, points_b)]
        alerts = detect_collision_risk(tracks)
        assert alerts == []

    def test_handles_multiple_track_pairs(self):
        close_dist = COLLISION_DIST_THRESHOLD / 2
        n = COLLISION_APPROACH_FRAMES + 3
        t1 = make_track(1, [{"frame": i, "x": 0, "y": i * 10} for i in range(n)])
        t2 = make_track(2, [{"frame": i, "x": close_dist, "y": i * 10} for i in range(n)])
        t3 = make_track(3, [{"frame": i, "x": 1000, "y": i * 10} for i in range(n)])
        alerts = detect_collision_risk([t1, t2, t3])
        # t1-t2 should trigger, t1-t3 and t2-t3 should not
        assert any(a["alertType"] == "COLLISION_RISK" for a in alerts)


# ── 静止检测 ─────────────────────────────────────────────────────────────────

class TestDetectStill:

    def test_no_alerts_when_moving(self):
        track = make_track(1, make_points_going_down(40))
        alerts = detect_still(track)
        assert alerts == []

    def test_detects_still_with_enough_frames(self):
        points = make_points_still(STILL_FRAMES + 10)
        track = make_track(1, points)
        alerts = detect_still(track)
        assert len(alerts) >= 1
        assert alerts[0]["alertType"] == "STILL_DETECTED"
        assert alerts[0]["severity"] == "DANGER"

    def test_no_alert_below_frame_threshold(self):
        points = make_points_still(STILL_FRAMES - 1)
        track = make_track(1, points)
        alerts = detect_still(track)
        assert alerts == []

    def test_detects_still_in_trailing_segment(self):
        # 先运动，再静止，末尾段也应触发
        moving = make_points_going_down(10)
        still = [{"frame": 10 + i, "x": 50, "y": 200} for i in range(STILL_FRAMES + 5)]
        track = make_track(1, moving + still)
        alerts = detect_still(track)
        assert len(alerts) >= 1

    def test_description_mentions_trackid(self):
        points = make_points_still(STILL_FRAMES + 5)
        track = make_track(99, points)
        alerts = detect_still(track)
        assert any("99" in a["description"] for a in alerts)


# ── detect_all 综合测试 ────────────────────────────────────────────────────────

class TestDetectAll:

    def test_returns_empty_for_normal_tracks(self):
        tracks = [make_track(1, make_points_going_down(20))]
        alerts = detect_all(tracks)
        assert alerts == []

    def test_combines_all_alert_types(self):
        # 逆行轨迹
        wrong_way = make_track(1, make_points_going_up(WRONG_WAY_FRAMES + 5))
        # 超速轨迹
        overspeed = make_track(2, make_points_fast(SPEED_FRAMES + 5, speed=SPEED_THRESHOLD + 20))
        # 静止轨迹
        still = make_track(3, make_points_still(STILL_FRAMES + 10))

        tracks = [wrong_way, overspeed, still]
        alerts = detect_all(tracks)

        types = {a["alertType"] for a in alerts}
        assert "WRONG_WAY" in types
        assert "OVERSPEED" in types
        assert "STILL_DETECTED" in types

    def test_skips_single_point_tracks(self):
        tracks = [make_track(1, [{"frame": 0, "x": 50, "y": 100}])]
        alerts = detect_all(tracks)
        assert alerts == []

    def test_collision_detected_between_two_close_tracks(self):
        n = COLLISION_APPROACH_FRAMES + 5
        close = COLLISION_DIST_THRESHOLD / 2
        t1 = make_track(1, [{"frame": i, "x": 0, "y": i * 5} for i in range(n)])
        t2 = make_track(2, [{"frame": i, "x": close, "y": i * 5} for i in range(n)])
        alerts = detect_all([t1, t2])
        assert any(a["alertType"] == "COLLISION_RISK" for a in alerts)
