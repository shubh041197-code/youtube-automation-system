"""Pipeline orchestrator — coordinates all engines to produce daily content."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

from src.audio_engine import AudioEngine
from src.content_engine import ContentEngine
from src.database import Database
from src.seo_engine import SEOEngine
from src.shorts_generator import ShortsGenerator
from src.thumbnail_engine import ThumbnailEngine
from src.utils import ensure_output_dir, load_config, safe_filename
from src.video_engine import VideoEngine
from src.youtube_uploader import YouTubeUploader

logger = logging.getLogger("youtube_automation")


class PipelineStatus:
    """Tracks current pipeline execution status for the dashboard."""

    def __init__(self):
        self.running = False
        self.current_step = ""
        self.progress = 0  # 0-100
        self.logs = []

    def update(self, step: str, progress: int, message: str = ""):
        self.current_step = step
        self.progress = progress
        msg = message or step
        self.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        logger.info(msg)

    def to_dict(self) -> dict:
        return {
            "running": self.running,
            "current_step": self.current_step,
            "progress": self.progress,
            "logs": self.logs[-50:]  # Keep last 50 log entries
        }


# Global status instance for dashboard access
pipeline_status = PipelineStatus()


class DailyPipeline:
    """Runs the complete daily content pipeline."""

    def __init__(self, config: dict = None):
        self.config = config or load_config()
        self.db = Database()
        self.content = ContentEngine(self.config)
        self.audio = AudioEngine(self.config)
        self.video = VideoEngine(self.config)
        self.shorts = ShortsGenerator(self.config)
        self.thumbnail = ThumbnailEngine(self.config)
        self.seo = SEOEngine(self.config)
        self.uploader = YouTubeUploader(self.config)

    def run_daily(self, dry_run: bool = False) -> dict:
        """Run the full daily pipeline: 1 long video + 3 shorts.

        Args:
            dry_run: If True, skip YouTube upload

        Returns:
            Dict with results summary
        """
        pipeline_status.running = True
        pipeline_status.logs = []
        run_id = self.db.create_run("daily")
        results = {"long_video": None, "shorts": [], "errors": []}

        try:
            pipeline_status.update("Starting", 0, "Starting daily pipeline...")

            # Run long video pipeline
            try:
                long_result = self.run_long_video(dry_run=dry_run)
                results["long_video"] = long_result
            except Exception as e:
                error = f"Long video pipeline failed: {e}"
                logger.error(error, exc_info=True)
                results["errors"].append(error)

            # Run shorts pipeline
            try:
                shorts_result = self.run_shorts(dry_run=dry_run)
                results["shorts"] = shorts_result
            except Exception as e:
                error = f"Shorts pipeline failed: {e}"
                logger.error(error, exc_info=True)
                results["errors"].append(error)

            # Complete
            status = "completed" if not results["errors"] else "completed_with_errors"
            pipeline_status.update("Complete", 100, f"Pipeline complete: {status}")
            self.db.complete_run(run_id, status=status)

            video_ids = []
            if results["long_video"]:
                video_ids.append(results["long_video"].get("video_db_id"))
            for s in results["shorts"]:
                if s:
                    video_ids.append(s.get("video_db_id"))
            self.db.update_run(run_id, videos=json.dumps(video_ids))

        except Exception as e:
            logger.error(f"Daily pipeline failed: {e}", exc_info=True)
            self.db.complete_run(run_id, status="failed", error=str(e))
            results["errors"].append(str(e))
        finally:
            pipeline_status.running = False

        return results

    def run_long_video(self, dry_run: bool = False) -> dict:
        """Run the long-form video pipeline."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_dir = ensure_output_dir(self.config, "long")

        # Step 1: Generate topic
        pipeline_status.update("Topic Generation", 5, "Generating topic...")
        used_topics = self.db.get_used_topics()
        topic = self.content.generate_topic(used_topics)
        logger.info(f"Topic selected: {topic}")

        # Create DB record
        video_id = self.db.create_video("long", topic)
        self.db.update_video(video_id, status="generating")

        try:
            # Step 2: Generate script
            pipeline_status.update("Script Writing", 15, f"Writing script for: {topic}")
            script = self.content.generate_script(topic)
            self.db.update_video(video_id, script=json.dumps(script))

            # Step 3: Generate audio
            pipeline_status.update("Audio Generation", 25, "Generating narration audio...")
            audio_dir = output_dir / "audio"
            section_audios = self.audio.generate_section_audio(script["sections"], str(audio_dir))

            # Step 4: Generate video
            pipeline_status.update("Video Assembly", 40, "Assembling video...")
            video_filename = f"long_{safe_filename(topic)}_{date_str}.mp4"
            video_path = str(output_dir / video_filename)

            # Check for background music
            music_dir = Path("assets/music")
            music_files = list(music_dir.glob("*.mp3")) if music_dir.exists() else []
            music_path = str(music_files[0]) if music_files else None

            self.video.create_video(script, section_audios, video_path, music_path)
            self.db.update_video(video_id, video_path=video_path)

            # Step 5: Generate thumbnail
            pipeline_status.update("Thumbnail", 55, "Creating thumbnail...")
            thumb_path = str(output_dir / f"thumb_{safe_filename(topic)}.jpg")
            self.thumbnail.generate_thumbnail(topic, thumb_path)
            self.db.update_video(video_id, thumbnail_path=thumb_path)

            # Step 6: Generate SEO
            pipeline_status.update("SEO Optimization", 60, "Optimizing SEO metadata...")
            seo = self.seo.generate_seo(topic, script, video_type="long")
            self.db.update_video(
                video_id,
                title=seo["title"],
                description=seo["description"],
                tags=json.dumps(seo["tags"])
            )

            # Step 7: Upload
            youtube_id = None
            if not dry_run:
                pipeline_status.update("Uploading", 65, "Uploading to YouTube...")
                youtube_id = self.uploader.upload_video(video_path, seo, thumb_path)
                self.db.update_video(
                    video_id,
                    youtube_id=youtube_id,
                    status="completed",
                    uploaded_at=datetime.now().isoformat()
                )
            else:
                logger.info("Dry run: skipping YouTube upload")
                self.db.update_video(video_id, status="completed")

            result = {
                "video_db_id": video_id,
                "topic": topic,
                "title": seo["title"],
                "video_path": video_path,
                "thumbnail_path": thumb_path,
                "youtube_id": youtube_id,
            }
            logger.info(f"Long video complete: {seo['title']}")
            return result

        except Exception as e:
            self.db.update_video(video_id, status="failed", error_message=str(e))
            raise

    def run_shorts(self, dry_run: bool = False, topic: str = None) -> list:
        """Run the shorts pipeline — generates and uploads 3 shorts."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_dir = ensure_output_dir(self.config, "shorts")
        count = self.config.get("shorts", {}).get("count", 3)

        # Step 1: Generate topic if not provided
        pipeline_status.update("Shorts Topics", 70, "Generating shorts content...")
        if not topic:
            used_topics = self.db.get_used_topics()
            topic = self.content.generate_topic(used_topics)

        # Step 2: Generate scripts
        pipeline_status.update("Shorts Scripts", 72, "Writing shorts scripts...")
        shorts_scripts = self.content.generate_shorts_scripts(topic)

        # Step 3: Generate SEO for all shorts
        pipeline_status.update("Shorts SEO", 75, "Optimizing shorts SEO...")
        shorts_seo = self.seo.generate_shorts_seo(shorts_scripts, topic)

        results = []
        for i in range(min(count, len(shorts_scripts))):
            script = shorts_scripts[i]
            seo = shorts_seo[i] if i < len(shorts_seo) else {"title": script["title"], "description": "", "tags": []}

            video_id = self.db.create_video("short", script.get("title", topic))
            self.db.update_video(video_id, status="generating")

            try:
                # Audio
                progress = 78 + (i * 7)
                pipeline_status.update(f"Short {i+1} Audio", progress, f"Generating audio for short {i+1}...")
                audio_path = str(output_dir / f"short_{i+1}_audio.mp3")
                audio_info = self.audio.generate_audio(script["narration"], audio_path)
                self.db.update_video(video_id, audio_path=audio_path)

                # Video
                pipeline_status.update(f"Short {i+1} Video", progress + 2, f"Creating short {i+1} video...")
                video_path = str(output_dir / f"short_{i+1}_{date_str}.mp4")
                self.shorts.create_short(script, audio_path, video_path, gradient_index=i)
                self.db.update_video(video_id, video_path=video_path)

                # Thumbnail
                thumb_path = str(output_dir / f"short_{i+1}_thumb.jpg")
                self.thumbnail.generate_thumbnail(script.get("title", topic), thumb_path)
                self.db.update_video(video_id, thumbnail_path=thumb_path)

                # SEO metadata
                self.db.update_video(
                    video_id,
                    title=seo["title"],
                    description=seo["description"],
                    tags=json.dumps(seo.get("tags", [])),
                    script=json.dumps(script)
                )

                # Upload
                youtube_id = None
                if not dry_run:
                    pipeline_status.update(f"Short {i+1} Upload", progress + 5, f"Uploading short {i+1}...")
                    youtube_id = self.uploader.upload_short(video_path, seo, thumb_path)
                    self.db.update_video(
                        video_id,
                        youtube_id=youtube_id,
                        status="completed",
                        uploaded_at=datetime.now().isoformat()
                    )
                else:
                    self.db.update_video(video_id, status="completed")

                results.append({
                    "video_db_id": video_id,
                    "title": seo["title"],
                    "video_path": video_path,
                    "youtube_id": youtube_id,
                })

            except Exception as e:
                logger.error(f"Short {i+1} failed: {e}", exc_info=True)
                self.db.update_video(video_id, status="failed", error_message=str(e))
                results.append(None)

        completed = sum(1 for r in results if r is not None)
        logger.info(f"Shorts complete: {completed}/{count} succeeded")
        return results
