"""Shared fixtures for all tests.\n\nIMPORTANT: we set env vars to empty values (not delete) so that\nload_dotenv() in config.py does not re-populate them from a real .env\nfile during importlib.reload(). Empty values are preserved by dotenv\n(since the key already exists), yielding deterministic defaults.\n"""

_KEYS = (
    "GITHUB_TOKEN",
    "GITHUB_API_URL",
    "REQUEST_TIMEOUT",
    "RESULTS_DIR",
    "LOG_LEVEL",
)


def clean_env(monkeypatch):
    """Set all GITHUB-related env vars to empty to force config defaults."""
    for key in _KEYS:
        monkeypatch.setenv(key, "")
