from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class RoomNode:
    room_id: int
    tiles: set[tuple[int, int]]

    @property
    def center(self) -> tuple[int, int]:
        xs = [x for x, _ in self.tiles]
        ys = [y for _, y in self.tiles]
        return (sum(xs) // len(xs), sum(ys) // len(ys))


class Dungeon:
    """Grid dungeon with room graph + walkability support."""

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self._blocked: set[tuple[int, int]] = set()
        self.room_nodes: dict[int, RoomNode] = {}
        self.edges: set[tuple[int, int]] = set()
        self.floor_tiles: set[tuple[int, int]] = set()

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def set_blocked(self, x: int, y: int, blocked: bool = True) -> None:
        if blocked:
            self._blocked.add((x, y))
        else:
            self._blocked.discard((x, y))

    def is_walkable(self, x: int, y: int) -> bool:
        if not self.in_bounds(x, y) or (x, y) in self._blocked:
            return False
        if self.floor_tiles:
            return (x, y) in self.floor_tiles
        return True

    def generate_rooms(
        self,
        room_count: int,
        *,
        seed: int = 0,
        max_attempts: int = 500,
        extra_cycles: int = 1,
    ) -> None:
        """
        Place preset room templates without overlap and connect as graph.
        """
        if room_count < 1:
            raise ValueError("room_count must be >= 1")

        rng = random.Random(seed)
        self.room_nodes.clear()
        self.edges.clear()
        self.floor_tiles.clear()

        templates = [
            {(0, 0)},  # 1x1
            {(0, 0), (1, 0)},  # 1x2
            {(0, 0), (1, 0), (0, 1)},  # ㄴ shape
        ]

        used_tiles: set[tuple[int, int]] = set()
        room_id = 0
        attempts = 0
        while room_id < room_count and attempts < max_attempts:
            attempts += 1
            template = rng.choice(templates)
            anchor_x = rng.randint(0, self.width - 1)
            anchor_y = rng.randint(0, self.height - 1)
            translated = {(anchor_x + dx, anchor_y + dy) for dx, dy in template}

            if any(not self.in_bounds(x, y) for x, y in translated):
                continue
            if translated & used_tiles:
                continue

            node = RoomNode(room_id=room_id, tiles=translated)
            self.room_nodes[room_id] = node
            used_tiles |= translated
            self.floor_tiles |= translated
            room_id += 1

        if len(self.room_nodes) != room_count:
            raise RuntimeError("Failed to place all rooms without overlap")

        self._build_spanning_tree(rng)
        self._add_extra_cycles(rng, extra_cycles=extra_cycles)
        self._carve_corridors()

    def _build_spanning_tree(self, rng: random.Random) -> None:
        room_ids = list(self.room_nodes.keys())
        if len(room_ids) <= 1:
            return

        connected = {room_ids[0]}
        unconnected = set(room_ids[1:])

        while unconnected:
            best_pair: tuple[int, int] | None = None
            best_dist = 10**9
            for a in connected:
                for b in unconnected:
                    dist = self._manhattan(self.room_nodes[a].center, self.room_nodes[b].center)
                    if dist < best_dist:
                        best_dist = dist
                        best_pair = (a, b)
            assert best_pair is not None
            if rng.random() < 0.5:
                a, b = best_pair
            else:
                # small randomness around nearest-link preference
                a = rng.choice(list(connected))
                b = min(
                    unconnected,
                    key=lambda rid: self._manhattan(self.room_nodes[a].center, self.room_nodes[rid].center),
                )
            self.edges.add(tuple(sorted((a, b))))
            connected.add(b)
            unconnected.remove(b)

    def _add_extra_cycles(self, rng: random.Random, extra_cycles: int) -> None:
        if extra_cycles <= 0 or len(self.room_nodes) <= 2:
            return

        candidates: list[tuple[int, int]] = []
        room_ids = list(self.room_nodes.keys())
        for i in range(len(room_ids)):
            for j in range(i + 1, len(room_ids)):
                edge = (room_ids[i], room_ids[j])
                if edge not in self.edges:
                    candidates.append(edge)

        rng.shuffle(candidates)
        for edge in candidates[:extra_cycles]:
            self.edges.add(tuple(sorted(edge)))

    def _carve_corridors(self) -> None:
        for a, b in self.edges:
            start = self.room_nodes[a].center
            end = self.room_nodes[b].center
            self._carve_l_corridor(start, end)

    def _carve_l_corridor(self, start: tuple[int, int], end: tuple[int, int]) -> None:
        x, y = start
        ex, ey = end
        while x != ex:
            if self.in_bounds(x, y):
                self.floor_tiles.add((x, y))
            x += 1 if ex > x else -1
        while y != ey:
            if self.in_bounds(x, y):
                self.floor_tiles.add((x, y))
            y += 1 if ey > y else -1
        if self.in_bounds(ex, ey):
            self.floor_tiles.add((ex, ey))

    @staticmethod
    def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

