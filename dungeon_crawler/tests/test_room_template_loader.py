from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from dungeon_crawler.models.room_template import (
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
            self.assertGreater(template.width, 0)
            self.assertGreater(template.height, 0)

    def test_loads_start_and_stair_templates(self) -> None:
        self.assertGreaterEqual(len(self.loader.load_all("start")), 1)
        self.assertGreaterEqual(len(self.loader.load_all("stair")), 1)

    def test_parses_tile_kinds(self) -> None:
        template = self.loader.load("normal", "2")
        self.assertTrue(template.enemy_spawns())
        self.assertTrue(template.walls())
        self.assertTrue(template.stairs() or template.floors())

    def test_loads_arbitrary_size_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "rooms" / "x"
            base.mkdir(parents=True)
            lines = ["0" * 7 for _ in range(8)]
            (base / "odd.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
            loader = RoomTemplateLoader(base_dir=base.parent)
            template = loader.load("x", "odd")
            self.assertEqual(template.width, 7)
            self.assertEqual(template.height, 8)

    def test_rejects_inconsistent_row_width(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "rooms"
            (base / "x").mkdir(parents=True)
            (base / "x" / "bad.txt").write_text("000\n0000\n", encoding="utf-8")
            loader = RoomTemplateLoader(base_dir=base)
            with self.assertRaises(ValueError):
                loader.load("x", "bad")

    def test_rejects_empty_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "rooms"
            (base / "x").mkdir(parents=True)
            (base / "x" / "bad.txt").write_text("", encoding="utf-8")
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

    def test_template_world_rect_uses_origin(self) -> None:
        template = self.loader.load("normal", "0")
        rect = template_world_rect(12, 7, template)
        self.assertEqual(rect, (12, 7, 12 + template.width - 1, 7 + template.height - 1))


if __name__ == "__main__":
    unittest.main()
