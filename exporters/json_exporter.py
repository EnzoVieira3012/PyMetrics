"""JSON exporter for metric dicts."""

import json
from pathlib import Path

from core.models import Report
from exporters.common import default_path


class JsonExporter(Report):
    """Export metrics as a pretty-printed JSON file (utf-8)."""

    def export(self, path: str | None = None) -> str:
        """Write JSON to path or RESULTS_DIR default; return file path."""
        target = default_path("json") if path is None else Path(path)
        if target.parent and not target.parent.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as file:
            json.dump(self._metrics, file, indent=2, ensure_ascii=False)
        return str(target)