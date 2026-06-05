from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

WORLD_WIDTH = 50
WORLD_HEIGHT = 30
CELL_SIZE = 5
META_COLS = WORLD_WIDTH // CELL_SIZE
META_ROWS = WORLD_HEIGHT // CELL_SIZE

VALID_CHARS = frozenset("01234")


@dataclass(frozen=True)
class RoomTemplate:
    name: str
    room_type: str
    width: int
    height: int
    cells: tuple[tuple[int, ...], ...]

    def tile_at(self, x: int, y: int) -> int:
        return self.cells[y][x]

    def floors(self) -> set[tuple[int, int]]:
        return {(x, y) for y in range(self.height) for x in range(self.width) if self.cells[y][x] == 0}

    def walls(self) -> set[tuple[int, int]]:
        return {(x, y) for y in range(self.height) for x in range(self.width) if self.cells[y][x] == 1}

    def stairs(self) -> set[tuple[int, int]]:
        return {(x, y) for y in range(self.height) for x in range(self.width) if self.cells[y][x] == 2}

    def enemy_spawns(self) -> set[tuple[int, int]]:
        return {(x, y) for y in range(self.height) for x in range(self.width) if self.cells[y][x] == 3}

    def item_spawns(self) -> set[tuple[int, int]]:
        return {(x, y) for y in range(self.height) for x in range(self.width) if self.cells[y][x] == 4}

    def edge_openings(self, edge: str) -> list[int]:
        """Return offsets along shared edge where tile is walkable floor (0)."""
        openings: list[int] = []
        if edge == "north":
            for x in range(self.width):
                if self.cells[0][x] == 0:
                    openings.append(x)
        elif edge == "south":
            for x in range(self.width):
                if self.cells[self.height - 1][x] == 0:
                    openings.append(x)
        elif edge == "west":
            for y in range(self.height):
                if self.cells[y][0] == 0:
                    openings.append(y)
        elif edge == "east":
            for y in range(self.height):
                if self.cells[y][self.width - 1] == 0:
                    openings.append(y)
        else:
            raise ValueError(f"unknown edge: {edge}")
        return openings


class RoomTemplateLoader:
    def __init__(self, base_dir: Path | None = None) -> None:
        if base_dir is None:
            base_dir = Path(__file__).resolve().parent.parent / "templates" / "rooms"
        self.base_dir = base_dir

    def load(self, room_type: str, name: str) -> RoomTemplate:
        path = self.base_dir / room_type / f"{name}.txt"
        return self._parse_file(path, room_type=room_type, name=name)

    def load_all(self, room_type: str) -> list[RoomTemplate]:
        folder = self.base_dir / room_type
        if not folder.is_dir():
            return []
        templates: list[RoomTemplate] = []
        for path in sorted(folder.glob("*.txt"), key=lambda p: p.stem):
            templates.append(self._parse_file(path, room_type=room_type, name=path.stem))
        return templates

    def _parse_file(self, path: Path, *, room_type: str, name: str) -> RoomTemplate:
        if not path.is_file():
            raise FileNotFoundError(path)
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        if not lines:
            raise ValueError(f"{path}: empty template")

        width = len(lines[0])
        if width == 0 or width % CELL_SIZE != 0:
            raise ValueError(f"{path}: width must be a positive multiple of {CELL_SIZE}")
        if len(lines) % CELL_SIZE != 0:
            raise ValueError(f"{path}: height must be a multiple of {CELL_SIZE}")

        cells: list[tuple[int, ...]] = []
        for row_idx, line in enumerate(lines):
            if len(line) != width:
                raise ValueError(f"{path}: inconsistent row width at line {row_idx + 1}")
            for ch in line:
                if ch not in VALID_CHARS:
                    raise ValueError(f"{path}: invalid character '{ch}'")
            cells.append(tuple(int(ch) for ch in line))

        return RoomTemplate(
            name=name,
            room_type=room_type,
            width=width,
            height=len(lines),
            cells=tuple(cells),
        )


def pick_template_for_meta_size(
    templates: list[RoomTemplate],
    meta_width: int,
    meta_height: int,
    rng: random.Random,
) -> RoomTemplate | None:
    target_w = meta_width * CELL_SIZE
    target_h = meta_height * CELL_SIZE
    matches = [t for t in templates if t.width == target_w and t.height == target_h]
    if not matches:
        return None
    return rng.choice(matches)


def build_stamp_grid(
    meta_width: int,
    meta_height: int,
    templates: list[RoomTemplate],
    rng: random.Random,
) -> list[tuple[int, int, RoomTemplate]]:
    """Fill a meta-sized room with templates, preferring one large template when available."""
    whole = pick_template_for_meta_size(templates, meta_width, meta_height, rng)
    if whole is not None:
        return [(0, 0, whole)]

    stamps: list[tuple[int, int, RoomTemplate]] = []
    for dy in range(meta_height):
        for dx in range(meta_width):
            stamps.append((dx, dy, rng.choice(templates)))
    return stamps


def find_connection_offsets(
    template_a: RoomTemplate,
    template_b: RoomTemplate,
    direction: str,
) -> list[int]:
    """
    Return offsets along the shared edge where both templates have floor (0).
    direction: a_to_b from A's perspective (east/south/west/north).
    """
    if direction == "east":
        edge_a, edge_b = "east", "west"
    elif direction == "west":
        edge_a, edge_b = "west", "east"
    elif direction == "south":
        edge_a, edge_b = "south", "north"
    elif direction == "north":
        edge_a, edge_b = "north", "south"
    else:
        raise ValueError(f"unknown direction: {direction}")

    openings_a = set(template_a.edge_openings(edge_a))
    openings_b = set(template_b.edge_openings(edge_b))
    return sorted(openings_a & openings_b)
