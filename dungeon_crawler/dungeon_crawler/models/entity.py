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

    def gain_exp(self, amount: int) -> bool:
        """
        Gain exp and apply a simple level-up rule.
        Returns True if leveled up.
        """
        self.exp += amount
        need = self.level * 10
        if self.exp < need:
            return False
        self.exp -= need
        self.level += 1
        self.max_hp += 2
        self.atk += 1
        self.defense += 1
        self.hp = self.max_hp
        return True

