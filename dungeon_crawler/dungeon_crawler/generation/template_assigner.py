from __future__ import annotations

import random

from dungeon_crawler.generation.geometry import Rect, rect_in_map, rects_overlap, template_rect
from dungeon_crawler.generation.template_pools import TemplatePools
from dungeon_crawler.generation.types import PlacedRoom, RoomAnchor
from dungeon_crawler.models.room_template import RoomTemplate


def assign_room_templates(
    anchors: list[RoomAnchor],
    pools: TemplatePools,
    rng: random.Random,
    *,
    map_width: int,
    map_height: int,
) -> list[PlacedRoom]:
    """Pick one template per anchor while avoiding overlap and map overflow."""
    placed: list[PlacedRoom] = []
    occupied_rects: list[Rect] = []

    # Place fixed-size roles first so large normal templates keep free space.
    order = sorted(
        range(len(anchors)),
        key=lambda idx: 0 if anchors[idx].role.value == "start" else 1 if anchors[idx].role.value == "stair" else 2,
    )

    for room_id in order:
        anchor = anchors[room_id]
        pool = pools.for_role(anchor.role.value)
        template = _pick_fitting_template(
            anchor,
            pool,
            occupied_rects,
            rng,
            map_width=map_width,
            map_height=map_height,
        )
        occupied_rects.append(template_rect(anchor.meta_col, anchor.meta_row, template))
        placed.append(PlacedRoom(room_id=room_id, anchor=anchor, template=template))

    placed.sort(key=lambda room: room.room_id)
    return placed


def _pick_fitting_template(
    anchor: RoomAnchor,
    templates: tuple[RoomTemplate, ...],
    occupied_rects: list[Rect],
    rng: random.Random,
    *,
    map_width: int,
    map_height: int,
) -> RoomTemplate:
    candidates = list(templates)
    rng.shuffle(candidates)
    candidates.sort(key=lambda template: template.width * template.height, reverse=True)

    for template in candidates:
        rect = template_rect(anchor.meta_col, anchor.meta_row, template)
        if not rect_in_map(rect, map_width=map_width, map_height=map_height):
            continue
        if any(rects_overlap(rect, other) for other in occupied_rects):
            continue
        return template

    raise RuntimeError(
        f"No fitting template for {anchor.role.value} room at meta ({anchor.meta_col}, {anchor.meta_row})"
    )
