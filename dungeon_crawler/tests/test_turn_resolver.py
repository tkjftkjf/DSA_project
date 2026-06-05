from __future__ import annotations

import unittest

from dungeon_crawler.actions.move_action import MoveAction
from dungeon_crawler.engine.turn_resolver import EntityTurnPlan, TurnResolver
from dungeon_crawler.models.dungeon import Dungeon
from dungeon_crawler.models.entity import Entity
from dungeon_crawler.utils.action_validator import GameContext


class TurnResolverTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dungeon = Dungeon(width=8, height=8)
        for x in range(1, 6):
            for y in range(1, 6):
                self.dungeon.floor_tiles.add((x, y))
        self.player = Entity(name="player", x=2, y=2)
        self.enemy = Entity(name="enemy", x=4, y=4)
        self.context = GameContext(
            dungeon=self.dungeon,
            entities=[self.player, self.enemy],
            ground_items={},
            player=self.player,
        )
        self.resolver = TurnResolver()

    def test_collect_actions_validates_before_queueing(self) -> None:
        attempts = {"count": 0}

        def propose_player() -> MoveAction | None:
            attempts["count"] += 1
            if attempts["count"] == 1:
                return MoveAction(turn_id=0, entity=self.player, dungeon=self.dungeon, dx=-2, dy=0)
            return MoveAction(turn_id=0, entity=self.player, dungeon=self.dungeon, dx=0, dy=1)

        plans = [
            EntityTurnPlan(entity=self.player, propose=propose_player, fallback=lambda: None),
        ]
        actions = self.resolver.collect_actions(plans, self.context)
        self.assertEqual(len(actions), 1)
        self.assertEqual(attempts["count"], 2)

    def test_collect_actions_returns_validated_moves(self) -> None:
        plans = [
            EntityTurnPlan(
                entity=self.player,
                propose=lambda: MoveAction(
                    turn_id=0, entity=self.player, dungeon=self.dungeon, dx=0, dy=1
                ),
                fallback=lambda: None,
            ),
            EntityTurnPlan(
                entity=self.enemy,
                propose=lambda: MoveAction(
                    turn_id=0, entity=self.enemy, dungeon=self.dungeon, dx=0, dy=-1
                ),
                fallback=lambda: None,
            ),
        ]
        actions = self.resolver.collect_actions(plans, self.context)
        self.assertEqual(len(actions), 2)
        for action in actions:
            action.execute()
        self.assertEqual(self.player.pos, (2, 3))
        self.assertEqual(self.enemy.pos, (4, 3))


if __name__ == "__main__":
    unittest.main()
