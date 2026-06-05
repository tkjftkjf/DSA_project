from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from dungeon_crawler.models.room_template import (
    CELL_SIZE,
    START_TEMPLATE_SIZE,
    RoomTemplateLoader,
    pick_room_template,
    start_templates_only,
    template_world_rect,
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

    def test_loads_start_and_stair_templates(self) -> None:
        self.assertGreaterEqual(len(self.loader.load_all("start")), 1)
        self.assertGreaterEqual(len(self.loader.load_all("stair")), 1)

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

    def test_start_templates_only_accepts_5x5(self) -> None:
        starts = self.loader.load_all("start")
        filtered = start_templates_only(starts)
        self.assertGreaterEqual(len(filtered), 1)
        for template in filtered:
            self.assertEqual(template.width, START_TEMPLATE_SIZE)
            self.assertEqual(template.height, START_TEMPLATE_SIZE)

    def test_pick_room_template_returns_member_of_pool(self) -> None:
        normals = self.loader.load_all("normal")
        picked = pick_room_template(normals, random.Random(0))
        self.assertIn(picked, normals)

    def test_template_world_rect_uses_meta_anchor(self) -> None:
        template = self.loader.load("normal", "0")
        rect = template_world_rect(2, 1, template)
        self.assertEqual(rect, (10, 5, 14, 9))


if __name__ == "__main__":
    unittest.main()
