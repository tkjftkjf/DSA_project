from __future__ import annotations

import unittest
from unittest.mock import patch

from dungeon_crawler.engine.session import compute_score, create_game_manager, derive_session_seed
from dungeon_crawler.models.room_template import WORLD_HEIGHT, WORLD_WIDTH


class SessionTest(unittest.TestCase):
    def test_derive_session_seed_uses_start_time(self) -> None:
        with patch("dungeon_crawler.engine.session.time.time_ns", return_value=1_700_000_000_000_000_000):
            self.assertEqual(derive_session_seed(), 1_700_000_000_000_000_000 % (2**31))

    def test_create_game_manager_uses_start_time_for_turn_rng(self) -> None:
        with patch("dungeon_crawler.engine.session.time.time_ns", return_value=4_242_000_000_000):
            manager = create_game_manager()
        expected_seed = 4_242_000_000_000 % (2**31)
        self.assertEqual(manager.base_seed, expected_seed)
        self.assertEqual(manager.turn_manager.base_seed, expected_seed)
        self.assertEqual(manager.turn_manager.current_seed(), expected_seed)

    def test_compute_score_formula(self) -> None:
        manager = create_game_manager()
        manager.kills = 2
        manager.player.exp = 12
        manager.player.level = 2
        manager.turn_manager.turn_id = 5
        score = compute_score(manager.player, manager.turn_manager.turn_id, manager.kills)
        self.assertEqual(score, 12 + 200 + 10 + 100)

    def test_create_game_manager_has_player_and_enemies(self) -> None:
        manager = create_game_manager()
        self.assertGreaterEqual(len(manager.entities), 2)
        self.assertTrue(any(e is manager.player for e in manager.entities))
        self.assertEqual(manager.active_dungeon.width, WORLD_WIDTH)
        self.assertEqual(manager.active_dungeon.height, WORLD_HEIGHT)
        self.assertIsNotNone(manager.floor_manager)


if __name__ == "__main__":
    unittest.main()
