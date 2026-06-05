from __future__ import annotations

import unittest

from dungeon_crawler.models.dungeon import Dungeon


class DungeonGenerationTest(unittest.TestCase):
    def test_generates_non_overlapping_rooms(self) -> None:
        dungeon = Dungeon(width=20, height=20)
        dungeon.generate_rooms(room_count=8, seed=7)

        all_tiles: set[tuple[int, int]] = set()
        for node in dungeon.room_nodes.values():
            self.assertFalse(node.tiles & all_tiles)
            all_tiles |= node.tiles

    def test_spanning_tree_connects_all_rooms(self) -> None:
        dungeon = Dungeon(width=20, height=20)
        dungeon.generate_rooms(room_count=6, seed=13, extra_cycles=0)

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
        self.assertEqual(len(dungeon.edges), len(dungeon.room_nodes) - 1)

    def test_extra_cycle_adds_additional_edge(self) -> None:
        dungeon = Dungeon(width=20, height=20)
        dungeon.generate_rooms(room_count=6, seed=21, extra_cycles=1)
        self.assertGreaterEqual(len(dungeon.edges), len(dungeon.room_nodes))

    def test_corridors_expand_floor_tiles(self) -> None:
        dungeon = Dungeon(width=20, height=20)
        dungeon.generate_rooms(room_count=6, seed=5, extra_cycles=0)
        room_tile_count = sum(len(n.tiles) for n in dungeon.room_nodes.values())
        self.assertGreater(len(dungeon.floor_tiles), room_tile_count)


if __name__ == "__main__":
    unittest.main()

