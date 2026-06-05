from __future__ import annotations

from dataclasses import dataclass, field

from dungeon_crawler.models.dungeon import Dungeon
from dungeon_crawler.models.room_template import RoomTemplateLoader


@dataclass
class FloorManager:
    """Manages three dungeon floors and floor transitions via stair tiles."""

    base_seed: int
    floors: list[Dungeon] = field(default_factory=list)
    current_floor_index: int = 0
    stair_links: dict[tuple[int, int], int] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        base_seed: int,
        room_count: int = 10,
        extra_cycles: int = 1,
        loader: RoomTemplateLoader | None = None,
    ) -> FloorManager:
        loader = loader or RoomTemplateLoader()
        manager = cls(base_seed=base_seed)
        for floor_id in (1, 2, 3):
            dungeon = Dungeon()
            dungeon.generate_floor(
                floor_id=floor_id,
                room_count=room_count,
                seed=base_seed + floor_id * 97,
                extra_cycles=extra_cycles,
                loader=loader,
            )
            manager.floors.append(dungeon)
        manager._link_stairs()
        return manager

    @property
    def current_floor(self) -> int:
        return self.current_floor_index + 1

    @property
    def current_dungeon(self) -> Dungeon:
        return self.floors[self.current_floor_index]

    def is_on_stairs(self, pos: tuple[int, int]) -> bool:
        return pos in self.current_dungeon.stair_tiles

    def can_descend(self) -> bool:
        return self.current_floor_index < len(self.floors) - 1

    def descend(self) -> tuple[int, int] | None:
        if not self.can_descend():
            return None
        next_index = self.current_floor_index + 1
        next_floor = self.floors[next_index]
        target = next_floor.start_spawn
        if target is None:
            floors = sorted(next_floor.floor_tiles)
            target = floors[0] if floors else (0, 0)
        self.current_floor_index = next_index
        return target

    def _link_stairs(self) -> None:
        for idx in range(len(self.floors) - 1):
            nxt = self.floors[idx + 1]
            if nxt.start_spawn is not None:
                self.stair_links[(idx, idx + 1)] = nxt.start_spawn
