from __future__ import annotations

import unittest

from dungeon_crawler.models.room_template import WORLD_HEIGHT, WORLD_WIDTH
from dungeon_crawler.ui.renderer import INPUT_RESERVE_ROWS, Renderer, TILE_DISPLAY_WIDTH


class ViewportSizeTest(unittest.TestCase):
    def test_layout_height_reserves_input_rows(self) -> None:
        self.assertEqual(Renderer.compute_layout_height(24), 24 - INPUT_RESERVE_ROWS)

    def test_larger_terminal_yields_larger_viewport(self) -> None:
        small = Renderer.compute_viewport_size(
            80, Renderer.compute_layout_height(24), map_width=WORLD_WIDTH, map_height=WORLD_HEIGHT
        )
        large = Renderer.compute_viewport_size(
            200, Renderer.compute_layout_height(50), map_width=WORLD_WIDTH, map_height=WORLD_HEIGHT
        )
        self.assertGreater(large[0], small[0])
        self.assertGreater(large[1], small[1])

    def test_minimum_viewport(self) -> None:
        layout_height = Renderer.compute_layout_height(10)
        width, height = Renderer.compute_viewport_size(40, layout_height, map_width=WORLD_WIDTH, map_height=WORLD_HEIGHT)
        self.assertGreaterEqual(width, 10)
        self.assertGreaterEqual(height, 4)

    def test_viewport_clamped_to_map_dimensions(self) -> None:
        width, height = Renderer.compute_viewport_size(300, 80, map_width=WORLD_WIDTH, map_height=WORLD_HEIGHT)
        self.assertLessEqual(width, WORLD_WIDTH)
        self.assertLessEqual(height, WORLD_HEIGHT)

    def test_emoji_width_reduces_tile_count(self) -> None:
        without_emoji = Renderer.compute_viewport_size(120, 40, tile_width=1)
        with_emoji = Renderer.compute_viewport_size(120, 40, tile_width=TILE_DISPLAY_WIDTH)
        self.assertLess(with_emoji[0], without_emoji[0])


if __name__ == "__main__":
    unittest.main()
