"""FastAPI web dashboard for the YouTube Automation Platform."""

import threading
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.database import Database
from src.pipeline import DailyPipeline, pipeline_status
from src.utils import load_config

app = FastAPI(title="YouTube Automation Platform", version="1.0.0")

# Static files and templates
dashboard_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(dashboard_dir / "static")), name="static")
templates = Jinja2Templates(directory=str(dashboard_dir / "templates"))


def _get_db() -> Database:
    return Database()


# ─── Pages ────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    db = _get_db()
    stats = db.get_stats()
    recent_videos = db.get_recent_videos(limit=20)
    recent_runs = db.get_recent_runs(limit=10)
    config = load_config()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "stats": stats,
        "videos": recent_videos,
        "runs": recent_runs,
        "config": config,
        "status": pipeline_status.to_dict()
    })


# ─── API Endpoints ────────────────────────────────────────────

@app.get("/api/status")
async def get_status():
    """Get current pipeline status."""
    return JSONResponse(pipeline_status.to_dict())


@app.get("/api/stats")
async def get_stats():
    """Get platform statistics."""
    db = _get_db()
    return JSONResponse(db.get_stats())


@app.get("/api/videos")
async def get_videos():
    """Get recent videos."""
    db = _get_db()
    videos = db.get_recent_videos(limit=50)
    return JSONResponse(videos)


@app.get("/api/runs")
async def get_runs():
    """Get recent pipeline runs."""
    db = _get_db()
    runs = db.get_recent_runs(limit=20)
    return JSONResponse(runs)


@app.post("/api/trigger/{run_type}")
async def trigger_pipeline(run_type: str, dry_run: bool = False):
    """Trigger a pipeline run."""
    if pipeline_status.running:
        return JSONResponse(
            {"error": "Pipeline is already running"},
            status_code=409
        )

    valid_types = ["daily", "long", "shorts"]
    if run_type not in valid_types:
        return JSONResponse(
            {"error": f"Invalid type. Choose: {valid_types}"},
            status_code=400
        )

    def _run():
        config = load_config()
        pipeline = DailyPipeline(config)
        if run_type == "daily":
            pipeline.run_daily(dry_run=dry_run)
        elif run_type == "long":
            pipeline.run_long_video(dry_run=dry_run)
        elif run_type == "shorts":
            pipeline.run_shorts(dry_run=dry_run)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return JSONResponse({
        "message": f"Pipeline '{run_type}' triggered",
        "dry_run": dry_run
    })


@app.get("/api/config")
async def get_config():
    """Get current configuration (sanitized)."""
    config = load_config()
    # Remove sensitive keys
    safe_config = {k: v for k, v in config.items() if k != "ai"}
    safe_config["ai"] = {
        "model": config.get("ai", {}).get("model", "N/A"),
        "api_key_set": bool(config.get("ai", {}).get("api_key"))
    }
    return JSONResponse(safe_config)
