"""SQLite database for tracking videos, pipeline runs, and analytics."""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.utils import load_config, setup_logging

logger = setup_logging()

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_type TEXT NOT NULL,
    topic TEXT NOT NULL,
    script TEXT,
    audio_path TEXT,
    video_path TEXT,
    thumbnail_path TEXT,
    title TEXT,
    description TEXT,
    tags TEXT,
    youtube_id TEXT,
    status TEXT DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_type TEXT NOT NULL,
    status TEXT DEFAULT 'running',
    videos TEXT DEFAULT '[]',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);
"""


class Database:
    """SQLite database manager for the automation platform."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            config = load_config()
            db_path = config.get("database", {}).get("path", "automation.db")
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database tables."""
        with self._connect() as conn:
            conn.executescript(CREATE_TABLES_SQL)

    def _connect(self) -> sqlite3.Connection:
        """Create a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # --- Video Operations ---

    def create_video(self, video_type: str, topic: str) -> int:
        """Create a new video record. Returns the video ID."""
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO videos (video_type, topic, status) VALUES (?, ?, 'pending')",
                (video_type, topic)
            )
            return cursor.lastrowid

    def update_video(self, video_id: int, **kwargs):
        """Update video fields."""
        allowed = {
            "script", "audio_path", "video_path", "thumbnail_path",
            "title", "description", "tags", "youtube_id", "status",
            "error_message", "uploaded_at"
        }
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return

        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [video_id]

        with self._connect() as conn:
            conn.execute(f"UPDATE videos SET {set_clause} WHERE id = ?", values)

    def get_video(self, video_id: int) -> Optional[dict]:
        """Get a video by ID."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
            return dict(row) if row else None

    def get_recent_videos(self, limit: int = 50) -> list:
        """Get recent videos ordered by creation date."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM videos ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_used_topics(self, days: int = 30) -> list:
        """Get topics used in the last N days to avoid repeats."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT DISTINCT topic FROM videos WHERE created_at >= datetime('now', ?)",
                (f"-{days} days",)
            ).fetchall()
            return [r["topic"] for r in rows]

    # --- Pipeline Run Operations ---

    def create_run(self, run_type: str) -> int:
        """Create a new pipeline run. Returns run ID."""
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO pipeline_runs (run_type, status) VALUES (?, 'running')",
                (run_type,)
            )
            return cursor.lastrowid

    def update_run(self, run_id: int, **kwargs):
        """Update pipeline run fields."""
        allowed = {"status", "videos", "completed_at", "error_message"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return

        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [run_id]

        with self._connect() as conn:
            conn.execute(f"UPDATE pipeline_runs SET {set_clause} WHERE id = ?", values)

    def complete_run(self, run_id: int, status: str = "completed", error: str = None):
        """Mark a pipeline run as complete."""
        self.update_run(
            run_id,
            status=status,
            completed_at=datetime.now().isoformat(),
            error_message=error
        )

    def get_active_run(self) -> Optional[dict]:
        """Get the currently running pipeline, if any."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM pipeline_runs WHERE status = 'running' ORDER BY started_at DESC LIMIT 1"
            ).fetchone()
            return dict(row) if row else None

    def get_recent_runs(self, limit: int = 20) -> list:
        """Get recent pipeline runs."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    # --- Analytics ---

    def get_stats(self) -> dict:
        """Get platform statistics."""
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) as c FROM videos").fetchone()["c"]
            completed = conn.execute(
                "SELECT COUNT(*) as c FROM videos WHERE status = 'completed'"
            ).fetchone()["c"]
            uploaded = conn.execute(
                "SELECT COUNT(*) as c FROM videos WHERE youtube_id IS NOT NULL"
            ).fetchone()["c"]
            failed = conn.execute(
                "SELECT COUNT(*) as c FROM videos WHERE status = 'failed'"
            ).fetchone()["c"]
            runs = conn.execute("SELECT COUNT(*) as c FROM pipeline_runs").fetchone()["c"]

            return {
                "total_videos": total,
                "completed_videos": completed,
                "uploaded_videos": uploaded,
                "failed_videos": failed,
                "total_runs": runs,
                "success_rate": round(completed / total * 100, 1) if total > 0 else 0
            }
