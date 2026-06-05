from __future__ import annotations

import unittest

from dungeon_crawler.engine.game_manager import GameManager
from dungeon_crawler.models.dungeon import Dungeon
from dungeon_crawler.models.entity import Entity
from dungeon_crawler.models.inventory import Inventory
from dungeon_crawler.models.item import Item


class GameplayFlowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dungeon = Dungeon(width=8, height=8)
        for y in range(8):
            for x in range(8):
                self.dungeon.set_blocked(x, y, False)
        self.player = Entity(name="player", x=1, y=1, atk=5, defense=1, hp=20, max_hp=20, inventory=Inventory())
        self.enemy = Entity(name="enemy", x=2, y=1, hp=6, max_hp=6, atk=2, defense=0, exp_reward=5)
        self.manager = GameManager(
            dungeon=self.dungeon,
            player=self.player,
            entities=[self.player, self.enemy],
            base_seed=99,
        )

    def test_move_into_enemy_triggers_combat(self) -> None:
        acted = self.manager.try_player_move(dx=1, dy=0)
        self.assertTrue(acted)
        self.assertEqual(self.player.pos, (1, 1))
        self.assertLess(self.enemy.hp, 6)

    def test_melee_mode_requires_direction_then_attacks(self) -> None:
        self.manager.set_attack_mode("melee")
        acted = self.manager.try_player_attack(dx=1, dy=0)
        self.assertTrue(acted)
        self.assertIsNone(self.manager.pending_attack_mode)

    def test_ranged_mode_consumes_arrow(self) -> None:
        assert self.player.inventory is not None
        self.player.inventory.add_item(Item(name="arrow", icon="🏹"))
        self.enemy.set_pos(4, 1)
        self.manager.set_attack_mode("ranged")
        acted = self.manager.try_player_attack(dx=1, dy=0)
        self.assertTrue(acted)
        self.assertEqual(self.player.inventory.counts.get("arrow", 0), 0)

    def test_auto_loot_on_move(self) -> None:
        potion = Item(name="heart_red", icon="❤️", heal_amount=3)
        self.manager.ground_items_by_floor[1] = {(1, 2): [potion]}
        moved = self.manager.try_player_move(dx=0, dy=1)
        self.assertTrue(moved)
        assert self.player.inventory is not None
        self.assertEqual(self.player.inventory.counts.get("heart_red", 0), 1)

    def test_failed_attack_keeps_pending_mode(self) -> None:
        self.manager.set_attack_mode("melee")
        acted = self.manager.try_player_attack(dx=0, dy=-1)
        self.assertFalse(acted)
        self.assertEqual(self.manager.pending_attack_mode, "melee")

    def test_kill_increments_kills_and_levels_up(self) -> None:
        self.enemy.hp = 1
        self.enemy.exp_reward = 20
        self.player.exp = 0
        self.manager.try_player_move(dx=1, dy=0)
        self.assertEqual(self.manager.kills, 1)
        self.assertGreaterEqual(self.player.level, 2)


if __name__ == "__main__":
    unittest.main()

