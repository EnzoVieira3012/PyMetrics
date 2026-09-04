"""@log_execution decorator: logs calls with sanitized arguments."""

import functools
import logging

logger = logging.getLogger(__name__)

_SENSITIVE_NAMES = ("token", "password", "passwd", "secret", "api_key", "key")


def log_execution(func):
    """Log each call of the function, hiding sensitive argument values."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        def _safe_value(name: str, value) -> str:
            lower = name.lower()
            if any(part in lower for part in _SENSITIVE_NAMES):
                return "***"
            return repr(value)

        varnames = func.__code__.co_varnames
        positional = [
            _safe_value(varnames[i] if i < len(varnames) else f"arg{i}", a)
            for i, a in enumerate(args)
            if not (i == 0 and varnames and varnames[0] == "self")
        ]
        call_args = ", ".join(positional)
        call_kwargs = ", ".join(f"{k}={_safe_value(k, v)}" for k, v in kwargs.items())
        parts = [p for p in (call_args, call_kwargs) if p]
        logger.info("%s(%s)", func.__name__, ", ".join(parts))
        return func(*args, **kwargs)

    return wrapper
