from __future__ import annotations

import random
from dataclasses import dataclass

from dungeon_crawler.models.entity import Entity
from dungeon_crawler.models.item import Item

HEART_ITEMS: tuple[Item, ...] = (
    Item(name="heart_red", icon="❤️", heal_amount=3),
    Item(name="heart_orange", icon="🧡", heal_amount=5),
    Item(name="heart_yellow", icon="💛", heal_amount=10),
    Item(name="heart_green", icon="💚", heal_amount=15),
    Item(name="heart_blue", icon="💙", heal_amount=20),
    Item(name="heart_purple", icon="💜", heal_amount=30),
)

FLOOR_STAT_RANGES: dict[int, dict[str, tuple[int, int]]] = {
    1: {"hp": (6, 10), "atk": (2, 4), "defense": (0, 1), "exp": (4, 8)},
    2: {"hp": (10, 16), "atk": (3, 6), "defense": (0, 2), "exp": (8, 14)},
    3: {"hp": (14, 22), "atk": (5, 8), "defense": (1, 3), "exp": (12, 20)},
}


@dataclass(frozen=True)
class SpawnResolver:
    base_seed: int

    def _rng(self, floor_id: int, spawn_index: int, *, salt: int = 0) -> random.Random:
        return random.Random(self.base_seed + floor_id * 1000 + spawn_index * 10 + salt)

    def roll_enemy_stats(self, floor_id: int, spawn_index: int, *, boss: bool = False) -> dict[str, int]:
        ranges = FLOOR_STAT_RANGES[floor_id]
        rng = self._rng(floor_id, spawn_index, salt=1)
        stats = {
            "hp": rng.randint(*ranges["hp"]),
            "atk": rng.randint(*ranges["atk"]),
            "defense": rng.randint(*ranges["defense"]),
            "exp_reward": rng.randint(*ranges["exp"]),
        }
        if boss:
            stats["hp"] = int(stats["hp"] * 1.5)
        return stats

    def roll_heart_item(self, floor_id: int, spawn_index: int) -> Item:
        rng = self._rng(floor_id, spawn_index, salt=2)
        template = rng.choice(HEART_ITEMS)
        return Item(name=template.name, icon=template.icon, heal_amount=template.heal_amount)

    def spawn_enemies(
        self,
        positions: list[tuple[int, int]],
        *,
        floor_id: int,
        boss_indices: set[int] | None = None,
    ) -> list[Entity]:
        boss_indices = boss_indices or set()
        enemies: list[Entity] = []
        for idx, (x, y) in enumerate(positions):
            stats = self.roll_enemy_stats(floor_id, idx, boss=idx in boss_indices)
            enemies.append(
                Entity(
                    name=f"enemy_f{floor_id}_{idx + 1}",
                    x=x,
                    y=y,
                    hp=stats["hp"],
                    max_hp=stats["hp"],
                    atk=stats["atk"],
                    defense=stats["defense"],
                    exp_reward=stats["exp_reward"],
                )
            )
        return enemies

    def spawn_ground_items(
        self,
        positions: list[tuple[int, int]],
        *,
        floor_id: int,
    ) -> dict[tuple[int, int], list[Item]]:
        ground: dict[tuple[int, int], list[Item]] = {}
        for idx, pos in enumerate(positions):
            ground.setdefault(pos, []).append(self.roll_heart_item(floor_id, idx))
        return ground
