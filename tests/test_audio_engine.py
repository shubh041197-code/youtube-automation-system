"""Tests for the audio generation engine."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.audio_engine import AudioEngine


@pytest.fixture
def engine():
    config = {
        "audio": {
            "voice": "en-US-GuyNeural",
            "rate": "+0%",
            "volume": "+0%",
            "fallback_voice": "en-US-JennyNeural",
        }
    }
    return AudioEngine(config)


class TestAudioEngine:
    def test_init_defaults(self, engine):
        """Should initialize with correct config values."""
        assert engine.voice == "en-US-GuyNeural"
        assert engine.rate == "+0%"
        assert engine.fallback_voice == "en-US-JennyNeural"

    @patch("src.audio_engine.AudioFileClip")
    @patch("src.audio_engine.edge_tts.Communicate")
    def test_generate_audio(self, mock_communicate, mock_audio_clip, engine, tmp_path):
        """Should generate audio and return path + duration."""
        # Mock edge-tts
        mock_comm_instance = MagicMock()
        mock_comm_instance.save = AsyncMock()
        mock_communicate.return_value = mock_comm_instance

        # Mock moviepy AudioFileClip for duration
        mock_clip = MagicMock()
        mock_clip.duration = 10.5
        mock_clip.close = MagicMock()
        mock_audio_clip.return_value = mock_clip

        output = str(tmp_path / "test.mp3")
        # Create the file so moviepy mock works
        with open(output, "w") as f:
            f.write("fake audio")

        result = engine.generate_audio("Hello world", output)

        assert result["path"] == output
        assert result["duration"] == 10.5

    def test_section_audio_empty_sections(self, engine, tmp_path):
        """Should handle empty sections list."""
        results = engine.generate_section_audio([], str(tmp_path))
        assert results == []

    @patch("src.audio_engine.AudioFileClip")
    @patch("src.audio_engine.edge_tts.Communicate")
    def test_generate_section_audio(self, mock_communicate, mock_audio_clip, engine, tmp_path):
        """Should generate audio for each section."""
        mock_comm_instance = MagicMock()
        mock_comm_instance.save = AsyncMock()
        mock_communicate.return_value = mock_comm_instance

        mock_clip = MagicMock()
        mock_clip.duration = 5.0
        mock_clip.close = MagicMock()
        mock_audio_clip.return_value = mock_clip

        sections = [
            {"title": "Intro", "narration": "Hello"},
            {"title": "Main", "narration": "Content"},
        ]

        results = engine.generate_section_audio(sections, str(tmp_path))
        assert len(results) == 2
        assert results[0]["section_index"] == 0
        assert results[1]["section_index"] == 1
