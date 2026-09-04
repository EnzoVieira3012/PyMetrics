"""Unit tests for the pure pagination/sorting helpers (api/pagination.py).

No Flask, no network: these helpers are pure functions.
"""

from datetime import datetime, timezone

import pytest

from api.pagination import (
    OrderDir,
    SortField,
    paginate,
    parse_params,
    sort_commits,
)


class FakeCommit:
    """Minimal stand-in for Commit with author/date for sorting tests."""

    def __init__(self, author: str, date: datetime) -> None:
        self.author = author
        self.date = date


UTC = timezone.utc


def commit(author: str, iso: str) -> FakeCommit:
    return FakeCommit(author, datetime.fromisoformat(iso))


# --- parse_params -------------------------------------------------------


def test_parse_params_defaults():
    result = parse_params("20", "1", "date", "desc")
    assert result == {
        "per_page": 20,
        "page": 1,
        "sort": SortField.DATE,
        "order": OrderDir.DESC,
    }


@pytest.mark.parametrize(
    "value,expected",
    [
        ("10", 10),
        ("20", 20),
        ("50", 50),
        ("100", 100),
        ("total", "total"),
    ],
)
def test_parse_params_valid_per_page(value, expected):
    result = parse_params(value, "1", "date", "desc")
    assert result["per_page"] == expected


def test_parse_params_invalid_per_page_raises():
    with pytest.raises(ValueError, match="per_page deve ser 10, 20, 50, 100 ou total"):
        parse_params("5", "1", "date", "desc")


@pytest.mark.parametrize("value", ["0", "-1", "abc"])
def test_parse_params_invalid_page_raises(value):
    with pytest.raises(ValueError, match="page deve ser um inteiro maior ou igual a 1"):
        parse_params("20", value, "date", "desc")


def test_parse_params_invalid_sort_raises():
    with pytest.raises(ValueError, match="sort deve ser date ou author"):
        parse_params("20", "1", "stars", "desc")


def test_parse_params_invalid_order_raises():
    with pytest.raises(ValueError, match="order deve ser asc ou desc"):
        parse_params("20", "1", "date", "up")


# --- paginate ------------------------------------------------------------


def test_paginate_first_page():
    result = paginate(list(range(250)), page=1, per_page=50)
    assert len(result["items"]) == 50
    assert result["page"] == 1
    assert result["total_commits"] == 250
    assert result["total_pages"] == 5
    assert result["has_next"] is True
    assert result["has_prev"] is False


def test_paginate_middle_page():
    result = paginate(list(range(5)), page=2, per_page=2)
    assert result["items"] == [2, 3]
    assert result["total_pages"] == 3
    assert result["has_next"] is True
    assert result["has_prev"] is True


def test_paginate_last_page():
    result = paginate(list(range(5)), page=3, per_page=2)
    assert result["items"] == [4]
    assert result["has_next"] is False


def test_paginate_past_end_empty_items():
    result = paginate(list(range(3)), page=99, per_page=10)
    assert result["items"] == []
    assert result["has_next"] is False
    assert result["has_prev"] is True


def test_paginate_empty_list():
    result = paginate([], page=1, per_page=20)
    assert result["items"] == []
    assert result["total_pages"] == 0
    assert result["has_next"] is False
    assert result["has_prev"] is False


# --- sort_commits ---------------------------------------------------------


def test_sort_by_author_asc():
    commits = [
        commit("b", "2026-09-01T10:00:00+00:00"),
        commit("a", "2026-09-01T09:00:00+00:00"),
    ]
    result = sort_commits(commits, SortField.AUTHOR, OrderDir.ASC)
    assert [c.author for c in result] == ["a", "b"]


def test_sort_by_author_desc():
    commits = [
        commit("a", "2026-09-01T09:00:00+00:00"),
        commit("b", "2026-09-01T10:00:00+00:00"),
    ]
    result = sort_commits(commits, SortField.AUTHOR, OrderDir.DESC)
    assert [c.author for c in result] == ["b", "a"]


def test_sort_by_date_recent_first():
    commits = [
        commit("a", "2026-09-01T09:00:00+00:00"),
        commit("b", "2026-09-02T09:00:00+00:00"),
    ]
    result = sort_commits(commits, SortField.DATE, OrderDir.DESC)
    assert [c.author for c in result] == ["b", "a"]


def test_sort_by_date_oldest_first():
    commits = [
        commit("b", "2026-09-02T09:00:00+00:00"),
        commit("a", "2026-09-01T09:00:00+00:00"),
    ]
    result = sort_commits(commits, SortField.DATE, OrderDir.ASC)
    assert [c.author for c in result] == ["a", "b"]


def test_paginate_with_real_total():
    result = paginate([1, 2], page=1, per_page=10, total=23267)
    assert result["total_commits"] == 23267
    assert result["total_pages"] == 2327
    assert result["has_next"] is True


def test_sort_does_not_mutate_original():
    commits = [
        commit("b", "2026-09-01T10:00:00+00:00"),
        commit("a", "2026-09-01T09:00:00+00:00"),
    ]
    original_authors = [c.author for c in commits]
    sort_commits(commits, SortField.AUTHOR, OrderDir.ASC)
    assert [c.author for c in commits] == original_authors


def test_sort_stable_on_ties():
    c1 = commit("a", "2026-09-01T10:00:00+00:00")
    c2 = commit("a", "2026-09-01T09:00:00+00:00")
    commits = [c1, c2]
    result = sort_commits(commits, SortField.AUTHOR, OrderDir.ASC)
    assert result == [c1, c2]
