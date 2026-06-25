"""The production config guard refuses to boot with insecure defaults."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.main import _DEV_JWT_SECRET, _validate_production_settings


def _settings(**overrides: object) -> SimpleNamespace:
    base: dict[str, object] = {
        "api_env": "production",
        "auth_mode": "supabase",
        "supabase_jwt_secret": "a-real-rotated-production-secret-value-32+chars",
        "fernet_key": "ZmFrZS1mZXJuZXQta2V5LWZvci10ZXN0aW5nLW9ubHk=",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_development_skips_the_check() -> None:
    # Defaults are fine in development; nothing should raise.
    _validate_production_settings(
        _settings(api_env="development", supabase_jwt_secret=_DEV_JWT_SECRET, fernet_key="")
    )


def test_production_rejects_default_jwt_secret() -> None:
    with pytest.raises(RuntimeError, match="SUPABASE_JWT_SECRET"):
        _validate_production_settings(_settings(supabase_jwt_secret=_DEV_JWT_SECRET))


def test_production_rejects_empty_fernet_key() -> None:
    with pytest.raises(RuntimeError, match="FERNET_KEY"):
        _validate_production_settings(_settings(fernet_key=""))


def test_production_allows_properly_configured_secrets() -> None:
    _validate_production_settings(_settings())


def test_dev_auth_mode_does_not_require_jwt_secret() -> None:
    # In dev-auth mode the JWT secret is unused, so its default is acceptable.
    _validate_production_settings(
        _settings(auth_mode="dev", supabase_jwt_secret=_DEV_JWT_SECRET)
    )
