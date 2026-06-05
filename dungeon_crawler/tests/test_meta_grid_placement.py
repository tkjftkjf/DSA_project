from __future__ import annotations

import unittest

from dungeon_crawler.models.dungeon import Dungeon
from dungeon_crawler.models.room_template import WORLD_HEIGHT, WORLD_WIDTH
from dungeon_crawler.utils.pathfinding import find_path


class MetaGridPlacementTest(unittest.TestCase):
    def test_floor1_world_size(self) -> None:
        dungeon = Dungeon()
        dungeon.generate_floor(floor_id=1, room_count=8, seed=7)
        self.assertEqual(dungeon.width, WORLD_WIDTH)
        self.assertEqual(dungeon.height, WORLD_HEIGHT)

    def test_rooms_are_spread_across_map(self) -> None:
        dungeon = Dungeon()
        dungeon.generate_floor(floor_id=1, room_count=8, seed=7)
        cols = {node.meta_col for node in dungeon.room_nodes.values()}
        rows = {node.meta_row for node in dungeon.room_nodes.values()}
        self.assertGreaterEqual(len(cols), 3)
        self.assertGreaterEqual(len(rows), 3)
        xs = [x for x, _ in dungeon.floor_tiles]
        self.assertGreater(max(xs) - min(xs), 10)

    def test_spanning_tree_connects_all_rooms(self) -> None:
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

    def test_corridors_connect_graph_rooms(self) -> None:
        dungeon = Dungeon()
        dungeon.generate_floor(floor_id=1, room_count=6, seed=5, extra_cycles=0)
        room_tile_count = sum(len(n.tiles) for n in dungeon.room_nodes.values())
        self.assertGreater(len(dungeon.floor_tiles), room_tile_count)

    def test_each_floor_has_one_start_and_one_stair(self) -> None:
        for floor_id, seed in ((1, 11), (2, 17), (3, 23)):
            dungeon = Dungeon()
            dungeon.generate_floor(floor_id=floor_id, room_count=8, seed=seed)
            roles = [node.room_role for node in dungeon.room_nodes.values()]
            self.assertEqual(roles.count("start"), 1)
            self.assertEqual(roles.count("stair"), 1)
            self.assertTrue(dungeon.stair_tiles)
            self.assertIsNotNone(dungeon.start_spawn)

    def test_normal_rooms_can_merge_into_larger_spaces(self) -> None:
        merged_found = False
        for seed in range(20):
            dungeon = Dungeon()
            dungeon.generate_floor(floor_id=1, room_count=10, seed=seed, merge_chance=0.8)
            for node in dungeon.room_nodes.values():
                if node.room_role == "normal" and (node.meta_width > 1 or node.meta_height > 1):
                    merged_found = True
                    self.assertGreater(len(node.tiles), 25)
                    break
            if merged_found:
                break
        self.assertTrue(merged_found)

    def test_start_spawn_exists_on_floor1(self) -> None:
        dungeon = Dungeon()
        dungeon.generate_floor(floor_id=1, room_count=5, seed=3)
        assert dungeon.start_spawn is not None
        self.assertIn(dungeon.start_spawn, dungeon.floor_tiles)

    def test_start_spawn_can_reach_stairs(self) -> None:
        for seed in range(50):
            dungeon = Dungeon()
            dungeon.generate_floor(floor_id=1, room_count=10, seed=seed, merge_chance=0.4)
            assert dungeon.start_spawn is not None
            stair = next(iter(dungeon.stair_tiles))
            path = find_path(dungeon, dungeon.start_spawn, stair)
            self.assertTrue(path, f"seed {seed}: no path from start to stairs")

    def test_spawn_markers_collected_from_templates(self) -> None:
        dungeon = Dungeon()
        dungeon.generate_floor(floor_id=2, room_count=10, seed=21)
        for pos in dungeon.enemy_spawn_tiles:
            self.assertIn(pos, dungeon.floor_tiles)
        for pos in dungeon.item_spawn_tiles:
            self.assertIn(pos, dungeon.floor_tiles)


if __name__ == "__main__":
    unittest.main()
