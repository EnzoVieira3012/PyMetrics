"""Pure pagination and sorting helpers for the REST API.

No Flask, no I/O: every function here is a pure function, easy to test
and reuse. Param validation happens at the trust boundary (parse_params
raises ValueError with a clear message; the endpoint turns it into 400).
"""

from __future__ import annotations

from enum import Enum


class PageSize(Enum):
    """Allowed per_page values. TOTAL means "fetch everything at once"."""

    DEZ = 10
    VINTE = 20
    CINQUENTA = 50
    CEM = 100
    TOTAL = "total"


class SortField(Enum):
    """Field used to order the commit list."""

    DATE = "date"
    AUTHOR = "author"


class OrderDir(Enum):
    """Sort direction."""

    ASC = "asc"
    DESC = "desc"


def parse_params(per_page: str, page: str, sort: str, order: str) -> dict:
    """Validate query params at the API boundary.

    Returns a dict with per_page (int or "total"), page (int), sort
    (SortField), order (OrderDir). Raises ValueError on invalid input.
    """
    page_size = _page_size(per_page)
    page_num = _page_num(page)
    sort_field = _sort_field(sort)
    order_dir = _order_dir(order)
    return {
        "per_page": page_size,
        "page": page_num,
        "sort": sort_field,
        "order": order_dir,
    }


def paginate(items: list, page: int, per_page: int, total: int | None = None) -> dict:
    """Slice a full list into one page plus navigation metadata.

    total lets the caller report the repo's REAL commit count (GitHub
    Link header) instead of the fetched sample; None falls back to
    len(items).
    """
    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]
    if total is None:
        total = len(items)
    total_pages = -(-total // per_page) if total else 0
    return {
        "items": page_items,
        "page": page,
        "per_page": per_page,
        "total_commits": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }


def sort_commits(commits: list, sort: SortField, order: OrderDir) -> list:
    """Return a new sorted list (original untouched), stable sort."""
    key = (lambda c: c.author) if sort is SortField.AUTHOR else (lambda c: c.date)
    return sorted(commits, key=key, reverse=order is OrderDir.DESC)


def _page_size(value: str) -> int | str:
    for candidate in PageSize:
        if value == str(candidate.value):
            return candidate.value
    raise ValueError("per_page deve ser 10, 20, 50, 100 ou total")


def _page_num(value: str) -> int:
    try:
        page = int(value)
    except (TypeError, ValueError):
        raise ValueError("page deve ser um inteiro maior ou igual a 1") from None
    if page < 1:
        raise ValueError("page deve ser um inteiro maior ou igual a 1")
    return page


def _sort_field(value: str) -> SortField:
    try:
        return SortField(value)
    except ValueError:
        raise ValueError("sort deve ser date ou author") from None


def _order_dir(value: str) -> OrderDir:
    try:
        return OrderDir(value)
    except ValueError:
        raise ValueError("order deve ser asc ou desc") from None
