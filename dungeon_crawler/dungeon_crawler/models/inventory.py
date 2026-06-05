from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from dungeon_crawler.models.item import Item


@dataclass
class Inventory:
    size: int = 10
    slots: list[Item | None] = field(default_factory=list)
    counts: defaultdict[str, int] = field(default_factory=lambda: defaultdict(int))

    def __post_init__(self) -> None:
        if not self.slots:
            self.slots = [None for _ in range(self.size)]

    def add_item(self, item: Item) -> int:
        for idx, slot in enumerate(self.slots):
            if slot is None:
                self.slots[idx] = item
                self.counts[item.name] += 1
                return idx
        raise ValueError("Inventory is full")

    def remove_from_slot(self, slot_idx: int) -> Item:
        if slot_idx < 0 or slot_idx >= len(self.slots):
            raise IndexError("Slot index out of range")
        item = self.slots[slot_idx]
        if item is None:
            raise ValueError("Slot is empty")
        self.slots[slot_idx] = None
        self.counts[item.name] -= 1
        if self.counts[item.name] <= 0:
            del self.counts[item.name]
        return item

