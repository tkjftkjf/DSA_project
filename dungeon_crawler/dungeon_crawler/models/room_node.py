from __future__ import annotations

from dataclasses import dataclass

from dungeon_crawler.models.room_template import CELL_SIZE


@dataclass(frozen=True)
class RoomNode:
    room_id: int
    tiles: set[tuple[int, int]]
    meta_col: int = 0
    meta_row: int = 0
    template_width: int = CELL_SIZE
    template_height: int = CELL_SIZE
    template_name: str = ""
    room_role: str = "normal"

    @property
    def center(self) -> tuple[int, int]:
        xs = [x for x, _ in self.tiles]
        ys = [y for _, y in self.tiles]
        return (sum(xs) // len(xs), sum(ys) // len(ys))
