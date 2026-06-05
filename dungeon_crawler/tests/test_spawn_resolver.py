from __future__ import annotations

import unittest

from dungeon_crawler.engine.spawn_resolver import FLOOR_STAT_RANGES, HEART_ITEMS, SpawnResolver


class SpawnResolverTest(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = SpawnResolver(base_seed=2026)

    def test_enemy_stats_within_floor_ranges(self) -> None:
        for floor_id in (1, 2, 3):
            ranges = FLOOR_STAT_RANGES[floor_id]
            for idx in range(5):
                stats = self.resolver.roll_enemy_stats(floor_id, idx)
                self.assertBetween(stats["hp"], *ranges["hp"])
                self.assertBetween(stats["atk"], *ranges["atk"])
                self.assertBetween(stats["defense"], *ranges["defense"])
                self.assertBetween(stats["exp_reward"], *ranges["exp"])

    def test_enemy_stats_are_deterministic(self) -> None:
        a = self.resolver.roll_enemy_stats(2, 3)
        b = SpawnResolver(base_seed=2026).roll_enemy_stats(2, 3)
        self.assertEqual(a, b)

    def test_heart_spawn_uses_six_kinds(self) -> None:
        names = {self.resolver.roll_heart_item(1, i).name for i in range(30)}
        self.assertTrue(names.issubset({item.name for item in HEART_ITEMS}))
        self.assertGreater(len(names), 1)

    def test_heart_spawn_is_deterministic(self) -> None:
        item_a = self.resolver.roll_heart_item(2, 4)
        item_b = SpawnResolver(base_seed=2026).roll_heart_item(2, 4)
        self.assertEqual(item_a.name, item_b.name)
        self.assertEqual(item_a.heal_amount, item_b.heal_amount)

    def test_spawn_enemies_and_items(self) -> None:
        enemies = self.resolver.spawn_enemies([(1, 1), (3, 3)], floor_id=1)
        self.assertEqual(len(enemies), 2)
        items = self.resolver.spawn_ground_items([(2, 2)], floor_id=1)
        self.assertIn((2, 2), items)
        self.assertEqual(len(items[(2, 2)]), 1)

    def assertBetween(self, value: int, low: int, high: int) -> None:
        self.assertGreaterEqual(value, low)
        self.assertLessEqual(value, high)


if __name__ == "__main__":
    unittest.main()
