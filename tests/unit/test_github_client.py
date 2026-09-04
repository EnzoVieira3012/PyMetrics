"""Unit tests for the GitHub API client (mocked, no network)."""

from unittest.mock import Mock

import pytest

from core.errors import GithubClientError
from core.github_client import GithubClient


def _client_with_response(status=200, payload=None, headers=None):
    client = GithubClient.__new__(GithubClient)
    client._base_url = "https://api.github.com"
    client._timeout = 30
    client._session = Mock()
    response = Mock(
        status_code=status,
        json=lambda: payload if payload is not None else {},
        headers=headers or {},
    )
    client._session.get.return_value = response
    return client, response


# ------------- get_repository -------------

def test_get_repository_success():
    client, _ = _client_with_response(
        200,
        {"name": "PyMetrics", "owner": {"login": "EnzoVieira3012"},
         "language": "Python", "stargazers_count": 5},
    )
    repo = client.get_repository("EnzoVieira3012", "PyMetrics")
    assert repo.name == "PyMetrics"
    assert repo.url == "https://github.com/EnzoVieira3012/PyMetrics"
    client._session.get.assert_called_once()


# ------------- get_developer -------------

def test_get_developer_success():
    client, _ = _client_with_response(200, {"login": "enzovieira"})
    dev = client.get_developer("enzovieira")
    assert dev.username == "enzovieira"


# ------------- iter_commits (paginacao lazy) -------------

def _commit_item(sha):
    return {"sha": sha, "commit": {"message": f"msg {sha}",
            "author": {"date": "2026-09-04T10:00:00Z"}, "author": {}}}


def test_iter_commits_two_pages():
    page1 = [_commit_item("a") for _ in range(30)]
    page2 = [_commit_item("b") for _ in range(2)]
    client, _ = _client_with_response(200, page1)
    responses = iter([Mock(status_code=200, json=lambda: page1, headers={}),
                      Mock(status_code=200, json=lambda: page2, headers={})])
    client._session.get.side_effect = lambda *a, **k: next(responses)
    commits = list(client.iter_commits("o", "r", per_page=30))
    assert len(commits) == 32
    assert client._session.get.call_count == 2


def test_iter_commits_last_partial_page():
    page1 = [_commit_item("a") for _ in range(30)]
    page2 = [_commit_item("b") for _ in range(2)]
    responses = iter([Mock(status_code=200, json=lambda: page1, headers={}),
                      Mock(status_code=200, json=lambda: page2, headers={})])
    client = GithubClient.__new__(GithubClient)
    client._base_url = "https://api.github.com"
    client._timeout = 30
    client._session = Mock()
    client._session.get.side_effect = lambda *a, **k: next(responses)
    commits = list(client.iter_commits("o", "r", per_page=30))
    assert len(commits) == 32


def test_iter_commits_empty_page_stops():
    client, _ = _client_with_response(200, [])
    commits = list(client.iter_commits("o", "r"))
    assert commits == []


# ------------- error mapping -------------

def test_404_raises_friendly_message():
    client, _ = _client_with_response(404)
    with pytest.raises(GithubClientError, match="não encontrado"):
        client.get_repository("nope", "nope")


def test_401_raises_token_message():
    client, _ = _client_with_response(401)
    with pytest.raises(GithubClientError, match="[Tt]oken"):
        client.get_repository("o", "r")


def test_403_rate_limit_message():
    client, _ = _client_with_response(403, headers={"X-RateLimit-Remaining": "0"})
    with pytest.raises(GithubClientError, match="rate limit"):
        client.get_repository("o", "r")


def test_missing_token_raises():
    with pytest.raises(GithubClientError, match="GITHUB_TOKEN"):
        GithubClient(token="")


def test_constructor_configures_auth_headers():
    import requests
    client = GithubClient(token="ghp_fake_token")
    assert client._base_url == "https://api.github.com"
    assert client._timeout == 30
    assert isinstance(client._session, requests.Session)
    assert client._session.headers["Authorization"] == "Bearer ghp_fake_token"
    client._session.close()


def test_network_failure_raises_friendly_message():
    client = GithubClient.__new__(GithubClient)
    client._base_url = "https://api.github.com"
    client._timeout = 30
    client._session = Mock()
    import requests
    client._session.get.side_effect = requests.ConnectionError("boom")
    with pytest.raises(GithubClientError, match="Falha de conexão"):
        client.get_repository("o", "r")


def test_generic_5xx_raises():
    client, _ = _client_with_response(500)
    with pytest.raises(GithubClientError, match="erro 500"):
        client.get_repository("o", "r")


# ------------- languages / issues -------------

def test_get_repo_languages():
    client, _ = _client_with_response(200, {"Python": 1000})
    assert client.get_repo_languages("o", "r") == {"Python": 1000}


def test_get_open_issues_count():
    client, _ = _client_with_response(200, {"open_issues_count": 3})
    assert client.get_open_issues_count("o", "r") == 3