from __future__ import annotations

import heapq

from dungeon_crawler.models.dungeon import Dungeon

Point = tuple[int, int]


def find_path(
    dungeon: Dungeon,
    start: Point,
    goal: Point,
    blocked: set[Point] | None = None,
) -> list[Point]:
    """
    A* shortest path over 4-direction grid.
    Returns full path including start and goal. Empty list when unreachable.
    """
    if start == goal:
        return [start]

    blocked_set = blocked or set()

    def is_walkable(x: int, y: int) -> bool:
        return dungeon.is_walkable(x, y) and (x, y) not in blocked_set

    if not is_walkable(*start) or not is_walkable(*goal):
        return []

    open_heap: list[tuple[int, int, Point]] = []
    came_from: dict[Point, Point] = {}
    g_score: dict[Point, int] = {start: 0}

    heapq.heappush(open_heap, (_heuristic(start, goal), 0, start))
    closed: set[Point] = set()

    while open_heap:
        _, current_g, current = heapq.heappop(open_heap)
        if current in closed:
            continue
        closed.add(current)

        if current == goal:
            return _reconstruct_path(came_from, current)

        for neighbor in _neighbors(current):
            if not is_walkable(*neighbor):
                continue

            tentative_g = current_g + 1
            if tentative_g < g_score.get(neighbor, 10**9):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + _heuristic(neighbor, goal)
                heapq.heappush(open_heap, (f_score, tentative_g, neighbor))

    return []


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

