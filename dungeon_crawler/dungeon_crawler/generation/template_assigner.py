from __future__ import annotations

import random

from dungeon_crawler.generation.geometry import Rect, rect_in_map, rects_overlap, template_rect
from dungeon_crawler.generation.template_pools import TemplatePools
from dungeon_crawler.generation.types import PlacedRoom, RoomAnchor, RoomRole
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

    normal_anchors = [anchor for anchor in anchors if anchor.role == RoomRole.NORMAL]
    normal_plan = _build_normal_template_plan(normal_anchors, pools.normal, rng)
    if len(normal_anchors) != len(normal_plan):
        raise RuntimeError("Normal room plan size mismatch")
    normal_plan_by_anchor = dict(zip(normal_anchors, normal_plan))

    order = sorted(
        range(len(anchors)),
        key=lambda idx: 0 if anchors[idx].role.value == "start" else 1 if anchors[idx].role.value == "stair" else 2,
    )

    for room_id in order:
        anchor = anchors[room_id]
        pool = pools.for_role(anchor.role.value)
        preferred = normal_plan_by_anchor.get(anchor)
        fitted_anchor, template = _pick_fitting_placement(
            anchor,
            pool,
            occupied_rects,
            rng,
            map_width=map_width,
            map_height=map_height,
            preferred=preferred,
        )
        occupied_rects.append(template_rect(fitted_anchor.x, fitted_anchor.y, template))
        placed.append(PlacedRoom(room_id=room_id, anchor=fitted_anchor, template=template))

    placed.sort(key=lambda room: room.room_id)
    return placed


def _build_normal_template_plan(
    normal_anchors: list[RoomAnchor],
    templates: tuple[RoomTemplate, ...],
    rng: random.Random,
) -> list[RoomTemplate]:
    """When there are enough normal slots, place every normal template once."""
    if not normal_anchors:
        return []

    all_templates = list(templates)
    if len(normal_anchors) >= len(all_templates):
        plan = list(all_templates)
        rng.shuffle(plan)
        while len(plan) < len(normal_anchors):
            plan.append(rng.choice(all_templates))
        return plan

    return [rng.choice(all_templates) for _ in normal_anchors]


def _pick_fitting_placement(
    anchor: RoomAnchor,
    templates: tuple[RoomTemplate, ...],
    occupied_rects: list[Rect],
    rng: random.Random,
    *,
    map_width: int,
    map_height: int,
    preferred: RoomTemplate | None = None,
) -> tuple[RoomAnchor, RoomTemplate]:
    offsets = _candidate_offsets(anchor.role)
    rng.shuffle(offsets)

    if preferred is not None:
        fallbacks = [template for template in templates if template.name != preferred.name]
        rng.shuffle(fallbacks)
        template_order = [preferred, *fallbacks]
    else:
        template_order = list(templates)
        rng.shuffle(template_order)

    options: list[tuple[RoomAnchor, RoomTemplate]] = []
    for dx, dy in offsets:
        shifted = RoomAnchor(x=anchor.x + dx, y=anchor.y + dy, role=anchor.role)
        for template in template_order:
            rect = template_rect(shifted.x, shifted.y, template)
            if not rect_in_map(rect, map_width=map_width, map_height=map_height):
                continue
            if any(rects_overlap(rect, other) for other in occupied_rects):
                continue
            options.append((shifted, template))

    if not options:
        raise RuntimeError(
            f"No fitting template for {anchor.role.value} room near ({anchor.x}, {anchor.y})"
        )

    if preferred is not None:
        preferred_options = [option for option in options if option[1].name == preferred.name]
        if preferred_options:
            return rng.choice(preferred_options)
    return rng.choice(options)


def _candidate_offsets(role: RoomRole) -> list[tuple[int, int]]:
    if role == RoomRole.NORMAL:
        deltas = [0, 4, -4, 8, -8, 12, -12]
        return [(0, 0)] + [(dx, dy) for dx in deltas for dy in deltas if dx or dy]
    return [(0, 0)]
