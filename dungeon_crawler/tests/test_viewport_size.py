from __future__ import annotations

import unittest

from dungeon_crawler.ui.renderer import Renderer, TILE_DISPLAY_WIDTH


class ViewportSizeTest(unittest.TestCase):
    def test_larger_terminal_yields_larger_viewport(self) -> None:
        small = Renderer.compute_viewport_size(80, 24, map_width=80, map_height=45)
        large = Renderer.compute_viewport_size(200, 50, map_width=80, map_height=45)
        self.assertGreater(large[0], small[0])
        self.assertGreater(large[1], small[1])

    def test_minimum_viewport(self) -> None:
        width, height = Renderer.compute_viewport_size(40, 10, map_width=80, map_height=45)
        self.assertGreaterEqual(width, 10)
        self.assertGreaterEqual(height, 8)

    def test_viewport_clamped_to_map_dimensions(self) -> None:
        width, height = Renderer.compute_viewport_size(300, 80, map_width=80, map_height=45)
        self.assertLessEqual(width, 80)
        self.assertLessEqual(height, 45)

    def test_emoji_width_reduces_tile_count(self) -> None:
        without_emoji = Renderer.compute_viewport_size(120, 40, tile_width=1)
        with_emoji = Renderer.compute_viewport_size(120, 40, tile_width=TILE_DISPLAY_WIDTH)
        self.assertLess(with_emoji[0], without_emoji[0])


if __name__ == "__main__":
    unittest.main()
