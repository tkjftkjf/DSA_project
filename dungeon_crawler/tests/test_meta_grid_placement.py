from __future__ import annotations

import unittest

from dungeon_crawler.models.dungeon import Dungeon
from dungeon_crawler.models.room_template import WORLD_HEIGHT, WORLD_WIDTH


class MetaGridPlacementTest(unittest.TestCase):
    def test_floor1_world_size(self) -> None:
        dungeon = Dungeon()
        dungeon.generate_floor(floor_id=1, room_count=8, seed=7)
        self.assertEqual(dungeon.width, WORLD_WIDTH)
        self.assertEqual(dungeon.height, WORLD_HEIGHT)

    def test_spanning_tree_connects_meta_rooms(self) -> None:
        dungeon = Dungeon()
        dungeon.generate_floor(floor_id=1, room_count=6, seed=13, extra_cycles=0)
        graph: dict[int, set[int]] = {rid: set() for rid in dungeon.room_nodes}
        for a, b in dungeon.edges:
            graph[a].add(b)
            graph[b].add(a)

        start = next(iter(graph))
        visited: set[int] = set()
        stack = [start]
        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            stack.extend(graph[cur] - visited)

        self.assertEqual(visited, set(dungeon.room_nodes.keys()))

    def test_start_spawn_exists_on_floor1(self) -> None:
        dungeon = Dungeon()
        dungeon.generate_floor(floor_id=1, room_count=5, seed=3)
        self.assertIsNotNone(dungeon.start_spawn)
        assert dungeon.start_spawn is not None
        self.assertIn(dungeon.start_spawn, dungeon.floor_tiles)

    def test_spawn_markers_collected_from_templates(self) -> None:
        dungeon = Dungeon()
        dungeon.generate_floor(floor_id=2, room_count=10, seed=21)
        for pos in dungeon.enemy_spawn_tiles:
            self.assertIn(pos, dungeon.floor_tiles)
        for pos in dungeon.item_spawn_tiles:
            self.assertIn(pos, dungeon.floor_tiles)

    def test_connections_only_add_floor_tiles(self) -> None:
        dungeon = Dungeon()
        dungeon.generate_floor(floor_id=1, room_count=6, seed=5, extra_cycles=1)
        room_tile_count = sum(len(n.tiles) for n in dungeon.room_nodes.values())
        self.assertGreaterEqual(len(dungeon.floor_tiles), room_tile_count)


if __name__ == "__main__":
    unittest.main()
