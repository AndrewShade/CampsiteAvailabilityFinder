from datetime import date
import re
import threading
import time
import httpx
from .config import get_settings

settings = get_settings()

RIDB_BASE = "https://ridb.recreation.gov/api/v1"
AVAIL_BASE = "https://www.recreation.gov/api/camps/availability/campground"

_HEADERS = {
    "User-Agent": "CampsiteAvailabilityFinder/1.0 (github.com/AndrewShade/CampsiteAvailabilityFinder)"
}

# Global rate limiter — 45 req/min across all threads (headroom below the 50/min limit)
_rate_lock = threading.Lock()
_last_request_at: float = 0.0
_MIN_INTERVAL = 60.0 / 45


def _get(client: httpx.Client, url: str, **kwargs) -> httpx.Response:
    global _last_request_at
    with _rate_lock:
        wait = _MIN_INTERVAL - (time.monotonic() - _last_request_at)
        if wait > 0:
            time.sleep(wait)
        _last_request_at = time.monotonic()
    return client.get(url, **kwargs)


def search_by_name(query: str) -> list[dict]:
    with httpx.Client(timeout=10) as client:
        resp = _get(client,
            f"{RIDB_BASE}/facilities",
            params={"query": query, "limit": 50, "apikey": settings.ridb_api_key, "facilitytype": "Campground"},
            headers=_HEADERS,
        )
        resp.raise_for_status()
        results = [_parse_facility(f) for f in resp.json().get("RECDATA", [])]

    results.sort(key=lambda r: _name_score(query, r["facility_name"]), reverse=True)
    return results


def _name_score(query: str, facility_name: str) -> int:
    q = query.lower()
    name = facility_name.lower()
    if q == name:
        return 100
    if q in name:
        return 50
    return sum(1 for word in q.split() if word in name)


def search_by_park(park_name: str) -> list[dict]:
    with httpx.Client(timeout=10) as client:
        rec_area_ids = _search_rec_area_ids(client, park_name)
        seen: set[str] = set()
        results: list[dict] = []
        for rec_area_id in rec_area_ids:
            for facility in _facilities_for_rec_area(client, rec_area_id):
                fid = facility["FacilityID"]
                if fid not in seen:
                    seen.add(fid)
                    results.append(_parse_facility(facility))
    return results[:50]


def search_by_facility_id(facility_id: str) -> list[dict]:
    with httpx.Client(timeout=10) as client:
        resp = _get(client,
            f"{RIDB_BASE}/facilities/{facility_id.strip()}",
            params={"apikey": settings.ridb_api_key},
            headers=_HEADERS,
        )
        if resp.is_error:
            return []
        return [_parse_facility(resp.json())]


_campsite_cache: dict[str, list[dict]] = {}  # facility_id -> raw RECDATA


def _fetch_campsites(facility_id: str) -> list[dict]:
    if facility_id not in _campsite_cache:
        with httpx.Client(timeout=10) as client:
            resp = _get(client,
                f"{RIDB_BASE}/facilities/{facility_id}/campsites",
                params={"apikey": settings.ridb_api_key, "limit": 500},
                headers=_HEADERS,
            )
            _campsite_cache[facility_id] = [] if resp.is_error else resp.json().get("RECDATA", [])
    return _campsite_cache[facility_id]


def get_site_types(facility_id: str) -> dict[str, int]:
    """Return {CampsiteType: count} for overnight sites, sorted alphabetically."""
    counts: dict[str, int] = {}
    for site in _fetch_campsites(facility_id):
        if site.get("TypeOfUse", "").upper() not in ("OVERNIGHT", ""):
            continue
        t = site.get("CampsiteType", "").strip().upper()
        if t:
            counts[t] = counts.get(t, 0) + 1
    return dict(sorted(counts.items()))


def get_campsite_type_map(facility_id: str) -> dict[str, str]:
    """Return {campsite_id: CampsiteType} built from RIDB, used to resolve types during availability checks."""
    return {
        str(s["CampsiteID"]): s.get("CampsiteType", "").strip().upper()
        for s in _fetch_campsites(facility_id)
        if s.get("CampsiteID")
    }


def search_by_state(state_code: str) -> list[dict]:
    with httpx.Client(timeout=10) as client:
        resp = _get(client,
            f"{RIDB_BASE}/facilities",
            params={"state": state_code, "limit": 50, "apikey": settings.ridb_api_key, "facilitytype": "Campground"},
            headers=_HEADERS,
        )
        resp.raise_for_status()
        return [_parse_facility(f) for f in resp.json().get("RECDATA", [])]


def _search_rec_area_ids(client: httpx.Client, query: str) -> list[str]:
    resp = client.get(
        f"{RIDB_BASE}/recareas",
        params={"query": query, "limit": 5, "apikey": settings.ridb_api_key},
        headers=_HEADERS,
    )
    if resp.is_error:
        return []
    return [ra["RecAreaID"] for ra in resp.json().get("RECDATA", [])]


def _facilities_for_rec_area(client: httpx.Client, rec_area_id: str) -> list[dict]:
    resp = client.get(
        f"{RIDB_BASE}/recareas/{rec_area_id}/facilities",
        params={"apikey": settings.ridb_api_key, "facilitytype": "Campground", "limit": 50},
        headers=_HEADERS,
    )
    if resp.is_error:
        return []
    return resp.json().get("RECDATA", [])


def _parse_facility(facility: dict) -> dict:
    addr = (facility.get("FACILITYADDRESS") or [{}])[0]
    raw_desc = facility.get("FacilityDescription") or ""
    return {
        "facility_id": facility["FacilityID"],
        "facility_name": facility["FacilityName"].strip(),
        "parent_name": facility.get("ParentRecAreaName", ""),
        "city": addr.get("City", ""),
        "state": addr.get("AddressStateCode", ""),
        "reservable": bool(facility.get("Reservable", False)),
        "description": _strip_html(raw_desc)[:300],
    }


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text).strip()


def get_availability(campground_id: str, start_date: date, end_date: date) -> dict:
    months = _months_in_range(start_date, end_date)
    merged: dict = {}

    with httpx.Client(timeout=15) as client:
        for month in months:
            try:
                resp = _get(client,
                    f"{AVAIL_BASE}/{campground_id}/month",
                    params={"start_date": f"{month}T00:00:00.000Z"},
                    headers=_HEADERS,
                )
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPStatusError:
                continue

            for site_id, site in data.get("campsites", {}).items():
                if site_id not in merged:
                    merged[site_id] = {**site, "availabilities": {}}
                merged[site_id]["availabilities"].update(site.get("availabilities", {}))

    return merged


def _months_in_range(start: date, end: date) -> list[str]:
    months: list[str] = []
    current = start.replace(day=1)
    end_month = end.replace(day=1)
    while current <= end_month:
        months.append(current.isoformat())
        month = current.month + 1
        year = current.year + (1 if month > 12 else 0)
        current = current.replace(year=year, month=month if month <= 12 else 1)
    return months
