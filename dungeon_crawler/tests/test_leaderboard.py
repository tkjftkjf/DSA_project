from __future__ import annotations

import unittest

from dungeon_crawler.utils.leaderboard import Leaderboard, ScoreEntry


class LeaderboardTest(unittest.TestCase):
    def test_insertion_sort_descending(self) -> None:
        board = Leaderboard(capacity=5)
        board.add(ScoreEntry(name="a", score=10, level=1))
        board.add(ScoreEntry(name="b", score=25, level=2))
        board.add(ScoreEntry(name="c", score=15, level=3))

        names = [entry.name for entry in board.list()]
        self.assertEqual(names, ["b", "c", "a"])

    def test_tie_breaker_uses_level(self) -> None:
        board = Leaderboard(capacity=5)
        board.add(ScoreEntry(name="a", score=20, level=1))
        board.add(ScoreEntry(name="b", score=20, level=5))

        names = [entry.name for entry in board.list()]
        self.assertEqual(names, ["b", "a"])

    def test_capacity_is_enforced(self) -> None:
        board = Leaderboard(capacity=2)
        board.add(ScoreEntry(name="a", score=5, level=1))
        board.add(ScoreEntry(name="b", score=10, level=1))
        board.add(ScoreEntry(name="c", score=7, level=1))

        names = [entry.name for entry in board.list()]
        self.assertEqual(names, ["b", "c"])


if __name__ == "__main__":
    unittest.main()

