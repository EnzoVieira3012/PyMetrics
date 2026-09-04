"""Unit tests for CSV and JSON exporters."""

import csv
import json

from exporters.common import flatten_metrics
from exporters.csv_exporter import CsvExporter
from exporters.json_exporter import JsonExporter

METRICS = {
    "total_commits": 5,
    "avg_changes_per_commit": 4.0,
    "top_authors": [("enzo", 3)],
    "nested": {"a": 1, "b": {"c": "x", "ç": "á"}},
}


def test_flatten_metrics_dots():
    flat = flatten_metrics({"k": {"a": 1, "b": {"c": 2}}})
    assert flat == {"k.a": 1, "k.b.c": 2}


def test_flatten_metrics_flat_input_unchanged():
    assert flatten_metrics({"x": 1}) == {"x": 1}


def test_csv_exporter_writes_file(tmp_path):
    target = tmp_path / "out.csv"
    result = CsvExporter(METRICS).export(str(target))
    assert result == str(target)
    assert target.exists()
    with target.open(encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    assert rows[0] == ["total_commits", "avg_changes_per_commit", "top_authors",
                       "nested.a", "nested.b.c", "nested.b.ç"]
    assert rows[1] == ["5", "4.0", "[('enzo', 3)]", "1", "x", "á"]


def test_json_exporter_writes_file(tmp_path):
    target = tmp_path / "out.json"
    result = JsonExporter(METRICS).export(str(target))
    assert result == str(target)
    assert target.exists()
    with target.open(encoding="utf-8") as f:
        data = json.load(f)
    assert data["total_commits"] == 5
    assert data["avg_changes_per_commit"] == 4.0
    assert data["top_authors"] == [["enzo", 3]]  # tuples become lists in JSON
    assert data["nested"] == {"a": 1, "b": {"c": "x", "ç": "á"}}


def test_csv_exporter_creates_default_dir(monkeypatch, tmp_path):
    import config
    monkeypatch.setattr(config, "RESULTS_DIR", tmp_path / "novo" / "results")
    path = CsvExporter(METRICS).export()
    assert (tmp_path / "novo" / "results").exists()
    assert path.endswith(".csv")


def test_json_exporter_creates_default_dir(monkeypatch, tmp_path):
    import config
    monkeypatch.setattr(config, "RESULTS_DIR", tmp_path / "novo2" / "results")
    path = JsonExporter(METRICS).export()
    assert (tmp_path / "novo2" / "results").exists()
    assert path.endswith(".json")


def test_csv_exporter_creates_parent_for_custom_path(tmp_path):
    target = tmp_path / "sub" / "novo" / "out.csv"
    CsvExporter(METRICS).export(str(target))
    assert target.exists()


def test_json_exporter_creates_parent_for_custom_path(tmp_path):
    target = tmp_path / "sub" / "novo" / "out.json"
    JsonExporter(METRICS).export(str(target))
    assert target.exists()


def test_exporters_inherit_summary():
    assert CsvExporter(METRICS).summary() == JsonExporter(METRICS).summary()
    assert "total_commits: 5" in CsvExporter(METRICS).summary()