from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ridb_api_key: str = ""
    check_interval_minutes: int = 15
    database_url: str = "sqlite:///./data/campfinder.db"
    timezone: str = "UTC"
    discord_webhook_url: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
