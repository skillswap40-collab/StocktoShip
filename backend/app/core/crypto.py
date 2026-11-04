"""Field-level encryption (Fernet) and keyed fingerprints (HMAC-SHA256) for sensitive data."""

import hashlib
import hmac
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken, MultiFernet

from app.core.config import get_settings


class DecryptionError(Exception):
    pass


@lru_cache
def _fernet() -> MultiFernet:
    keys = get_settings().data_encryption_key_list
    if not keys:
        raise RuntimeError("DATA_ENCRYPTION_KEY is empty")
    # The first key encrypts; every key is tried when decrypting, so old keys keep working.
    return MultiFernet([Fernet(k.encode()) for k in keys])


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise DecryptionError("Could not decrypt value") from exc


def fingerprint(value: str) -> str:
    """Deterministic keyed hash: finds duplicates without decrypting anything."""
    key = get_settings().data_hash_key.encode()
    return hmac.new(key, value.encode(), hashlib.sha256).hexdigest()
