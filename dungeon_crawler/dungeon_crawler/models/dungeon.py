from __future__ import annotations


class Dungeon:
    """Minimal walkability grid for movement unit tests."""

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self._blocked: set[tuple[int, int]] = set()

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def set_blocked(self, x: int, y: int, blocked: bool = True) -> None:
        if blocked:
            self._blocked.add((x, y))
        else:
            self._blocked.discard((x, y))

    def is_walkable(self, x: int, y: int) -> bool:
        return self.in_bounds(x, y) and (x, y) not in self._blocked

