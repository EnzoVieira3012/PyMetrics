"""Data models for PyMetrics (POO core).

Pure data structures — no GitHub API calls here.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class Commit:
    """A single commit with change statistics."""

    def __init__(
        self,
        sha: str,
        message: str,
        author: str,
        author_email: str,
        date: datetime,
        additions: int = 0,
        deletions: int = 0,
        files_changed: int = 0,
    ) -> None:
        if not sha or not message:
            raise ValueError("sha and message are required")
        self._sha = sha
        self._message = message
        self._author = author
        self._author_email = author_email
        self._date = date
        self._additions = additions
        self._deletions = deletions
        self._files_changed = files_changed

    @property
    def sha(self) -> str:
        return self._sha

    @property
    def message(self) -> str:
        return self._message

    @property
    def author(self) -> str:
        return self._author

    @property
    def author_email(self) -> str:
        return self._author_email

    @property
    def date(self) -> datetime:
        return self._date

    @property
    def additions(self) -> int:
        return self._additions

    @property
    def deletions(self) -> int:
        return self._deletions

    @property
    def files_changed(self) -> int:
        return self._files_changed

    def total_changes(self) -> int:
        """Sum of additions and deletions."""
        return self._additions + self._deletions

    def brief(self) -> str:
        """Short one-line summary: sha | message | date."""
        return f"{self._sha[:7]} | {self._message} | {self._date:%Y-%m-%d %H:%M}"

    @classmethod
    def from_api_dict(cls, data: dict) -> "Commit":
        """Build a Commit from a raw GitHub API dict, with safe defaults."""
        commit = data.get("commit", {})
        author_info = commit.get("author", {})
        try:
            date = datetime.fromisoformat(author_info.get("date", "").replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            date = datetime.fromisoformat("1970-01-01T00:00:00+00:00")
        return cls(
            sha=data.get("sha", ""),
            message=commit.get("message", ""),
            author=(data.get("author") or {}).get("login", ""),
            author_email=author_info.get("email", ""),
            date=date,
            additions=int(data.get("stats", {}).get("additions", 0) or 0),
            deletions=int(data.get("stats", {}).get("deletions", 0) or 0),
            files_changed=int(data.get("files_count", 0) or 0),
        )


class Repository:
    """A GitHub repository."""

    def __init__(
        self,
        name: str,
        owner: str,
        description: str | None = None,
        lang: str = "",
        stars: int = 0,
    ) -> None:
        self._name = name
        self._owner = owner
        self._description = description
        self._lang = lang
        self._stars = stars

    @property
    def name(self) -> str:
        return self._name

    @property
    def owner(self) -> str:
        return self._owner

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def lang(self) -> str:
        return self._lang

    @property
    def stars(self) -> int:
        return self._stars

    @property
    def url(self) -> str:
        """Derived property: repository URL on GitHub."""
        return f"https://github.com/{self._owner}/{self._name}"

    @classmethod
    def from_api_dict(cls, data: dict) -> "Repository":
        """Build a Repository from a raw GitHub API dict."""
        return cls(
            name=data.get("name", ""),
            owner=(data.get("owner") or {}).get("login", ""),
            description=data.get("description"),
            lang=data.get("language") or "",
            stars=int(data.get("stargazers_count", 0) or 0),
        )


class Developer:
    """A GitHub developer with a list of repositories."""

    def __init__(self, username: str, repos: list[Repository] | None = None) -> None:
        self._username = username
        self._repos = list(repos or [])

    @property
    def username(self) -> str:
        return self._username

    @property
    def repos(self) -> list[Repository]:
        return list(self._repos)

    def add_repo(self, repo: Repository) -> None:
        """Add a repository to the developer."""
        self._repos.append(repo)

    @property
    def repo_count(self) -> int:
        return len(self._repos)

    @classmethod
    def from_api_dict(cls, data: dict) -> "Developer":
        return cls(username=data.get("login", ""))


class Analyzer(ABC):
    """Abstract base for metric analysis over a list of commits."""

    def __init__(self, commits: list[Commit]) -> None:
        self._commits = list(commits)

    @abstractmethod
    def analyze(self) -> dict[str, Any]:
        """Compute metrics and return them as a dict."""

    def commit_count(self) -> int:
        """Concrete helper: number of commits analyzed."""
        return len(self._commits)

    def compute_average(self) -> float:
        """Average total_changes per commit; 0.0 when empty."""
        if not self._commits:
            return 0.0
        total = sum(c.total_changes() for c in self._commits)
        return total / len(self._commits)

    def summary(self) -> str:
        """Human-readable summary of the analyzed metrics."""
        lines = [f"{key}: {value}" for key, value in self.analyze().items()]
        return "\n".join(lines)


class Report(ABC):
    """Abstract base for metric export."""

    def __init__(self, metrics: dict[str, Any]) -> None:
        self._metrics = dict(metrics)

    @abstractmethod
    def export(self, path: str | None = None) -> str:
        """Render metrics as a string; write to file if path given."""

    def summary(self) -> str:
        """Concrete helper: human-readable metric listing."""
        lines = [f"{key}: {value}" for key, value in self._metrics.items()]
        return "\n".join(lines)