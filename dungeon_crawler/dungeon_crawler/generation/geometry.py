from __future__ import annotations

from dungeon_crawler.models.room_template import RoomTemplate, template_world_rect

Rect = tuple[int, int, int, int]
Point = tuple[int, int]


def manhattan(a: Point, b: Point) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def rects_overlap(a: Rect, b: Rect) -> bool:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return ax0 <= bx1 and bx0 <= ax1 and ay0 <= by1 and by0 <= ay1


def rect_in_map(rect: Rect, *, map_width: int, map_height: int) -> bool:
    _, _, x1, y1 = rect
    return x1 < map_width and y1 < map_height


def template_rect(anchor_col: int, anchor_row: int, template: RoomTemplate) -> Rect:
    return template_world_rect(anchor_col, anchor_row, template)
