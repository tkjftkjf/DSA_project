from __future__ import annotations

import unittest

from dungeon_crawler.actions.move_action import MoveAction
from dungeon_crawler.models.dungeon import Dungeon
from dungeon_crawler.models.entity import Entity


class MoveActionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dungeon = Dungeon(width=5, height=5)
        self.player = Entity(name="player", x=2, y=2)

    def test_execute_moves_entity_when_walkable(self) -> None:
        action = MoveAction(turn_id=1, entity=self.player, dungeon=self.dungeon, dx=1, dy=0)
        action.execute()
        self.assertEqual(self.player.pos, (3, 2))

    def test_execute_does_not_move_into_blocked_tile(self) -> None:
        self.dungeon.set_blocked(3, 2, True)
        action = MoveAction(turn_id=1, entity=self.player, dungeon=self.dungeon, dx=1, dy=0)
        action.execute()
        self.assertEqual(self.player.pos, (2, 2))

    def test_execute_does_not_move_out_of_bounds(self) -> None:
        edge_entity = Entity(name="edge", x=0, y=0)
        action = MoveAction(turn_id=1, entity=edge_entity, dungeon=self.dungeon, dx=-1, dy=0)
        action.execute()
        self.assertEqual(edge_entity.pos, (0, 0))

    def test_undo_restores_previous_position(self) -> None:
        action = MoveAction(turn_id=1, entity=self.player, dungeon=self.dungeon, dx=0, dy=1)
        action.execute()
        self.assertEqual(self.player.pos, (2, 3))
        action.undo()
        self.assertEqual(self.player.pos, (2, 2))


if __name__ == "__main__":
    unittest.main()

