"""Unit tests for the concrete analyzers."""

import pytest

from core.analyzer import CommitAnalyzer, DeveloperAnalyzer, RepositoryAnalyzer
from core.models import Analyzer
from tests.fixtures.factories import make_commit, make_dev, make_repo


# --------------- CommitAnalyzer ---------------

def test_commit_analyzer_full_metrics():
    commits = [
        make_commit("c1", "2026-09-01T10:00:00+00:00", "enzo", additions=5, deletions=3),
        make_commit("c2", "2026-09-01T10:00:00+00:00", "ana", additions=1, deletions=1),
        make_commit("c3", "2026-09-01T11:00:00+00:00", "enzo", additions=2, deletions=2),
    ]
    result = CommitAnalyzer(commits).analyze()
    assert result["total_commits"] == 3
    # total_changes: 8, 2, 4 -> avg 14/3
    assert result["avg_changes_per_commit"] == pytest.approx(14 / 3)
    assert result["most_common_day"] == "Tuesday"  # 2026-09-01 é terça
    assert result["most_common_hour"] in (10, 11, 12)
    assert result["top_authors"][0][0] == "enzo"  # 2 commits
    assert result["commits_by_author"] == {"enzo": 2, "ana": 1}
    assert result["largest_commit"] == "c1"  # 8 mudanças


def test_commit_analyzer_filters_empty_authors():
    commits = [
        make_commit("c1", "2026-09-01T10:00:00+00:00", "enzo"),
        make_commit("c2", "2026-09-01T11:00:00+00:00", ""),
        make_commit("c3", "2026-09-01T12:00:00+00:00", "ana"),
    ]
    result = CommitAnalyzer(commits).analyze()
    assert result["commits_by_author"] == {"enzo": 1, "ana": 1}
    assert "" not in result["commits_by_author"]


def test_commit_analyzer_lambda_first_last():
    commits = [
        make_commit("c1", "2026-09-01T10:00:00+00:00", "enzo"),
        make_commit("c2", "2026-09-02T10:00:00+00:00", "enzo"),
    ]
    result = CommitAnalyzer(commits).analyze()
    assert result["first_commit"] == "c1"
    assert result["last_commit"] == "c2"


def test_commit_analyzer_empty():
    result = CommitAnalyzer([]).analyze()
    assert result["total_commits"] == 0
    assert result["avg_changes_per_commit"] == 0.0
    assert result["most_common_day"] is None
    assert result["most_common_hour"] is None
    assert result["top_authors"] == []


def test_commit_analyzer_inherits_compute_average():
    assert hasattr(CommitAnalyzer, "compute_average")
    assert issubclass(CommitAnalyzer, Analyzer)


# --------------- RepositoryAnalyzer ---------------

def test_repository_analyzer():
    repos = [
        make_repo("a", lang="Python", stars=10),
        make_repo("b", lang="Python", stars=20),
        make_repo("c", lang="JavaScript", stars=30),
    ]
    result = RepositoryAnalyzer(repos).analyze()
    assert result["total_repos"] == 3
    assert result["total_stars"] == 60
    assert result["avg_stars"] == 20.0
    assert result["top_languages"][0] == ("Python", 2)
    assert result["most_popular"] == repos[2].url
    assert result["ranked_repos"] == [repos[2].url, repos[1].url, repos[0].url]


def test_repository_analyzer_skips_empty_lang():
    repos = [make_repo("a", lang="", stars=1), make_repo("b", lang="Go", stars=2)]
    result = RepositoryAnalyzer(repos).analyze()
    langs = dict(result["top_languages"])
    assert "" not in langs


def test_repository_analyzer_empty():
    result = RepositoryAnalyzer([]).analyze()
    assert result["total_repos"] == 0
    assert result["avg_stars"] == 0.0
    assert result["top_languages"] == []
    assert result["most_popular"] is None
    assert result["ranked_repos"] == []


# --------------- DeveloperAnalyzer ---------------

def test_developer_analyzer():
    devs = [
        make_dev("enzo", repo_count=3),
        make_dev("ana", repo_count=1),
        make_dev("lucas", repo_count=2),
    ]
    result = DeveloperAnalyzer(devs).analyze()
    assert result["total_devs"] == 3
    assert result["avg_repos_per_dev"] == 2.0
    assert result["top_developers"][0] == ("enzo", 3)
    assert result["most_prolific"] == "enzo"


def test_developer_analyzer_empty():
    result = DeveloperAnalyzer([]).analyze()
    assert result["total_devs"] == 0
    assert result["avg_repos_per_dev"] == 0.0
    assert result["top_developers"] == []
    assert result["most_prolific"] is None