"""Base logging configuration for PyMetrics."""

import logging
import sys


def setup_logging(log_level: str | None = None) -> None:
    """Configure console logging with standard format.

    Args:
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR).
                   Falls back to INFO if None or invalid.
    """
    level = getattr(logging, (log_level or "INFO").upper(), logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)

    # Avoid duplicate handlers on repeated calls
    if not root.handlers:
        root.addHandler(handler)
