import json
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session
from .models import WatchlistEntry, AvailabilityResult
from .recreation_gov import get_availability, get_campsite_type_map

_AVAILABLE = {"Available", "Open"}


def check_entry(entry: WatchlistEntry, db: Session) -> list[AvailabilityResult]:
    """Poll Recreation.gov and persist any newly available campsites for this entry."""
    campsites = get_availability(entry.campground_id, entry.start_date, entry.end_date)

    type_filter = {t.strip().upper() for t in entry.site_types.split(",") if t.strip()}
    ridb_type_map = get_campsite_type_map(entry.campground_id) if type_filter else {}
    desired = {
        (entry.start_date + timedelta(days=i)).isoformat()
        for i in range((entry.end_date - entry.start_date).days + 1)
    }

    # Snapshot which (campsite_id, dates) combos were already notified so we can
    # preserve notification_sent=True after clearing — prevents the scheduler from
    # re-pinging for sites that haven't changed since the last notification.
    prev_notified: set[tuple] = {
        (r.campsite_id, r.available_dates)
        for r in db.query(AvailabilityResult).filter_by(entry_id=entry.id, notification_sent=True)
    }

    # Clear all existing results so stale filter/date results never persist across edits.
    db.query(AvailabilityResult).filter_by(entry_id=entry.id).delete()

    all_results: list[AvailabilityResult] = []
    new_results: list[AvailabilityResult] = []

    for site_id, site in campsites.items():
        if site.get("type_of_use", "").upper() not in ("OVERNIGHT", ""):
            continue
        site_type = ridb_type_map.get(str(site_id)) or site.get("type", "Unknown")
        if type_filter and site_type.upper() not in type_filter:
            continue

        windows = _consecutive_windows(site.get("availabilities", {}), desired, entry.min_nights)
        windows = _filter_by_days(windows, entry.check_in_day, entry.check_out_day, entry.min_nights, entry.max_nights)
        if not windows:
            continue

        site_name = f"Site {site.get('site', site_id)}"
        site_loop = site.get("loop", "")
        for window in windows:
            available_dates_json = json.dumps(sorted(window))
            already_notified = (site_id, available_dates_json) in prev_notified
            result = AvailabilityResult(
                entry_id=entry.id,
                campsite_id=site_id,
                campsite_name=site_name,
                site_type=site_type,
                loop=site_loop,
                available_dates=available_dates_json,
                notification_sent=already_notified,
            )
            db.add(result)
            all_results.append(result)
            if not already_notified:
                new_results.append(result)

    entry.last_checked = datetime.now(timezone.utc).replace(tzinfo=None)
    entry.status = "found" if all_results else "watching"
    db.commit()
    for r in all_results:
        db.refresh(r)
    return new_results


def _filter_by_days(
    windows: list[list[str]],
    check_in_day: str | None,
    check_out_day: str | None,
    min_nights: int,
    max_nights: int | None = None,
) -> list[list[str]]:
    in_days = {int(d) for d in str(check_in_day).split(",") if d} if check_in_day is not None else set()
    out_days = {int(d) for d in str(check_out_day).split(",") if d} if check_out_day is not None else set()
    if not in_days and not out_days and max_nights is None:
        return windows

    # Slide through each window extracting sub-windows that satisfy the day/length constraints.
    # A whole run like Mon–Sun must not be rejected just because it doesn't start on Friday —
    # the valid Fri check-in sub-window (and max_nights cap) is enforced here, not upstream.
    result: list[list[str]] = []
    seen: set[tuple] = set()
    for window in windows:
        for i in range(len(window)):
            if in_days and date.fromisoformat(window[i]).weekday() not in in_days:
                continue
            j_max = min(i + max_nights - 1, len(window) - 1) if max_nights else len(window) - 1
            for j in range(i + min_nights - 1, j_max + 1):
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
