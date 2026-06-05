from __future__ import annotations

import unittest
from dataclasses import dataclass

from dungeon_crawler.actions.base_action import Action
from dungeon_crawler.engine.undo_manager import UndoManager


@dataclass
class Counter:
    value: int = 0


@dataclass(frozen=True)
class DeltaAction(Action):
    counter: Counter
    delta: int

    def execute(self) -> None:
        self.counter.value += self.delta

    def undo(self) -> None:
        self.counter.value -= self.delta


class UndoManagerTest(unittest.TestCase):
    def test_undo_redo_single_turn(self) -> None:
        counter = Counter()
        manager = UndoManager()

        a1 = DeltaAction(turn_id=1, counter=counter, delta=3)
        a2 = DeltaAction(turn_id=1, counter=counter, delta=2)
        a1.execute()
        manager.record(a1)
        a2.execute()
        manager.record(a2)
        manager.end_turn(turn_id=1)

        self.assertEqual(counter.value, 5)

        undone_turn = manager.undo_turn()
        self.assertEqual(undone_turn, 1)
        self.assertEqual(counter.value, 0)

        redone_turn = manager.redo_turn()
        self.assertEqual(redone_turn, 1)
        self.assertEqual(counter.value, 5)

    def test_new_action_clears_redo_history(self) -> None:
        counter = Counter()
        manager = UndoManager()

        a1 = DeltaAction(turn_id=1, counter=counter, delta=5)
        a1.execute()
        manager.record(a1)
        manager.end_turn(turn_id=1)
        manager.undo_turn()

        # branch new timeline
        a2 = DeltaAction(turn_id=2, counter=counter, delta=7)
        a2.execute()
        manager.record(a2)
        manager.end_turn(turn_id=2)

        self.assertFalse(manager.can_redo())
        self.assertIsNone(manager.redo_turn())
        self.assertEqual(counter.value, 7)


if __name__ == "__main__":
    unittest.main()

