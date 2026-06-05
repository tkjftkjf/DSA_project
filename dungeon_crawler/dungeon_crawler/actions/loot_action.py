from __future__ import annotations

from dataclasses import dataclass, field

from dungeon_crawler.actions.base_action import Action
from dungeon_crawler.models.entity import Entity
from dungeon_crawler.models.item import Item


@dataclass(frozen=True)
class LootAction(Action):
    looter: Entity
    item: Item
    position: tuple[int, int]
    ground_items: dict[tuple[int, int], list[Item]]
    _inventory_slot: int | None = field(default=None, init=False, repr=False, compare=False)
    _executed: bool = field(default=False, init=False, repr=False, compare=False)

    def execute(self) -> None:
        if self._executed:
            return
        if self.looter.inventory is None:
            raise ValueError("Looter has no inventory")

        items = self.ground_items.get(self.position, [])
        if self.item not in items:
            raise ValueError("Item not found on ground at position")
        items.remove(self.item)
        if not items and self.position in self.ground_items:
            del self.ground_items[self.position]

        slot = self.looter.inventory.add_item(self.item)
        object.__setattr__(self, "_inventory_slot", slot)
        object.__setattr__(self, "_executed", True)

    def undo(self) -> None:
        if not self._executed:
            return
        if self.looter.inventory is None or self._inventory_slot is None:
            return

        removed = self.looter.inventory.remove_from_slot(self._inventory_slot)
        if removed != self.item:
            raise ValueError("Unexpected inventory state while undoing loot")
        self.ground_items.setdefault(self.position, []).append(self.item)
        object.__setattr__(self, "_executed", False)

