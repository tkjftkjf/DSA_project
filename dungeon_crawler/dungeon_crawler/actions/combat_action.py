from __future__ import annotations

from dataclasses import dataclass, field

from dungeon_crawler.actions.base_action import Action
from dungeon_crawler.models.entity import Entity


@dataclass(frozen=True)
class CombatAction(Action):
    attacker: Entity
    defender: Entity
    entity_pool: list[Entity] | None = None
    _damage: int = field(default=0, init=False, repr=False, compare=False)
    _defender_prev_hp: int = field(default=0, init=False, repr=False, compare=False)
    _defender_prev_alive: bool = field(default=True, init=False, repr=False, compare=False)
    _attacker_prev_exp: int = field(default=0, init=False, repr=False, compare=False)
    _removed_index: int | None = field(default=None, init=False, repr=False, compare=False)
    _executed: bool = field(default=False, init=False, repr=False, compare=False)

    def execute(self) -> None:
        if self._executed or not self.defender.is_alive:
            return

        object.__setattr__(self, "_defender_prev_hp", self.defender.hp)
        object.__setattr__(self, "_defender_prev_alive", self.defender.is_alive)
        object.__setattr__(self, "_attacker_prev_exp", self.attacker.exp)

        damage = max(1, self.attacker.atk - self.defender.defense)
        object.__setattr__(self, "_damage", damage)

        self.defender.hp = max(0, self.defender.hp - damage)
        if self.defender.hp == 0:
            self.defender.is_alive = False
            self.attacker.exp += self.defender.exp_reward
            if self.entity_pool is not None and self.defender in self.entity_pool:
                idx = self.entity_pool.index(self.defender)
                self.entity_pool.pop(idx)
                object.__setattr__(self, "_removed_index", idx)

        object.__setattr__(self, "_executed", True)

    def undo(self) -> None:
        if not self._executed:
            return

        if (
            self.entity_pool is not None
            and self._removed_index is not None
            and self.defender not in self.entity_pool
        ):
            self.entity_pool.insert(self._removed_index, self.defender)

        self.attacker.exp = self._attacker_prev_exp
        self.defender.hp = self._defender_prev_hp
        self.defender.is_alive = self._defender_prev_alive
        object.__setattr__(self, "_executed", False)

