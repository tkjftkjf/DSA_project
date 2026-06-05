from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class TurnManager:
    """
    Turn counter with deterministic RNG seeding per turn.

    Seeding contract:
    - Call `prepare_turn_rng()` right before resolving actions for current turn.
    - Seed = base_seed + turn_id.
    """

    base_seed: int
    turn_id: int = 0

    def current_seed(self) -> int:
        return self.base_seed + self.turn_id

    def prepare_turn_rng(self) -> int:
        seed = self.current_seed()
        random.seed(seed)
        return seed

    def end_turn(self) -> None:
        self.turn_id += 1

    def set_turn_id(self, turn_id: int) -> None:
        if turn_id < 0:
            raise ValueError("turn_id must be >= 0")
        self.turn_id = turn_id
