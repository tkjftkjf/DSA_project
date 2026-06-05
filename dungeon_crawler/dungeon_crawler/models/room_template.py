from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

WORLD_WIDTH = 53
WORLD_HEIGHT = 30
START_TEMPLATE_SIZE = 5

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
        if width == 0:
            raise ValueError(f"{path}: width must be positive")

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


def start_templates_only(templates: list[RoomTemplate]) -> list[RoomTemplate]:
    """Start rooms must be exactly 5x5."""
    matches = [
        template
        for template in templates
        if template.width == START_TEMPLATE_SIZE and template.height == START_TEMPLATE_SIZE
    ]
    if not matches:
        raise RuntimeError("start templates must include at least one 5x5 room")
    return matches


def pick_room_template(templates: list[RoomTemplate], rng: random.Random) -> RoomTemplate:
    if not templates:
        raise RuntimeError("no room templates available")
    return rng.choice(templates)


def template_world_rect(origin_x: int, origin_y: int, template: RoomTemplate) -> tuple[int, int, int, int]:
    """Return inclusive world bounds (x0, y0, x1, y1) for a template at the given origin."""
    return (origin_x, origin_y, origin_x + template.width - 1, origin_y + template.height - 1)
