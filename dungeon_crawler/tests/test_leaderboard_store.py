from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dungeon_crawler.utils.leaderboard import Leaderboard, ScoreEntry
from dungeon_crawler.utils.leaderboard_store import load_leaderboard, save_leaderboard


class LeaderboardStoreTest(unittest.TestCase):
    def test_save_and_load_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "board.json"
            board = Leaderboard(capacity=5)
            board.add(ScoreEntry(name="alice", score=120, level=2))
            board.add(ScoreEntry(name="bob", score=200, level=3))
            save_leaderboard(board, path=path)

            loaded = load_leaderboard(path=path)
            names = [e.name for e in loaded.list()]
            self.assertEqual(names, ["bob", "alice"])


if __name__ == "__main__":
    unittest.main()
