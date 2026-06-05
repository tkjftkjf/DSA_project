from __future__ import annotations

import random
from dataclasses import dataclass

from dungeon_crawler.models.room_template import (
    CELL_SIZE,
    META_COLS,
    META_ROWS,
    WORLD_HEIGHT,
    WORLD_WIDTH,
    RoomTemplate,
    RoomTemplateLoader,
    find_connection_offsets,
)


@dataclass(frozen=True)
class RoomNode:
    room_id: int
    tiles: set[tuple[int, int]]
    meta_col: int = 0
    meta_row: int = 0
    template_name: str = ""

    @property
    def center(self) -> tuple[int, int]:
        xs = [x for x, _ in self.tiles]
        ys = [y for _, y in self.tiles]
        return (sum(xs) // len(xs), sum(ys) // len(ys))


@dataclass
class PlacedRoom:
    room_id: int
    meta_col: int
    meta_row: int
    template: RoomTemplate


class Dungeon:
    """Grid dungeon with template-based room placement and graph connectivity."""

    def __init__(self, width: int = WORLD_WIDTH, height: int = WORLD_HEIGHT) -> None:
        self.width = width
        self.height = height
        self._blocked: set[tuple[int, int]] = set()
        self.room_nodes: dict[int, RoomNode] = {}
        self.edges: set[tuple[int, int]] = set()
        self.floor_tiles: set[tuple[int, int]] = set()
        self.stair_tiles: set[tuple[int, int]] = set()
        self.enemy_spawn_tiles: list[tuple[int, int]] = []
        self.item_spawn_tiles: list[tuple[int, int]] = []
        self.start_spawn: tuple[int, int] | None = None
        self.floor_id: int = 1

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

    def generate_floor(
        self,
        *,
        floor_id: int,
        room_count: int,
        seed: int = 0,
        extra_cycles: int = 1,
        loader: RoomTemplateLoader | None = None,
    ) -> None:
        if room_count < 1:
            raise ValueError("room_count must be >= 1")
        if floor_id not in (1, 2, 3):
            raise ValueError("floor_id must be 1, 2, or 3")

        loader = loader or RoomTemplateLoader()
        start_templates = loader.load_all("start")
        normal_templates = loader.load_all("normal")
        boss_templates = loader.load_all("boss")
        if not start_templates and floor_id == 1:
            raise RuntimeError("No start room templates found")
        if not normal_templates:
            raise RuntimeError("No normal room templates found")
        if floor_id == 3 and not boss_templates:
            raise RuntimeError("No boss room templates found")

        rng = random.Random(seed)
        self._reset_generation_state(floor_id=floor_id)

        origin = (rng.randint(0, META_COLS - 1), rng.randint(0, META_ROWS - 1))
        meta_cells = self._grow_meta_cells(rng, room_count, origin)
        if len(meta_cells) < room_count:
            raise RuntimeError("Failed to place enough connected meta cells")

        placed = self._assign_templates(
            meta_cells,
            rng=rng,
            floor_id=floor_id,
            start_templates=start_templates,
            normal_templates=normal_templates,
            boss_templates=boss_templates,
        )

        for room in placed.values():
            self._stamp_template(room)

        self._build_meta_spanning_tree(rng, placed)
        self._add_extra_meta_cycles(rng, placed, extra_cycles=extra_cycles)
        self._open_connections(rng, placed)

        if floor_id == 1 and self.start_spawn is None:
            start_room = next(iter(placed.values()))
            self.start_spawn = self._room_walkable_center(start_room)

    def generate_rooms(
        self,
        room_count: int,
        *,
        seed: int = 0,
        max_attempts: int = 500,
        extra_cycles: int = 1,
    ) -> None:
        """Legacy small-map generator kept for isolated unit tests."""
        if room_count < 1:
            raise ValueError("room_count must be >= 1")

        rng = random.Random(seed)
        self._reset_generation_state(floor_id=1)

        templates = [
            {(0, 0)},
            {(0, 0), (1, 0)},
            {(0, 0), (1, 0), (0, 1)},
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

        self._build_legacy_spanning_tree(rng)
        self._add_legacy_extra_cycles(rng, extra_cycles=extra_cycles)
        self._carve_legacy_corridors()

    def _reset_generation_state(self, *, floor_id: int) -> None:
        self.floor_id = floor_id
        self.room_nodes.clear()
        self.edges.clear()
        self.floor_tiles.clear()
        self._blocked.clear()
        self.stair_tiles.clear()
        self.enemy_spawn_tiles.clear()
        self.item_spawn_tiles.clear()
        self.start_spawn = None

    def _grow_meta_cells(
        self,
        rng: random.Random,
        count: int,
        origin: tuple[int, int],
    ) -> set[tuple[int, int]]:
        cells = {origin}
        while len(cells) < count:
            frontier: list[tuple[int, int]] = []
            for mc, mr in cells:
                for nc, nr in self._meta_neighbors(mc, mr):
                    if (nc, nr) not in cells:
                        frontier.append((nc, nr))
            if not frontier:
                break
            cells.add(rng.choice(frontier))
        return cells

    @staticmethod
    def _meta_neighbors(mc: int, mr: int) -> list[tuple[int, int]]:
        candidates = [(mc + 1, mr), (mc - 1, mr), (mc, mr + 1), (mc, mr - 1)]
        return [(c, r) for c, r in candidates if 0 <= c < META_COLS and 0 <= r < META_ROWS]

    def _assign_templates(
        self,
        meta_cells: set[tuple[int, int]],
        *,
        rng: random.Random,
        floor_id: int,
        start_templates: list[RoomTemplate],
        normal_templates: list[RoomTemplate],
        boss_templates: list[RoomTemplate],
    ) -> dict[int, PlacedRoom]:
        ordered = sorted(meta_cells)
        special_col, special_row = ordered[0]
        placed: dict[int, PlacedRoom] = {}

        for room_id, (mc, mr) in enumerate(ordered):
            if floor_id == 1 and (mc, mr) == (special_col, special_row):
                template = rng.choice(start_templates)
            elif floor_id == 3 and room_id == 0:
                template = rng.choice(boss_templates)
            else:
                template = rng.choice(normal_templates)

            placed[room_id] = PlacedRoom(
                room_id=room_id,
                meta_col=mc,
                meta_row=mr,
                template=template,
            )
        return placed

    def _stamp_template(self, room: PlacedRoom) -> None:
        room_tiles: set[tuple[int, int]] = set()
        origin_x = room.meta_col * CELL_SIZE
        origin_y = room.meta_row * CELL_SIZE

        for ty in range(room.template.height):
            for tx in range(room.template.width):
                wx = origin_x + tx
                wy = origin_y + ty
                if not self.in_bounds(wx, wy):
                    continue
                value = room.template.tile_at(tx, ty)
                pos = (wx, wy)
                if value == 0:
                    self.floor_tiles.add(pos)
                    room_tiles.add(pos)
                elif value == 1:
                    self._blocked.add(pos)
                elif value == 2:
                    self.floor_tiles.add(pos)
                    room_tiles.add(pos)
                    self.stair_tiles.add(pos)
                elif value == 3:
                    self.floor_tiles.add(pos)
                    room_tiles.add(pos)
                    self.enemy_spawn_tiles.append(pos)
                elif value == 4:
                    self.floor_tiles.add(pos)
                    room_tiles.add(pos)
                    self.item_spawn_tiles.append(pos)

        self.room_nodes[room.room_id] = RoomNode(
            room_id=room.room_id,
            tiles=room_tiles,
            meta_col=room.meta_col,
            meta_row=room.meta_row,
            template_name=room.template.name,
        )

        if room.template.room_type == "start":
            self.start_spawn = self._room_walkable_center(room)

    def _room_walkable_center(self, room: PlacedRoom) -> tuple[int, int]:
        floors = sorted(self.room_nodes[room.room_id].tiles)
        if not floors:
            return (room.meta_col * CELL_SIZE + 2, room.meta_row * CELL_SIZE + 2)
        return floors[len(floors) // 2]

    def _build_meta_spanning_tree(self, rng: random.Random, placed: dict[int, PlacedRoom]) -> None:
        room_ids = list(placed.keys())
        if len(room_ids) <= 1:
            return

        connected = {room_ids[0]}
        unconnected = set(room_ids[1:])

        while unconnected:
            best_pair: tuple[int, int] | None = None
            best_dist = 10**9
            for a in connected:
                for b in unconnected:
                    if not self._meta_adjacent(placed[a], placed[b]):
                        continue
                    dist = self._manhattan_meta(placed[a], placed[b])
                    if dist < best_dist:
                        best_dist = dist
                        best_pair = (a, b)
            if best_pair is None:
                break
            a, b = best_pair
            if rng.random() < 0.5:
                self.edges.add(tuple(sorted((a, b))))
            else:
                a = rng.choice(list(connected))
                neighbors = [
                    rid
                    for rid in unconnected
                    if self._meta_adjacent(placed[a], placed[rid])
                ]
                if not neighbors:
                    self.edges.add(tuple(sorted(best_pair)))
                else:
                    b = min(neighbors, key=lambda rid: self._manhattan_meta(placed[a], placed[rid]))
                    self.edges.add(tuple(sorted((a, b))))
            connected.add(b)
            unconnected.remove(b)

    def _add_extra_meta_cycles(
        self,
        rng: random.Random,
        placed: dict[int, PlacedRoom],
        *,
        extra_cycles: int,
    ) -> None:
        if extra_cycles <= 0 or len(placed) <= 2:
            return

        candidates: list[tuple[int, int]] = []
        room_ids = list(placed.keys())
        for i in range(len(room_ids)):
            for j in range(i + 1, len(room_ids)):
                a, b = room_ids[i], room_ids[j]
                edge = tuple(sorted((a, b)))
                if edge in self.edges:
                    continue
                if self._meta_adjacent(placed[a], placed[b]):
                    candidates.append(edge)

        rng.shuffle(candidates)
        for edge in candidates[:extra_cycles]:
            self.edges.add(edge)

    def _open_connections(self, rng: random.Random, placed: dict[int, PlacedRoom]) -> None:
        for a, b in self.edges:
            room_a = placed[a]
            room_b = placed[b]
            direction = self._connection_direction(room_a, room_b)
            if direction is None:
                continue
            offsets = find_connection_offsets(room_a.template, room_b.template, direction)
            if not offsets:
                continue
            offset = rng.choice(offsets)
            for pos in self._connection_tiles(room_a, room_b, direction, offset):
                self.floor_tiles.add(pos)
                self._blocked.discard(pos)

    @staticmethod
    def _meta_adjacent(a: PlacedRoom, b: PlacedRoom) -> bool:
        return abs(a.meta_col - b.meta_col) + abs(a.meta_row - b.meta_row) == 1

    @staticmethod
    def _manhattan_meta(a: PlacedRoom, b: PlacedRoom) -> int:
        return abs(a.meta_col - b.meta_col) + abs(a.meta_row - b.meta_row)

    @staticmethod
    def _connection_direction(a: PlacedRoom, b: PlacedRoom) -> str | None:
        dc = b.meta_col - a.meta_col
        dr = b.meta_row - a.meta_row
        if dc == 1 and dr == 0:
            return "east"
        if dc == -1 and dr == 0:
            return "west"
        if dc == 0 and dr == 1:
            return "south"
        if dc == 0 and dr == -1:
            return "north"
        return None

    @staticmethod
    def _connection_tiles(
        room_a: PlacedRoom,
        room_b: PlacedRoom,
        direction: str,
        offset: int,
    ) -> list[tuple[int, int]]:
        ax = room_a.meta_col * CELL_SIZE
        ay = room_a.meta_row * CELL_SIZE
        bx = room_b.meta_col * CELL_SIZE
        by = room_b.meta_row * CELL_SIZE

        if direction == "east":
            return [(ax + CELL_SIZE - 1, ay + offset), (bx, by + offset)]
        if direction == "west":
            return [(ax, ay + offset), (bx + CELL_SIZE - 1, by + offset)]
        if direction == "south":
            return [(ax + offset, ay + CELL_SIZE - 1), (bx + offset, by)]
        if direction == "north":
            return [(ax + offset, ay), (bx + offset, by + CELL_SIZE - 1)]
        raise ValueError(f"unknown direction: {direction}")

    def _build_legacy_spanning_tree(self, rng: random.Random) -> None:
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
                a = rng.choice(list(connected))
                b = min(
                    unconnected,
                    key=lambda rid: self._manhattan(self.room_nodes[a].center, self.room_nodes[rid].center),
                )
            self.edges.add(tuple(sorted((a, b))))
            connected.add(b)
            unconnected.remove(b)

    def _add_legacy_extra_cycles(self, rng: random.Random, extra_cycles: int) -> None:
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

    def _carve_legacy_corridors(self) -> None:
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
