# YouTube Automation Platform

AI-powered YouTube automation system that generates and uploads **1 long-form video + 3 shorts daily** — fully automated, zero manual intervention.

## Features

- **AI Content Engine** — Generates unique topics, scripts, and SEO metadata (no repeats)
- **Text-to-Speech** — High-quality narration via edge-tts (free, no API key needed)
- **Video Assembly** — MoviePy creates professional videos with text overlays, transitions, background music
- **Shorts Generator** — Vertical 9:16 shorts with mobile-optimized text and gradient backgrounds
- **Thumbnail Engine** — Auto-generated thumbnails with 3 template styles
- **SEO Optimization** — AI-powered titles, descriptions, tags, and hashtags
- **YouTube Upload** — OAuth2 auto-upload with resumable uploads and retry logic
- **Web Dashboard** — Monitor, trigger, and configure everything from your browser
- **Daily Scheduler** — APScheduler runs the full pipeline automatically

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API keys:
#   AI_API_KEY=your-openai-api-key
```

Edit `config/config.yaml` to customize your niche, schedule, voice, and upload settings.

### 3. YouTube API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable the **YouTube Data API v3**
3. Create OAuth 2.0 credentials (Desktop app)
4. Download `client_secret.json` to the project root
5. First run will open a browser for OAuth consent

### 4. Run

```bash
# Full daily pipeline (1 long video + 3 shorts)
python -m src.main run

# Dry run (no YouTube upload)
python -m src.main run --dry-run

# Long video only
python -m src.main run --type long

# Shorts only
python -m src.main run --type shorts

# Start daily scheduler (auto-runs at configured time)
python -m src.main schedule

# Start web dashboard
python -m src.main dashboard

# Check platform status
python -m src.main status
```

## Web Dashboard

Start the dashboard:

```bash
python -m src.main dashboard
```

Open http://localhost:8000 to:
- Trigger pipelines with one click
- Monitor live progress
- View video history and analytics
- See current configuration

## Project Structure

```
youtube-automation-system/
├── config/config.yaml          # All settings (niche, schedule, voice, etc.)
├── src/
│   ├── main.py                 # CLI entry point + scheduler
│   ├── pipeline.py             # Orchestrator
│   ├── content_engine.py       # AI topic/script generation
│   ├── audio_engine.py         # Text-to-speech (edge-tts)
│   ├── video_engine.py         # Video assembly (MoviePy)
│   ├── shorts_generator.py     # Shorts creation (9:16)
│   ├── thumbnail_engine.py     # Thumbnail generation (Pillow)
│   ├── seo_engine.py           # SEO optimization
│   ├── youtube_uploader.py     # YouTube API upload
│   ├── database.py             # SQLite tracking
│   └── utils.py                # Config, logging, retry
├── dashboard/                  # FastAPI web dashboard
├── assets/music/               # Background music (add .mp3 files)
├── output/                     # Generated content
└── tests/                      # Unit tests
```

## Configuration

All settings are in `config/config.yaml`:

| Setting | Description | Default |
|---------|-------------|---------|
| `content.niche` | Your channel topic | `technology` |
| `audio.voice` | TTS voice | `en-US-GuyNeural` |
| `schedule.hour` | Daily run hour (UTC) | `6` |
| `youtube.privacy_status` | Upload privacy | `private` |
| `shorts.count` | Shorts per day | `3` |
| `video.fps` | Video frame rate | `24` |

## Requirements

- Python 3.9+
- ffmpeg (for MoviePy video rendering)
- OpenAI API key (or compatible API)
- Google Cloud project with YouTube Data API v3

## License

MIT License - see [LICENSE](LICENSE) for details.
