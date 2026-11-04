"""Field encryption and keyed fingerprints."""

import pytest
from cryptography.fernet import Fernet, MultiFernet

from app.core import crypto


def test_encrypt_decrypt_round_trip():
    token = crypto.encrypt("123456789")
    assert "123456789" not in token
    assert crypto.decrypt(token) == "123456789"


def test_encryption_is_randomized():
    assert crypto.encrypt("123456789") != crypto.encrypt("123456789")


def test_fingerprint_is_stable_and_64_hex_chars():
    fp = crypto.fingerprint("123456789")
    assert fp == crypto.fingerprint("123456789")
    assert len(fp) == 64 and int(fp, 16) >= 0
    assert fp != crypto.fingerprint("123456780")


def test_tampered_ciphertext_raises():
    token = crypto.encrypt("123456789")
    tampered = token[:-4] + ("AAAA" if not token.endswith("AAAA") else "BBBB")
    with pytest.raises(crypto.DecryptionError):
        crypto.decrypt(tampered)


def test_rotated_key_still_decrypts_old_values(monkeypatch):
    old_key, new_key = Fernet.generate_key(), Fernet.generate_key()
    token = Fernet(old_key).encrypt(b"123456789").decode()
    monkeypatch.setattr(crypto, "_fernet", lambda: MultiFernet([Fernet(new_key), Fernet(old_key)]))
    assert crypto.decrypt(token) == "123456789"
