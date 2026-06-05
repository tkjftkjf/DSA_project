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
    floor_id: int = 1
    arrows: int = 0
    is_alive: bool = True
    inventory: Optional[Inventory] = None

    @property
    def pos(self) -> tuple[int, int]:
        return (self.x, self.y)

    def set_pos(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def exp_required_for_level_up(self) -> int:
        return self.level * 10

    def heal(self, amount: int) -> int:
        if self.hp >= self.max_hp:
            return 0
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before

    def gain_exp(self, amount: int) -> bool:
        """Add exp then attempt level-up. Returns True if leveled up."""
        self.exp += amount
        return self.try_level_up()

    def try_level_up(self) -> bool:
        """Apply level-up while exp threshold is met. Returns True if at least one level gained."""
        leveled = False
        while self.exp >= self.level * 10:
            self.exp -= self.level * 10
            self.level += 1
            self.max_hp += 2
            self.atk += 1
            self.defense += 1
            self.hp = self.max_hp
            leveled = True
        return leveled

