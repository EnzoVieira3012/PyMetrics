"""Unit tests for the disk-backed result cache."""

import config
from decorators.disk_cache import disk_cache_result


def _cache(monkeypatch, tmp_path, ttl_hours=1):
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(config, "CACHE_TTL_HOURS", ttl_hours)


@disk_cache_result
def _compute(x: int) -> dict:
    _compute.calls += 1
    return {"x": x}


def test_disk_cache_hits_disk(monkeypatch, tmp_path):
    _cache(monkeypatch, tmp_path)
    _compute.calls = 0
    assert _compute(1) == {"x": 1}
    assert _compute(1) == {"x": 1}
    assert _compute(1) == {"x": 1}
    assert _compute.calls == 1


def test_disk_cache_distinct_args(monkeypatch, tmp_path):
    _cache(monkeypatch, tmp_path)
    _compute.calls = 0
    assert _compute(1) == {"x": 1}
    assert _compute(2) == {"x": 2}
    assert _compute(2) == {"x": 2}
    assert _compute.calls == 2


def test_disk_cache_ttl_expired_refetches(monkeypatch, tmp_path):
    _cache(monkeypatch, tmp_path, ttl_hours=0)
    _compute.calls = 0
    assert _compute(3) == {"x": 3}
    assert _compute(3) == {"x": 3}
    assert _compute.calls == 2


def test_disk_cache_persists_across_instances(monkeypatch, tmp_path):
    _cache(monkeypatch, tmp_path)

    class _Fake:
        def __init__(self, value: int) -> None:
            self.value = value

        @disk_cache_result
        def get(self, key: str) -> dict:
            _Fake.calls += 1
            return {"key": key, "value": self.value}

    _Fake.calls = 0
    a = _Fake(1)
    b = _Fake(2)
    assert a.get("x") == {"key": "x", "value": 1}
    # Second call comes from disk (self was dropped from the key):
    assert b.get("x") == {"key": "x", "value": 1}
    assert _Fake.calls == 1
