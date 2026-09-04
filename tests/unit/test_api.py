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
    fake.get_commit_count.return_value = None
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


def test_repo_metrics_limit_param(client):
    test_client, fake = client
    fake.iter_commits.return_value = [make_commit("c1"), make_commit("c2")]
    resp = test_client.get("/api/repos/EnzoVieira3012/PyMetrics?limit=2")
    assert resp.status_code == 200
    fake.iter_commits.assert_called_once_with("EnzoVieira3012", "PyMetrics", limit=2)


def test_repo_metrics_truncated_flag(client):
    test_client, fake = client
    fake.iter_commits.return_value = [make_commit("c1"), make_commit("c2")]
    resp = test_client.get("/api/repos/EnzoVieira3012/PyMetrics?limit=2")
    data = resp.get_json()
    assert data["truncated"] is True
    assert data["sampled_commits"] == 2


def test_repo_metrics_no_truncation(client):
    test_client, fake = client
    fake.iter_commits.return_value = [make_commit("c1"), make_commit("c2")]
    resp = test_client.get("/api/repos/EnzoVieira3012/PyMetrics")
    data = resp.get_json()
    assert data["truncated"] is False


def test_swagger_spec_route(app):
    resp = app.test_client().get("/swagger.json")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["openapi"].startswith("3.")
    assert "/api/repos/{owner}/{name}" in data["paths"]


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


def test_commits_paginated_real_total(client):
    test_client, fake = client
    fake.iter_commits.return_value = [make_commit("c1"), make_commit("c2")]
    fake.get_commit_count.return_value = 23267
    resp = test_client.get("/api/repos/yt-dlp/yt-dlp/commits?per_page=10&page=2")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total_commits"] == 23267
    assert data["total_pages"] == 2327
    assert data["has_next"] is True


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


def test_commits_endpoint_paginates(client):
    test_client, _ = client
    resp = test_client.get(
        "/api/repos/EnzoVieira3012/PyMetrics/commits?per_page=10&page=1"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["page"] == 1
    assert data["per_page"] == 10
    assert data["total_commits"] == 2
    assert data["total_pages"] == 1
    assert data["has_prev"] is False
    assert data["has_next"] is False
    assert len(data["items"]) == 2


def test_commits_invalid_per_page_400(client):
    test_client, _ = client
    resp = test_client.get("/api/repos/EnzoVieira3012/PyMetrics/commits?per_page=5")
    assert resp.status_code == 400
    assert "per_page" in resp.get_json()["error"]


def test_commits_invalid_page_400(client):
    test_client, _ = client
    resp = test_client.get("/api/repos/EnzoVieira3012/PyMetrics/commits?page=0")
    assert resp.status_code == 400
    assert "page" in resp.get_json()["error"]


def test_commits_total_mode_uses_extended_timeout(client):
    import config

    test_client, fake = client
    resp = test_client.get("/api/repos/EnzoVieira3012/PyMetrics/commits?per_page=total")
    assert resp.status_code == 200
    fake.iter_commits.assert_called_once_with(
        "EnzoVieira3012",
        "PyMetrics",
        limit=None,
        timeout=config.REQUEST_TIMEOUT_TOTAL,
    )
    assert resp.get_json()["mode"] == "total"


def test_commits_normal_mode_default_timeout(client):
    test_client, fake = client
    resp = test_client.get(
        "/api/repos/EnzoVieira3012/PyMetrics/commits?per_page=20&page=1"
    )
    assert resp.status_code == 200
    fake.iter_commits.assert_called_once_with(
        "EnzoVieira3012", "PyMetrics", limit=20, timeout=None
    )


def test_commits_sort_by_author(client):
    test_client, fake = client
    fake.iter_commits.return_value = [
        make_commit("c1", author="b"),
        make_commit("c2", author="a"),
    ]
    resp = test_client.get(
        "/api/repos/EnzoVieira3012/PyMetrics/commits?sort=author&order=asc"
    )
    assert resp.status_code == 200
    authors = [c["author"] for c in resp.get_json()["items"]]
    assert authors == ["a", "b"]


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
