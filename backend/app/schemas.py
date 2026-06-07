from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


# ── Watchlist ────────────────────────────────────────────────────────────────

class WatchlistEntryCreate(BaseModel):
    campground_id: str
    campground_name: str
    park_name: str
    start_date: date
    end_date: date
    min_nights: int = 1
    site_types: str = ""


class WatchlistEntryUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_nights: Optional[int] = None
    site_types: Optional[str] = None
    status: Optional[str] = None


class AvailabilityResultOut(BaseModel):
    id: int
    campsite_id: str
    campsite_name: str
    site_type: str
    loop: str
    available_dates: str  # raw JSON; client parses it
    found_at: datetime
    notification_sent: bool

    model_config = {"from_attributes": True}


class WatchlistEntryOut(BaseModel):
    id: int
    campground_id: str
    campground_name: str
    park_name: str
    start_date: date
    end_date: date
    min_nights: int
    site_types: str
    status: str
    last_checked: Optional[datetime]
    created_at: datetime
    results: list[AvailabilityResultOut]

    model_config = {"from_attributes": True}


# ── Search ───────────────────────────────────────────────────────────────────

class CampgroundResult(BaseModel):
    facility_id: str
    facility_name: str
    parent_name: str
    city: str
    state: str
    latitude: float
    longitude: float
    reservable: bool
    description: str


# ── Webhooks ─────────────────────────────────────────────────────────────────

class WebhookCreate(BaseModel):
    name: str
    webhook_type: str
    url: str


class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    webhook_type: Optional[str] = None
    url: Optional[str] = None
    enabled: Optional[bool] = None


class WebhookOut(BaseModel):
    id: int
    name: str
    webhook_type: str
    url: str
    enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── App settings ─────────────────────────────────────────────────────────────

class AppSettings(BaseModel):
    check_interval_minutes: int
    ridb_api_key_configured: bool
