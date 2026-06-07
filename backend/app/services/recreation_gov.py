from datetime import date
from typing import Any
import httpx
from ..config import get_settings

settings = get_settings()

RIDB_BASE = "https://ridb.recreation.gov/api/v1"
AVAIL_BASE = "https://www.recreation.gov/api/camps/availability/campground"

_HEADERS = {
    "User-Agent": (
        "CampsiteAvailabilityFinder/1.0 "
        "(https://github.com/AndrewShade/CampsiteAvailabilityFinder)"
    )
}


async def search_campgrounds(query: str) -> list[dict]:
    if not settings.ridb_api_key:
        return []
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{RIDB_BASE}/campgrounds",
            params={"query": query, "limit": 20, "apikey": settings.ridb_api_key},
            headers=_HEADERS,
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    for facility in data.get("RECDATA", []):
        addr = (facility.get("FACILITYADDRESS") or [{}])[0]
        results.append(
            {
                "facility_id": facility["FacilityID"],
                "facility_name": facility["FacilityName"].strip(),
                "parent_name": facility.get("ParentRecAreaName", ""),
                "city": addr.get("City", ""),
                "state": addr.get("AddressStateCode", ""),
                "latitude": float(facility.get("FacilityLatitude") or 0),
                "longitude": float(facility.get("FacilityLongitude") or 0),
                "reservable": bool(facility.get("Reservable", False)),
                "description": (facility.get("FacilityDescription") or "")[:300].strip(),
            }
        )
    return results


async def get_availability(
    campground_id: str, start_date: date, end_date: date
) -> dict[str, Any]:
    """Fetch and merge availability for every month spanning start_date → end_date."""
    months = _months_in_range(start_date, end_date)
    merged: dict[str, Any] = {}

    async with httpx.AsyncClient(timeout=15) as client:
        for month in months:
            url = f"{AVAIL_BASE}/{campground_id}/month"
            try:
                resp = await client.get(
                    url,
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
