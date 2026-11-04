"""Application settings, read from environment variables or a .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = "change-me-in-production"
# Development-only keys. Production refuses to start with either of them.
DEV_DATA_ENCRYPTION_KEY = "Bmi3VuJAR65JK-E92jqUpT0LICvNtkUFA2Te-sYJrWM="
DEV_DATA_HASH_KEY = "A6SjaqVFHdQZWyGfX_bUMbJmIelU8St9YunQFOHN9Ok"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "StocktoShip API"
    environment: str = "development"  # development | test | production

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/stocktoship"

    # Auth
    jwt_secret: str = DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60

    # Sensitive-field protection (tax IDs). DATA_ENCRYPTION_KEY is a comma-separated list of
    # Fernet keys: the first encrypts, all decrypt (key rotation). DATA_HASH_KEY must never
    # change once real data exists, or duplicate detection breaks.
    data_encryption_key: str = DEV_DATA_ENCRYPTION_KEY
    data_hash_key: str = DEV_DATA_HASH_KEY

    # CORS: comma-separated list of allowed web origins
    cors_origins: str = "http://localhost:5173"

    def validate_for_runtime(self) -> None:
        """Refuse to start production with development secrets."""
        if self.environment != "production":
            return
        if self.jwt_secret == DEFAULT_JWT_SECRET:
            raise RuntimeError("JWT_SECRET must be set to a strong random value in production")
        if DEV_DATA_ENCRYPTION_KEY in self.data_encryption_key_list:
            raise RuntimeError("DATA_ENCRYPTION_KEY must not contain the development key")
        if self.data_hash_key == DEV_DATA_HASH_KEY:
            raise RuntimeError("DATA_HASH_KEY must be set to a strong random value in production")

    @property
    def data_encryption_key_list(self) -> list[str]:
        return [k.strip() for k in self.data_encryption_key.split(",") if k.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
