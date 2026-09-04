"""Shared fixtures/factory functions for analyzer tests (DRY)."""

from datetime import datetime

from core.models import Commit, Developer, Repository


def make_commit(sha="c1", date="2026-09-00T10:00:00+00:00", author="enzo",
                additions=5, deletions=3):
    return Commit(
        sha=sha,
        message=f"msg {sha}",
        author=author,
        author_email=f"{author}@x.com",
        date=datetime.fromisoformat(date),
        additions=additions,
        deletions=deletions,
        files_changed=0,
    )


def make_repo(name="reponame", owner="EnzoVieira3012", lang="Python", stars=10):
    return Repository(name, owner, lang=lang, stars=stars)


def make_dev(username="enzo", repo_count=2):
    dev = Developer(username)
    for i in range(repo_count):
        dev.add_repo(Repository(f"{username}-repo{i}", "owner"))
    return dev