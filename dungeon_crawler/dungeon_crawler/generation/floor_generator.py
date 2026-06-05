from __future__ import annotations

import random
from dataclasses import dataclass

from dungeon_crawler.generation.anchor_placer import scatter_anchors
from dungeon_crawler.generation.corridor_carver import carve_room_corridors
from dungeon_crawler.generation.role_assigner import assign_room_anchors
from dungeon_crawler.generation.room_graph import build_room_graph
from dungeon_crawler.generation.room_stamper import stamp_room
from dungeon_crawler.generation.template_assigner import assign_room_templates
from dungeon_crawler.generation.template_pools import TemplatePools
from dungeon_crawler.generation.types import PlacedRoom, RoomStamp
from dungeon_crawler.models.dungeon import Dungeon
from dungeon_crawler.models.room_node import RoomNode
from dungeon_crawler.models.room_template import RoomTemplateLoader


@dataclass(frozen=True)
class FloorGeneratorConfig:
    floor_id: int
    room_count: int
    seed: int
    extra_cycles: int = 1
    anchor_min_dist: int = 3


class FloorGenerator:
    """
    Template-driven floor pipeline:

    1. scatter anchors on meta grid
    2. assign start / stair / normal roles
    3. pick one template per anchor
    4. stamp rooms onto the dungeon grid
    5. connect rooms with a graph + carved corridors
    """

    def __init__(self, loader: RoomTemplateLoader | None = None) -> None:
        self.loader = loader or RoomTemplateLoader()

    def generate(self, dungeon: Dungeon, config: FloorGeneratorConfig) -> None:
        self._validate_config(config)

        rng = random.Random(config.seed)
        pools = TemplatePools.load(self.loader)
        dungeon.reset_for_floor(config.floor_id)

        anchors = scatter_anchors(rng, config.room_count, min_dist=config.anchor_min_dist)
        if len(anchors) < config.room_count:
            raise RuntimeError("Failed to place enough scattered meta anchors")

        room_anchors = assign_room_anchors(anchors, room_count=config.room_count)
        placed_rooms = assign_room_templates(
            room_anchors,
            pools,
            rng,
            map_width=dungeon.width,
            map_height=dungeon.height,
        )

        stamps = [stamp_room(room, map_width=dungeon.width, map_height=dungeon.height) for room in placed_rooms]
        self._apply_stamps(dungeon, placed_rooms, stamps)

        edges = build_room_graph(dungeon.room_nodes, rng, extra_cycles=config.extra_cycles)
        dungeon.edges = edges
        carve_room_corridors(dungeon, dungeon.room_nodes, edges)

        if not dungeon.stair_tiles:
            raise RuntimeError(f"Floor {config.floor_id} has no stair tiles")
        if dungeon.start_spawn is None:
            raise RuntimeError(f"Floor {config.floor_id} has no start spawn")

    @staticmethod
    def _validate_config(config: FloorGeneratorConfig) -> None:
        if config.room_count < 3:
            raise ValueError("room_count must be >= 3 (start + stair + normal)")
        if config.floor_id not in (1, 2, 3):
            raise ValueError("floor_id must be 1, 2, or 3")

    @staticmethod
    def _apply_stamps(
        dungeon: Dungeon,
        placed_rooms: list[PlacedRoom],
        stamps: list[RoomStamp],
    ) -> None:
        for placed, stamp in zip(placed_rooms, stamps):
            dungeon.floor_tiles |= stamp.floor_tiles
            for pos in stamp.blocked_tiles:
                dungeon.set_blocked(*pos, blocked=True)
            dungeon.stair_tiles |= stamp.stair_tiles
            dungeon.enemy_spawn_tiles.extend(stamp.enemy_spawn_tiles)
            dungeon.item_spawn_tiles.extend(stamp.item_spawn_tiles)

            if stamp.start_spawn is not None:
                dungeon.start_spawn = stamp.start_spawn

            anchor = placed.anchor
            template = placed.template
            dungeon.room_nodes[placed.room_id] = RoomNode(
                room_id=placed.room_id,
                tiles=set(stamp.floor_tiles),
                meta_col=anchor.meta_col,
                meta_row=anchor.meta_row,
                template_width=template.width,
                template_height=template.height,
                template_name=template.name,
                room_role=anchor.role.value,
            )
