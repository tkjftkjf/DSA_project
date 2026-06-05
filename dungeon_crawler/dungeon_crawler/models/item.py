from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    name: str
    icon: str
    heal_amount: int = 0

