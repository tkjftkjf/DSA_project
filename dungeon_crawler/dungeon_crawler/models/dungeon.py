from __future__ import annotations

import random
from dataclasses import dataclass, field

from dungeon_crawler.models.room_template import (
    CELL_SIZE,
    META_COLS,
    META_ROWS,
    WORLD_HEIGHT,
    WORLD_WIDTH,
    RoomTemplate,
    RoomTemplateLoader,
    build_stamp_grid,
)


@dataclass(frozen=True)
class RoomNode:
    room_id: int
    tiles: set[tuple[int, int]]
    meta_col: int = 0
    meta_row: int = 0
    meta_width: int = 1
    meta_height: int = 1
    template_name: str = ""
    room_role: str = "normal"

    @property
    def center(self) -> tuple[int, int]:
        xs = [x for x, _ in self.tiles]
        ys = [y for _, y in self.tiles]
        return (sum(xs) // len(xs), sum(ys) // len(ys))


@dataclass(frozen=True)
class MetaRoomUnit:
    cells: frozenset[tuple[int, int]]
    role: str

    @property
    def meta_col(self) -> int:
        return min(col for col, _ in self.cells)

    @property
    def meta_row(self) -> int:
        return min(row for _, row in self.cells)

    @property
    def meta_width(self) -> int:
        return max(col for col, _ in self.cells) - self.meta_col + 1

    @property
    def meta_height(self) -> int:
        return max(row for _, row in self.cells) - self.meta_row + 1


@dataclass
class PlacedRoom:
    room_id: int
    unit: MetaRoomUnit
    stamps: list[tuple[int, int, RoomTemplate]] = field(default_factory=list)


class Dungeon:
    """Grid dungeon with scattered rooms, optional merges, and corridor graph."""

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
        merge_chance: float = 0.4,
    ) -> None:
        if room_count < 3:
            raise ValueError("room_count must be >= 3 (start + stair + normal)")
        if floor_id not in (1, 2, 3):
            raise ValueError("floor_id must be 1, 2, or 3")

        loader = loader or RoomTemplateLoader()
        start_templates = loader.load_all("start")
        stair_templates = loader.load_all("stair")
        normal_templates = loader.load_all("normal")
        if not start_templates:
            raise RuntimeError("No start room templates found")
        if not stair_templates:
            raise RuntimeError("No stair room templates found")
        if not normal_templates:
            raise RuntimeError("No normal room templates found")

        rng = random.Random(seed)
        self._reset_generation_state(floor_id=floor_id)

        meta_cells = self._scatter_meta_cells(rng, room_count, min_dist=2)
        if len(meta_cells) < room_count:
            raise RuntimeError("Failed to place enough scattered meta cells")

        units = self._build_room_units(
            rng,
            meta_cells,
            room_count=room_count,
            merge_chance=merge_chance,
        )
        placed = self._assign_templates(
            units,
            rng=rng,
            start_templates=start_templates,
            stair_templates=stair_templates,
            normal_templates=normal_templates,
        )

        for room in placed.values():
            self._stamp_room(room)

        self._build_room_graph_spanning_tree(rng)
        self._add_extra_room_cycles(rng, extra_cycles=extra_cycles)
        self._carve_room_corridors()

        if not self.stair_tiles:
            raise RuntimeError(f"Floor {floor_id} has no stair tiles")
        if self.start_spawn is None:
            raise RuntimeError(f"Floor {floor_id} has no start spawn")

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

        self._build_room_graph_spanning_tree(rng)
        self._add_extra_room_cycles(rng, extra_cycles=extra_cycles)
        self._carve_room_corridors()

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

    def _scatter_meta_cells(
        self,
        rng: random.Random,
        count: int,
        *,
        min_dist: int = 2,
    ) -> set[tuple[int, int]]:
        candidates = [(col, row) for col in range(META_COLS) for row in range(META_ROWS)]
        rng.shuffle(candidates)

        picked: list[tuple[int, int]] = []
        for cell in candidates:
            if len(picked) >= count:
                break
            if all(self._manhattan(cell, other) >= min_dist for other in picked):
                picked.append(cell)

        if len(picked) < count:
            seed_cell = picked[0] if picked else (META_COLS // 2, META_ROWS // 2)
            picked_set = set(picked)
            while len(picked_set) < count:
                frontier: list[tuple[int, int]] = []
                for mc, mr in picked_set:
                    for neighbor in self._meta_neighbors(mc, mr):
                        if neighbor not in picked_set:
                            frontier.append(neighbor)
                if not frontier:
                    break
                picked_set.add(rng.choice(frontier))
            return picked_set

        return set(picked)

    @staticmethod
    def _meta_neighbors(mc: int, mr: int) -> list[tuple[int, int]]:
        candidates = [(mc + 1, mr), (mc - 1, mr), (mc, mr + 1), (mc, mr - 1)]
        return [(c, r) for c, r in candidates if 0 <= c < META_COLS and 0 <= r < META_ROWS]

    def _build_room_units(
        self,
        rng: random.Random,
        meta_cells: set[tuple[int, int]],
        *,
        room_count: int,
        merge_chance: float,
    ) -> list[MetaRoomUnit]:
        cells = sorted(meta_cells)
        start_cell = min(cells, key=lambda cell: (cell[1], cell[0]))
        stair_cell = max(cells, key=lambda cell: self._manhattan(cell, start_cell))
        if stair_cell == start_cell:
            stair_cell = max(
                (cell for cell in cells if cell != start_cell),
                key=lambda cell: self._manhattan(cell, start_cell),
            )

        reserved = {start_cell, stair_cell}
        free = set(cells) - reserved
        normal_target = room_count - 2

        units: list[MetaRoomUnit] = [
            MetaRoomUnit(cells=frozenset({start_cell}), role="start"),
            MetaRoomUnit(cells=frozenset({stair_cell}), role="stair"),
        ]

        occupied = set(meta_cells)
        while len(units) - 2 < normal_target and free:
            if len(units) - 2 < normal_target and rng.random() < merge_chance:
                merged = self._take_merge_pair(rng, free, occupied)
                if merged is not None:
                    units.append(MetaRoomUnit(cells=frozenset(merged), role="normal"))
                    continue

            cell = rng.choice(sorted(free))
            free.remove(cell)
            units.append(MetaRoomUnit(cells=frozenset({cell}), role="normal"))

        while len(units) - 2 < normal_target and free:
            cell = free.pop()
            units.append(MetaRoomUnit(cells=frozenset({cell}), role="normal"))

        if len(units) < room_count:
            raise RuntimeError("Failed to build required room units")

        return units[:room_count]

    def _take_merge_pair(
        self,
        rng: random.Random,
        free: set[tuple[int, int]],
        occupied: set[tuple[int, int]],
    ) -> set[tuple[int, int]] | None:
        candidates: list[set[tuple[int, int]]] = []
        free_list = sorted(free)
        for col, row in free_list:
            for ncol, nrow in ((col + 1, row), (col, row + 1)):
                if (ncol, nrow) in free:
                    candidates.append({(col, row), (ncol, nrow)})

        if not candidates:
            for col, row in free_list:
                for ncol, nrow in ((col + 1, row), (col, row + 1)):
                    partner = (ncol, nrow)
                    if partner in occupied:
                        continue
                    if not (0 <= ncol < META_COLS and 0 <= nrow < META_ROWS):
                        continue
                    if all(self._manhattan(partner, other) >= 2 for other in occupied if other != (col, row)):
                        candidates.append({(col, row), partner})

        if not candidates:
            for col, row in free_list:
                block = {(col, row), (col + 1, row), (col, row + 1), (col + 1, row + 1)}
                if not all(0 <= c < META_COLS and 0 <= r < META_ROWS for c, r in block):
                    continue
                missing = [cell for cell in block if cell not in free and cell not in occupied]
                if not missing:
                    candidates.append(set(block))
                    continue
                if all(
                    all(self._manhattan(m, o) >= 2 for o in occupied)
                    for m in missing
                ):
                    candidates.append(set(block))

        if not candidates:
            return None

        chosen = rng.choice(candidates)
        for cell in chosen:
            free.discard(cell)
            occupied.add(cell)
        return chosen

    def _assign_templates(
        self,
        units: list[MetaRoomUnit],
        *,
        rng: random.Random,
        start_templates: list[RoomTemplate],
        stair_templates: list[RoomTemplate],
        normal_templates: list[RoomTemplate],
    ) -> dict[int, PlacedRoom]:
        placed: dict[int, PlacedRoom] = {}
        for room_id, unit in enumerate(units):
            if unit.role == "start":
                stamps = [(0, 0, rng.choice(start_templates))]
            elif unit.role == "stair":
                stamps = [(0, 0, rng.choice(stair_templates))]
            else:
                stamps = build_stamp_grid(
                    unit.meta_width,
                    unit.meta_height,
                    normal_templates,
                    rng,
                )

            placed[room_id] = PlacedRoom(room_id=room_id, unit=unit, stamps=stamps)
        return placed

    def _stamp_room(self, room: PlacedRoom) -> None:
        unit = room.unit
        room_tiles: set[tuple[int, int]] = set()
        template_names: list[str] = []

        for stamp_dx, stamp_dy, template in room.stamps:
            origin_x = (unit.meta_col + stamp_dx) * CELL_SIZE
            origin_y = (unit.meta_row + stamp_dy) * CELL_SIZE
            template_names.append(template.name)

            for ty in range(template.height):
                for tx in range(template.width):
                    wx = origin_x + tx
                    wy = origin_y + ty
                    if not self.in_bounds(wx, wy):
                        continue
                    value = template.tile_at(tx, ty)
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

        label = "+".join(template_names)
        self.room_nodes[room.room_id] = RoomNode(
            room_id=room.room_id,
            tiles=room_tiles,
            meta_col=unit.meta_col,
            meta_row=unit.meta_row,
            meta_width=unit.meta_width,
            meta_height=unit.meta_height,
            template_name=label,
            room_role=unit.role,
        )

        if unit.role == "start":
            floors = sorted(room_tiles)
            self.start_spawn = floors[len(floors) // 2] if floors else (
                unit.meta_col * CELL_SIZE + 2,
                unit.meta_row * CELL_SIZE + 2,
            )

    def _build_room_graph_spanning_tree(self, rng: random.Random) -> None:
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

    def _add_extra_room_cycles(self, rng: random.Random, *, extra_cycles: int) -> None:
        if extra_cycles <= 0 or len(self.room_nodes) <= 2:
            return

        room_ids = list(self.room_nodes.keys())
        candidates: list[tuple[int, int]] = []
        for i in range(len(room_ids)):
            for j in range(i + 1, len(room_ids)):
                edge = tuple(sorted((room_ids[i], room_ids[j])))
                if edge not in self.edges:
                    candidates.append(edge)

        rng.shuffle(candidates)
        for edge in candidates[:extra_cycles]:
            self.edges.add(edge)

    def _carve_room_corridors(self) -> None:
        for a, b in self.edges:
            start, end = self._pick_connection_tiles(self.room_nodes[a], self.room_nodes[b])
            self._carve_l_corridor(start, end)

    def _pick_connection_tiles(
        self,
        node_a: RoomNode,
        node_b: RoomNode,
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        """Pick the closest walkable tiles between two rooms (usually facing edges)."""
        best_dist = 10**9
        best_pair = (node_a.center, node_b.center)
        for tile_a in node_a.tiles:
            for tile_b in node_b.tiles:
                dist = self._manhattan(tile_a, tile_b)
                if dist < best_dist:
                    best_dist = dist
                    best_pair = (tile_a, tile_b)
        return best_pair

    def _carve_tile(self, x: int, y: int) -> None:
        if not self.in_bounds(x, y):
            return
        self.floor_tiles.add((x, y))
        self._blocked.discard((x, y))

    def _widen_corridor_junction(self, pos: tuple[int, int]) -> None:
        """Carve a 3-wide opening so corridors are not blocked by interior room walls."""
        x, y = pos
        self._carve_tile(x, y)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            self._carve_tile(x + dx, y + dy)

    def _carve_l_corridor(self, start: tuple[int, int], end: tuple[int, int]) -> None:
        x, y = start
        ex, ey = end
        self._widen_corridor_junction(start)
        while x != ex:
            self._carve_tile(x, y)
            x += 1 if ex > x else -1
        while y != ey:
            self._carve_tile(x, y)
            y += 1 if ey > y else -1
        self._widen_corridor_junction(end)

    @staticmethod
    def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
