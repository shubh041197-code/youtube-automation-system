"""Video assembly engine using MoviePy — creates long-form YouTube videos."""

import logging
import textwrap
from pathlib import Path

import numpy as np
from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeAudioClip,
    CompositeVideoClip,
    TextClip,
    concatenate_videoclips,
)

from src.utils import load_config, retry

logger = logging.getLogger("youtube_automation")


def _create_gradient_frame(width: int, height: int, color1: tuple, color2: tuple) -> np.ndarray:
    """Create a vertical gradient background frame."""
    gradient = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        gradient[y, :] = [r, g, b]
    return gradient


class VideoEngine:
    """Creates long-form YouTube videos with text overlays and audio."""

    def __init__(self, config: dict = None):
        self.config = config or load_config()
        video_config = self.config.get("video", {})
        self.width, self.height = video_config.get("resolution", [1920, 1080])
        self.fps = video_config.get("fps", 24)
        self.bg_color = tuple(video_config.get("background_color", [15, 15, 35]))
        self.text_color = video_config.get("text_color", "white")
        self.font_size = video_config.get("font_size", 48)
        self.font = video_config.get("font", "DejaVu-Sans-Bold")
        self.music_volume = video_config.get("music_volume", 0.08)
        self.transition_duration = video_config.get("transition_duration", 0.5)

    @retry(max_attempts=2, backoff=3.0)
    def create_video(self, script: dict, section_audios: list, output_path: str,
                     music_path: str = None) -> str:
        """Assemble a full video from script sections and audio files.

        Args:
            script: Script dict with 'sections' list
            section_audios: List of dicts with 'path', 'duration', 'section_index'
            output_path: Output MP4 file path
            music_path: Optional background music file path

        Returns:
            Path to the created video file
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        sections = script.get("sections", [])
        section_clips = []

        # Build audio lookup by section index
        audio_lookup = {a["section_index"]: a for a in section_audios}

        for i, section in enumerate(sections):
            audio_info = audio_lookup.get(i)
            if not audio_info:
                continue

            duration = audio_info["duration"]
            title = section.get("title", "")
            narration_text = section.get("narration", "")

            clip = self._create_section_clip(title, narration_text, duration)
            section_clips.append(clip)

        if not section_clips:
            raise ValueError("No valid sections to assemble")

        # Concatenate all sections
        if len(section_clips) > 1 and self.transition_duration > 0:
            # Simple concatenation (crossfade can be heavy, use padding instead)
            final_video = concatenate_videoclips(section_clips, method="compose")
        else:
            final_video = concatenate_videoclips(section_clips, method="compose")

        # Combine all section audios into one track
        audio_clips = []
        current_time = 0
        for i, section in enumerate(sections):
            audio_info = audio_lookup.get(i)
            if not audio_info:
                continue
            audio_clip = AudioFileClip(audio_info["path"]).with_start(current_time)
            audio_clips.append(audio_clip)
            current_time += audio_info["duration"]

        # Mix narration with background music
        if music_path and Path(music_path).exists():
            try:
                music = AudioFileClip(music_path)
                if music.duration < final_video.duration:
                    # Loop music
                    loops_needed = int(final_video.duration / music.duration) + 1
                    music_clips = [music.with_start(i * music.duration) for i in range(loops_needed)]
                    music = CompositeAudioClip(music_clips).with_duration(final_video.duration)
                else:
                    music = music.with_duration(final_video.duration)
                music = music.with_volume_scaled(self.music_volume)
                audio_clips.append(music)
            except Exception as e:
                logger.warning(f"Could not load background music: {e}")

        final_audio = CompositeAudioClip(audio_clips)
        final_video = final_video.with_audio(final_audio)

        # Write output
        logger.info(f"Rendering video: {output} ({final_video.duration:.1f}s)")
        final_video.write_videofile(
            str(output),
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
            logger=None,  # Suppress moviepy progress bars
            preset="medium",
            threads=4
        )

        # Cleanup
        final_video.close()
        for clip in section_clips:
            clip.close()
        for ac in audio_clips:
            ac.close()

        logger.info(f"Video created: {output}")
        return str(output)

    def _create_section_clip(self, title: str, narration: str, duration: float) -> CompositeVideoClip:
        """Create a video clip for one script section."""
        # Background with gradient
        gradient = _create_gradient_frame(
            self.width, self.height,
            self.bg_color,
            (self.bg_color[0] + 20, self.bg_color[1] + 10, self.bg_color[2] + 40)
        )
        bg = ColorClip(size=(self.width, self.height), color=self.bg_color).with_duration(duration)

        layers = [bg]

        # Section title (top area)
        if title:
            try:
                title_clip = TextClip(
                    text=title.upper(),
                    font_size=int(self.font_size * 0.8),
                    color="cyan",
                    font=self.font,
                    size=(self.width - 200, None),
                    method="caption",
                ).with_duration(duration).with_position(("center", 80))
                layers.append(title_clip)
            except Exception as e:
                logger.warning(f"Could not create title text: {e}")

        # Main narration text (center)
        if narration:
            wrapped = textwrap.fill(narration, width=55)
            try:
                text_clip = TextClip(
                    text=wrapped,
                    font_size=self.font_size,
                    color=self.text_color,
                    font=self.font,
                    size=(self.width - 300, None),
                    method="caption",
                ).with_duration(duration).with_position("center")
                layers.append(text_clip)
            except Exception as e:
                logger.warning(f"Could not create narration text: {e}")

        return CompositeVideoClip(layers, size=(self.width, self.height)).with_duration(duration)
