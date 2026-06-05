from __future__ import annotations

import unittest

from dungeon_crawler.actions.loot_action import LootAction
from dungeon_crawler.models.entity import Entity
from dungeon_crawler.models.inventory import Inventory
from dungeon_crawler.models.item import Item


class LootActionTest(unittest.TestCase):
    def test_loot_execute_and_undo(self) -> None:
        potion = Item(name="heart_red", icon="❤️", heal_amount=3)
        player = Entity(name="player", x=2, y=2, inventory=Inventory())
        ground_items: dict[tuple[int, int], list[Item]] = {(2, 2): [potion]}

        action = LootAction(
            turn_id=1,
            looter=player,
            item=potion,
            position=(2, 2),
            ground_items=ground_items,
        )

        action.execute()
        self.assertNotIn((2, 2), ground_items)
        self.assertEqual(player.inventory.counts["heart_red"], 1)  # type: ignore[index]

        action.undo()
        self.assertIn((2, 2), ground_items)
        self.assertEqual(len(ground_items[(2, 2)]), 1)
        self.assertEqual(ground_items[(2, 2)][0], potion)
        self.assertEqual(player.inventory.counts.get("heart_red", 0), 0)  # type: ignore[union-attr]


if __name__ == "__main__":
    unittest.main()

