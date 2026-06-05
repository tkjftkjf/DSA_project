from __future__ import annotations

import unittest

from dungeon_crawler.models.dungeon import Dungeon


class DungeonGenerationTest(unittest.TestCase):
    def test_generates_non_overlapping_rooms(self) -> None:
        dungeon = Dungeon()
        dungeon.generate_floor(floor_id=1, room_count=12, seed=7)

        all_tiles: set[tuple[int, int]] = set()
        for node in dungeon.room_nodes.values():
            self.assertFalse(node.tiles & all_tiles)
            all_tiles |= node.tiles

    def test_spanning_tree_connects_all_rooms(self) -> None:
        dungeon = Dungeon()
        dungeon.generate_floor(floor_id=1, room_count=12, seed=13, extra_cycles=0)

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
        dungeon = Dungeon()
        dungeon.generate_floor(floor_id=1, room_count=12, seed=21, extra_cycles=1)
        self.assertGreater(len(dungeon.edges), len(dungeon.room_nodes) - 1)

    def test_corridors_expand_floor_tiles(self) -> None:
        dungeon = Dungeon()
        dungeon.generate_floor(floor_id=1, room_count=12, seed=5, extra_cycles=0)
        room_tile_count = sum(len(n.tiles) for n in dungeon.room_nodes.values())
        self.assertGreater(len(dungeon.floor_tiles), room_tile_count)

    def test_corridors_do_not_punch_through_room_walls(self) -> None:
        for seed in (3, 7, 11, 17, 23, 29, 37):
            dungeon = Dungeon()
            dungeon.generate_floor(floor_id=1, room_count=12, seed=seed, extra_cycles=2)
            for node in dungeon.room_nodes.values():
                x0, y0, x1, y1 = (
                    node.anchor_x,
                    node.anchor_y,
                    node.anchor_x + node.template_width - 1,
                    node.anchor_y + node.template_height - 1,
                )
                for x in range(x0, x1 + 1):
                    for y in range(y0, y1 + 1):
                        pos = (x, y)
                        if pos in dungeon.floor_tiles and pos not in node.tiles:
                            self.fail(
                                f"seed={seed}: corridor carved {pos} inside room "
                                f"{node.room_id} ({node.template_name})"
                            )


if __name__ == "__main__":
    unittest.main()
