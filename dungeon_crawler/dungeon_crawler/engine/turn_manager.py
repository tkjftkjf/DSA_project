from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field

from dungeon_crawler.models.entity import Entity


@dataclass
class DelayedAction:
    """Simple delayed callback entry managed by turn countdown."""

    turns_left: int
    callback: str


@dataclass
class TurnManager:
    """
    FIFO turn scheduler with deterministic RNG seeding per turn.

    Seeding contract:
    - Call `prepare_turn_rng()` right before resolving actions for current turn.
    - Seed = base_seed + turn_id.
    """

    base_seed: int
    turn_id: int = 0
    _queue: deque[Entity] = field(default_factory=deque)
    _delayed_actions: list[DelayedAction] = field(default_factory=list)

    def register(self, entity: Entity) -> None:
        if entity not in self._queue:
            self._queue.append(entity)

    def unregister(self, entity: Entity) -> None:
        self._queue = deque(e for e in self._queue if e is not entity)

    def has_entities(self) -> bool:
        return bool(self._queue)

    def current_seed(self) -> int:
        return self.base_seed + self.turn_id

    def prepare_turn_rng(self) -> int:
        seed = self.current_seed()
        random.seed(seed)
        return seed

    def next_entity(self) -> Entity | None:
        """Pop next living entity and rotate it back to queue tail."""
        if not self._queue:
            return None

        checked = 0
        while checked < len(self._queue):
            entity = self._queue.popleft()
            checked += 1
            if entity.is_alive:
                self._queue.append(entity)
                return entity
        return None

    def end_turn(self) -> None:
        self.turn_id += 1

    def set_turn_id(self, turn_id: int) -> None:
        if turn_id < 0:
            raise ValueError("turn_id must be >= 0")
        self.turn_id = turn_id

    def schedule_delayed(self, turns_left: int, callback: str) -> None:
        if turns_left < 1:
            raise ValueError("turns_left must be >= 1")
        self._delayed_actions.append(DelayedAction(turns_left=turns_left, callback=callback))

    def tick_delayed(self) -> list[str]:
        """
        Decrease delayed counters and return callbacks that reached zero.
        """
        triggered: list[str] = []
        survivors: list[DelayedAction] = []
        for action in self._delayed_actions:
            action.turns_left -= 1
            if action.turns_left <= 0:
                triggered.append(action.callback)
            else:
                survivors.append(action)
        self._delayed_actions = survivors
        return triggered

