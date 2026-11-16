import pytest
from pydantic import ValidationError

from astrology_evidence.config import Settings


def test_safe_local_defaults():
    settings = Settings(_env_file=None)
    assert not settings.ai_enabled
    assert not settings.dev_login_enabled
    assert not settings.authentication_enabled
    assert settings.app_env == "development"


def test_production_requires_postgres_and_explicit_gates():
    with pytest.raises(ValidationError):
        Settings(app_env="production", _env_file=None)


def test_provider_url_is_not_arbitrary():
    with pytest.raises(ValidationError):
        Settings(ai_base_url="http://127.0.0.1:8080", _env_file=None)


def test_secret_repr_is_redacted():
    settings = Settings(openai_api_key="example-private-value", _env_file=None)
    assert "example-private-value" not in repr(settings)


def test_guest_production_retains_operating_gates_without_requiring_google():
    values = {
        "_env_file": None,
        "app_env": "production",
        "secure_cookies": True,
        "app_public_origin": "https://astrology.example",
        "database_url": "postgresql+psycopg://user:example@localhost/db",
        "privacy_executor_ready": True,
        "ephemeris_license_reviewed": True,
        "ephemeris_mode": "swiss",
        "ephemeris_path": "/reviewed-ephemeris",
    }
    settings = Settings(**values)
    assert settings.session_cookie == "__Host-session"
    assert not settings.authentication_enabled
    with pytest.raises(ValidationError, match="Google identity"):
        Settings(**values, authentication_enabled=True)
    for missing in ("privacy_executor_ready", "ephemeris_license_reviewed", "secure_cookies"):
        with pytest.raises(ValidationError):
            Settings(**{**values, missing: False})
