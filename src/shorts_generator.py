"""YouTube Shorts generator — creates vertical 9:16 short-form videos."""

import logging
import textwrap
from pathlib import Path

import numpy as np
from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    TextClip,
)

from src.utils import load_config, retry

logger = logging.getLogger("youtube_automation")

# Gradient color pairs for shorts backgrounds
DEFAULT_GRADIENTS = [
    ((138, 43, 226), (30, 0, 80)),     # Purple
    ((0, 128, 128), (0, 40, 60)),       # Teal
    ((220, 20, 60), (80, 0, 20)),       # Crimson
    ((255, 140, 0), (100, 40, 0)),      # Orange
    ((0, 100, 200), (0, 30, 80)),       # Blue
]


def _create_vertical_gradient(width: int, height: int, color1: tuple, color2: tuple) -> np.ndarray:
    """Create a vertical gradient for shorts background."""
    gradient = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        ratio = y / height
        for c in range(3):
            gradient[y, :, c] = int(color1[c] * (1 - ratio) + color2[c] * ratio)
    return gradient


class ShortsGenerator:
    """Creates YouTube Shorts (vertical 9:16 videos)."""

    def __init__(self, config: dict = None):
        self.config = config or load_config()
        shorts_config = self.config.get("shorts", {})
        self.width, self.height = shorts_config.get("resolution", [1080, 1920])
        self.fps = shorts_config.get("fps", 30)
        self.font_size = shorts_config.get("font_size", 64)
        self.count = shorts_config.get("count", 3)
        self.font = self.config.get("video", {}).get("font", "DejaVu-Sans-Bold")

    @retry(max_attempts=2, backoff=3.0)
    def create_short(self, script: dict, audio_path: str, output_path: str,
                     gradient_index: int = 0) -> str:
        """Create a single YouTube Short video.

        Args:
            script: Dict with 'title' and 'narration'
            audio_path: Path to the narration audio file
            output_path: Output MP4 file path
            gradient_index: Which gradient color pair to use

        Returns:
            Path to the created video file
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        # Load audio to get duration
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration

        # Get gradient colors
        colors = DEFAULT_GRADIENTS[gradient_index % len(DEFAULT_GRADIENTS)]

        # Create background
        gradient_frame = _create_vertical_gradient(self.width, self.height, colors[0], colors[1])
        bg = ColorClip(size=(self.width, self.height), color=colors[0]).with_duration(duration)

        layers = [bg]

        title = script.get("title", "")
        narration = script.get("narration", "")

        # Title text (large, top third)
        if title:
            try:
                title_clip = TextClip(
                    text=title.upper(),
                    font_size=int(self.font_size * 1.2),
                    color="white",
                    font=self.font,
                    stroke_color="black",
                    stroke_width=3,
                    size=(self.width - 120, None),
                    method="caption",
                ).with_duration(duration).with_position(("center", 250))
                layers.append(title_clip)
            except Exception as e:
                logger.warning(f"Could not create short title: {e}")

        # Narration text (center, large for mobile)
        if narration:
            wrapped = textwrap.fill(narration, width=28)
            try:
                text_clip = TextClip(
                    text=wrapped,
                    font_size=self.font_size,
                    color="white",
                    font=self.font,
                    stroke_color="black",
                    stroke_width=2,
                    size=(self.width - 100, None),
                    method="caption",
                ).with_duration(duration).with_position("center")
                layers.append(text_clip)
            except Exception as e:
                logger.warning(f"Could not create narration text: {e}")

        # CTA at bottom
        try:
            cta_clip = TextClip(
                text="FOLLOW FOR MORE",
                font_size=36,
                color="yellow",
                font=self.font,
                stroke_color="black",
                stroke_width=2,
                size=(self.width - 100, None),
                method="caption",
            ).with_duration(duration).with_position(("center", self.height - 200))
            layers.append(cta_clip)
        except Exception as e:
            logger.warning(f"Could not create CTA text: {e}")

        # Compose
        video = CompositeVideoClip(layers, size=(self.width, self.height)).with_duration(duration)
        video = video.with_audio(audio_clip)

        # Render
        logger.info(f"Rendering short: {output} ({duration:.1f}s)")
        video.write_videofile(
            str(output),
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
            logger=None,
            preset="medium",
            threads=4
        )

        # Cleanup
        video.close()
        audio_clip.close()
        for layer in layers:
            layer.close()

        logger.info(f"Short created: {output}")
        return str(output)

    def create_all_shorts(self, shorts_scripts: list, audio_paths: list,
                          output_dir: str) -> list:
        """Create all shorts videos.

        Args:
            shorts_scripts: List of script dicts with 'title' and 'narration'
            audio_paths: List of audio file paths
            output_dir: Directory to save shorts

        Returns:
            List of output video file paths
        """
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        results = []

        for i, (script, audio_path) in enumerate(zip(shorts_scripts, audio_paths)):
            video_path = output / f"short_{i + 1}.mp4"
            result = self.create_short(script, audio_path, str(video_path), gradient_index=i)
            results.append(result)

        logger.info(f"Created {len(results)} shorts in {output_dir}")
        return results
