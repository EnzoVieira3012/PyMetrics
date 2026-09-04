"""Shared fixtures for all tests.\n\nIMPORTANT: we set env vars to empty values (not delete) so that\nload_dotenv() in config.py does not re-populate them from a real .env\nfile during importlib.reload(). Empty values are preserved by dotenv\n(since the key already exists), yielding deterministic defaults.\n"""

import pytest

import config

_KEYS = (
    "GITHUB_TOKEN",
    "GITHUB_API_URL",
    "REQUEST_TIMEOUT",
    "RESULTS_DIR",
    "LOG_LEVEL",
    "CACHE_DIR",
    "CACHE_TTL_HOURS",
    "DEFAULT_LIMIT",
)


@pytest.fixture(autouse=True)
def _isolated_cache_dir(tmp_path, monkeypatch):
    """Point the disk cache at a per-test temp dir so unit tests never
    read or write the real .cache folder."""
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path / "cache")


def clean_env(monkeypatch):
    """Set all GITHUB-related env vars to empty to force config defaults."""
    for key in _KEYS:
        monkeypatch.setenv(key, "")
