from __future__ import annotations

import unittest

from dungeon_crawler.engine.input_handler import InputHandler


class InputHandlerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.handler = InputHandler()

    def test_move_keys(self) -> None:
        self.assertEqual(self.handler.parse_key("w").kind, "move")  # type: ignore[union-attr]
        self.assertEqual(self.handler.parse_key("a").payload, (-1, 0))  # type: ignore[union-attr]

    def test_undo_redo_keys(self) -> None:
        self.assertEqual(self.handler.parse_key("u").kind, "undo")  # type: ignore[union-attr]
        self.assertEqual(self.handler.parse_key("r").kind, "redo")  # type: ignore[union-attr]

    def test_slot_key(self) -> None:
        cmd = self.handler.parse_key("3")
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.kind, "use_slot")
        self.assertEqual(cmd.payload, "3")

    def test_unknown_key_returns_none(self) -> None:
        self.assertIsNone(self.handler.parse_key("x"))


if __name__ == "__main__":
    unittest.main()

