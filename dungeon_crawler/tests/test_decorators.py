from __future__ import annotations

import unittest

from dungeon_crawler.utils.decorators import validate_action


class DecoratorsTest(unittest.TestCase):
    def test_validate_action_returns_result_on_success(self) -> None:
        @validate_action
        def ok() -> str:
            return "done"

        self.assertEqual(ok(), "done")

    def test_validate_action_returns_false_on_known_errors(self) -> None:
        @validate_action
        def fail() -> bool:
            raise ValueError("invalid")

        self.assertFalse(fail())


if __name__ == "__main__":
    unittest.main()

