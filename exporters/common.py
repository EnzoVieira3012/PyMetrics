"""Shared helpers for exporters (DRY)."""

from datetime import datetime
from pathlib import Path
from typing import Any

import config


def flatten_metrics(metrics: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten a nested dict into dotted keys (a.b.c) for CSV columns."""
    flat: dict[str, Any] = {}
    for key, value in metrics.items():
        dotted = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(flatten_metrics(value, dotted))
        else:
            flat[dotted] = value
    return flat


def default_path(extension: str) -> Path:
    """RESULTS_DIR/report_YYYYMMDD_HHMMSS.<ext>, creating RESULTS_DIR."""
    folder = Path(config.RESULTS_DIR)
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return folder / f"report_{stamp}.{extension}"