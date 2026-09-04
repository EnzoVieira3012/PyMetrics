"""Central configuration for PyMetrics.

Loads environment variables via python-dotenv.
All settings use UPPER_SNAKE_CASE with sensible defaults.
Empty-string values fall back to defaults (avoids int('') crashes).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _env(key: str, default: str) -> str:
    """Get env var, treating empty string as unset."""
    value = os.getenv(key)
    return value if value else default


GITHUB_TOKEN: str = _env("GITHUB_TOKEN", "")
GITHUB_API_URL: str = _env("GITHUB_API_URL", "https://api.github.com")
REQUEST_TIMEOUT: int = int(_env("REQUEST_TIMEOUT", "30"))
RESULTS_DIR: Path = Path(_env("RESULTS_DIR", "results"))
LOG_LEVEL: str = _env("LOG_LEVEL", "INFO")
