"""
RAG Engine 单元测试
主要测试 fallback 定责建议逻辑（不依赖 LLM/ChromaDB）
"""
import pytest
from app.services.rag_engine import RAGEngine


@pytest.fixture
def engine():
    return RAGEngine()


class TestFallbackSuggestion:

    def test_no_alerts_returns_no_liability(self, engine):
        result = engine._fallback_suggestion([])
        assert "未检测到" in result
        assert "无需定责" in result

    def test_wrong_way_alert_mentions_rule(self, engine):
        alerts = [{"alertType": "WRONG_WAY", "trackId": 1, "severity": "WARNING"}]
        result = engine._fallback_suggestion(alerts)
        assert "WRONG_WAY" in result or "逆行" in result
        assert "轨迹 1" in result

    def test_overspeed_alert_mentions_rule(self, engine):
        alerts = [{"alertType": "OVERSPEED", "trackId": 2, "severity": "WARNING"}]
        result = engine._fallback_suggestion(alerts)
        assert "超速" in result
        assert "轨迹 2" in result

    def test_collision_risk_alert_mentions_rule(self, engine):
        alerts = [{"alertType": "COLLISION_RISK", "trackId": 3, "severity": "DANGER"}]
        result = engine._fallback_suggestion(alerts)
        assert "碰撞" in result
        assert "轨迹 3" in result

    def test_still_detected_alert_mentions_rescue(self, engine):
        alerts = [{"alertType": "STILL_DETECTED", "trackId": 4, "severity": "DANGER"}]
        result = engine._fallback_suggestion(alerts)
        assert "静止" in result or "摔倒" in result or "救援" in result
        assert "轨迹 4" in result

    def test_multiple_alerts_all_appear_in_result(self, engine):
        alerts = [
            {"alertType": "WRONG_WAY", "trackId": 1, "severity": "WARNING"},
            {"alertType": "COLLISION_RISK", "trackId": 2, "severity": "DANGER"},
        ]
        result = engine._fallback_suggestion(alerts)
        assert "轨迹 1" in result
        assert "轨迹 2" in result

    def test_result_is_string(self, engine):
        alerts = [{"alertType": "OVERSPEED", "trackId": 5, "severity": "WARNING"}]
        result = engine._fallback_suggestion(alerts)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_unknown_alert_type_does_not_crash(self, engine):
        alerts = [{"alertType": "UNKNOWN_TYPE", "trackId": 9, "severity": "INFO"}]
        result = engine._fallback_suggestion(alerts)
        assert isinstance(result, str)


class TestGenerateLiabilitySuggestion:

    def test_uses_fallback_when_no_api_key(self, engine):
        """没有 API key 时应自动使用 fallback。"""
        engine.openai_api_key = ""
        alerts = [{"alertType": "WRONG_WAY", "trackId": 1, "severity": "WARNING"}]
        tracks = []
        result = engine.generate_liability_suggestion(alerts, tracks)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_uses_fallback_when_api_key_is_placeholder(self, engine):
        engine.openai_api_key = "your_openai_api_key"
        alerts = [{"alertType": "OVERSPEED", "trackId": 2, "severity": "WARNING"}]
        result = engine.generate_liability_suggestion(alerts, [])
        assert isinstance(result, str)
        assert "超速" in result or "OVERSPEED" in result

    def test_empty_alerts_returns_no_liability(self, engine):
        engine.openai_api_key = ""
        result = engine.generate_liability_suggestion([], [])
        assert "未检测到" in result


class TestBuildPrompt:

    def test_prompt_contains_alert_types(self, engine):
        alerts = [
            {"alertType": "WRONG_WAY", "severity": "WARNING", "trackId": 1,
             "description": "轨迹1逆行"},
        ]
        tracks = [
            {"trackId": 1, "className": "person",
             "points": [{"frame": 0, "x": 0, "y": 0}, {"frame": 1, "x": 5, "y": 10}]}
        ]
        prompt = engine._build_prompt(alerts, tracks)
        assert "WRONG_WAY" in prompt
        assert "轨迹1逆行" in prompt
        assert "轨迹ID 1" in prompt

    def test_prompt_contains_track_summary(self, engine):
        alerts = []
        tracks = [
            {"trackId": 5, "className": "person",
             "points": [{"frame": 0, "x": 0.0, "y": 0.0}, {"frame": 1, "x": 30.0, "y": 40.0}]}
        ]
        prompt = engine._build_prompt(alerts, tracks)
        assert "轨迹ID 5" in prompt
        assert "50" in prompt or "帧" in prompt  # 总位移 50px

    def test_prompt_is_chinese(self, engine):
        prompt = engine._build_prompt([], [])
        assert "滑雪场" in prompt or "定责" in prompt
