"""Unit tests for config module."""

import importlib

from tests.conftest import clean_env


def test_default_api_url(monkeypatch):
    """GITHUB_API_URL defaults to https://api.github.com when unset."""
    clean_env(monkeypatch)
    import config
    importlib.reload(config)
    assert config.GITHUB_API_URL == "https://api.github.com"


def test_default_timeout(monkeypatch):
    """REQUEST_TIMEOUT defaults to 30 when unset."""
    clean_env(monkeypatch)
    import config
    importlib.reload(config)
    assert config.REQUEST_TIMEOUT == 30


def test_default_log_level(monkeypatch):
    """LOG_LEVEL defaults to INFO when unset."""
    clean_env(monkeypatch)
    import config
    importlib.reload(config)
    assert config.LOG_LEVEL == "INFO"


def test_default_token_empty(monkeypatch):
    """GITHUB_TOKEN defaults to empty string when unset."""
    clean_env(monkeypatch)
    import config
    importlib.reload(config)
    assert config.GITHUB_TOKEN == ""


def test_override_api_url(monkeypatch):
    """GITHUB_API_URL respects env override."""
    monkeypatch.setenv("GITHUB_API_URL", "https://custom.api/v2")
    import config
    importlib.reload(config)
    assert config.GITHUB_API_URL == "https://custom.api/v2"


def test_override_timeout(monkeypatch):
    """REQUEST_TIMEOUT respects env override as int."""
    monkeypatch.setenv("REQUEST_TIMEOUT", "60")
    import config
    importlib.reload(config)
    assert config.REQUEST_TIMEOUT == 60


def test_override_token(monkeypatch):
    """GITHUB_TOKEN reads env value."""
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token_value")
    import config
    importlib.reload(config)
    assert config.GITHUB_TOKEN == "ghp_test_token_value"
