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

    def test_compute_viewport_clamps_near_edges(self) -> None:
        vp = Renderer.compute_viewport(
            map_width=20,
            map_height=20,
            player_pos=(1, 1),
            viewport_width=8,
            viewport_height=6,
        )
        self.assertEqual((vp.x0, vp.y0), (0, 0))

    def test_render_viewport_overlays_player(self) -> None:
        grid = [
            ["🟫", "🟫", "🟫"],
            ["🟫", "🟫", "🟫"],
            ["🟫", "🟫", "🟫"],
        ]
        vp = Renderer.compute_viewport(3, 3, (1, 1), 3, 3)
        text = Renderer.render_viewport(grid, player_pos=(1, 1), viewport=vp)
        self.assertIn("🧙", text)


if __name__ == "__main__":
    unittest.main()

