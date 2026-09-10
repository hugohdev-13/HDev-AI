"""Production configuration must reject incomplete secure deployments."""

import os
from unittest.mock import patch

import pytest

from config import DevelopmentConfig, ProductionConfig


def _environment(**overrides):
    values = {
        "DB_AUTH_MODE": "trusted",
        "DB_DRIVER": "ODBC Driver 18 for SQL Server",
        "DB_SERVER": "server.example",
        "DB_DATABASE": "hdev",
    }
    values.update(overrides)
    return values


def test_production_fails_fast_without_secret_key():
    with patch.dict(os.environ, _environment(N8N_API_KEY="n8n-key"), clear=True):
        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            ProductionConfig()


def test_production_fails_fast_without_n8n_key_when_enabled():
    with patch.dict(os.environ, _environment(SECRET_KEY="session-key"), clear=True):
        with pytest.raises(RuntimeError, match="N8N_API_KEY"):
            ProductionConfig()


def test_production_allows_disabled_n8n_and_uses_secure_cookie_flags():
    environment = _environment(
        SECRET_KEY="session-key",
        N8N_INTEGRATION_ENABLED="false",
    )
    with patch.dict(os.environ, environment, clear=True):
        config = ProductionConfig()

    assert config.SESSION_COOKIE_HTTPONLY is True
    assert config.SESSION_COOKIE_SECURE is True
    assert config.SESSION_COOKIE_SAMESITE == "Lax"


def test_development_does_not_require_production_secrets():
    with patch.dict(os.environ, _environment(), clear=True):
        config = DevelopmentConfig()

    assert config.DEBUG is True
