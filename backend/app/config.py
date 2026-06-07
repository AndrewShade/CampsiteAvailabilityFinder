from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Campsite Availability Finder"
    debug: bool = False

    ridb_api_key: str = ""
    check_interval_minutes: int = 15
    database_url: str = "sqlite:////app/data/campfinder.db"
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
