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
    anchor_min_spacing: int = 10
    min_enemy_spawns: int = 6
    max_generation_attempts: int = 100


class FloorGenerator:
    """
    Template-driven floor pipeline:

    1. scatter room origins on the world grid
    2. assign start / stair / normal roles
    3. pick one template per origin (random among valid fits)
    4. stamp rooms onto the dungeon grid
    5. connect rooms with a graph + carved corridors
    6. retry with a new seed when enemy spawn count is too low
    """

    def __init__(self, loader: RoomTemplateLoader | None = None) -> None:
        self.loader = loader or RoomTemplateLoader()

    def generate(self, dungeon: Dungeon, config: FloorGeneratorConfig) -> None:
        self._validate_config(config)
        pools = TemplatePools.load(self.loader)
        self._validate_room_count_for_templates(config, pools)

        for attempt in range(config.max_generation_attempts):
            attempt_seed = config.seed + attempt * 131
            rng = random.Random(attempt_seed)
            dungeon.reset_for_floor(config.floor_id)

            try:
                self._build_floor(dungeon, config, pools, rng)
            except RuntimeError:
                continue

            if len(dungeon.enemy_spawn_tiles) >= config.min_enemy_spawns:
                return

        raise RuntimeError(
            f"Floor {config.floor_id}: failed to generate at least "
            f"{config.min_enemy_spawns} enemy spawns after "
            f"{config.max_generation_attempts} attempts"
        )

    def _build_floor(
        self,
        dungeon: Dungeon,
        config: FloorGeneratorConfig,
        pools: TemplatePools,
        rng: random.Random,
    ) -> None:
        origins = scatter_anchors(
            rng,
            config.room_count,
            map_width=dungeon.width,
            map_height=dungeon.height,
            min_spacing=config.anchor_min_spacing,
            max_room_width=pools.max_room_width,
            max_room_height=pools.max_room_height,
        )
        if len(origins) < config.room_count:
            raise RuntimeError("Failed to place enough scattered room origins")

        room_anchors = assign_room_anchors(origins, room_count=config.room_count)
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
        if config.min_enemy_spawns <= 5:
            raise ValueError("min_enemy_spawns must be greater than 5")

    @staticmethod
    def _validate_room_count_for_templates(config: FloorGeneratorConfig, pools: TemplatePools) -> None:
        required = 2 + len(pools.normal)
        if config.room_count < required:
            raise ValueError(
                f"room_count must be >= {required} to place every normal template "
                f"(start + stair + {len(pools.normal)} normals)"
            )

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
                anchor_x=anchor.x,
                anchor_y=anchor.y,
                template_width=template.width,
                template_height=template.height,
                template_name=template.name,
                room_role=anchor.role.value,
            )
