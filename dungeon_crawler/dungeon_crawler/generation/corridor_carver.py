from __future__ import annotations

import heapq

from dungeon_crawler.generation.geometry import Point, manhattan
from dungeon_crawler.models.dungeon import Dungeon
from dungeon_crawler.models.room_node import RoomNode


def carve_room_corridors(
    dungeon: Dungeon,
    room_nodes: dict[int, RoomNode],
    edges: set[tuple[int, int]],
) -> None:
    for room_a_id, room_b_id in edges:
        node_a = room_nodes[room_a_id]
        node_b = room_nodes[room_b_id]
        protected, _allowed = build_protected_cells(
            room_nodes,
            node_a,
            node_b,
            dungeon.width,
            dungeon.height,
        )
        path = find_corridor_path(node_a, node_b, protected, dungeon.width, dungeon.height)
        if not path:
            raise RuntimeError(f"No corridor path between room {room_a_id} and {room_b_id}")
        carve_corridor_path(dungeon, path, protected)


def room_bounds(node: RoomNode) -> tuple[int, int, int, int]:
    return (
        node.anchor_x,
        node.anchor_y,
        node.anchor_x + node.template_width - 1,
        node.anchor_y + node.template_height - 1,
    )


def iter_rect_cells(bounds: tuple[int, int, int, int]) -> list[Point]:
    x0, y0, x1, y1 = bounds
    return [(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]


def build_protected_cells(
    room_nodes: dict[int, RoomNode],
    node_a: RoomNode,
    node_b: RoomNode,
    width: int,
    height: int,
) -> tuple[set[Point], set[Point]]:
    """
    Cells that corridors must not carve through.

    Every room template cell is protected except the walkable floors of the
    two rooms being connected.
    """
    allowed = node_a.tiles | node_b.tiles
    protected: set[Point] = set()
    for node in room_nodes.values():
        for pos in iter_rect_cells(room_bounds(node)):
            x, y = pos
            if not (0 <= x < width and 0 <= y < height):
                continue
            if pos not in allowed:
                protected.add(pos)
    return protected, allowed


def perimeter_tiles(node: RoomNode) -> set[Point]:
    tiles: set[Point] = set()
    for x, y in node.tiles:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            if (x + dx, y + dy) not in node.tiles:
                tiles.add((x, y))
                break
    return tiles


def find_corridor_path(
    node_a: RoomNode,
    node_b: RoomNode,
    protected: set[Point],
    width: int,
    height: int,
) -> list[Point]:
    perim_a = perimeter_tiles(node_a)
    perim_b = perimeter_tiles(node_b)
    if not perim_a or not perim_b:
        return []

    candidates: list[tuple[int, Point, Point]] = []
    for tile_a in perim_a:
        for tile_b in perim_b:
            candidates.append((manhattan(tile_a, tile_b), tile_a, tile_b))
    candidates.sort(key=lambda item: item[0])

    for _, start, end in candidates:
        path = _astar_corridor(start, end, protected, width, height)
        if path:
            return path
    return []


def _is_passable(pos: Point, protected: set[Point], width: int, height: int) -> bool:
    x, y = pos
    if not (0 <= x < width and 0 <= y < height):
        return False
    return pos not in protected


def _astar_corridor(
    start: Point,
    goal: Point,
    protected: set[Point],
    width: int,
    height: int,
) -> list[Point]:
    if start == goal:
        return [start]

    open_heap: list[tuple[int, int, Point]] = []
    heapq.heappush(open_heap, (_heuristic(start, goal), 0, start))
    came_from: dict[Point, Point] = {}
    g_score: dict[Point, int] = {start: 0}
    closed: set[Point] = set()

    while open_heap:
        _, current_g, current = heapq.heappop(open_heap)
        if current in closed:
            continue
        closed.add(current)

        if current == goal:
            return _reconstruct_path(came_from, current)

        for neighbor in _neighbors(current):
            if not _is_passable(neighbor, protected, width, height):
                continue
            tentative_g = current_g + 1
            if tentative_g < g_score.get(neighbor, 10**9):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + _heuristic(neighbor, goal)
                heapq.heappush(open_heap, (f_score, tentative_g, neighbor))

    return []


def carve_corridor_path(
    dungeon: Dungeon,
    path: list[Point],
    protected: set[Point],
) -> None:
    for pos in path:
        carve_if_allowed(dungeon, pos, protected)
    if path:
        widen_corridor_junction(dungeon, path[0], protected)
        widen_corridor_junction(dungeon, path[-1], protected)


def widen_corridor_junction(dungeon: Dungeon, pos: Point, protected: set[Point]) -> None:
    x, y = pos
    carve_if_allowed(dungeon, pos, protected)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        carve_if_allowed(dungeon, (x + dx, y + dy), protected)


def carve_if_allowed(dungeon: Dungeon, pos: Point, protected: set[Point]) -> None:
    if pos in protected:
        return
    carve_tile(dungeon, *pos)


def carve_tile(dungeon: Dungeon, x: int, y: int) -> None:
    if not dungeon.in_bounds(x, y):
        return
    dungeon.floor_tiles.add((x, y))
    dungeon.set_blocked(x, y, blocked=False)


def _heuristic(a: Point, b: Point) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _neighbors(point: Point) -> list[Point]:
    x, y = point
    return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]


def _reconstruct_path(came_from: dict[Point, Point], current: Point) -> list[Point]:
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path
