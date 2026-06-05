from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING

from dungeon_crawler.utils.action_validator import ValidationResult

if TYPE_CHECKING:
    from dungeon_crawler.actions.base_action import Action


def validate_action(func: Callable[..., object]) -> Callable[..., object | bool]:
    """
    Legacy wrapper for player entrypoints that still return bool.
    Validation errors are converted to False.
    """

    @wraps(func)
    def wrapper(*args: object, **kwargs: object) -> object | bool:
        try:
            return func(*args, **kwargs)
        except (ValueError, IndexError, RuntimeError):
            return False

    return wrapper


def validate_proposal(
    validator: Callable[["Action"], ValidationResult],
) -> Callable[[Callable[..., "Action | None"]], Callable[..., ValidationResult]]:
    """Decorator factory for propose_action methods."""

    def decorator(func: Callable[..., Action | None]) -> Callable[..., ValidationResult]:
        @wraps(func)
        def wrapper(*args: object, **kwargs: object) -> ValidationResult:
            action = func(*args, **kwargs)
            if action is None:
                return ValidationResult(ok=False, reason="no_proposal")
            return validator(action)

        return wrapper

    return decorator
