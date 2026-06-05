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


if __name__ == "__main__":
    unittest.main()
