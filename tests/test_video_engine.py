"""Tests for the video and thumbnail engines."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.video_engine import VideoEngine, _create_gradient_frame
from src.thumbnail_engine import ThumbnailEngine


class TestGradientFrame:
    def test_creates_correct_shape(self):
        """Should create array with correct dimensions."""
        frame = _create_gradient_frame(100, 50, (0, 0, 0), (255, 255, 255))
        assert frame.shape == (50, 100, 3)

    def test_gradient_top_is_color1(self):
        """Top row should be close to color1."""
        frame = _create_gradient_frame(10, 100, (255, 0, 0), (0, 0, 255))
        assert frame[0, 0, 0] == 255  # Red at top
        assert frame[0, 0, 2] == 0    # No blue at top

    def test_gradient_bottom_is_color2(self):
        """Bottom row should be close to color2."""
        frame = _create_gradient_frame(10, 100, (255, 0, 0), (0, 0, 255))
        assert frame[99, 0, 0] < 10   # Little red at bottom
        assert frame[99, 0, 2] > 245  # Mostly blue at bottom


class TestVideoEngine:
    def test_init_defaults(self):
        config = {
            "video": {
                "resolution": [1920, 1080],
                "fps": 24,
                "background_color": [15, 15, 35],
                "text_color": "white",
                "font_size": 48,
                "font": "DejaVu-Sans-Bold",
                "music_volume": 0.08,
                "transition_duration": 0.5,
            }
        }
        engine = VideoEngine(config)
        assert engine.width == 1920
        assert engine.height == 1080
        assert engine.fps == 24
        assert engine.font_size == 48


class TestThumbnailEngine:
    @pytest.fixture
    def engine(self):
        config = {
            "thumbnail": {
                "resolution": [1280, 720],
                "font_size": 72,
                "templates": ["gradient_bold", "split_accent", "dark_glow"],
            }
        }
        return ThumbnailEngine(config)

    def test_generate_gradient_bold(self, engine, tmp_path):
        """Should create a thumbnail file."""
        output = str(tmp_path / "thumb.jpg")
        result = engine.generate_thumbnail("Test Title", output, template="gradient_bold")
        assert Path(result).exists()
        assert Path(result).stat().st_size > 0

    def test_generate_split_accent(self, engine, tmp_path):
        """Should create a thumbnail with split accent template."""
        output = str(tmp_path / "thumb2.jpg")
        result = engine.generate_thumbnail("Another Title", output, template="split_accent")
        assert Path(result).exists()

    def test_generate_dark_glow(self, engine, tmp_path):
        """Should create a thumbnail with dark glow template."""
        output = str(tmp_path / "thumb3.jpg")
        result = engine.generate_thumbnail("Glow Title", output, template="dark_glow")
        assert Path(result).exists()

    def test_random_template(self, engine, tmp_path):
        """Should pick a random template when none specified."""
        output = str(tmp_path / "thumb4.jpg")
        result = engine.generate_thumbnail("Random", output)
        assert Path(result).exists()
