from __future__ import annotations

import random

from dungeon_crawler.engine.game_manager import GameManager
from dungeon_crawler.models.dungeon import Dungeon
from dungeon_crawler.models.entity import Entity
from dungeon_crawler.models.inventory import Inventory
from dungeon_crawler.models.item import Item

HEART_ITEMS = [
    Item(name="heart_red", icon="❤️", heal_amount=3),
    Item(name="heart_orange", icon="🧡", heal_amount=5),
    Item(name="heart_yellow", icon="💛", heal_amount=10),
    Item(name="heart_green", icon="💚", heal_amount=15),
    Item(name="heart_blue", icon="💙", heal_amount=20),
    Item(name="heart_purple", icon="💜", heal_amount=30),
]


def compute_score(player: Entity, turn_id: int, kills: int) -> int:
    return player.exp + player.level * 100 + turn_id * 2 + kills * 50


def create_game_manager(seed: int = 7) -> GameManager:
    dungeon = Dungeon(width=30, height=20)
    dungeon.generate_rooms(room_count=10, seed=seed, extra_cycles=2)

    floor = sorted(dungeon.floor_tiles)
    if not floor:
        raise RuntimeError("Dungeon has no floor tiles")

    player_pos = floor[0]
    player = Entity(
        name="player",
        x=player_pos[0],
        y=player_pos[1],
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
    enemy_spots = [floor[min(i, len(floor) - 1)] for i in (8, 14, 20, 26)]
    for idx, pos in enumerate(enemy_spots[:3]):
        enemies.append(
            Entity(
                name=f"enemy{idx + 1}",
                x=pos[0],
                y=pos[1],
                hp=8 + idx * 2,
                max_hp=8 + idx * 2,
                atk=2 + idx,
                defense=idx % 2,
                exp_reward=5 + idx * 3,
            )
        )

    manager = GameManager(
        dungeon=dungeon,
        player=player,
        entities=[player, *enemies],
        base_seed=2026 + seed,
    )

    rng = random.Random(seed)
    loot_spots = rng.sample(floor[1:], k=min(4, len(floor) - 1))
    for spot in loot_spots:
        item = rng.choice(HEART_ITEMS)
        manager.ground_items.setdefault(spot, []).append(item)

    manager.logs.append("던전에 진입했습니다.")
    return manager
