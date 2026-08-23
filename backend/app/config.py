"""Runtime configuration loaded from local environment variables only."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "OPD SmartQueue API"
    app_version: str = "0.1.0"
    app_env: str = "development"
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_server_selection_timeout_ms: int = 15000
    database_name: str = "opd_queue_management"
    jwt_secret: str = "change_this_in_local_env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    frontend_url: str = "http://localhost:3000"
    approaching_threshold: int = 2
    baseline_recent_weight: float = 0.50
    baseline_today_weight: float = 0.30
    baseline_historical_weight: float = 0.20
    login_max_attempts: int = 8
    login_window_seconds: int = 300

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_url.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() in {"production", "prod"}

    @property
    def has_safe_jwt_secret(self) -> bool:
        return self.jwt_secret != "change_this_in_local_env" and len(self.jwt_secret) >= 32


@lru_cache
def get_settings() -> Settings:
    return Settings()
