"""
RAG Engine 单元测试
主要测试 fallback 定责建议逻辑（不依赖 LLM/ChromaDB）
"""
import json
import pytest
from app.services.rag_engine import RAGEngine


@pytest.fixture
def engine():
    return RAGEngine()


class TestFallbackSuggestion:

    def test_no_alerts_returns_no_liability(self, engine):
        result = engine._fallback_suggestion([])
        parsed = json.loads(result)
        assert "未检测到" in parsed["behavior_analysis"]
        assert len(parsed["liability"]["parties"]) == 0

    def test_wrong_way_alert_mentions_rule(self, engine):
        alerts = [{"alertType": "WRONG_WAY", "trackId": 1, "severity": "WARNING"}]
        result = engine._fallback_suggestion(alerts)
        parsed = json.loads(result)
        assert any("逆行" in p["reason"] for p in parsed["liability"]["parties"])
        assert any("轨迹1" in p["name"] for p in parsed["liability"]["parties"])

    def test_overspeed_alert_mentions_rule(self, engine):
        alerts = [{"alertType": "OVERSPEED", "trackId": 2, "severity": "WARNING"}]
        result = engine._fallback_suggestion(alerts)
        parsed = json.loads(result)
        assert any("超速" in p["reason"] for p in parsed["liability"]["parties"])
        assert any("轨迹2" in p["name"] for p in parsed["liability"]["parties"])

    def test_collision_risk_alert_mentions_rule(self, engine):
        alerts = [{"alertType": "COLLISION_RISK", "trackId": 3, "severity": "DANGER"}]
        result = engine._fallback_suggestion(alerts)
        parsed = json.loads(result)
        assert "碰撞" in parsed["behavior_analysis"]

    def test_still_detected_alert_mentions_rescue(self, engine):
        alerts = [{"alertType": "STILL_DETECTED", "trackId": 4, "severity": "DANGER"}]
        result = engine._fallback_suggestion(alerts)
        parsed = json.loads(result)
        assert "静止" in parsed["behavior_analysis"] or "救援" in parsed["suggestion"]

    def test_multiple_alerts_all_appear_in_result(self, engine):
        alerts = [
            {"alertType": "WRONG_WAY", "trackId": 1, "severity": "WARNING"},
            {"alertType": "COLLISION_RISK", "trackId": 2, "severity": "DANGER"},
        ]
        result = engine._fallback_suggestion(alerts)
        parsed = json.loads(result)
        names = [p["name"] for p in parsed["liability"]["parties"]]
        assert any("1" in n for n in names)
        assert any("2" in n for n in names)

    def test_result_is_valid_json_string(self, engine):
        alerts = [{"alertType": "OVERSPEED", "trackId": 5, "severity": "WARNING"}]
        result = engine._fallback_suggestion(alerts)
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "liability" in parsed
        assert "behavior_analysis" in parsed
        assert "references" in parsed
        assert "suggestion" in parsed

    def test_unknown_alert_type_does_not_crash(self, engine):
        alerts = [{"alertType": "UNKNOWN_TYPE", "trackId": 9, "severity": "INFO"}]
        result = engine._fallback_suggestion(alerts)
        assert isinstance(result, str)
        json.loads(result)  # should not raise


class TestGenerateLiabilitySuggestion:

    def test_uses_fallback_when_no_api_key(self, engine):
        engine.qwen_api_key = ""
        alerts = [{"alertType": "WRONG_WAY", "trackId": 1, "severity": "WARNING"}]
        tracks = []
        result = engine.generate_liability_suggestion(alerts, tracks)
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "liability" in parsed

    def test_uses_fallback_when_api_key_is_placeholder(self, engine):
        engine.qwen_api_key = "your_qwen_api_key"
        alerts = [{"alertType": "OVERSPEED", "trackId": 2, "severity": "WARNING"}]
        result = engine.generate_liability_suggestion(alerts, [])
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert any("超速" in p["reason"] for p in parsed["liability"]["parties"])

    def test_empty_alerts_returns_no_liability(self, engine):
        engine.qwen_api_key = ""
        result = engine.generate_liability_suggestion([], [])
        parsed = json.loads(result)
        assert "未检测到" in parsed["behavior_analysis"]


class TestQueryKnowledge:

    def test_returns_json_when_no_api_key(self, engine):
        engine.qwen_api_key = ""
        result = engine.query_knowledge("逆行如何定责？")
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "liability" in parsed
        assert "behavior_analysis" in parsed

    def test_returns_json_when_api_key_is_placeholder(self, engine):
        engine.qwen_api_key = "your_qwen_api_key"
        result = engine.query_knowledge("超速违规怎么处理？")
        parsed = json.loads(result)
        assert "liability" in parsed


class TestBuildPrompt:

    def test_video_prompt_contains_alert_types(self, engine):
        alerts = [
            {"alertType": "WRONG_WAY", "severity": "WARNING", "trackId": 1,
             "description": "轨迹1逆行"},
        ]
        tracks = [
            {"trackId": 1, "className": "person",
             "points": [{"frame": 0, "x": 0, "y": 0}, {"frame": 1, "x": 5, "y": 10}]}
        ]
        prompt = engine._build_video_prompt(alerts, tracks)
        assert "WRONG_WAY" in prompt
        assert "轨迹1逆行" in prompt
        assert "轨迹ID 1" in prompt

    def test_video_prompt_contains_track_summary(self, engine):
        alerts = []
        tracks = [
            {"trackId": 5, "className": "person",
             "points": [{"frame": 0, "x": 0.0, "y": 0.0}, {"frame": 1, "x": 30.0, "y": 40.0}]}
        ]
        prompt = engine._build_video_prompt(alerts, tracks)
        assert "轨迹ID 5" in prompt
        assert "50" in prompt or "帧" in prompt

    def test_video_prompt_requests_json(self, engine):
        prompt = engine._build_video_prompt([], [])
        assert "JSON" in prompt

    def test_query_prompt_contains_question(self, engine):
        prompt = engine._build_query_prompt("逆行违规如何定责？")
        assert "逆行违规如何定责" in prompt
        assert "JSON" in prompt


class TestExtractJson:

    def test_extracts_from_markdown_code_block(self, engine):
        text = '```json\n{"liability":{"parties":[],"resort_liability":"无"}}\n```'
        result = engine._extract_json(text)
        parsed = json.loads(result)
        assert "liability" in parsed

    def test_extracts_plain_json(self, engine):
        text = '{"liability":{"parties":[],"resort_liability":"无"}}'
        result = engine._extract_json(text)
        parsed = json.loads(result)
        assert "liability" in parsed

    def test_extracts_json_with_surrounding_text(self, engine):
        text = 'Here is the result:\n{"liability":{"parties":[],"resort_liability":"无"}}\nDone.'
        result = engine._extract_json(text)
        parsed = json.loads(result)
        assert "liability" in parsed

    def test_returns_original_if_no_json(self, engine):
        text = "This is just plain text with no JSON."
        result = engine._extract_json(text)
        assert result == text
