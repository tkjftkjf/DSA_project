from __future__ import annotations

from dungeon_crawler.generation.geometry import Point, manhattan
from dungeon_crawler.models.dungeon import Dungeon
from dungeon_crawler.models.room_node import RoomNode


def carve_room_corridors(
    dungeon: Dungeon,
    room_nodes: dict[int, RoomNode],
    edges: set[tuple[int, int]],
) -> None:
    for room_a, room_b in edges:
        start, end = pick_connection_tiles(room_nodes[room_a], room_nodes[room_b])
        carve_l_corridor(dungeon, start, end)


def pick_connection_tiles(
    node_a: RoomNode,
    node_b: RoomNode,
) -> tuple[Point, Point]:
    """Pick the closest walkable tiles between two rooms."""
    best_dist = 10**9
    best_pair = (node_a.center, node_b.center)
    for tile_a in node_a.tiles:
        for tile_b in node_b.tiles:
            dist = manhattan(tile_a, tile_b)
            if dist < best_dist:
                best_dist = dist
                best_pair = (tile_a, tile_b)
    return best_pair


def carve_l_corridor(dungeon: Dungeon, start: Point, end: Point) -> None:
    x, y = start
    ex, ey = end
    widen_corridor_junction(dungeon, start)
    while x != ex:
        carve_tile(dungeon, x, y)
        x += 1 if ex > x else -1
    while y != ey:
        carve_tile(dungeon, x, y)
        y += 1 if ey > y else -1
    widen_corridor_junction(dungeon, end)


def widen_corridor_junction(dungeon: Dungeon, pos: Point) -> None:
    x, y = pos
    carve_tile(dungeon, x, y)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        carve_tile(dungeon, x + dx, y + dy)


def carve_tile(dungeon: Dungeon, x: int, y: int) -> None:
    if not dungeon.in_bounds(x, y):
        return
    dungeon.floor_tiles.add((x, y))
    dungeon.set_blocked(x, y, blocked=False)
