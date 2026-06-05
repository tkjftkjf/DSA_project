from __future__ import annotations

import unittest

from dungeon_crawler.actions.move_action import MoveAction
from dungeon_crawler.engine.game_manager import GameManager
from dungeon_crawler.models.dungeon import Dungeon
from dungeon_crawler.models.entity import Entity


class GameManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dungeon = Dungeon(width=8, height=8)
        self.player = Entity(name="player", x=1, y=1)
        self.enemy = Entity(name="enemy", x=3, y=3)
        self.manager = GameManager(
            dungeon=self.dungeon,
            player=self.player,
            entities=[self.player, self.enemy],
            base_seed=1234,
        )

    def test_execute_action_records_log_and_stack(self) -> None:
        action = MoveAction(turn_id=0, entity=self.player, dungeon=self.dungeon, dx=1, dy=0)
        self.manager.execute_action(action, log_message="player moved")
        self.assertEqual(self.player.pos, (2, 1))
        self.assertEqual(self.manager.logs[-1], "player moved")
        self.assertEqual(len(self.manager.undo_manager.undo_stack), 1)

    def test_finalize_turn_and_undo_append_system_log(self) -> None:
        action = MoveAction(turn_id=0, entity=self.player, dungeon=self.dungeon, dx=1, dy=0)
        self.manager.execute_action(action, log_message="player moved")
        self.manager.finalize_turn()

        undone = self.manager.undo_turn()
        self.assertEqual(undone, 0)
        self.assertEqual(self.player.pos, (1, 1))
        self.assertIn("[System] 턴 0의 행동을 되돌렸습니다.", self.manager.logs)

    def test_redo_reapplies_action_and_appends_log(self) -> None:
        action = MoveAction(turn_id=0, entity=self.player, dungeon=self.dungeon, dx=0, dy=1)
        self.manager.execute_action(action, log_message="player moved")
        self.manager.finalize_turn()
        self.manager.undo_turn()

        redone = self.manager.redo_turn()
        self.assertEqual(redone, 0)
        self.assertEqual(self.player.pos, (1, 2))
        self.assertIn("[System] 턴 0의 행동을 다시 적용했습니다.", self.manager.logs)


if __name__ == "__main__":
    unittest.main()

