from __future__ import annotations

import unittest

from dungeon_crawler.models.dungeon import Dungeon
from dungeon_crawler.utils.pathfinding import find_path


class PathfindingTest(unittest.TestCase):
    def test_finds_shortest_path_in_open_grid(self) -> None:
        dungeon = Dungeon(width=5, height=5)
        path = find_path(dungeon, start=(0, 0), goal=(2, 0))
        self.assertEqual(path, [(0, 0), (1, 0), (2, 0)])

    def test_avoids_blocked_tiles(self) -> None:
        dungeon = Dungeon(width=5, height=5)
        dungeon.set_blocked(1, 0, True)
        path = find_path(dungeon, start=(0, 0), goal=(2, 0))
        self.assertTrue(path)
        self.assertNotIn((1, 0), path)

    def test_treats_dynamic_blocked_positions_as_walls(self) -> None:
        dungeon = Dungeon(width=5, height=5)
        # represents other monsters/items temporarily treated as obstacles
        dynamic_blocked = {(1, 0)}
        path = find_path(dungeon, start=(0, 0), goal=(2, 0), blocked=dynamic_blocked)
        self.assertTrue(path)
        self.assertNotIn((1, 0), path)

    def test_returns_empty_when_no_path_exists(self) -> None:
        dungeon = Dungeon(width=3, height=3)
        dungeon.set_blocked(1, 0, True)
        dungeon.set_blocked(1, 1, True)
        dungeon.set_blocked(1, 2, True)
        path = find_path(dungeon, start=(0, 1), goal=(2, 1))
        self.assertEqual(path, [])


if __name__ == "__main__":
    unittest.main()

