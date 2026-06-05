from __future__ import annotations

import unittest

from dungeon_crawler.actions.consume_action import ConsumeAction
from dungeon_crawler.models.entity import Entity
from dungeon_crawler.models.inventory import Inventory
from dungeon_crawler.models.item import Item


class ConsumeActionTest(unittest.TestCase):
    def test_consume_execute_and_undo(self) -> None:
        inventory = Inventory()
        potion = Item(name="heart_blue", icon="💙", heal_amount=5)
        slot = inventory.add_item(potion)
        player = Entity(name="player", x=0, y=0, hp=4, max_hp=10, inventory=inventory)

        action = ConsumeAction(turn_id=3, consumer=player, slot_idx=slot)
        action.execute()

        self.assertEqual(player.hp, 9)
        self.assertIsNone(player.inventory.slots[slot])  # type: ignore[union-attr]
        self.assertEqual(player.inventory.counts.get("heart_blue", 0), 0)  # type: ignore[union-attr]

        action.undo()
        self.assertEqual(player.hp, 4)
        self.assertEqual(player.inventory.slots[slot], potion)  # type: ignore[union-attr]
        self.assertEqual(player.inventory.counts["heart_blue"], 1)  # type: ignore[index]

    def test_consume_respects_max_hp(self) -> None:
        inventory = Inventory()
        potion = Item(name="heart_purple", icon="💜", heal_amount=30)
        slot = inventory.add_item(potion)
        player = Entity(name="player", x=0, y=0, hp=9, max_hp=10, inventory=inventory)

        action = ConsumeAction(turn_id=4, consumer=player, slot_idx=slot)
        action.execute()
        self.assertEqual(player.hp, 10)


if __name__ == "__main__":
    unittest.main()

