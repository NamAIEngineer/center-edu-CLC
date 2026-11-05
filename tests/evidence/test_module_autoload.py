"""Focused checks for the coordinator module loading seams."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app as app_module
from app import CenterEduService


class ModuleAutoloadTests(unittest.TestCase):
    def setUp(self) -> None:
        self._old_rich = os.environ.get("CENTER_EDU_RICH_DEMO")
        os.environ.pop("CENTER_EDU_RICH_DEMO", None)
        self.tmp = tempfile.TemporaryDirectory()
        self.service = CenterEduService(Path(self.tmp.name) / "autoload.sqlite3")

    def tearDown(self) -> None:
        self.service.close()
        self.tmp.cleanup()
        if self._old_rich is None:
            os.environ.pop("CENTER_EDU_RICH_DEMO", None)
        else:
            os.environ["CENTER_EDU_RICH_DEMO"] = self._old_rich

    def test_frontend_manifest_is_allowlisted_and_stable(self) -> None:
        names = self.service.frontend_module_names()
        self.assertGreaterEqual(len(names), 20)
        self.assertEqual(names, sorted(names))
        self.assertTrue(all(name.endswith(".js") and "/" not in name for name in names))

    def test_one_broken_optional_module_does_not_stop_loader(self) -> None:
        original = app_module.importlib.import_module

        def import_or_fail(name: str):
            if name == "modules.crm_domain":
                raise RuntimeError("synthetic optional failure")
            return original(name)

        with patch.object(app_module.importlib, "import_module", side_effect=import_or_fail):
            self.service._autoload_modules()

        self.assertIn("crm_domain", self.service.module_load_errors)
        self.assertEqual(self.service.module_registry["crm_domain"]["status"], "LOAD_ERROR")
        self.assertIn("finance_bill", self.service.module_registry)


if __name__ == "__main__":
    unittest.main()
