from functools import lru_cache
from typing import List, Optional

from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    app_name: str = "Stock Alert API"
    debug: bool = False
    database_url: str
    admin_api_key: str
    auto_create_tables: bool = True
    allowed_origins: List[str] = ["*"]
    request_timeout: int = 10
    cache_timeout: int = 300
    enable_caching: bool = True
    min_request_delay: float = 1.0
    max_request_delay: float = 3.0
    apns_key_id: Optional[str] = None
    apns_team_id: Optional[str] = None
    apns_bundle_id: str = "com.stockalert.app"
    apns_private_key: Optional[str] = None
    apns_use_sandbox: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False

    @validator("allowed_origins", pre=True)
    def parse_allowed_origins(cls, value):  # type: ignore[override]
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @validator("database_url")
    def require_hosted_postgres(cls, value: str) -> str:
        lowered = value.lower()
        if "sqlite" in lowered:
            raise ValueError("SQLite/local database URLs are not allowed")
        if not (
            lowered.startswith("postgres://")
            or lowered.startswith("postgresql://")
            or lowered.startswith("postgresql+asyncpg://")
        ):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL")
        return value

    @property
    def DEBUG(self) -> bool:
        return self.debug

    @property
    def DATABASE_URL(self) -> str:
        return self.database_url

    @property
    def CACHE_TIMEOUT(self) -> int:
        return self.cache_timeout

    @property
    def ENABLE_CACHING(self) -> bool:
        return self.enable_caching

    @property
    def REQUEST_TIMEOUT(self) -> int:
        return self.request_timeout

    @property
    def MIN_REQUEST_DELAY(self) -> float:
        return self.min_request_delay

    @property
    def MAX_REQUEST_DELAY(self) -> float:
        return self.max_request_delay


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
