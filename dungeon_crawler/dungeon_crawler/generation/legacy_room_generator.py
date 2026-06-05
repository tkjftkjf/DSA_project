from __future__ import annotations

import random

from dungeon_crawler.generation.corridor_carver import carve_room_corridors
from dungeon_crawler.generation.room_graph import build_room_graph
from dungeon_crawler.models.dungeon import Dungeon
from dungeon_crawler.models.room_node import RoomNode


def generate_legacy_rooms(
    dungeon: Dungeon,
    room_count: int,
    *,
    seed: int = 0,
    max_attempts: int = 500,
    extra_cycles: int = 1,
) -> None:
    """Small-map room scatter used by isolated unit tests."""
    if room_count < 1:
        raise ValueError("room_count must be >= 1")

    rng = random.Random(seed)
    dungeon.reset_for_floor(floor_id=1)

    templates = [
        {(0, 0)},
        {(0, 0), (1, 0)},
        {(0, 0), (1, 0), (0, 1)},
    ]

    used_tiles: set[tuple[int, int]] = set()
    room_id = 0
    attempts = 0
    while room_id < room_count and attempts < max_attempts:
        attempts += 1
        template = rng.choice(templates)
        anchor_x = rng.randint(0, dungeon.width - 1)
        anchor_y = rng.randint(0, dungeon.height - 1)
        translated = {(anchor_x + dx, anchor_y + dy) for dx, dy in template}

        if any(not dungeon.in_bounds(x, y) for x, y in translated):
            continue
        if translated & used_tiles:
            continue

        dungeon.room_nodes[room_id] = RoomNode(room_id=room_id, tiles=translated)
        used_tiles |= translated
        dungeon.floor_tiles |= translated
        room_id += 1

    if len(dungeon.room_nodes) != room_count:
        raise RuntimeError("Failed to place all rooms without overlap")

    edges = build_room_graph(dungeon.room_nodes, rng, extra_cycles=extra_cycles)
    dungeon.edges = edges
    carve_room_corridors(dungeon, dungeon.room_nodes, edges)
