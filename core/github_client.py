"""GitHub API client for PyMetrics.

Uses requests.Session (one reused session), lazy pagination with
generators, and maps HTTP errors to friendly GithubClientError messages.
"""

from collections.abc import Iterable
from typing import Any

import requests

import config
from core.errors import GithubClientError
from core.models import Commit, Developer, Repository
from decorators.cache import cache_result
from decorators.logger import log_execution
from decorators.timer import timer

_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


class GithubClient:
    """Authenticated client for the GitHub REST API."""

    def __init__(self, token: str | None = None) -> None:
        self._token = token if token is not None else config.GITHUB_TOKEN
        if not self._token:
            raise GithubClientError(
                "GITHUB_TOKEN ausente. Configure o .env com seu token "
                "(veja .env.example)"
            )
        self._base_url = config.GITHUB_API_URL.rstrip("/")
        self._timeout = config.REQUEST_TIMEOUT
        self._session = requests.Session()
        self._session.headers.update(_HEADERS)
        self._session.headers["Authorization"] = f"Bearer {self._token}"

    @log_execution
    def _get(self, url: str, params: dict[str, Any] | None = None) -> dict:
        """Central GET helper: request, error mapping, rate-limit check."""
        try:
            response = self._session.get(
                f"{self._base_url}{url}", params=params, timeout=self._timeout
            )
        except requests.RequestException as exc:
            raise GithubClientError(f"Falha de conexão com GitHub API: {exc}") from exc

        if response.status_code == 401:
            raise GithubClientError(
                "Token inválido ou expirado. Gere um novo em "
                "github.com/settings/tokens e atualize o .env"
            )
        if response.status_code == 403:
            remaining = response.headers.get("X-RateLimit-Remaining", "?")
            reset = response.headers.get("X-RateLimit-Reset", "?")
            raise GithubClientError(
                f"Acesso negado ou rate limit atingido "
                f"(restantes: {remaining}, reset: {reset})"
            )
        if response.status_code == 404:
            raise GithubClientError(
                f"Recurso não encontrado na GitHub API: {url} (status 404)"
            )
        if response.status_code >= 400:
            raise GithubClientError(
                f"GitHub API retornou erro {response.status_code} para {url}"
            )
        return response.json()

    @cache_result
    @timer
    def get_repository(self, owner: str, name: str) -> Repository:
        """Fetch a repository by owner and name."""
        data = self._get(f"/repos/{owner}/{name}")
        return Repository.from_api_dict(data)

    @cache_result
    @timer
    def get_developer(self, username: str) -> Developer:
        """Fetch a developer (user) by username."""
        data = self._get(f"/users/{username}")
        return Developer.from_api_dict(data)

    @timer
    def iter_commits(
        self, owner: str, name: str, per_page: int = 30
    ) -> Iterable[Commit]:
        """Yield commits of a repository, one page at a time (lazy)."""
        page = 1
        while True:
            data = self._get(
                f"/repos/{owner}/{name}/commits",
                params={"page": page, "per_page": per_page},
            )
            if not data:
                return
            for item in data:
                yield Commit.from_api_dict(item)
            if len(data) < per_page:
                return
            page += 1

    @timer
    def get_repo_languages(self, owner: str, name: str) -> dict[str, int]:
        """Fetch byte counts per language of a repository."""
        return self._get(f"/repos/{owner}/{name}/languages")

    @cache_result
    @timer
    def get_open_issues_count(self, owner: str, name: str) -> int:
        """Open issues count, read from the repository payload."""
        data = self._get(f"/repos/{owner}/{name}")
        return int(data.get("open_issues_count", 0) or 0)
