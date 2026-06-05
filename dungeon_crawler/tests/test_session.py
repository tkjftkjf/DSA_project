from __future__ import annotations

import unittest

from dungeon_crawler.engine.session import compute_score, create_game_manager


class SessionTest(unittest.TestCase):
    def test_compute_score_formula(self) -> None:
        manager = create_game_manager(seed=3)
        manager.kills = 2
        manager.player.exp = 12
        manager.player.level = 2
        manager.turn_manager.turn_id = 5
        score = compute_score(manager.player, manager.turn_manager.turn_id, manager.kills)
        self.assertEqual(score, 12 + 200 + 10 + 100)

    def test_create_game_manager_has_player_and_enemies(self) -> None:
        manager = create_game_manager(seed=11)
        self.assertGreaterEqual(len(manager.entities), 2)
        self.assertTrue(any(e is manager.player for e in manager.entities))
        self.assertEqual(manager.active_dungeon.width, 50)
        self.assertEqual(manager.active_dungeon.height, 30)
        self.assertIsNotNone(manager.floor_manager)


if __name__ == "__main__":
    unittest.main()
