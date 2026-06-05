from __future__ import annotations

import unittest

from dungeon_crawler.engine.floor_manager import FloorManager
from dungeon_crawler.models.room_template import WORLD_HEIGHT, WORLD_WIDTH


class FloorManagerTest(unittest.TestCase):
    def test_creates_three_floors(self) -> None:
        manager = FloorManager.create(base_seed=7, room_count=6)
        self.assertEqual(len(manager.floors), 3)
        for dungeon in manager.floors:
            self.assertEqual(dungeon.width, WORLD_WIDTH)
            self.assertEqual(dungeon.height, WORLD_HEIGHT)

    def test_descend_moves_to_next_floor(self) -> None:
        manager = FloorManager.create(base_seed=11, room_count=6)
        self.assertEqual(manager.current_floor, 1)
        target = manager.descend()
        self.assertEqual(manager.current_floor, 2)
        self.assertIsNotNone(target)
        assert target is not None
        self.assertIn(target, manager.current_dungeon.floor_tiles)

    def test_cannot_descend_from_floor3(self) -> None:
        manager = FloorManager.create(base_seed=3, room_count=5)
        manager.descend()
        manager.descend()
        self.assertEqual(manager.current_floor, 3)
        self.assertFalse(manager.can_descend())
        self.assertIsNone(manager.descend())

    def test_stair_links_land_on_next_floor_start(self) -> None:
        manager = FloorManager.create(base_seed=7, room_count=8)
        self.assertIn((0, 1), manager.stair_links)
        self.assertIn((1, 2), manager.stair_links)
        self.assertEqual(manager.stair_links[(0, 1)], manager.floors[1].start_spawn)
        self.assertEqual(manager.stair_links[(1, 2)], manager.floors[2].start_spawn)
        for floor in manager.floors:
            self.assertTrue(floor.stair_tiles)
            self.assertIsNotNone(floor.start_spawn)


if __name__ == "__main__":
    unittest.main()
