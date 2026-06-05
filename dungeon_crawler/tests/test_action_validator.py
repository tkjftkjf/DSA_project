from __future__ import annotations

import unittest

from dungeon_crawler.actions.move_action import MoveAction
from dungeon_crawler.models.dungeon import Dungeon
from dungeon_crawler.models.entity import Entity
from dungeon_crawler.utils.action_validator import ActionValidator, GameContext


class ActionValidatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dungeon = Dungeon(width=8, height=8)
        for x in range(1, 6):
            for y in range(1, 6):
                self.dungeon.floor_tiles.add((x, y))
        self.player = Entity(name="player", x=2, y=2)
        self.enemy = Entity(name="enemy", x=4, y=2)
        self.context = GameContext(
            dungeon=self.dungeon,
            entities=[self.player, self.enemy],
            ground_items={},
            player=self.player,
        )
        self.validator = ActionValidator()

    def test_move_rejected_into_wall(self) -> None:
        action = MoveAction(turn_id=0, entity=self.player, dungeon=self.dungeon, dx=-2, dy=0)
        result = self.validator.validate(action, self.context)
        self.assertFalse(result.ok)
        self.assertEqual(self.player.pos, (2, 2))

    def test_move_rejected_into_occupied_tile(self) -> None:
        action = MoveAction(turn_id=0, entity=self.player, dungeon=self.dungeon, dx=2, dy=0)
        result = self.validator.validate(action, self.context)
        self.assertFalse(result.ok)
        self.assertEqual(self.player.pos, (2, 2))

    def test_move_accepted_into_open_tile(self) -> None:
        action = MoveAction(turn_id=0, entity=self.player, dungeon=self.dungeon, dx=0, dy=1)
        result = self.validator.validate(action, self.context)
        self.assertTrue(result.ok)

    def test_consume_rejected_when_hp_is_full(self) -> None:
        from dungeon_crawler.actions.consume_action import ConsumeAction
        from dungeon_crawler.models.inventory import Inventory
        from dungeon_crawler.models.item import Item

        inventory = Inventory()
        slot = inventory.add_item(Item(name="heart_red", icon="❤️", heal_amount=3))
        self.player.hp = 10
        self.player.max_hp = 10
        self.player.inventory = inventory
        action = ConsumeAction(turn_id=0, consumer=self.player, slot_idx=slot)
        result = self.validator.validate(action, self.context)
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, "hp_full")

    def test_consume_allowed_when_overheal_partially_fills_hp(self) -> None:
        from dungeon_crawler.actions.consume_action import ConsumeAction
        from dungeon_crawler.models.inventory import Inventory
        from dungeon_crawler.models.item import Item

        inventory = Inventory()
        slot = inventory.add_item(Item(name="heart_yellow", icon="💛", heal_amount=10))
        self.player.hp = 8
        self.player.max_hp = 10
        self.player.inventory = inventory
        action = ConsumeAction(turn_id=0, consumer=self.player, slot_idx=slot)
        result = self.validator.validate(action, self.context)
        self.assertTrue(result.ok)

    def test_move_ignores_entities_on_other_floors(self) -> None:
        self.player.floor_id = 1
        self.enemy.floor_id = 2
        action = MoveAction(turn_id=0, entity=self.player, dungeon=self.dungeon, dx=2, dy=0)
        result = self.validator.validate(action, self.context)
        self.assertTrue(result.ok)


if __name__ == "__main__":
    unittest.main()
