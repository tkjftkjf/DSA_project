from __future__ import annotations

import time

from dungeon_crawler.engine.floor_manager import FloorManager
from dungeon_crawler.engine.game_manager import GameManager
from dungeon_crawler.engine.spawn_resolver import SpawnResolver
from dungeon_crawler.models.entity import Entity
from dungeon_crawler.models.inventory import Inventory
from dungeon_crawler.models.item import Item


def compute_score(player: Entity, turn_id: int, kills: int) -> int:
    return player.exp + player.level * 100 + turn_id * 2 + kills * 50


def derive_session_seed() -> int:
    """Derive session seed from game start time (nanosecond clock)."""
    return time.time_ns() % (2**31)


def create_game_manager() -> GameManager:
    session_seed = derive_session_seed()
    floor_manager = FloorManager.create(base_seed=session_seed, room_count=12, extra_cycles=2)
    dungeon = floor_manager.current_dungeon
    spawn_resolver = SpawnResolver(base_seed=session_seed)

    if dungeon.start_spawn is None:
        raise RuntimeError("Floor 1 has no start spawn")
    player = Entity(
        name="player",
        x=dungeon.start_spawn[0],
        y=dungeon.start_spawn[1],
        hp=20,
        max_hp=20,
        atk=5,
        defense=1,
        arrows=3,
        inventory=Inventory(),
    )

    enemies: list[Entity] = []
    ground_items_by_floor: dict[int, dict[tuple[int, int], list[Item]]] = {}

    for floor_idx, floor_dungeon in enumerate(floor_manager.floors):
        floor_id = floor_idx + 1
        floor_enemies = spawn_resolver.spawn_enemies(
            floor_dungeon.enemy_spawn_tiles,
            floor_id=floor_id,
        )
        enemies.extend(floor_enemies)
        floor_items = spawn_resolver.spawn_ground_items(
            floor_dungeon.item_spawn_tiles,
            floor_id=floor_id,
        )
        ground_items_by_floor[floor_id] = floor_items

    manager = GameManager(
        dungeon=dungeon,
        floor_manager=floor_manager,
        player=player,
        entities=[player, *enemies],
        base_seed=session_seed,
        ground_items_by_floor=ground_items_by_floor,
    )
    manager.logs.append(f"던전에 진입했습니다. (session seed={session_seed})")
    return manager
