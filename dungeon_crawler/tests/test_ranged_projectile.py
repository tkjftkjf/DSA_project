from __future__ import annotations

import unittest

from dungeon_crawler.engine.game_manager import GameManager
from dungeon_crawler.models.dungeon import Dungeon
from dungeon_crawler.models.entity import Entity
from dungeon_crawler.models.inventory import Inventory
from dungeon_crawler.models.item import Item


class RangedProjectileTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dungeon = Dungeon(width=10, height=10)
        for x in range(1, 9):
            self.dungeon.floor_tiles.add((x, 4))
        self.player = Entity(name="player", x=2, y=4, inventory=Inventory())
        assert self.player.inventory is not None
        self.player.inventory.add_item(Item(name="arrow", icon="🏹"))
        self.enemy = Entity(name="enemy", x=6, y=4, hp=10, max_hp=10)
        self.manager = GameManager(
            dungeon=self.dungeon,
            player=self.player,
            entities=[self.player, self.enemy],
            base_seed=1,
        )

    def test_ranged_miss_consumes_arrow_and_consumes_turn(self) -> None:
        self.manager.set_attack_mode("ranged")
        arrows_before = self.player.inventory.counts.get("arrow", 0)  # type: ignore[union-attr]
        ok = self.manager.try_player_attack(0, -1)
        self.assertTrue(ok)
        arrows_after = self.player.inventory.counts.get("arrow", 0)  # type: ignore[union-attr]
        self.assertEqual(arrows_after, arrows_before - 1)

    def test_ranged_hit_damages_enemy(self) -> None:
        self.manager.set_attack_mode("ranged")
        self.manager.try_player_attack(1, 0)
        self.assertLess(self.enemy.hp, 10)


if __name__ == "__main__":
    unittest.main()
