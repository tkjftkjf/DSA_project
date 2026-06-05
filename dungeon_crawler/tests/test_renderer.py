from __future__ import annotations

import unittest

from dungeon_crawler.ui.renderer import Renderer


class RendererTest(unittest.TestCase):
    def test_compute_viewport_centers_player_when_possible(self) -> None:
        vp = Renderer.compute_viewport(
            map_width=20,
            map_height=20,
            player_pos=(10, 10),
            viewport_width=7,
            viewport_height=5,
        )
        self.assertEqual((vp.x0, vp.y0), (7, 8))
        self.assertEqual((vp.width, vp.height), (7, 5))

    def test_compute_viewport_clamps_near_edges(self) -> None:
        vp = Renderer.compute_viewport(
            map_width=20,
            map_height=20,
            player_pos=(1, 1),
            viewport_width=8,
            viewport_height=6,
        )
        self.assertEqual((vp.x0, vp.y0), (0, 0))

    def test_compute_viewport_scrolls_when_player_moves_right(self) -> None:
        vp_left = Renderer.compute_viewport(50, 30, (10, 12), 20, 12)
        vp_right = Renderer.compute_viewport(50, 30, (30, 12), 20, 12)
        self.assertLess(vp_left.x0, vp_right.x0)
        self.assertEqual(vp_left.y0, vp_right.y0)

    def test_compute_viewport_never_exceeds_map_size(self) -> None:
        vp = Renderer.compute_viewport(50, 30, (2, 2), 200, 100)
        self.assertLessEqual(vp.width, 50)
        self.assertLessEqual(vp.height, 30)

    def test_render_viewport_overlays_player(self) -> None:
        grid = [
            ["🟫", "🟫", "🟫"],
            ["🟫", "🟫", "🟫"],
            ["🟫", "🟫", "🟫"],
        ]
        vp = Renderer.compute_viewport(3, 3, (1, 1), 3, 3)
        text = Renderer.render_viewport(grid, player_pos=(1, 1), viewport=vp)
        self.assertIn("🧙", text)

    def test_render_scrolled_map_output_fits_requested_tile_budget(self) -> None:
        grid = [["⬛" for _ in range(50)] for _ in range(30)]
        for y in range(20):
            for x in range(15):
                grid[y][x] = "🟫"
        grid[10][12] = "🧙"

        map_text, viewport = Renderer.render_scrolled_map(
            grid,
            (12, 10),
            map_width=50,
            map_height=30,
            terminal_cols=200,
            terminal_rows=50,
        )
        rendered_rows = map_text.splitlines()
        self.assertLessEqual(len(rendered_rows), viewport.height)
        if rendered_rows:
            self.assertLessEqual(len(rendered_rows[0]), viewport.width)
        self.assertIn("🧙", map_text)


if __name__ == "__main__":
    unittest.main()
