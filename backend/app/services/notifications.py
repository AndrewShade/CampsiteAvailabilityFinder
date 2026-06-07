import json
import logging
import httpx
from sqlalchemy.orm import Session
from ..models import AvailabilityResult, NotificationWebhook, WatchlistEntry

logger = logging.getLogger(__name__)

BOOKING_URL = "https://www.recreation.gov/camping/campsites/{site_id}"


def _slack_payload(entry: WatchlistEntry, result: AvailabilityResult) -> dict:
    dates: list[str] = json.loads(result.available_dates)
    span = f"{dates[0]} – {dates[-1]}" if len(dates) > 1 else dates[0]
    return {
        "text": (
            f":tent: *Campsite Available!*\n"
            f"*{result.campsite_name}* ({result.site_type})\n"
            f"*Campground:* {entry.campground_name} — {entry.park_name}\n"
            f"*Loop:* {result.loop or 'N/A'}\n"
            f"*Dates:* {span} ({len(dates)} night{'s' if len(dates) != 1 else ''})\n"
            f"*Book now:* {BOOKING_URL.format(site_id=result.campsite_id)}"
        )
    }


def _discord_payload(entry: WatchlistEntry, result: AvailabilityResult) -> dict:
    dates: list[str] = json.loads(result.available_dates)
    span = f"{dates[0]} – {dates[-1]}" if len(dates) > 1 else dates[0]
    return {
        "embeds": [
            {
                "title": "Campsite Available!",
                "color": 0x22C55E,
                "url": BOOKING_URL.format(site_id=result.campsite_id),
                "fields": [
                    {"name": "Site", "value": f"{result.campsite_name} ({result.site_type})", "inline": True},
                    {"name": "Campground", "value": entry.campground_name, "inline": True},
                    {"name": "Park", "value": entry.park_name, "inline": True},
                    {"name": "Loop", "value": result.loop or "N/A", "inline": True},
                    {"name": "Available Dates", "value": f"{span} ({len(dates)} night{'s' if len(dates) != 1 else ''})", "inline": False},
                ],
            }
        ]
    }


def _generic_payload(entry: WatchlistEntry, result: AvailabilityResult) -> dict:
    return {
        "campground": entry.campground_name,
        "park": entry.park_name,
        "campsite_id": result.campsite_id,
        "campsite_name": result.campsite_name,
        "site_type": result.site_type,
        "loop": result.loop,
        "available_dates": json.loads(result.available_dates),
        "booking_url": BOOKING_URL.format(site_id=result.campsite_id),
    }


async def send_notifications(
    entry: WatchlistEntry, results: list[AvailabilityResult], db: Session
) -> None:
    webhooks = db.query(NotificationWebhook).filter_by(enabled=True).all()
    if not webhooks:
        return

    async with httpx.AsyncClient(timeout=10) as client:
        for result in results:
            if result.notification_sent:
                continue
            for webhook in webhooks:
                if webhook.webhook_type == "slack":
                    payload = _slack_payload(entry, result)
                elif webhook.webhook_type == "discord":
                    payload = _discord_payload(entry, result)
                else:
                    payload = _generic_payload(entry, result)
                try:
                    await client.post(webhook.url, json=payload)
                except Exception as exc:
                    logger.warning("Webhook %d failed: %s", webhook.id, exc)
            result.notification_sent = True

    db.commit()
