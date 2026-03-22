"""Tests for the content generation engine."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.content_engine import ContentEngine, FALLBACK_TEMPLATES, FALLBACK_SHORTS


@pytest.fixture
def engine():
    config = {
        "ai": {
            "api_key": "test-key",
            "api_base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini",
            "max_tokens": 4096,
            "temperature": 0.8,
        },
        "content": {
            "niche": "technology",
            "topics": ["AI", "programming", "cybersecurity"],
            "language": "en",
            "long_video_target_duration": 480,
            "short_target_duration": 45,
        },
        "shorts": {"count": 3},
    }
    return ContentEngine(config)


class TestGenerateTopic:
    def test_fallback_when_no_api_key(self):
        """Should use fallback topics when API key is empty."""
        config = {
            "ai": {"api_key": ""},
            "content": {
                "niche": "technology",
                "topics": ["AI", "programming"],
            },
            "shorts": {"count": 3},
        }
        engine = ContentEngine(config)
        topic = engine.generate_topic()
        assert topic in ["AI", "programming"]

    def test_fallback_avoids_used_topics(self):
        """Should avoid recently used topics."""
        config = {
            "ai": {"api_key": ""},
            "content": {
                "niche": "technology",
                "topics": ["AI", "programming", "cybersecurity"],
            },
            "shorts": {"count": 3},
        }
        engine = ContentEngine(config)
        topic = engine.generate_topic(used_topics=["AI", "programming"])
        assert topic == "cybersecurity"

    @patch("src.content_engine.httpx.Client")
    def test_ai_topic_generation(self, mock_client_class, engine):
        """Should call AI API and return cleaned topic."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '"AI in Healthcare"'}}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        topic = engine.generate_topic()
        assert topic == "AI in Healthcare"


class TestGenerateScript:
    def test_fallback_script_structure(self, engine):
        """Fallback templates should have valid structure."""
        for template in FALLBACK_TEMPLATES:
            assert "topic" in template
            assert "sections" in template
            assert len(template["sections"]) >= 3
            for section in template["sections"]:
                assert "title" in section
                assert "narration" in section
                assert "duration_hint" in section

    @patch("src.content_engine.httpx.Client")
    def test_ai_script_generation(self, mock_client_class, engine):
        """Should parse AI-generated script JSON."""
        script_data = {
            "sections": [
                {"title": "Intro", "narration": "Welcome!", "duration_hint": 15},
                {"title": "Main", "narration": "Content here.", "duration_hint": 90},
                {"title": "Outro", "narration": "Thanks!", "duration_hint": 15},
            ]
        }
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(script_data)}}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        script = engine.generate_script("Test Topic")
        assert "sections" in script
        assert len(script["sections"]) == 3


class TestGenerateShortsScripts:
    def test_fallback_shorts_structure(self):
        """Fallback shorts should have required fields."""
        for short in FALLBACK_SHORTS:
            assert "title" in short
            assert "narration" in short
            assert len(short["narration"]) > 20

    @patch("src.content_engine.httpx.Client")
    def test_ai_shorts_generation(self, mock_client_class, engine):
        """Should generate correct number of shorts."""
        shorts_data = {
            "shorts": [
                {"title": "Short 1", "narration": "Content 1..."},
                {"title": "Short 2", "narration": "Content 2..."},
                {"title": "Short 3", "narration": "Content 3..."},
            ]
        }
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(shorts_data)}}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        shorts = engine.generate_shorts_scripts("Test Topic")
        assert len(shorts) == 3
