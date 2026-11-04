import pytest
from cryptography.fernet import Fernet

from app.core.config import (
    DEFAULT_JWT_SECRET,
    DEV_DATA_ENCRYPTION_KEY,
    DEV_DATA_HASH_KEY,
    Settings,
)

PROD_SECRETS = {
    "jwt_secret": "x" * 48,
    "data_encryption_key": Fernet.generate_key().decode(),
    "data_hash_key": "h" * 43,
}


@pytest.mark.parametrize(
    "override",
    [
        {"jwt_secret": DEFAULT_JWT_SECRET},
        {"data_encryption_key": DEV_DATA_ENCRYPTION_KEY},
        # The dev key anywhere in the rotation list is refused, not just in first place.
        {"data_encryption_key": f"{Fernet.generate_key().decode()}, {DEV_DATA_ENCRYPTION_KEY}"},
        {"data_hash_key": DEV_DATA_HASH_KEY},
    ],
)
def test_production_refuses_dev_secrets(override):
    settings = Settings(environment="production", **{**PROD_SECRETS, **override})
    with pytest.raises(RuntimeError):
        settings.validate_for_runtime()


def test_production_accepts_custom_secrets():
    Settings(environment="production", **PROD_SECRETS).validate_for_runtime()


def test_development_allows_defaults():
    Settings(
        environment="development",
        jwt_secret=DEFAULT_JWT_SECRET,
        data_encryption_key=DEV_DATA_ENCRYPTION_KEY,
        data_hash_key=DEV_DATA_HASH_KEY,
    ).validate_for_runtime()


def test_cors_origins_parsed():
    s = Settings(cors_origins="http://a.test, http://b.test")
    assert s.cors_origin_list == ["http://a.test", "http://b.test"]
