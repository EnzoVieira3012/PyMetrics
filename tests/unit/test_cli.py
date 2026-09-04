"""Unit tests for CLI commands (mocked input/print, no network)."""

from unittest.mock import Mock

import pytest

from cli.commands import cmd_dev_analysis, cmd_export, cmd_repo_analysis
from core.errors import GithubClientError
from core.models import Commit, Developer, Repository
from tests.fixtures.factories import make_commit


def _fake_client(commits=2):
    client = Mock()
    client.iter_commits.return_value = [
        make_commit(f"c{i}") for i in range(commits)
    ]
    client.get_repository.return_value = Repository("PyMetrics", "EnzoVieira3012")
    client.get_developer.return_value = Developer("enzovieira")
    return client


def test_cmd_repo_analysis(monkeypatch, capsys):
    answers = iter(["EnzoVieira3012", "PyMetrics", "s"])
    monkeypatch.setattr("builtins.input", lambda *a: next(answers))
    metrics = cmd_repo_analysis(_fake_client())
    out = capsys.readouterr().out
    assert "PyMetrics" in out
    assert metrics["total_repos"] == 1
    assert metrics["commits"]["total_commits"] == 2


def test_cmd_repo_analysis_exports_csv(monkeypatch, capsys, tmp_path):
    answers = iter(["EnzoVieira3012", "PyMetrics", "csv"])
    monkeypatch.setattr("builtins.input", lambda *a: next(answers))
    import config
    monkeypatch.setattr(config, "RESULTS_DIR", tmp_path)
    cmd_repo_analysis(_fake_client())
    out = capsys.readouterr().out
    assert "Relatório salvo" in out
    assert any(tmp_path.glob("report_*.csv"))


def test_cmd_dev_analysis(monkeypatch, capsys):
    answers = iter(["enzovieira", "s"])
    monkeypatch.setattr("builtins.input", lambda *a: next(answers))
    metrics = cmd_dev_analysis(_fake_client())
    out = capsys.readouterr().out
    assert "enzovieira" in out
    assert metrics["total_devs"] == 1


def test_cmd_export_without_analysis(capsys):
    cmd_export(None)
    assert "Nenhuma análise" in capsys.readouterr().out


def test_cmd_export_reuses_metrics(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr("builtins.input", lambda *a: "csv")
    import config
    monkeypatch.setattr(config, "RESULTS_DIR", tmp_path)
    metrics = {"total_commits": 3, "ok": True}
    cmd_export(metrics)
    assert "Relatório salvo" in capsys.readouterr().out


def test_cmd_export_unknown_format(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda *a: "xml")
    cmd_export({"a": 1})
    assert "Formato não reconhecido" in capsys.readouterr().out