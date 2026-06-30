import json
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from .models import WatchlistEntry, AvailabilityResult
from .recreation_gov import get_availability

_AVAILABLE = {"Available", "Open"}


def check_entry(entry: WatchlistEntry, db: Session) -> list[AvailabilityResult]:
    """Poll Recreation.gov and persist any newly available campsites for this entry."""
    campsites = get_availability(entry.campground_id, entry.start_date, entry.end_date)

    type_filter = {t.strip().upper() for t in entry.site_types.split(",") if t.strip()}
    desired = {
        (entry.start_date + timedelta(days=i)).isoformat()
        for i in range((entry.end_date - entry.start_date).days + 1)
    }

    new_results: list[AvailabilityResult] = []

    for site_id, site in campsites.items():
        if site.get("type_of_use", "").upper() not in ("OVERNIGHT", ""):
            continue
        if type_filter and site.get("type", "").upper() not in type_filter:
            continue

        windows = _consecutive_windows(site.get("availabilities", {}), desired, entry.min_nights)
        windows = _filter_by_days(windows, entry.check_in_day, entry.check_out_day, entry.min_nights)
        if not windows:
            continue

        available_dates = sorted({d for window in windows for d in window})

        existing = db.query(AvailabilityResult).filter_by(
            entry_id=entry.id, campsite_id=site_id
        ).first()
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


def _filter_by_days(
    windows: list[list[str]], check_in_day: str | None, check_out_day: str | None, min_nights: int
) -> list[list[str]]:
    in_days = {int(d) for d in check_in_day.split(",") if d} if check_in_day else set()
    out_days = {int(d) for d in check_out_day.split(",") if d} if check_out_day else set()
    if not in_days and not out_days:
        return windows

    # Slide through each window extracting sub-windows that satisfy the day constraints.
    # A whole window like Thu–Sun must not be rejected just because it doesn't start on Friday —
    # there may be a valid Fri check-in sub-window inside it.
    result: list[list[str]] = []
    seen: set[tuple] = set()
    for window in windows:
        for i in range(len(window)):
            if in_days and date.fromisoformat(window[i]).weekday() not in in_days:
                continue
            for j in range(i + min_nights - 1, len(window)):
                checkout = date.fromisoformat(window[j]) + timedelta(days=1)
                if out_days and checkout.weekday() not in out_days:
                    continue
                sub = tuple(window[i:j + 1])
                if sub not in seen:
                    seen.add(sub)
                    result.append(list(sub))
    return result


def _consecutive_windows(
    availabilities: dict, desired: set, min_nights: int
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
