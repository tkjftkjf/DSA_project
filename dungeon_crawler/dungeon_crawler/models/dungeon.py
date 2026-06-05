from __future__ import annotations

from dungeon_crawler.models.room_node import RoomNode
from dungeon_crawler.models.room_template import WORLD_HEIGHT, WORLD_WIDTH, RoomTemplateLoader

__all__ = ["Dungeon", "RoomNode"]


class Dungeon:
    """Playable grid state: walkability, room metadata, and spawn markers."""

    def __init__(self, width: int = WORLD_WIDTH, height: int = WORLD_HEIGHT) -> None:
        self.width = width
        self.height = height
        self._blocked: set[tuple[int, int]] = set()
        self.room_nodes: dict[int, RoomNode] = {}
        self.edges: set[tuple[int, int]] = set()
        self.floor_tiles: set[tuple[int, int]] = set()
        self.stair_tiles: set[tuple[int, int]] = set()
        self.enemy_spawn_tiles: list[tuple[int, int]] = []
        self.item_spawn_tiles: list[tuple[int, int]] = []
        self.start_spawn: tuple[int, int] | None = None
        self.floor_id: int = 1

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def set_blocked(self, x: int, y: int, blocked: bool = True) -> None:
        if blocked:
            self._blocked.add((x, y))
        else:
            self._blocked.discard((x, y))

    def is_walkable(self, x: int, y: int) -> bool:
        if not self.in_bounds(x, y) or (x, y) in self._blocked:
            return False
        if self.floor_tiles:
            return (x, y) in self.floor_tiles
        return True

    def reset_for_floor(self, floor_id: int) -> None:
        self.floor_id = floor_id
        self.room_nodes.clear()
        self.edges.clear()
        self.floor_tiles.clear()
        self._blocked.clear()
        self.stair_tiles.clear()
        self.enemy_spawn_tiles.clear()
        self.item_spawn_tiles.clear()
        self.start_spawn = None

    def generate_floor(
        self,
        *,
        floor_id: int,
        room_count: int,
        seed: int = 0,
        extra_cycles: int = 1,
        loader: RoomTemplateLoader | None = None,
    ) -> None:
        from dungeon_crawler.generation.floor_generator import FloorGenerator, FloorGeneratorConfig

        FloorGenerator(loader=loader).generate(
            self,
            FloorGeneratorConfig(
                floor_id=floor_id,
                room_count=room_count,
                seed=seed,
                extra_cycles=extra_cycles,
            ),
        )

    def generate_rooms(
        self,
        room_count: int,
        *,
        seed: int = 0,
        max_attempts: int = 500,
        extra_cycles: int = 1,
    ) -> None:
        from dungeon_crawler.generation.legacy_room_generator import generate_legacy_rooms

        generate_legacy_rooms(
            self,
            room_count,
            seed=seed,
            max_attempts=max_attempts,
            extra_cycles=extra_cycles,
        )
