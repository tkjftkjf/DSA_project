from __future__ import annotations

from dungeon_crawler.generation.geometry import manhattan
from dungeon_crawler.generation.types import RoomAnchor, RoomRole

Anchor = tuple[int, int]


def assign_room_anchors(
    anchors: set[Anchor],
    *,
    room_count: int,
) -> list[RoomAnchor]:
    """Assign one start, one stair, and the rest as normal rooms."""
    cells = sorted(anchors)
    start_pos = min(cells, key=lambda cell: (cell[1], cell[0]))
    stair_pos = max(cells, key=lambda cell: manhattan(cell, start_pos))
    if stair_pos == start_pos:
        stair_pos = max(
            (cell for cell in cells if cell != start_pos),
            key=lambda cell: manhattan(cell, start_pos),
        )

    reserved = {start_pos, stair_pos}
    normal_positions = [cell for cell in cells if cell not in reserved]

    room_anchors: list[RoomAnchor] = [
        RoomAnchor(x=start_pos[0], y=start_pos[1], role=RoomRole.START),
        RoomAnchor(x=stair_pos[0], y=stair_pos[1], role=RoomRole.STAIR),
    ]
    for x, y in normal_positions[: room_count - 2]:
        room_anchors.append(RoomAnchor(x=x, y=y, role=RoomRole.NORMAL))

    if len(room_anchors) < room_count:
        raise RuntimeError("Failed to build required room anchors")

    return room_anchors[:room_count]
