"""@disk_cache_result: persistent JSON result cache on disk.

Survives restarts: repeated GitHub requests read from disk instead of
hitting the API again. Each call is stored as a JSON file under
config.CACHE_DIR, keyed by a hash of (name, args, kwargs). Entries
expire after config.CACHE_TTL_HOURS.
"""

import functools
import hashlib
import json
import pathlib
import time

import config


def _key_path(func, args, kwargs) -> pathlib.Path:
    # Drop `self` from bound methods: its repr includes a memory address,
    # which would make cache keys differ across runs/restarts.
    call_args = args[1:] if args and hasattr(args[0], "__dict__") else args
    payload = json.dumps(
        {"name": func.__name__, "args": list(call_args), "kwargs": kwargs},
        sort_keys=True,
        default=str,
    )
    digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
    return config.CACHE_DIR / f"{func.__name__}_{digest}.json"


def disk_cache_result(func):
    """Cache the JSON-serializable result of func on disk."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        path = _key_path(func, args, kwargs)
        if path.exists():
            age = time.time() - path.stat().st_mtime
            if age < config.CACHE_TTL_HOURS * 3600:
                with path.open(encoding="utf-8") as f:
                    return json.load(f)
        result = func(*args, **kwargs)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False)
        return result

    return wrapper
