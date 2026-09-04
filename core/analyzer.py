"""Concrete analyzers producing metric dicts.

CommitAnalyzer, RepositoryAnalyzer and DeveloperAnalyzer all inherit
the abstract Analyzer base (core/models.py) and implement analyze().
"""

from collections import Counter

from core.models import Analyzer, Commit, Developer, Repository


def _top_n(counter: Counter, n: int, *, skip_empty: bool = False) -> list[tuple[str, int]]:
    """Return the n most common (key, count) pairs, excluding empty keys."""
    if skip_empty:
        counter = Counter({k: v for k, v in counter.items() if k})
    return counter.most_common(n)


class CommitAnalyzer(Analyzer):
    """Analyze a collection of Commit objects."""

    def analyze(self) -> dict[str, int | float | str | None | list[tuple[str, int]]]:
        if not self._commits:
            return {
                "total_commits": 0,
                "avg_changes_per_commit": 0.0,
                "most_common_day": None,
                "most_common_hour": None,
                "top_authors": [],
                "commits_by_author": {},
                "first_commit": None,
                "last_commit": None,
            }

        day_counter = Counter(c.date.strftime("%A") for c in self._commits)
        hour_counter = Counter(c.date.hour for c in self._commits)
        authors = list(filter(lambda c: c.author, self._commits))
        author_counter = Counter(c.author for c in authors)

        largest = max(self._commits, key=lambda c: c.total_changes())
        first = min(self._commits, key=lambda c: c.date)
        last = max(self._commits, key=lambda c: c.date)

        return {
            "total_commits": len(self._commits),
            "avg_changes_per_commit": self.compute_average(),
            "most_common_day": day_counter.most_common(1)[0][0],
            "most_common_hour": hour_counter.most_common(1)[0][0],
            "top_authors": author_counter.most_common(3),
            "commits_by_author": dict(author_counter),
            "largest_commit": largest.sha,
            "first_commit": first.sha,
            "last_commit": last.sha,
        }


class RepositoryAnalyzer(Analyzer):
    """Analyze a collection of Repository objects."""

    def __init__(self, repos: list[Repository] | None = None) -> None:
        super().__init__([r for r in (repos or []) if r])  # keep _commits as storage

    def analyze(self) -> dict[str, int | float | list[tuple[str, int]] | str | None]:
        repos = self._commits
        if not repos:
            return {
                "total_repos": 0,
                "total_stars": 0,
                "avg_stars": 0.0,
                "top_languages": [],
                "most_popular": None,
                "ranked_repos": [],
            }
        lang_counter = Counter(
            r.lang for r in repos if r.lang
        )
        popular = max(repos, key=lambda r: r.stars)
        ranked = sorted(repos, key=lambda r: r.stars, reverse=True)
        return {
            "total_repos": len(repos),
            "total_stars": sum(r.stars for r in repos),
            "avg_stars": sum(r.stars for r in repos) / len(repos),
            "top_languages": _top_n(lang_counter, 3),
            "most_popular": popular.url,
            "ranked_repos": [r.url for r in ranked],
        }


class DeveloperAnalyzer(Analyzer):
    """Analyze a collection of Developer objects."""

    def __init__(self, devs: list[Developer] | None = None) -> None:
        super().__init__([d for d in (devs or []) if d])  # keep _commits as storage

    def analyze(self) -> dict[str, int | float | list[tuple[str, int]] | str | None]:
        devs = self._commits
        if not devs:
            return {
                "total_devs": 0,
                "avg_repos_per_dev": 0.0,
                "top_developers": [],
                "most_prolific": None,
            }
        repo_counter = Counter(d.username for d in devs for _ in d.repos)
        prolific = max(devs, key=lambda d: d.repo_count)
        return {
            "total_devs": len(devs),
            "avg_repos_per_dev": sum(d.repo_count for d in devs) / len(devs),
            "top_developers": _top_n(repo_counter, 3),
            "most_prolific": prolific.username,
        }