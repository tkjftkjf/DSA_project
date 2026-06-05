from __future__ import annotations

from dataclasses import dataclass

from dungeon_crawler.models.room_template import RoomTemplate, RoomTemplateLoader, start_templates_only


@dataclass(frozen=True)
class TemplatePools:
    start: tuple[RoomTemplate, ...]
    stair: tuple[RoomTemplate, ...]
    normal: tuple[RoomTemplate, ...]

    @classmethod
    def load(cls, loader: RoomTemplateLoader) -> TemplatePools:
        start = tuple(start_templates_only(loader.load_all("start")))
        stair = tuple(loader.load_all("stair"))
        normal = tuple(loader.load_all("normal"))
        if not stair:
            raise RuntimeError("No stair room templates found")
        if not normal:
            raise RuntimeError("No normal room templates found")
        return cls(start=start, stair=stair, normal=normal)

    def for_role(self, role: str) -> tuple[RoomTemplate, ...]:
        if role == "start":
            return self.start
        if role == "stair":
            return self.stair
        if role == "normal":
            return self.normal
        raise ValueError(f"unknown room role: {role}")
