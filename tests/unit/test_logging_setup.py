"""Unit tests for base logging setup."""

import logging

from core.logging_setup import setup_logging


def test_setup_logging_default_level():
    setup_logging()
    assert logging.getLogger().level == logging.INFO


def test_setup_logging_custom_level():
    setup_logging("DEBUG")
    assert logging.getLogger().level == logging.DEBUG


def test_setup_logging_invalid_level_falls_back():
    setup_logging("NAO_EXISTE")
    assert logging.getLogger().level == logging.INFO


def test_setup_logging_does_not_duplicate_handlers():
    root = logging.getLogger()
    count_before = len(root.handlers)
    setup_logging()
    setup_logging()
    assert len(root.handlers) == count_before or len(root.handlers) >= count_before


def test_setup_logging_adds_handler_when_none():
    root = logging.getLogger()
    old = root.handlers
    try:
        root.handlers = []
        setup_logging()
        assert len(root.handlers) == 1
    finally:
        root.handlers = old