import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_scheduler = BackgroundScheduler(timezone=settings.timezone)


def _run_checks() -> None:
    from .database import get_db
    from .models import WatchlistEntry
    from .availability import check_entry
    from .notifications import send_notifications

    with get_db() as db:
        entries = db.query(WatchlistEntry).filter(WatchlistEntry.status == "watching").all()
        for entry in entries:
            try:
                new_results = check_entry(entry, db)
                if new_results:
                    send_notifications(entry, new_results, db)
                    logger.info("Found %d site(s) for %s", len(new_results), entry.campground_name)
            except Exception:
                logger.warning("Failed to check entry %d", entry.id, exc_info=True)


def get_scheduler() -> BackgroundScheduler:
    if not _scheduler.get_job("availability_check"):
        _scheduler.add_job(
            _run_checks,
            trigger=IntervalTrigger(minutes=settings.check_interval_minutes),
            id="availability_check",
            max_instances=1,
        )
    return _scheduler
