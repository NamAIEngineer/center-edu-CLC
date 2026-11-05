"""Regression proof for explicit blank class-name rejection.

This test exercises the coordinator-owned API seam and the training wire
normalizer without starting a listener or touching any preserved database.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app import AppError, CenterEduService
from modules.training_routes import class_workflow_payload


class EmptyClassNameCorrectionTests(unittest.TestCase):
    def test_class_search_matches_persisted_name(self) -> None:
        with tempfile.TemporaryDirectory(prefix="center-edu-name-search-") as root:
            service = CenterEduService(Path(root) / "center.sqlite3")
            try:
                actor = service.db.execute(
                    "SELECT * FROM users WHERE username='admin'"
                ).fetchone()
                course = service.db.execute(
                    "SELECT id FROM courses ORDER BY id LIMIT 1"
                ).fetchone()
                created = service.create_class_workflow(
                    actor,
                    {
                        "course_id": course["id"],
                        "code": "NAME-SEARCH-01",
                        "name": "Lớp tìm theo tên",
                        "sessions": [],
                        "student_ids": [],
                    },
                )
                rows = service.classes(actor, query="tìm theo tên")
                self.assertIn(created["class"]["id"], {row["id"] for row in rows})
            finally:
                service.close()

    def test_explicit_blank_name_is_rejected_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="center-edu-empty-name-") as root:
            service = CenterEduService(Path(root) / "center.sqlite3")
            try:
                actor = service.db.execute(
                    "SELECT * FROM users WHERE username='admin'"
                ).fetchone()
                course = service.db.execute(
                    "SELECT id FROM courses ORDER BY id LIMIT 1"
                ).fetchone()
                before = service.db.execute(
                    "SELECT COUNT(*) AS n FROM classes"
                ).fetchone()["n"]
                with self.assertRaisesRegex(AppError, "Tên lớp là bắt buộc"):
                    service.create_class_workflow(
                        actor,
                        {
                            "course_id": course["id"],
                            "code": "EMPTY-NAME-API",
                            "name": "   ",
                            "sessions": [],
                            "student_ids": [],
                        },
                    )
                after = service.db.execute(
                    "SELECT COUNT(*) AS n FROM classes"
                ).fetchone()["n"]
                self.assertEqual(before, after)
            finally:
                service.close()

    def test_wire_rejects_explicit_blank_fullname_but_keeps_omitted_partial_contract(self) -> None:
        with self.assertRaisesRegex(ValueError, "Tên lớp là bắt buộc"):
            class_workflow_payload(
                {
                    "course_id": 1,
                    "code": "EMPTY-NAME-WIRE",
                    "fullname": "   ",
                    "sessions": [],
                    "student_ids": [],
                }
            )
        payload = class_workflow_payload(
            {
                "course_id": 1,
                "code": "OMITTED-NAME-WIRE",
                "sessions": [],
                "student_ids": [],
            }
        )
        self.assertNotIn("name", payload)


if __name__ == "__main__":
    unittest.main()
