from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Most terminals render game emojis as double-width cells.
TILE_DISPLAY_WIDTH = 2


@dataclass(frozen=True)
class Viewport:
    x0: int
    y0: int
    width: int
    height: int


class Renderer:
    WALL = "🟫"
    FLOOR = "⬛"
    PLAYER = "🧙"

    @staticmethod
    def compute_viewport_size(
        cols: int,
        rows: int,
        *,
        map_width: int | None = None,
        map_height: int | None = None,
        tile_width: int = TILE_DISPLAY_WIDTH,
    ) -> tuple[int, int]:
        """
        Derive how many map tiles fit on screen.

        Each tile emoji occupies `tile_width` terminal columns, so the tile
        count must be smaller than the raw character budget.
        """
        map_panel_cols = max(20, (cols * 2) // 3 - 4)
        tile_cols = max(10, map_panel_cols // tile_width - 1)
        tile_rows = max(8, rows - 6)

        if map_width is not None:
            tile_cols = min(tile_cols, map_width)
        if map_height is not None:
            tile_rows = min(tile_rows, map_height)
        return tile_cols, tile_rows

    @staticmethod
    def compute_viewport(
        map_width: int,
        map_height: int,
        player_pos: tuple[int, int],
        viewport_width: int,
        viewport_height: int,
    ) -> Viewport:
        """
        Player-centered camera window clamped to map bounds.
        """
        width = min(viewport_width, map_width)
        height = min(viewport_height, map_height)
        px, py = player_pos

        x0 = px - width // 2
        y0 = py - height // 2

        if map_width > width:
            x0 = max(0, min(x0, map_width - width))
        else:
            x0 = 0

        if map_height > height:
            y0 = max(0, min(y0, map_height - height))
        else:
            y0 = 0

        return Viewport(x0=x0, y0=y0, width=width, height=height)

    @staticmethod
    def render_viewport(
        grid: list[list[str]],
        player_pos: tuple[int, int],
        viewport: Viewport,
    ) -> str:
        rows: list[str] = []
        px, py = player_pos
        map_height = len(grid)
        map_width = len(grid[0]) if grid else 0

        for y in range(viewport.y0, min(map_height, viewport.y0 + viewport.height)):
            chars: list[str] = []
            for x in range(viewport.x0, min(map_width, viewport.x0 + viewport.width)):
                if (x, y) == (px, py):
                    chars.append(Renderer.PLAYER)
                else:
                    chars.append(grid[y][x])
            rows.append("".join(chars))
        return "\n".join(rows)

    @staticmethod
    def render_scrolled_map(
        grid: list[list[str]],
        player_pos: tuple[int, int],
        *,
        map_width: int,
        map_height: int,
        terminal_cols: int,
        terminal_rows: int,
    ) -> tuple[str, Viewport]:
        """
        Build a player-centered scrolled map view that fits the terminal.
        """
        viewport_width, viewport_height = Renderer.compute_viewport_size(
            terminal_cols,
            terminal_rows,
            map_width=map_width,
            map_height=map_height,
        )
        viewport = Renderer.compute_viewport(
            map_width=map_width,
            map_height=map_height,
            player_pos=player_pos,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
        )
        map_text = Renderer.render_viewport(grid, player_pos=player_pos, viewport=viewport)
        return map_text, viewport

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
