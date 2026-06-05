from __future__ import annotations

from dataclasses import dataclass, field

from dungeon_crawler.actions.base_action import Action
from dungeon_crawler.models.entity import Entity
from dungeon_crawler.models.item import Item


@dataclass(frozen=True)
class ConsumeAction(Action):
    consumer: Entity
    slot_idx: int
    _item: Item | None = field(default=None, init=False, repr=False, compare=False)
    _healed_amount: int = field(default=0, init=False, repr=False, compare=False)
    _previous_hp: int = field(default=0, init=False, repr=False, compare=False)
    _executed: bool = field(default=False, init=False, repr=False, compare=False)

    def execute(self) -> None:
        if self._executed:
            return
        if self.consumer.inventory is None:
            raise ValueError("Consumer has no inventory")

        item = self.consumer.inventory.remove_from_slot(self.slot_idx)
        object.__setattr__(self, "_item", item)
        object.__setattr__(self, "_previous_hp", self.consumer.hp)

        healed = self.consumer.heal(item.heal_amount)
        object.__setattr__(self, "_healed_amount", healed)
        object.__setattr__(self, "_executed", True)

    def undo(self) -> None:
        if not self._executed or self._item is None:
            return
        if self.consumer.inventory is None:
            return

        if self.consumer.inventory.slots[self.slot_idx] is not None:
            raise ValueError("Original slot is occupied while undoing consume")
        self.consumer.inventory.slots[self.slot_idx] = self._item
        self.consumer.inventory.counts[self._item.name] += 1
        self.consumer.hp = self._previous_hp
        object.__setattr__(self, "_executed", False)

