from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InputCommand:
    kind: str
    payload: str | tuple[int, int] | None = None


class InputHandler:
    MOVE_MAP: dict[str, tuple[int, int]] = {
        "w": (0, -1),
        "a": (-1, 0),
        "s": (0, 1),
        "d": (1, 0),
    }

    def parse_key(self, key: str) -> InputCommand | None:
        if not key:
            return None
        normalized = key.lower()

        if normalized in self.MOVE_MAP:
            return InputCommand(kind="move", payload=self.MOVE_MAP[normalized])
        if normalized == "u":
            return InputCommand(kind="undo")
        if normalized == "r":
            return InputCommand(kind="redo")
        if normalized == "i":
            return InputCommand(kind="toggle_inventory")
        if normalized in "1234567890":
            return InputCommand(kind="use_slot", payload=normalized)
        if normalized == "c":
            return InputCommand(kind="melee_mode")
        if normalized == "v":
            return InputCommand(kind="ranged_mode")
        if normalized == "esc":
            return InputCommand(kind="exit_to_menu")
        return None

