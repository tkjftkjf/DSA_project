from __future__ import annotations

from dungeon_crawler.engine.floor_manager import FloorManager
from dungeon_crawler.engine.game_manager import GameManager
from dungeon_crawler.engine.spawn_resolver import SpawnResolver
from dungeon_crawler.models.entity import Entity
from dungeon_crawler.models.inventory import Inventory
from dungeon_crawler.models.item import Item


def compute_score(player: Entity, turn_id: int, kills: int) -> int:
    return player.exp + player.level * 100 + turn_id * 2 + kills * 50


def create_game_manager(seed: int = 7) -> GameManager:
    base_seed = 2026 + seed
    floor_manager = FloorManager.create(base_seed=seed, room_count=10, extra_cycles=2)
    dungeon = floor_manager.current_dungeon
    spawn_resolver = SpawnResolver(base_seed=base_seed)

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
        inventory=Inventory(),
    )
    assert player.inventory is not None
    for _ in range(3):
        player.inventory.add_item(Item(name="arrow", icon="🏹"))

    enemies: list[Entity] = []
    ground_items_by_floor: dict[int, dict[tuple[int, int], list[Item]]] = {}

    for floor_idx, floor_dungeon in enumerate(floor_manager.floors):
        floor_id = floor_idx + 1
        boss_indices = {0} if floor_id == 3 and floor_dungeon.enemy_spawn_tiles else set()
        floor_enemies = spawn_resolver.spawn_enemies(
            floor_dungeon.enemy_spawn_tiles,
            floor_id=floor_id,
            boss_indices=boss_indices,
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
        base_seed=base_seed,
        ground_items_by_floor=ground_items_by_floor,
    )
    manager.logs.append("던전에 진입했습니다.")
    return manager
