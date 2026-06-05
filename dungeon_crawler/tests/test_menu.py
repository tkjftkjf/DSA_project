from __future__ import annotations

import unittest

from dungeon_crawler.ui.menu import format_leaderboard_text
from dungeon_crawler.utils.leaderboard import Leaderboard, ScoreEntry


class MenuTest(unittest.TestCase):
    def test_format_leaderboard_text(self) -> None:
        board = Leaderboard(capacity=5)
        board.add(ScoreEntry(name="hero", score=300, level=4))
        text = format_leaderboard_text(board, width=80)
        self.assertIn("LEADERBOARD", text)
        self.assertIn("hero", text)
        self.assertIn("score=300", text)


if __name__ == "__main__":
    unittest.main()
