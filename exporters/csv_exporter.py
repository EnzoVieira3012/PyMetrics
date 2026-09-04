"""CSV exporter for metric dicts (flat rows)."""

import csv
from pathlib import Path

from core.models import Report
from exporters.common import default_path, flatten_metrics


class CsvExporter(Report):
    """Export metrics as a flattened CSV file with a header row."""

    def export(self, path: str | None = None) -> str:
        """Write CSV (utf-8) to path or RESULTS_DIR default; return file path."""
        target = default_path("csv") if path is None else Path(path)
        if target.parent and not target.parent.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
        flat = flatten_metrics(self._metrics)
        with target.open("w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(flat.keys())
            writer.writerow(flat.values())
        return str(target)
