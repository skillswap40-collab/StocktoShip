import pytest

from app.core.config import DEFAULT_JWT_SECRET, Settings


def test_production_refuses_default_jwt_secret():
    settings = Settings(environment="production", jwt_secret=DEFAULT_JWT_SECRET)
    with pytest.raises(RuntimeError):
        settings.validate_for_runtime()


def test_production_accepts_custom_secret():
    Settings(environment="production", jwt_secret="x" * 48).validate_for_runtime()


def test_cors_origins_parsed():
    s = Settings(cors_origins="http://a.test, http://b.test")
    assert s.cors_origin_list == ["http://a.test", "http://b.test"]
