"""Integration test: full CLI flow with mocked GithubClient (no network)."""

from unittest.mock import Mock, patch

import pytest

import main
from core.models import Repository
from tests.fixtures.factories import make_commit


def test_full_menu_flow(monkeypatch, capsys, tmp_path):
    """Feed menu inputs: 1=repo (skip export), 3=export, 4=exit."""
    answers = iter(["1", "EnzoVieira3012", "PyMetrics", "s", "3", "csv", "4"])
    monkeypatch.setattr("builtins.input", lambda *a: next(answers))

    client = Mock()
    client.iter_commits.return_value = [make_commit("c1"), make_commit("c2")]
    client.get_repository.return_value = Repository("PyMetrics", "EnzoVieira3012")

    import config

    monkeypatch.setattr(config, "RESULTS_DIR", tmp_path)

    with patch("main.GithubClient", return_value=client):
        main.main()

    out = capsys.readouterr().out
    assert "PyMetrics" in out
    assert "Relatório salvo" in out
    assert "Até logo!" in out
    assert any(tmp_path.glob("report_*.csv"))


def test_cli_missing_token_exits(monkeypatch, capsys):
    from core.errors import GithubClientError

    with (
        patch("main.GithubClient", side_effect=GithubClientError("sem token")),
        pytest.raises(SystemExit),
    ):
        main.main()
    assert "sem token" in capsys.readouterr().out


def test_cli_github_error_no_crash(monkeypatch, capsys):
    """API error during analysis returns to menu, no crash."""
    answers = iter(["1", "o", "r", "4"])
    monkeypatch.setattr("builtins.input", lambda *a: next(answers))

    from core.errors import GithubClientError

    client = Mock()
    client.iter_commits.side_effect = GithubClientError("não encontrado")

    with patch("main.GithubClient", return_value=client):
        main.main()
    out = capsys.readouterr().out
    assert "não encontrado" in out
    assert "Até logo!" in out


def test_cli_dev_error_no_crash(monkeypatch, capsys):
    answers = iter(["2", "usuario", "4"])
    monkeypatch.setattr("builtins.input", lambda *a: next(answers))

    from core.errors import GithubClientError

    client = Mock()
    client.get_developer.side_effect = GithubClientError("dev não encontrado")

    with patch("main.GithubClient", return_value=client):
        main.main()
    out = capsys.readouterr().out
    assert "dev não encontrado" in out
    assert "Até logo!" in out


def test_cli_invalid_menu_option(monkeypatch, capsys):
    answers = iter(["9", "4"])
    monkeypatch.setattr("builtins.input", lambda *a: next(answers))
    client = Mock()
    with patch("main.GithubClient", return_value=client):
        main.main()
    assert "Opção inválida" in capsys.readouterr().out


def test_cli_ctrl_c_exits_clean(monkeypatch, capsys):
    import builtins

    real_input = builtins.input
    calls = {"n": 0}

    def fake_input(prompt):
        calls["n"] += 1
        if calls["n"] == 1:
            raise KeyboardInterrupt
        return real_input(prompt)

    monkeypatch.setattr("builtins.input", fake_input)
    client = Mock()
    with patch("main.GithubClient", return_value=client):
        main.main()
    assert "Até logo!" in capsys.readouterr().out
