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
        # Provider modes — read by the guard's production-warning pass.
        "meta_mode": "live",
        "billing_provider": "stripe",
        "media_provider": "mock",
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


def test_production_rejects_dev_auth_mode() -> None:
    # AUTH_MODE=dev is a full authentication bypass — it must never boot in prod,
    # even though its forged demo user wouldn't otherwise need a real JWT secret.
    with pytest.raises(RuntimeError, match="AUTH_MODE=dev"):
        _validate_production_settings(_settings(auth_mode="dev"))


def test_production_warns_but_boots_with_mock_providers(caplog: pytest.LogCaptureFixture) -> None:
    # Mock providers don't break startup (billing/media have no live key yet), but
    # the guard must log a loud warning so a deploy never silently fakes them.
    import logging

    with caplog.at_level(logging.WARNING, logger="presence.startup"):
        _validate_production_settings(
            _settings(meta_mode="mock", billing_provider="mock", media_provider="mock")
        )
    blob = " ".join(r.message for r in caplog.records)
    assert "META_MODE" in blob
    assert "BILLING_PROVIDER" in blob
    assert "MEDIA_PROVIDER" in blob


def test_production_live_providers_emit_no_warning(caplog: pytest.LogCaptureFixture) -> None:
    import logging

    with caplog.at_level(logging.WARNING, logger="presence.startup"):
        _validate_production_settings(
            _settings(meta_mode="live", billing_provider="stripe", media_provider="creatify")
        )
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]
