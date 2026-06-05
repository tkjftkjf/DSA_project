from __future__ import annotations

import random

from dungeon_crawler.models.room_template import META_COLS, META_ROWS

MetaCell = tuple[int, int]


def scatter_anchors(
    rng: random.Random,
    count: int,
    *,
    min_dist: int = 3,
) -> set[MetaCell]:
    """Pick spread-out meta-grid anchors for room placement."""
    candidates = [(col, row) for col in range(META_COLS) for row in range(META_ROWS)]
    rng.shuffle(candidates)

    picked: list[MetaCell] = []
    for cell in candidates:
        if len(picked) >= count:
            break
        if all(_manhattan(cell, other) >= min_dist for other in picked):
            picked.append(cell)

    if len(picked) >= count:
        return set(picked)

    picked_set = set(picked)
    if not picked_set:
        picked_set.add((META_COLS // 2, META_ROWS // 2))

    while len(picked_set) < count:
        frontier: list[MetaCell] = []
        for mc, mr in picked_set:
            for neighbor in _meta_neighbors(mc, mr):
                if neighbor not in picked_set:
                    frontier.append(neighbor)
        if not frontier:
            break
        picked_set.add(rng.choice(frontier))

    return picked_set


def _meta_neighbors(mc: int, mr: int) -> list[MetaCell]:
    candidates = [(mc + 1, mr), (mc - 1, mr), (mc, mr + 1), (mc, mr - 1)]
    return [(c, r) for c, r in candidates if 0 <= c < META_COLS and 0 <= r < META_ROWS]


def _manhattan(a: MetaCell, b: MetaCell) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
