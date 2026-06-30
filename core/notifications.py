import json
import logging
from collections import defaultdict
from datetime import date as _date
import httpx
from sqlalchemy.orm import Session
from .models import AvailabilityResult, NotificationWebhook, WatchlistEntry

logger = logging.getLogger(__name__)
BOOKING_URL = "https://www.recreation.gov/camping/campsites/{site_id}"


def _format_date_spans(dates: list[str]) -> str:
    """Convert a sorted date list into a human-readable span string, handling gaps.

    ["2026-07-03","2026-07-04","2026-07-10","2026-07-11"]
    → "2026-07-03 – 2026-07-04 (2 nights) · 2026-07-10 – 2026-07-11 (2 nights)"
    """
    runs: list[tuple[str, str]] = []
    run_start = dates[0]
    for i in range(1, len(dates)):
        prev = _date.fromisoformat(dates[i - 1])
        curr = _date.fromisoformat(dates[i])
        if (curr - prev).days != 1:
            runs.append((run_start, dates[i - 1]))
            run_start = dates[i]
    runs.append((run_start, dates[-1]))

    parts = []
    for start, end in runs:
        n = (_date.fromisoformat(end) - _date.fromisoformat(start)).days + 1
        nights = f"{n} night{'s' if n != 1 else ''}"
        span = f"{start} – {end}" if start != end else start
        parts.append(f"{span} ({nights})")
    return " · ".join(parts)


def send_notifications(
    entry: WatchlistEntry, results: list[AvailabilityResult], db: Session
) -> None:
    webhooks = db.query(NotificationWebhook).filter_by(enabled=True).all()
    if not webhooks:
        return

    unsent = [r for r in results if not r.notification_sent]
    if not unsent:
        return

    # Group by (site_type, sorted available_dates) so same-type sites with the
    # same window get one message instead of one per site.
    groups: dict[tuple, list[AvailabilityResult]] = defaultdict(list)
    for r in unsent:
        key = (r.site_type, r.available_dates)
        groups[key].append(r)

    with httpx.Client(timeout=10) as client:
        for group in groups.values():
            for webhook in webhooks:
                payload = _build_payload(webhook.webhook_type, entry, group)
                try:
                    client.post(webhook.url, json=payload)
                except Exception as exc:
                    logger.warning("Webhook %d failed: %s", webhook.id, exc)
            for r in group:
                r.notification_sent = True

    db.commit()


def _build_payload(webhook_type: str, entry: WatchlistEntry, group: list[AvailabilityResult]) -> dict:
    first = group[0]
    dates: list[str] = json.loads(first.available_dates)
    span = _format_date_spans(dates)
    site_type = first.site_type
    site_count = len(group)

    # List site names/numbers; link the first one for quick booking
    site_names = ", ".join(r.campsite_name for r in group)
    booking = BOOKING_URL.format(site_id=first.campsite_id)

    if webhook_type == "slack":
        sites_line = f"*Sites:* {site_names} ({site_type})"
        return {
            "text": (
                f":tent: *{site_count} Campsite{'s' if site_count > 1 else ''} Available!*\n"
                f"{sites_line}\n"
                f"*Campground:* {entry.campground_name} — {entry.park_name}\n"
                f"*Dates:* {span}\n"
                f"*Book now:* {booking}"
            )
        }

    if webhook_type == "discord":
        return {
            "embeds": [{
                "title": f"{site_count} Campsite{'s' if site_count > 1 else ''} Available!",
                "color": 0x22C55E,
                "url": booking,
                "fields": [
                    {"name": "Sites", "value": f"{site_names}\n({site_type})", "inline": False},
                    {"name": "Campground", "value": entry.campground_name, "inline": True},
                    {"name": "Park", "value": entry.park_name, "inline": True},
                    {"name": "Dates", "value": span, "inline": False},
                ],
            }]
        }

    # generic JSON POST
    return {
        "campground": entry.campground_name,
        "park": entry.park_name,
        "site_type": site_type,
        "sites": [{"campsite_id": r.campsite_id, "campsite_name": r.campsite_name} for r in group],
        "available_dates": dates,
        "booking_url": booking,
    }
