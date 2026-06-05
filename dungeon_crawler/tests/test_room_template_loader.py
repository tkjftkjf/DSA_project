from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dungeon_crawler.models.room_template import (
    CELL_SIZE,
    RoomTemplateLoader,
    find_connection_offsets,
)


class RoomTemplateLoaderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.loader = RoomTemplateLoader()

    def test_loads_normal_templates_from_disk(self) -> None:
        templates = self.loader.load_all("normal")
        self.assertGreaterEqual(len(templates), 1)
        for template in templates:
            self.assertEqual(template.room_type, "normal")
            self.assertEqual(template.width % CELL_SIZE, 0)
            self.assertEqual(template.height % CELL_SIZE, 0)

    def test_parses_tile_kinds(self) -> None:
        template = self.loader.load("normal", "2")
        self.assertIn((1, 4), template.enemy_spawns())
        self.assertTrue(template.walls())

    def test_rejects_invalid_width(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "rooms"
            (base / "x").mkdir(parents=True)
            (base / "x" / "bad.txt").write_text("000\n000\n", encoding="utf-8")
            loader = RoomTemplateLoader(base_dir=base)
            with self.assertRaises(ValueError):
                loader.load("x", "bad")

    def test_edge_openings_on_inner_perimeter_wall(self) -> None:
        template = self.loader.load("start", "4")
        north = template.edge_openings("north")
        self.assertIn(2, north)
        self.assertNotIn(0, north)
        self.assertNotIn(4, north)

    def test_find_connection_offsets_requires_both_zero(self) -> None:
        left = self.loader.load("start", "1")
        right = self.loader.load("normal", "0")
        offsets = find_connection_offsets(left, right, "east")
        self.assertEqual(offsets, [0, 1, 2, 3, 4])
        for offset in offsets:
            self.assertEqual(left.cells[offset][left.width - 1], 0)
            self.assertEqual(right.cells[offset][0], 0)


if __name__ == "__main__":
    unittest.main()
