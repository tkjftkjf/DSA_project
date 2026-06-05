from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Viewport:
    x0: int
    y0: int
    width: int
    height: int


class Renderer:
    WALL = "⬛"
    FLOOR = "🟫"
    PLAYER = "🧙"

    @staticmethod
    def compute_viewport(
        map_width: int,
        map_height: int,
        player_pos: tuple[int, int],
        viewport_width: int,
        viewport_height: int,
    ) -> Viewport:
        px, py = player_pos
        half_w = viewport_width // 2
        half_h = viewport_height // 2

        x0 = max(0, min(px - half_w, max(0, map_width - viewport_width)))
        y0 = max(0, min(py - half_h, max(0, map_height - viewport_height)))
        return Viewport(x0=x0, y0=y0, width=viewport_width, height=viewport_height)

    @staticmethod
    def render_viewport(
        grid: list[list[str]],
        player_pos: tuple[int, int],
        viewport: Viewport,
    ) -> str:
        rows: list[str] = []
        px, py = player_pos
        for y in range(viewport.y0, min(len(grid), viewport.y0 + viewport.height)):
            chars: list[str] = []
            for x in range(viewport.x0, min(len(grid[0]), viewport.x0 + viewport.width)):
                if (x, y) == (px, py):
                    chars.append(Renderer.PLAYER)
                else:
                    chars.append(grid[y][x])
            rows.append("".join(chars))
        return "\n".join(rows)

    @staticmethod
    def build_layout(map_text: str, status_text: str, log_text: str) -> Any:
        from rich.layout import Layout
        from rich.panel import Panel

        layout = Layout()
        layout.split_row(Layout(name="map", ratio=2), Layout(name="right", ratio=1))
        layout["right"].split_column(Layout(name="status", ratio=1), Layout(name="log", ratio=2))

        layout["map"].update(Panel(map_text, title="Map"))
        layout["status"].update(Panel(status_text, title="Status"))
        layout["log"].update(Panel(log_text, title="Log"))
        return layout

