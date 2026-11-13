"""Admin-only production bootstrap contract on disposable SQLite databases."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import CenterEduService, password_matches


class ProductionBootstrapTests(unittest.TestCase):
    def test_empty_production_db_creates_only_admin_and_needs_explicit_password(self) -> None:
        with tempfile.TemporaryDirectory(prefix="center-edu-production-") as root:
            db_path = Path(root) / "center.sqlite3"
            with patch.dict(os.environ, {"CENTER_EDU_ADMIN_PASSWORD": "R17-only-password"}, clear=False):
                service = CenterEduService(db_path, production=True)
            try:
                users = service.db.execute("SELECT username,role,password_hash FROM users").fetchall()
                self.assertEqual([(row[0], row[1]) for row in users], [("admin", "ADMIN")])
                self.assertTrue(password_matches("R17-only-password", users[0][2]))
                for table in ("students", "courses", "classes", "classrooms", "enrollments", "timetable_sessions", "generated_screen_records", "bm_branches"):
                    self.assertEqual(service.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], 0, table)
                self.assertEqual(service.db.execute("SELECT COUNT(*) FROM bm_tenants").fetchone()[0], 1)
                self.assertEqual(service.db.execute("SELECT name FROM bm_tenants").fetchone()[0], "Center EDU")
            finally:
                service.close()

            # Restarting a populated production DB is idempotent and does not
            # require the original secret again.
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("CENTER_EDU_ADMIN_PASSWORD", None)
                reopened = CenterEduService(db_path, production=True)
            try:
                self.assertEqual(reopened.db.execute("SELECT COUNT(*) FROM users").fetchone()[0], 1)
                self.assertEqual(reopened.db.execute("SELECT username FROM users").fetchone()[0], "admin")
            finally:
                reopened.close()

    def test_production_rich_demo_flag_cannot_seed_rows(self) -> None:
        with tempfile.TemporaryDirectory(prefix="center-edu-production-rich-") as root:
            with patch.dict(os.environ, {"CENTER_EDU_RICH_DEMO": "1", "CENTER_EDU_ADMIN_PASSWORD": "R17-only-password"}, clear=False):
                service = CenterEduService(Path(root) / "center.sqlite3", production=True)
            try:
                self.assertEqual(service.db.execute("SELECT COUNT(*) FROM users").fetchone()[0], 1)
                self.assertEqual(service.db.execute("SELECT COUNT(*) FROM generated_screen_records").fetchone()[0], 0)
                self.assertEqual(service.db.execute("SELECT COUNT(*) FROM finance_bills").fetchone()[0], 0)
            finally:
                service.close()

    def test_empty_production_db_without_password_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="center-edu-production-required-") as root:
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("CENTER_EDU_ADMIN_PASSWORD", None)
                os.environ.pop("CENTER_EDU_ADMIN_PASSWORD_FILE", None)
                with self.assertRaisesRegex(RuntimeError, "requires"):
                    CenterEduService(Path(root) / "center.sqlite3", production=True)

    def test_password_file_source_and_existing_rows_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory(prefix="center-edu-production-file-") as root:
            db_path = Path(root) / "center.sqlite3"
            password_file = Path(root) / "admin-password"
            password_file.write_text("R17-file-password\n", encoding="utf-8")
            with patch.dict(os.environ, {"CENTER_EDU_ADMIN_PASSWORD_FILE": str(password_file)}, clear=False):
                os.environ.pop("CENTER_EDU_ADMIN_PASSWORD", None)
                service = CenterEduService(db_path, production=True)
            try:
                admin_id = service.db.execute("SELECT id FROM users WHERE username='admin'").fetchone()[0]
                service.db.execute("UPDATE users SET full_name=? WHERE id=?", ("Owner-preserved", admin_id))
                service.db.commit()
            finally:
                service.close()
            password_file.unlink()
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("CENTER_EDU_ADMIN_PASSWORD", None)
                os.environ.pop("CENTER_EDU_ADMIN_PASSWORD_FILE", None)
                reopened = CenterEduService(db_path, production=True)
            try:
                row = reopened.db.execute("SELECT full_name FROM users WHERE id=?", (admin_id,)).fetchone()
                self.assertEqual(row[0], "Owner-preserved")
            finally:
                reopened.close()


if __name__ == "__main__":
    unittest.main()
