"""Main entry point — CLI interface + scheduler for the YouTube Automation Platform."""

import argparse
import logging
import signal
import sys
import threading

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from src.pipeline import DailyPipeline, pipeline_status
from src.utils import load_config, setup_logging

logger = None


def run_pipeline(run_type: str = "daily", dry_run: bool = False):
    """Execute the content pipeline."""
    config = load_config()
    pipeline = DailyPipeline(config)

    if run_type == "daily":
        results = pipeline.run_daily(dry_run=dry_run)
    elif run_type == "long":
        results = {"long_video": pipeline.run_long_video(dry_run=dry_run)}
    elif run_type == "shorts":
        results = {"shorts": pipeline.run_shorts(dry_run=dry_run)}
    else:
        logger.error(f"Unknown run type: {run_type}")
        return

    # Summary
    errors = results.get("errors", [])
    if errors:
        logger.warning(f"Pipeline completed with {len(errors)} error(s):")
        for e in errors:
            logger.warning(f"  - {e}")
    else:
        logger.info("Pipeline completed successfully!")

    if results.get("long_video"):
        lv = results["long_video"]
        logger.info(f"  Long video: {lv.get('title', 'N/A')}")
        if lv.get("youtube_id"):
            logger.info(f"    -> https://youtube.com/watch?v={lv['youtube_id']}")

    for i, short in enumerate(results.get("shorts", [])):
        if short:
            logger.info(f"  Short {i+1}: {short.get('title', 'N/A')}")
            if short.get("youtube_id"):
                logger.info(f"    -> https://youtube.com/watch?v={short['youtube_id']}")


def start_scheduler():
    """Start the APScheduler for daily automated runs."""
    config = load_config()
    schedule_config = config.get("schedule", {})

    if not schedule_config.get("enabled", True):
        logger.info("Scheduler is disabled in config. Exiting.")
        return

    hour = schedule_config.get("hour", 6)
    minute = schedule_config.get("minute", 0)
    timezone = schedule_config.get("timezone", "UTC")

    scheduler = BlockingScheduler()
    trigger = CronTrigger(hour=hour, minute=minute, timezone=timezone)

    scheduler.add_job(
        run_pipeline,
        trigger=trigger,
        kwargs={"run_type": "daily", "dry_run": False},
        id="daily_pipeline",
        name="Daily YouTube Pipeline",
        misfire_grace_time=3600,  # 1 hour grace period
        max_instances=1
    )

    logger.info(f"Scheduler started: daily at {hour:02d}:{minute:02d} {timezone}")
    logger.info("Press Ctrl+C to stop.")

    # Graceful shutdown
    def shutdown(signum, frame):
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    scheduler.start()


def start_dashboard():
    """Start the web dashboard."""
    try:
        import uvicorn
        from dashboard.app import app

        config = load_config()
        logger.info("Starting dashboard at http://localhost:8000")
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except ImportError as e:
        logger.error(f"Dashboard dependencies missing: {e}")
        logger.error("Run: pip install fastapi uvicorn jinja2")
        sys.exit(1)


def main():
    """CLI entry point."""
    global logger

    parser = argparse.ArgumentParser(
        description="YouTube Automation Platform - AI-powered content pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main run                  # Run full daily pipeline (1 long + 3 shorts)
  python -m src.main run --type long      # Generate only long-form video
  python -m src.main run --type shorts    # Generate only shorts
  python -m src.main run --dry-run        # Run without uploading to YouTube
  python -m src.main schedule             # Start daily scheduler
  python -m src.main dashboard            # Start web dashboard
  python -m src.main status               # Show platform status
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run the content pipeline")
    run_parser.add_argument(
        "--type", choices=["daily", "long", "shorts"], default="daily",
        help="Type of content to generate (default: daily)"
    )
    run_parser.add_argument(
        "--dry-run", action="store_true",
        help="Run pipeline without uploading to YouTube"
    )

    # Schedule command
    subparsers.add_parser("schedule", help="Start the daily scheduler")

    # Dashboard command
    subparsers.add_parser("dashboard", help="Start the web dashboard")

    # Status command
    subparsers.add_parser("status", help="Show platform status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Setup
    config = load_config()
    logger = setup_logging(config)

    if args.command == "run":
        logger.info(f"Starting {args.type} pipeline (dry_run={args.dry_run})")
        run_pipeline(run_type=args.type, dry_run=args.dry_run)

    elif args.command == "schedule":
        start_scheduler()

    elif args.command == "dashboard":
        start_dashboard()

    elif args.command == "status":
        from src.database import Database
        db = Database()
        stats = db.get_stats()
        active = db.get_active_run()

        print("\n=== YouTube Automation Platform Status ===\n")
        print(f"  Total videos generated:  {stats['total_videos']}")
        print(f"  Successfully completed:  {stats['completed_videos']}")
        print(f"  Uploaded to YouTube:     {stats['uploaded_videos']}")
        print(f"  Failed:                  {stats['failed_videos']}")
        print(f"  Success rate:            {stats['success_rate']}%")
        print(f"  Total pipeline runs:     {stats['total_runs']}")
        print(f"\n  Pipeline active:         {'Yes' if active else 'No'}")
        if active:
            print(f"  Current run type:        {active.get('run_type')}")
            print(f"  Started at:              {active.get('started_at')}")
        print()


if __name__ == "__main__":
    main()
