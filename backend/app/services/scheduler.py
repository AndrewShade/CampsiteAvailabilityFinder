import asyncio
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from ..config import get_settings
from ..database import SessionLocal
from ..models import WatchlistEntry
from .availability import check_entry
from .notifications import send_notifications

logger = logging.getLogger(__name__)
settings = get_settings()

_scheduler = BackgroundScheduler(timezone="UTC")


def _run_checks() -> None:
    db = SessionLocal()
    try:
        entries = db.query(WatchlistEntry).filter(WatchlistEntry.status == "watching").all()
        if not entries:
            return
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_check_all(entries, db))
        finally:
            loop.close()
            asyncio.set_event_loop(None)
    except Exception:
        logger.exception("Unhandled error in availability check")
    finally:
        db.close()


async def _check_all(entries: list[WatchlistEntry], db) -> None:
    for entry in entries:
        try:
            new_results = await check_entry(entry, db)
            if new_results:
                await send_notifications(entry, new_results, db)
                logger.info(
                    "Found %d new site(s) for entry %d (%s)",
                    len(new_results),
                    entry.id,
                    entry.campground_name,
                )
        except Exception:
            logger.warning("Failed to check entry %d", entry.id, exc_info=True)


def start_scheduler() -> None:
    _scheduler.add_job(
        _run_checks,
        trigger=IntervalTrigger(minutes=settings.check_interval_minutes),
        id="availability_check",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()
    logger.info("Scheduler started — checking every %d min", settings.check_interval_minutes)


def stop_scheduler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
