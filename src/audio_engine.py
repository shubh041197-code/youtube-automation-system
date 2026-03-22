"""Text-to-speech audio generation using edge-tts (free, high quality)."""

import asyncio
import logging
from pathlib import Path

import edge_tts
from moviepy import AudioFileClip

from src.utils import load_config, retry

logger = logging.getLogger("youtube_automation")


class AudioEngine:
    """Converts text scripts to audio using Microsoft Edge TTS."""

    def __init__(self, config: dict = None):
        self.config = config or load_config()
        audio_config = self.config.get("audio", {})
        self.voice = audio_config.get("voice", "en-US-GuyNeural")
        self.rate = audio_config.get("rate", "+0%")
        self.volume = audio_config.get("volume", "+0%")
        self.fallback_voice = audio_config.get("fallback_voice", "en-US-JennyNeural")

    @retry(max_attempts=3, backoff=2.0)
    def generate_audio(self, text: str, output_path: str) -> dict:
        """Generate audio from text. Returns dict with path and duration."""
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        try:
            asyncio.run(self._generate(text, str(output), self.voice))
        except Exception as e:
            logger.warning(f"Primary voice failed: {e}. Trying fallback voice.")
            asyncio.run(self._generate(text, str(output), self.fallback_voice))

        duration = self._get_duration(str(output))
        logger.info(f"Audio generated: {output} ({duration:.1f}s)")

        return {"path": str(output), "duration": duration}

    async def _generate(self, text: str, output_path: str, voice: str):
        """Async edge-tts generation."""
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=self.rate,
            volume=self.volume
        )
        await communicate.save(output_path)

    def _get_duration(self, audio_path: str) -> float:
        """Get audio duration in seconds using moviepy."""
        clip = AudioFileClip(audio_path)
        duration = clip.duration
        clip.close()
        return duration

    def generate_section_audio(self, sections: list, output_dir: str) -> list:
        """Generate audio for each script section. Returns list of audio info dicts."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = []
        for i, section in enumerate(sections):
            narration = section.get("narration", "")
            if not narration.strip():
                continue

            audio_file = output_path / f"section_{i:02d}.mp3"
            info = self.generate_audio(narration, str(audio_file))
            info["section_index"] = i
            info["title"] = section.get("title", f"Section {i}")
            results.append(info)

        total_duration = sum(r["duration"] for r in results)
        logger.info(f"Generated {len(results)} section audios, total: {total_duration:.1f}s")
        return results

    def generate_full_audio(self, script_text: str, output_path: str) -> dict:
        """Generate a single audio file from full script text."""
        return self.generate_audio(script_text, output_path)

    @staticmethod
    def list_voices() -> list:
        """List available edge-tts voices."""
        async def _list():
            voices = await edge_tts.list_voices()
            return voices
        return asyncio.run(_list())
