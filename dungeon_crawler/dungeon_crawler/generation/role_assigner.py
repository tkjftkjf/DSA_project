from __future__ import annotations

from dungeon_crawler.generation.geometry import manhattan
from dungeon_crawler.generation.types import RoomAnchor, RoomRole

MetaCell = tuple[int, int]


def assign_room_anchors(
    meta_cells: set[MetaCell],
    *,
    room_count: int,
) -> list[RoomAnchor]:
    """Assign one start, one stair, and the rest as normal rooms."""
    cells = sorted(meta_cells)
    start_cell = min(cells, key=lambda cell: (cell[1], cell[0]))
    stair_cell = max(cells, key=lambda cell: manhattan(cell, start_cell))
    if stair_cell == start_cell:
        stair_cell = max(
            (cell for cell in cells if cell != start_cell),
            key=lambda cell: manhattan(cell, start_cell),
        )

    reserved = {start_cell, stair_cell}
    normal_cells = [cell for cell in cells if cell not in reserved]

    anchors: list[RoomAnchor] = [
        RoomAnchor(meta_col=start_cell[0], meta_row=start_cell[1], role=RoomRole.START),
        RoomAnchor(meta_col=stair_cell[0], meta_row=stair_cell[1], role=RoomRole.STAIR),
    ]
    for col, row in normal_cells[: room_count - 2]:
        anchors.append(RoomAnchor(meta_col=col, meta_row=row, role=RoomRole.NORMAL))

    if len(anchors) < room_count:
        raise RuntimeError("Failed to build required room anchors")

    return anchors[:room_count]
