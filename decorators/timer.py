"""@timer decorator: logs function execution time."""

import functools
import logging
import time

logger = logging.getLogger(__name__)


def timer(func):
    """Log how long the decorated function took to run."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info("%s executada em %.3fs", func.__name__, elapsed)
        return result

    return wrapper
