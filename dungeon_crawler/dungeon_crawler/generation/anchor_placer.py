from __future__ import annotations

import random

from dungeon_crawler.generation.geometry import manhattan

Anchor = tuple[int, int]


def scatter_anchors(
    rng: random.Random,
    count: int,
    *,
    map_width: int,
    map_height: int,
    min_spacing: int = 15,
    step: int = 4,
    max_room_width: int = 1,
    max_room_height: int = 1,
) -> set[Anchor]:
    """Pick spread-out world-tile origins for room placement."""
    max_x = map_width - max_room_width
    max_y = map_height - max_room_height
    if max_x < 0 or max_y < 0:
        raise RuntimeError("Map is too small for the largest room template")

    candidates = [(x, y) for x in range(0, max_x + 1, step) for y in range(0, max_y + 1, step)]
    rng.shuffle(candidates)

    picked: list[Anchor] = []
    for pos in candidates:
        if len(picked) >= count:
            break
        if all(manhattan(pos, other) >= min_spacing for other in picked):
            picked.append(pos)

    if len(picked) >= count:
        return set(picked)

    picked_set = set(picked)
    if not picked_set:
        picked_set.add((max_x // 2, max_y // 2))

    while len(picked_set) < count:
        frontier: list[Anchor] = []
        for ax, ay in picked_set:
            for dx, dy in ((step, 0), (-step, 0), (0, step), (0, -step)):
                neighbor = (ax + dx, ay + dy)
                if 0 <= neighbor[0] <= max_x and 0 <= neighbor[1] <= max_y:
                    if neighbor not in picked_set:
                        frontier.append(neighbor)
        if not frontier:
            break
        picked_set.add(rng.choice(frontier))

    return picked_set
