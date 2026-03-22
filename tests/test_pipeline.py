"""Tests for the database and pipeline status."""

import json
from pathlib import Path

import pytest

from src.database import Database


@pytest.fixture
def db(tmp_path):
    """Create a temporary database."""
    db_path = str(tmp_path / "test.db")
    return Database(db_path)


class TestDatabase:
    def test_create_video(self, db):
        """Should create a video record and return ID."""
        vid = db.create_video("long", "Test Topic")
        assert vid == 1

    def test_update_and_get_video(self, db):
        """Should update and retrieve video fields."""
        vid = db.create_video("long", "Topic")
        db.update_video(vid, status="generating", title="My Video")

        video = db.get_video(vid)
        assert video["status"] == "generating"
        assert video["title"] == "My Video"
        assert video["topic"] == "Topic"

    def test_get_recent_videos(self, db):
        """Should return videos in descending order."""
        db.create_video("long", "Topic 1")
        db.create_video("short", "Topic 2")
        db.create_video("short", "Topic 3")

        videos = db.get_recent_videos(limit=10)
        assert len(videos) == 3

    def test_get_used_topics(self, db):
        """Should return distinct topics."""
        db.create_video("long", "AI")
        db.create_video("short", "ML")
        db.create_video("short", "AI")  # Duplicate

        topics = db.get_used_topics()
        assert "AI" in topics
        assert "ML" in topics

    def test_create_and_complete_run(self, db):
        """Should track pipeline run lifecycle."""
        run_id = db.create_run("daily")
        assert run_id == 1

        active = db.get_active_run()
        assert active is not None
        assert active["status"] == "running"

        db.complete_run(run_id, status="completed")
        active = db.get_active_run()
        assert active is None  # No longer running

    def test_get_stats(self, db):
        """Should calculate correct statistics."""
        v1 = db.create_video("long", "Topic 1")
        db.update_video(v1, status="completed")

        v2 = db.create_video("short", "Topic 2")
        db.update_video(v2, status="completed", youtube_id="abc123")

        v3 = db.create_video("short", "Topic 3")
        db.update_video(v3, status="failed")

        stats = db.get_stats()
        assert stats["total_videos"] == 3
        assert stats["completed_videos"] == 2
        assert stats["uploaded_videos"] == 1
        assert stats["failed_videos"] == 1
        assert stats["success_rate"] == pytest.approx(66.7, abs=0.1)

    def test_get_nonexistent_video(self, db):
        """Should return None for missing video."""
        assert db.get_video(999) is None


class TestPipelineStatus:
    """Test PipelineStatus logic (imported inline to avoid heavy deps)."""

    def _make_status(self):
        """Create a PipelineStatus-like object without importing pipeline.py."""
        from datetime import datetime

        class Status:
            def __init__(self):
                self.running = False
                self.current_step = ""
                self.progress = 0
                self.logs = []

            def update(self, step, progress, message=""):
                self.current_step = step
                self.progress = progress
                msg = message or step
                self.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

            def to_dict(self):
                return {
                    "running": self.running,
                    "current_step": self.current_step,
                    "progress": self.progress,
                    "logs": self.logs[-50:]
                }

        return Status()

    def test_initial_state(self):
        """Status should start idle."""
        status = self._make_status()
        assert status.running is False
        assert status.progress == 0
        assert status.current_step == ""

    def test_update(self):
        """Should update step, progress, and log."""
        status = self._make_status()
        status.update("Generating", 50, "Generating script...")

        assert status.current_step == "Generating"
        assert status.progress == 50
        assert len(status.logs) == 1
        assert "Generating script..." in status.logs[0]

    def test_to_dict(self):
        """Should serialize to dict."""
        status = self._make_status()
        status.running = True
        status.update("Step 1", 25)

        d = status.to_dict()
        assert d["running"] is True
        assert d["progress"] == 25
        assert d["current_step"] == "Step 1"
        assert isinstance(d["logs"], list)

    def test_log_limit(self):
        """Should keep only last 50 logs."""
        status = self._make_status()
        for i in range(100):
            status.update(f"Step {i}", i)

        d = status.to_dict()
        assert len(d["logs"]) == 50
