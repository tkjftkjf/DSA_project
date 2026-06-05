from __future__ import annotations

import random
import unittest

from dungeon_crawler.engine.turn_manager import TurnManager


class TurnManagerTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
