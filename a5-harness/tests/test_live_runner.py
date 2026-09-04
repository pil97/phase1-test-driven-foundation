from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from a5_harness.live_runner import _render


class LiveRunnerSupportTest(unittest.TestCase):
    def test_render_replaces_all_placeholders(self) -> None:
        result = _render("A={{A}} B={{B}}", A="one", B="two")
        self.assertEqual("A=one B=two", result)

    def test_render_rejects_unresolved_placeholder(self) -> None:
        with self.assertRaises(ValueError):
            _render("A={{A}} B={{B}}", A="one")


if __name__ == "__main__":
    unittest.main()
