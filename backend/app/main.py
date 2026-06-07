import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .database import engine, Base
from .routers import search, watchlist, settings as settings_router
from .services.scheduler import start_scheduler, stop_scheduler

settings = get_settings()

os.makedirs("/app/data", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Campsite Availability Finder",
    description="Monitor Recreation.gov campgrounds and get notified the moment a site opens up.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["settings"])


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok", "app": settings.app_name}
