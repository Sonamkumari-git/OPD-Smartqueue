"""Runtime configuration loaded from local environment variables only."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "OPD SmartQueue API"
    app_version: str = "0.1.0"
    app_env: str = "development"
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "opd_queue_management"
    jwt_secret: str = "change_this_in_local_env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    frontend_url: str = "http://localhost:3000"
    approaching_threshold: int = 2
    baseline_recent_weight: float = 0.50
    baseline_today_weight: float = 0.30
    baseline_historical_weight: float = 0.20

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_url.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
