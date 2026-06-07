from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import WatchlistEntry
from ..schemas import WatchlistEntryCreate, WatchlistEntryUpdate, WatchlistEntryOut
from ..services.availability import check_entry
from ..services.notifications import send_notifications

router = APIRouter()


@router.get("", response_model=list[WatchlistEntryOut])
def list_watchlist(db: Session = Depends(get_db)):
    return db.query(WatchlistEntry).order_by(WatchlistEntry.created_at.desc()).all()


@router.post("", response_model=WatchlistEntryOut, status_code=201)
def create_entry(body: WatchlistEntryCreate, db: Session = Depends(get_db)):
    entry = WatchlistEntry(**body.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.patch("/{entry_id}", response_model=WatchlistEntryOut)
def update_entry(entry_id: int, body: WatchlistEntryUpdate, db: Session = Depends(get_db)):
    entry = _get_or_404(entry_id, db)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=204)
def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = _get_or_404(entry_id, db)
    db.delete(entry)
    db.commit()


@router.post("/{entry_id}/check", response_model=WatchlistEntryOut)
async def force_check(entry_id: int, db: Session = Depends(get_db)):
    entry = _get_or_404(entry_id, db)
    new_results = await check_entry(entry, db)
    if new_results:
        await send_notifications(entry, new_results, db)
    db.refresh(entry)
    return entry


def _get_or_404(entry_id: int, db: Session) -> WatchlistEntry:
    entry = db.get(WatchlistEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found.")
    return entry
