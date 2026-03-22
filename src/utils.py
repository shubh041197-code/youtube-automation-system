"""Shared utilities: config loading, logging, retry decorator, file helpers."""

import functools
import logging
import os
import time
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

_config_cache = None


def load_config(config_path: str = "config/config.yaml") -> dict:
    """Load YAML configuration file with environment variable overrides."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path) as f:
        config = yaml.safe_load(f)

    # Environment variable overrides
    if os.getenv("AI_API_KEY"):
        config.setdefault("ai", {})["api_key"] = os.getenv("AI_API_KEY")
    if os.getenv("AI_API_BASE_URL"):
        config["ai"]["api_base_url"] = os.getenv("AI_API_BASE_URL")
    if os.getenv("AI_MODEL"):
        config["ai"]["model"] = os.getenv("AI_MODEL")
    if os.getenv("SCHEDULE_HOUR"):
        config.setdefault("schedule", {})["hour"] = int(os.getenv("SCHEDULE_HOUR"))
    if os.getenv("VIDEO_NICHE"):
        config.setdefault("content", {})["niche"] = os.getenv("VIDEO_NICHE")

    _config_cache = config
    return config


def reset_config_cache():
    """Reset the cached config (useful for testing)."""
    global _config_cache
    _config_cache = None


def setup_logging(config: dict = None) -> logging.Logger:
    """Set up application logging."""
    if config is None:
        config = load_config()

    log_config = config.get("logging", {})
    level = getattr(logging, log_config.get("level", "INFO").upper())
    log_file = log_config.get("file", "automation.log")

    logger = logging.getLogger("youtube_automation")
    logger.setLevel(level)

    if not logger.handlers:
        # Console handler
        console = logging.StreamHandler()
        console.setLevel(level)
        console.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        logger.addHandler(console)

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        logger.addHandler(file_handler)

    return logger


def retry(max_attempts: int = 3, backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """Retry decorator with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger("youtube_automation")
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        wait = backoff ** attempt
                        logger.warning(
                            f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                            f"Retrying in {wait:.1f}s..."
                        )
                        time.sleep(wait)
                    else:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
            raise last_exception
        return wrapper
    return decorator


def ensure_output_dir(config: dict = None, subdir: str = "") -> Path:
    """Create and return the output directory path for today's run."""
    if config is None:
        config = load_config()

    base = Path(config.get("output", {}).get("base_dir", "output"))
    date_dir = base / datetime.now().strftime("%Y-%m-%d")
    if subdir:
        date_dir = date_dir / subdir

    date_dir.mkdir(parents=True, exist_ok=True)
    return date_dir


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def safe_filename(text: str, max_length: int = 50) -> str:
    """Convert text to a safe filename."""
    safe = "".join(c if c.isalnum() or c in " -_" else "" for c in text)
    safe = safe.strip().replace(" ", "_")[:max_length]
    return safe or "untitled"
