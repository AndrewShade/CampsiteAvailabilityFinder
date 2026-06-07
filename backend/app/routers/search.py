from fastapi import APIRouter, HTTPException
from ..schemas import CampgroundResult
from ..services.recreation_gov import search_campgrounds
from ..config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("", response_model=list[CampgroundResult])
async def search(q: str):
    if len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters.")
    if not settings.ridb_api_key:
        raise HTTPException(
            status_code=503,
            detail="RIDB_API_KEY is not configured. Get a free key at https://ridb.recreation.gov/apikeys.",
        )
    return await search_campgrounds(q.strip())
