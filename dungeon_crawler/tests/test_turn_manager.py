from __future__ import annotations

import random
import unittest

from dungeon_crawler.engine.turn_manager import TurnManager
from dungeon_crawler.models.entity import Entity


class TurnManagerTest(unittest.TestCase):
    def test_fifo_rotation_skips_dead_entities(self) -> None:
        manager = TurnManager(base_seed=100)
        p = Entity(name="player", x=0, y=0, is_alive=True)
        e1 = Entity(name="enemy1", x=1, y=0, is_alive=False)
        e2 = Entity(name="enemy2", x=2, y=0, is_alive=True)
        manager.register(p)
        manager.register(e1)
        manager.register(e2)

        self.assertEqual(manager.next_entity(), p)
        self.assertEqual(manager.next_entity(), e2)
        self.assertEqual(manager.next_entity(), p)

    def test_rng_seed_is_deterministic_per_turn_id(self) -> None:
        manager = TurnManager(base_seed=42, turn_id=7)
        seed = manager.prepare_turn_rng()
        value1 = random.randint(1, 1000)

        manager.set_turn_id(7)
        manager.prepare_turn_rng()
        value2 = random.randint(1, 1000)

        self.assertEqual(seed, 49)
        self.assertEqual(value1, value2)

    def test_end_turn_increments_turn_id(self) -> None:
        manager = TurnManager(base_seed=1, turn_id=3)
        manager.end_turn()
        self.assertEqual(manager.turn_id, 4)
        self.assertEqual(manager.current_seed(), 5)

    def test_delayed_actions_trigger_on_countdown(self) -> None:
        manager = TurnManager(base_seed=1)
        manager.schedule_delayed(turns_left=2, callback="spawn")
        manager.schedule_delayed(turns_left=1, callback="heal")

        first = manager.tick_delayed()
        second = manager.tick_delayed()

        self.assertEqual(first, ["heal"])
        self.assertEqual(second, ["spawn"])


if __name__ == "__main__":
    unittest.main()

