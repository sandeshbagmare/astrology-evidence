import pytest
from pydantic import ValidationError

from astrology_evidence.config import Settings


def test_safe_local_defaults():
    settings = Settings(_env_file=None)
    assert not settings.ai_enabled
    assert not settings.dev_login_enabled
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
