from __future__ import annotations

from dataclasses import dataclass

from dungeon_crawler.models.room_template import START_TEMPLATE_SIZE


@dataclass(frozen=True)
class RoomNode:
    room_id: int
    tiles: set[tuple[int, int]]
    anchor_x: int = 0
    anchor_y: int = 0
    template_width: int = START_TEMPLATE_SIZE
    template_height: int = START_TEMPLATE_SIZE
    template_name: str = ""
    room_role: str = "normal"

    @property
    def center(self) -> tuple[int, int]:
        xs = [x for x, _ in self.tiles]
        ys = [y for _, y in self.tiles]
        return (sum(xs) // len(xs), sum(ys) // len(ys))
