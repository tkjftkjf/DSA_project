from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from dungeon_crawler.models.room_template import RoomTemplate


class RoomRole(str, Enum):
    START = "start"
    STAIR = "stair"
    NORMAL = "normal"


@dataclass(frozen=True)
class RoomAnchor:
    """Top-left world tile where a room template is placed."""
    x: int
    y: int
    role: RoomRole


@dataclass(frozen=True)
class PlacedRoom:
    room_id: int
    anchor: RoomAnchor
    template: RoomTemplate


@dataclass
class RoomStamp:
    room_id: int
    floor_tiles: set[tuple[int, int]] = field(default_factory=set)
    blocked_tiles: set[tuple[int, int]] = field(default_factory=set)
    stair_tiles: set[tuple[int, int]] = field(default_factory=set)
    enemy_spawn_tiles: list[tuple[int, int]] = field(default_factory=list)
    item_spawn_tiles: list[tuple[int, int]] = field(default_factory=list)
    start_spawn: tuple[int, int] | None = None
