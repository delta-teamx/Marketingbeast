"""Symmetric encryption for secrets at rest (e.g. social OAuth tokens).

Uses Fernet (AES-128-CBC + HMAC). The key comes from the FERNET_KEY env var.
Generate one with:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Phase 0 ships the helper; the social connect flow that uses it lands in Phase 1.
"""

from __future__ import annotations

from cryptography.fernet import Fernet

from app.core.config import get_settings


def _fernet() -> Fernet:
    key = get_settings().fernet_key
    if not key:
        raise RuntimeError("FERNET_KEY is not set; cannot encrypt/decrypt secrets")
    return Fernet(key.encode())


def encrypt_secret(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    return _fernet().decrypt(ciphertext.encode()).decode()
