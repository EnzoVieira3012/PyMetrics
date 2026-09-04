"""Unit tests for the Flask REST API (mocked client, no network)."""

from unittest.mock import Mock

import pytest

from api.server import create_app
from core.errors import GithubClientError
from core.models import Repository
from tests.fixtures.factories import make_commit


@pytest.fixture()
def app():
    test_app = create_app(client=Mock())
    test_app.config["TESTING"] = True
    return test_app


@pytest.fixture()
def client(app, monkeypatch, tmp_path):
    fake = Mock()
    fake.get_repository.return_value = Repository("PyMetrics", "EnzoVieira3012")
    fake.iter_commits.return_value = [make_commit("c1"), make_commit("c2")]
    fake.get_developer.return_value = __import__(
        "core.models", fromlist=["Developer"]
    ).Developer("enzovieira")
    import config

    monkeypatch.setattr(config, "RESULTS_DIR", tmp_path)
    test_app = create_app(client=fake)
    test_app.config["TESTING"] = True
    return test_app.test_client(), fake


def test_health(app):
    resp = app.test_client().get("/api/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_repo_metrics(client):
    test_client, _ = client
    resp = test_client.get("/api/repos/EnzoVieira3012/PyMetrics")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total_repos"] == 1
    assert data["commits"]["total_commits"] == 2


def test_dev_metrics(client):
    test_client, _ = client
    resp = test_client.get("/api/devs/enzovieira")
    assert resp.status_code == 200
    assert resp.get_json()["total_devs"] == 1


def test_github_error_becomes_json(client):
    test_client, fake = client
    fake.iter_commits.side_effect = GithubClientError("não encontrado")
    resp = test_client.get("/api/repos/x/y")
    assert resp.status_code == 400
    assert "não encontrado" in resp.get_json()["error"]


def test_export_csv(client, tmp_path):
    test_client, _ = client
    resp = test_client.get("/api/repos/EnzoVieira3012/PyMetrics/export?format=csv")
    assert resp.status_code == 200
    assert resp.mimetype == "text/csv"
    assert resp.headers["Content-Disposition"].endswith(
        "report_20260904_153041.csv"
    ) or resp.headers["Content-Disposition"].endswith(".csv")


def test_export_json(client, tmp_path):
    test_client, _ = client
    resp = test_client.get("/api/repos/EnzoVieira3012/PyMetrics/export?format=json")
    assert resp.status_code == 200
    assert resp.mimetype == "application/json"


def test_export_invalid_format(client):
    test_client, _ = client
    resp = test_client.get("/api/repos/EnzoVieira3012/PyMetrics/export?format=xml")
    assert resp.status_code == 400
    assert "formato" in resp.get_json()["error"]


def test_not_found_default(app):
    resp = app.test_client().get("/api/nao/existe")
    assert resp.status_code == 404
    assert "não encontrado" in resp.get_json()["error"]


def test_internal_error_returns_json_no_traceback(app, monkeypatch):
    test_app = app
    fake = Mock()
    fake.get_repository.side_effect = RuntimeError("segredo interno")
    test_app = create_app(client=fake)
    test_app.config["TESTING"] = False  # Testing=True propaga exceção
    resp = test_app.test_client().get("/api/repos/o/r")
    assert resp.status_code == 500
    body = resp.get_json()
    assert "erro interno" in body["error"]
    assert "segredo" not in body["error"]
