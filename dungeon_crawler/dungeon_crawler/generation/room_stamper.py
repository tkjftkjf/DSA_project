from __future__ import annotations

from dungeon_crawler.generation.types import PlacedRoom, RoomRole, RoomStamp


def stamp_room(
    placed: PlacedRoom,
    *,
    map_width: int,
    map_height: int,
) -> RoomStamp:
    """Rasterize one template onto world coordinates."""
    anchor = placed.anchor
    template = placed.template
    stamp = RoomStamp(room_id=placed.room_id)

    origin_x = anchor.x
    origin_y = anchor.y

    for ty in range(template.height):
        for tx in range(template.width):
            wx = origin_x + tx
            wy = origin_y + ty
            if not (0 <= wx < map_width and 0 <= wy < map_height):
                continue

            value = template.tile_at(tx, ty)
            pos = (wx, wy)
            if value == 0:
                stamp.floor_tiles.add(pos)
            elif value == 1:
                stamp.blocked_tiles.add(pos)
            elif value == 2:
                stamp.floor_tiles.add(pos)
                stamp.stair_tiles.add(pos)
            elif value == 3:
                stamp.floor_tiles.add(pos)
                stamp.enemy_spawn_tiles.append(pos)
            elif value == 4:
                stamp.floor_tiles.add(pos)
                stamp.item_spawn_tiles.append(pos)

    if anchor.role == RoomRole.START:
        floors = sorted(stamp.floor_tiles)
        stamp.start_spawn = floors[len(floors) // 2] if floors else (origin_x + 2, origin_y + 2)

    return stamp
