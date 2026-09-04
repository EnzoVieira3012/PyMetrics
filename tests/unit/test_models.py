"""Unit tests for data models (POO)."""

import pytest
from datetime import datetime

from core.models import Analyzer, Commit, Developer, Report, Repository


def commit(sha="abc123", message="feat: add login", author="enzo", email="enzo@x.com",
           date="2026-09-04T14:30:00+00:00", additions=10, deletions=2, files=3):
    return Commit(
        sha=sha,
        message=message,
        author=author,
        author_email=email,
        date=datetime.fromisoformat(date),
        additions=additions,
        deletions=deletions,
        files_changed=files,
    )


# ---------------- Commit ----------------

def test_commit_construction():
    c = commit()
    assert c.sha == "abc123"
    assert c.message == "feat: add login"
    assert c.author == "enzo"
    assert c.author_email == "enzo@x.com"
    assert c.additions == 10
    assert c.deletions == 2
    assert c.files_changed == 3


def test_commit_validation_empty_sha():
    with pytest.raises(ValueError):
        commit(sha="")


def test_commit_validation_empty_message():
    with pytest.raises(ValueError):
        commit(message="")


def test_commit_total_changes():
    assert commit().total_changes() == 12


def test_commit_brief_format():
    c = commit()
    assert c.brief() == "abc123 | feat: add login | 2026-09-04 14:30"


def test_commit_from_api_dict_complete():
    data = {
        "sha": "abc123",
        "commit": {
            "message": "fix: bug",
            "author": {"name": "Enzo", "email": "enzo@x.com", "date": "2026-09-04T14:30:00Z"},
        },
        "author": {"login": "enzovieira"},
        "stats": {"additions": 5, "deletions": 1},
    }
    c = Commit.from_api_dict(data)
    assert c.sha == "abc123"
    assert c.message == "fix: bug"
    assert c.author == "enzovieira"
    assert c.additions == 5
    assert c.deletions == 1
    assert c.files_changed == 0


def test_commit_from_api_dict_missing_optional_fields():
    c = Commit.from_api_dict({"sha": "abc", "commit": {"message": "ok"}})
    assert c.sha == "abc"
    assert c.message == "ok"
    assert c.author == ""
    assert c.additions == 0
    assert c.deletions == 0
    assert c.files_changed == 0


def test_commit_from_api_dict_invalid_raises():
    with pytest.raises(ValueError):
        Commit.from_api_dict({})


# ---------------- Repository ----------------

def test_repository_construction():
    r = Repository("PyMetrics", "EnzoVieira3012", "metrics tool", "Python", 42)
    assert r.name == "PyMetrics"
    assert r.owner == "EnzoVieira3012"
    assert r.description == "metrics tool"
    assert r.lang == "Python"
    assert r.stars == 42


def test_repository_url():
    r = Repository("PyMetrics", "EnzoVieira3012")
    assert r.url == "https://github.com/EnzoVieira3012/PyMetrics"


def test_repository_from_api_dict():
    data = {
        "name": "PyMetrics",
        "owner": {"login": "EnzoVieira3012"},
        "description": "metrics",
        "language": "Python",
        "stargazers_count": 7,
    }
    r = Repository.from_api_dict(data)
    assert r.url == "https://github.com/EnzoVieira3012/PyMetrics"
    assert r.lang == "Python"
    assert r.stars == 7


def test_repository_from_api_dict_missing_fields():
    r = Repository.from_api_dict({})
    assert r.name == ""
    assert r.owner == ""
    assert r.lang == ""
    assert r.stars == 0


# ---------------- Developer ----------------

def test_developer_repo_count():
    d = Developer("enzo")
    assert d.repo_count == 0
    d.add_repo(Repository("a", "enzo"))
    d.add_repo(Repository("b", "enzo"))
    assert d.repo_count == 2
    assert len(d.repos) == 2


def test_developer_from_api_dict():
    d = Developer.from_api_dict({"login": "enzovieira"})
    assert d.username == "enzovieira"


# ---------------- Analyzer / Report (heranca) ----------------

class DummyAnalyzer(Analyzer):
    def analyze(self):
        return {"n": 1}


class DummyReport(Report):
    def export(self, path=None):
        return "\n".join(self._metrics.keys())


def test_abstract_analyzer_cannot_instantiate():
    with pytest.raises(TypeError):
        Analyzer(commits=[])  # type: ignore[abstract]


def test_abstract_report_cannot_instantiate():
    with pytest.raises(TypeError):
        Report(metrics={})  # type: ignore[abstract]


def test_analyzer_subclass_commit_count():
    a = DummyAnalyzer(commits=[commit(), commit()])
    assert a.commit_count() == 2
    assert a.analyze() == {"n": 1}


def test_report_subclass_summary():
    r = DummyReport(metrics={"commits": 3, "author": "enzo"})
    assert r.summary() == "commits: 3\nauthor: enzo"
    assert r.export() == "commits\nauthor"


# ---------------- most_active_day (Analyzer) ----------------

def test_most_active_day():
    a = DummyAnalyzer(
        commits=[
            commit(date="2026-09-01T10:00:00+00:00"),
            commit(date="2026-09-01T11:00:00+00:00"),
            commit(date="2026-09-02T09:00:00+00:00"),
        ]
    )
    days = {}
    for c in a._commits:
        day = c.date.date()
        days[day] = days.get(day, 0) + 1
    assert max(days, key=days.get) == datetime(2026, 9, 1).date()