"""Application settings, read from environment variables or a .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = "change-me-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "StocktoShip API"
    environment: str = "development"  # development | test | production

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/stocktoship"

    # Auth
    jwt_secret: str = DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60

    # CORS: comma-separated list of allowed web origins
    cors_origins: str = "http://localhost:5173"

    def validate_for_runtime(self) -> None:
        """Refuse to start production with development secrets."""
        if self.environment == "production" and self.jwt_secret == DEFAULT_JWT_SECRET:
            raise RuntimeError("JWT_SECRET must be set to a strong random value in production")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
