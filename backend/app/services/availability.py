import json
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from ..models import WatchlistEntry, AvailabilityResult
from .recreation_gov import get_availability

_AVAILABLE = {"Available", "Open"}


async def check_entry(entry: WatchlistEntry, db: Session) -> list[AvailabilityResult]:
    """Poll Recreation.gov for entry's campground and persist any new available windows."""
    campsites = await get_availability(entry.campground_id, entry.start_date, entry.end_date)

    type_filter = {t.strip().upper() for t in entry.site_types.split(",") if t.strip()}
    desired = {(entry.start_date + timedelta(days=i)).isoformat() for i in range((entry.end_date - entry.start_date).days + 1)}

    new_results: list[AvailabilityResult] = []

    for site_id, site in campsites.items():
        if site.get("type_of_use", "").upper() not in ("OVERNIGHT", ""):
            continue
        if type_filter and site.get("type", "").upper() not in type_filter:
            continue

        windows = _consecutive_windows(site.get("availabilities", {}), desired, entry.min_nights)
        if not windows:
            continue

        available_dates = sorted({d for window in windows for d in window})

        existing = (
            db.query(AvailabilityResult)
            .filter_by(entry_id=entry.id, campsite_id=site_id)
            .first()
        )
        if existing and set(json.loads(existing.available_dates)) == set(available_dates):
            continue

        result = AvailabilityResult(
            entry_id=entry.id,
            campsite_id=site_id,
            campsite_name=f"Site {site.get('site', site_id)}",
            site_type=site.get("type", "Unknown"),
            loop=site.get("loop", ""),
            available_dates=json.dumps(available_dates),
        )
        db.add(result)
        new_results.append(result)

    entry.last_checked = datetime.utcnow()
    if new_results:
        entry.status = "found"
    db.commit()

    for r in new_results:
        db.refresh(r)

    return new_results


def _consecutive_windows(
    availabilities: dict[str, str],
    desired: set[str],
    min_nights: int,
) -> list[list[str]]:
    candidates = sorted(
        d[:10]
        for d, status in availabilities.items()
        if status in _AVAILABLE and d[:10] in desired
    )
    if not candidates:
        return []

    windows: list[list[str]] = []
    run = [candidates[0]]
    for i in range(1, len(candidates)):
        prev = date.fromisoformat(candidates[i - 1])
        curr = date.fromisoformat(candidates[i])
        if (curr - prev).days == 1:
            run.append(candidates[i])
        else:
            if len(run) >= min_nights:
                windows.append(run)
            run = [candidates[i]]
    if len(run) >= min_nights:
        windows.append(run)
    return windows
