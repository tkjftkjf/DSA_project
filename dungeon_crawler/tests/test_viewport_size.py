from __future__ import annotations

import unittest

from dungeon_crawler.ui.renderer import Renderer


class ViewportSizeTest(unittest.TestCase):
    def test_larger_terminal_yields_larger_viewport(self) -> None:
        small = Renderer.compute_viewport_size(80, 24)
        large = Renderer.compute_viewport_size(200, 50)
        self.assertGreater(large[0], small[0])
        self.assertGreater(large[1], small[1])

    def test_minimum_viewport(self) -> None:
        width, height = Renderer.compute_viewport_size(40, 10)
        self.assertGreaterEqual(width, 20)
        self.assertGreaterEqual(height, 8)


if __name__ == "__main__":
    unittest.main()
