from __future__ import annotations

import unittest

from dungeon_crawler.engine.game_manager import GameManager
from dungeon_crawler.models.dungeon import Dungeon
from dungeon_crawler.models.entity import Entity


class RangedProjectileTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dungeon = Dungeon(width=10, height=10)
        for x in range(1, 9):
            self.dungeon.floor_tiles.add((x, 4))
        self.player = Entity(name="player", x=2, y=4, arrows=1)
        self.enemy = Entity(name="enemy", x=6, y=4, hp=10, max_hp=10)
        self.manager = GameManager(
            dungeon=self.dungeon,
            player=self.player,
            entities=[self.player, self.enemy],
            base_seed=1,
        )

    def test_ranged_miss_consumes_arrow_and_consumes_turn(self) -> None:
        self.manager.set_attack_mode("ranged")
        arrows_before = self.player.arrows
        ok = self.manager.try_player_attack(0, -1)
        self.assertTrue(ok)
        self.assertEqual(self.player.arrows, arrows_before - 1)

    def test_ranged_hit_damages_enemy(self) -> None:
        self.manager.set_attack_mode("ranged")
        self.manager.try_player_attack(1, 0)
        self.assertLess(self.enemy.hp, 10)


if __name__ == "__main__":
    unittest.main()
