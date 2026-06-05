from __future__ import annotations

from collections.abc import Callable
from functools import wraps


def validate_action(func: Callable[..., object]) -> Callable[..., object | bool]:
    """
    Wrap action entrypoints and convert validation/runtime errors to False.
    """

    @wraps(func)
    def wrapper(*args: object, **kwargs: object) -> object | bool:
        try:
            return func(*args, **kwargs)
        except (ValueError, IndexError, RuntimeError):
            return False

    return wrapper

