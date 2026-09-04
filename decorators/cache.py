"""@cache_result decorator: in-memory result cache per function.

Limitations (documented):
- kwargs must be hashable (simple types OK).
- Returned mutable objects are cached by reference (no copy).
"""

import functools


def cache_result(func):
    """Cache the result of the function keyed by (name, args, kwargs)."""
    cache: dict = {}

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        key = (func.__name__, args, frozenset(kwargs.items()))
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]

    return wrapper