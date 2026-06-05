from __future__ import annotations

from dataclasses import dataclass

from .base_action import Action


@dataclass(frozen=True, slots=True)
class EndTurnAction(Action):
    """No-op marker separating turns in undo stacks."""

    def execute(self) -> None:
        return

    def undo(self) -> None:
        return

