"""Unit tests for the three custom decorators."""

import logging

from decorators.cache import cache_result
from decorators.logger import log_execution
from decorators.timer import timer

# ---------------- timer ----------------

def test_timer_logs_name_and_time(caplog):
    @timer
    def f():
        return 42

    with caplog.at_level(logging.INFO):
        result = f()
    assert result == 42
    assert any("f executada em" in r.message for r in caplog.records)


def test_timer_preserves_name():
    @timer
    def funcao_original():
        pass

    assert funcao_original.__name__ == "funcao_original"


# ---------------- cache_result ----------------

def test_cache_result_second_call_skips_execution():
    calls = {"n": 0}

    @cache_result
    def f(x):
        calls["n"] += 1
        return x * 2

    assert f(2) == 4
    assert f(2) == 4
    assert calls["n"] == 1


def test_cache_result_distinct_args():
    calls = {"n": 0}

    @cache_result
    def f(x):
        calls["n"] += 1
        return x

    f(1)
    f(2)
    assert calls["n"] == 2


def test_cache_result_preserves_return_value():
    @cache_result
    def f():
        return {"a": 1}

    assert f() == {"a": 1}
    assert f() is f()  # cached reference


def test_cache_result_preserves_name():
    @cache_result
    def funcao_original():
        pass

    assert funcao_original.__name__ == "funcao_original"


# ---------------- log_execution ----------------

def test_log_execution_logs_call(caplog):
    @log_execution
    def f(a, b=2):
        return a + b

    with caplog.at_level(logging.INFO):
        assert f(1, b=3) == 4
    assert any("f(1, b=3)" in r.message for r in caplog.records)


def test_log_execution_sanitizes_secrets(caplog):
    @log_execution
    def f(secret="x", token="y"):
        pass

    with caplog.at_level(logging.INFO):
        f(secret="x", token="y")
    messages = [r.message for r in caplog.records]
    assert any("***" in m for m in messages)
    assert all("x" not in m and "y" not in m for m in messages)


def test_log_execution_preserves_name():
    @log_execution
    def funcao_original():
        pass

    assert funcao_original.__name__ == "funcao_original"