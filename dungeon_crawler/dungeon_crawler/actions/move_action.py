from __future__ import annotations

from dataclasses import dataclass, field

from dungeon_crawler.actions.base_action import Action
from dungeon_crawler.models.dungeon import Dungeon
from dungeon_crawler.models.entity import Entity


@dataclass(frozen=True)
class MoveAction(Action):
    entity: Entity
    dungeon: Dungeon
    dx: int
    dy: int
    _previous_pos: tuple[int, int] | None = field(default=None, init=False, repr=False, compare=False)
    _executed: bool = field(default=False, init=False, repr=False, compare=False)

    def execute(self) -> None:
        target_x = self.entity.x + self.dx
        target_y = self.entity.y + self.dy
        if not self.dungeon.is_walkable(target_x, target_y):
            return

        object.__setattr__(self, "_previous_pos", self.entity.pos)
        self.entity.set_pos(target_x, target_y)
        object.__setattr__(self, "_executed", True)

    def undo(self) -> None:
        if not self._executed or self._previous_pos is None:
            return
        self.entity.set_pos(*self._previous_pos)
        object.__setattr__(self, "_executed", False)

