from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from .database import Base


class WatchlistEntry(Base):
    __tablename__ = "watchlist_entries"

    id = Column(Integer, primary_key=True, index=True)
    campground_id = Column(String, nullable=False, index=True)
    campground_name = Column(String, nullable=False)
    park_name = Column(String, nullable=False)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    min_nights = Column(Integer, default=1)
    site_types = Column(String, default="")  # comma-separated filter, empty = any

    status = Column(String, default="watching")  # watching | found | paused
    last_checked = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    results = relationship(
        "AvailabilityResult",
        back_populates="entry",
        cascade="all, delete-orphan",
        order_by="AvailabilityResult.found_at.desc()",
    )


class AvailabilityResult(Base):
    __tablename__ = "availability_results"

    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("watchlist_entries.id"), nullable=False)
    campsite_id = Column(String, nullable=False)
    campsite_name = Column(String, nullable=False)
    site_type = Column(String, nullable=False)
    loop = Column(String, default="")
    available_dates = Column(Text, nullable=False)  # JSON list of "YYYY-MM-DD" strings
    found_at = Column(DateTime, default=datetime.utcnow)
    notification_sent = Column(Boolean, default=False)

    entry = relationship("WatchlistEntry", back_populates="results")


class NotificationWebhook(Base):
    __tablename__ = "notification_webhooks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    webhook_type = Column(String, nullable=False)  # slack | discord | generic
    url = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
