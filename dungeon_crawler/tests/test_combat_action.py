from __future__ import annotations

import unittest

from dungeon_crawler.actions.combat_action import CombatAction
from dungeon_crawler.models.entity import Entity


class CombatActionTest(unittest.TestCase):
    def test_damage_uses_minimum_one_rule(self) -> None:
        attacker = Entity(name="player", x=0, y=0, atk=2, defense=0)
        defender = Entity(name="tank", x=1, y=0, hp=10, max_hp=10, atk=1, defense=999, is_alive=True)
        action = CombatAction(turn_id=1, attacker=attacker, defender=defender)

        action.execute()
        self.assertEqual(defender.hp, 9)

        action.undo()
        self.assertEqual(defender.hp, 10)
        self.assertTrue(defender.is_alive)

    def test_kill_grants_exp_and_removes_from_pool_then_undo_restores(self) -> None:
        attacker = Entity(name="player", x=0, y=0, atk=10, defense=0, exp=0)
        defender = Entity(
            name="enemy",
            x=1,
            y=0,
            hp=6,
            max_hp=6,
            atk=1,
            defense=0,
            exp_reward=15,
            is_alive=True,
        )
        entities = [attacker, defender]
        action = CombatAction(turn_id=2, attacker=attacker, defender=defender, entity_pool=entities)

        action.execute()
        self.assertEqual(defender.hp, 0)
        self.assertFalse(defender.is_alive)
        self.assertEqual(attacker.exp, 15)
        self.assertNotIn(defender, entities)

        action.undo()
        self.assertEqual(defender.hp, 6)
        self.assertTrue(defender.is_alive)
        self.assertEqual(attacker.exp, 0)
        self.assertEqual(entities, [attacker, defender])


if __name__ == "__main__":
    unittest.main()

