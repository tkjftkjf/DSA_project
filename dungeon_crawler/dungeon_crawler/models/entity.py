from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from dungeon_crawler.models.inventory import Inventory

@dataclass
class Entity:
    name: str
    x: int
    y: int
    hp: int = 10
    max_hp: int = 10
    atk: int = 2
    defense: int = 0
    level: int = 1
    exp: int = 0
    exp_reward: int = 0
    is_alive: bool = True
    inventory: Optional[Inventory] = None

    @property
    def pos(self) -> tuple[int, int]:
        return (self.x, self.y)

    def set_pos(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def heal(self, amount: int) -> int:
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before

