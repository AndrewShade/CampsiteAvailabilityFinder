import json
import logging
import httpx
from sqlalchemy.orm import Session
from .models import AvailabilityResult, NotificationWebhook, WatchlistEntry

logger = logging.getLogger(__name__)
BOOKING_URL = "https://www.recreation.gov/camping/campsites/{site_id}"


def send_notifications(
    entry: WatchlistEntry, results: list[AvailabilityResult], db: Session
) -> None:
    webhooks = db.query(NotificationWebhook).filter_by(enabled=True).all()
    if not webhooks:
        return

    with httpx.Client(timeout=10) as client:
        for result in results:
            if result.notification_sent:
                continue
            for webhook in webhooks:
                payload = _build_payload(webhook.webhook_type, entry, result)
                try:
                    client.post(webhook.url, json=payload)
                except Exception as exc:
                    logger.warning("Webhook %d failed: %s", webhook.id, exc)
            result.notification_sent = True

    db.commit()


def _build_payload(webhook_type: str, entry: WatchlistEntry, result: AvailabilityResult) -> dict:
    dates: list[str] = json.loads(result.available_dates)
    span = f"{dates[0]} – {dates[-1]}" if len(dates) > 1 else dates[0]
    nights = f"{len(dates)} night{'s' if len(dates) != 1 else ''}"
    booking = BOOKING_URL.format(site_id=result.campsite_id)

    if webhook_type == "slack":
        return {
            "text": (
                f":tent: *Campsite Available!*\n"
                f"*{result.campsite_name}* ({result.site_type})\n"
                f"*Campground:* {entry.campground_name} — {entry.park_name}\n"
                f"*Dates:* {span} ({nights})\n"
                f"*Book now:* {booking}"
            )
        }

    if webhook_type == "discord":
        return {
            "embeds": [{
                "title": "Campsite Available!",
                "color": 0x22C55E,
                "url": booking,
                "fields": [
                    {"name": "Site", "value": f"{result.campsite_name} ({result.site_type})", "inline": True},
                    {"name": "Campground", "value": entry.campground_name, "inline": True},
                    {"name": "Park", "value": entry.park_name, "inline": True},
                    {"name": "Dates", "value": f"{span} ({nights})", "inline": False},
                ],
            }]
        }

    # generic JSON POST
    return {
        "campground": entry.campground_name,
        "park": entry.park_name,
        "campsite_id": result.campsite_id,
        "campsite_name": result.campsite_name,
        "available_dates": dates,
        "booking_url": booking,
    }
