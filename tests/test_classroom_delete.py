"""Disposable UI/API contract for setup/classroom delete."""
from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from app import create_server
from test_app import ApiClient, TEST_PASSWORD


class ClassroomDeleteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.server = create_server(Path(self.tmp.name) / "classroom-delete.sqlite3", "127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.admin = ApiClient(self.server)
        status, payload = self.admin.request("POST", "/api/auth/login", {"login": "admin", "password": TEST_PASSWORD})
        self.assertEqual(status, 200, payload)

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.server.service.close()
        self.tmp.cleanup()

    def _create(self, code: str) -> int:
        status, payload = self.admin.request("POST", "/api/classrooms", {
            "code": code, "name": f"QA {code}", "capacity": 10, "description": "QA disposable",
        })
        self.assertEqual(status, 201, payload)
        return int(payload["data"]["id"])

    def test_unlinked_labelled_fixture_deletes_and_missing_is_json_404(self) -> None:
        classroom_id = self._create("TEST_CLASSROOM_DELETE")
        status, payload = self.admin.request("DELETE", f"/api/classrooms/{classroom_id}")
        self.assertEqual(status, 200, payload)
        self.assertTrue(payload["data"]["deleted"])
        status, payload = self.admin.request("GET", f"/api/classrooms/{classroom_id}")
        self.assertEqual(status, 404, payload)
        status, payload = self.admin.request("DELETE", f"/api/classrooms/{classroom_id}")
        self.assertEqual(status, 404, payload)

    def test_linked_fixture_is_retained_and_delete_is_409(self) -> None:
        classroom_id = self._create("TEST_CLASSROOM_LINKED")
        db = self.server.service.db
        course_id = db.execute("SELECT id FROM courses WHERE active=1 ORDER BY id LIMIT 1").fetchone()[0]
        db.execute("INSERT INTO classes(course_id,code,name,room,status) VALUES(?,?,?,?,?)", (
            course_id, "TEST_CLASSROOM_LINKED_CLASS", "QA linked class", "TEST_CLASSROOM_LINKED", "OPEN",
        ))
        db.commit()
        status, payload = self.admin.request("DELETE", f"/api/classrooms/{classroom_id}")
        self.assertEqual(status, 409, payload)
        self.assertEqual(payload["error"]["code"], "CLASSROOM_IN_USE")
        status, payload = self.admin.request("GET", f"/api/classrooms/{classroom_id}")
        self.assertEqual(status, 200, payload)
        self.assertEqual(payload["data"]["code"], "TEST_CLASSROOM_LINKED")

    def test_linked_room_match_is_case_and_trim_insensitive_for_class_and_session(self) -> None:
        classroom_id = self._create("Room A1")
        db = self.server.service.db
        course_id = db.execute("SELECT id FROM courses WHERE active=1 ORDER BY id LIMIT 1").fetchone()[0]
        teacher_id = db.execute("SELECT id FROM users WHERE role='TEACHER' ORDER BY id LIMIT 1").fetchone()[0]
        class_row = db.execute(
            "INSERT INTO classes(course_id,code,name,room,status) VALUES(?,?,?,?,?) RETURNING id",
            (course_id, "TEST_ROOM_CASE_CLASS", "QA case linked class", "  room a1  ", "OPEN"),
        ).fetchone()
        db.execute(
            "INSERT INTO timetable_sessions(class_id,session_date,start_time,end_time,room,teacher_id) VALUES(?,?,?,?,?,?)",
            (class_row[0], "2026-11-14", "18:30", "20:00", " ROOM A1 ", teacher_id),
        )
        db.commit()
        status, payload = self.admin.request("DELETE", f"/api/classrooms/{classroom_id}")
        self.assertEqual(status, 409, payload)
        self.assertEqual(payload["error"]["code"], "CLASSROOM_IN_USE")
        self.assertIsNotNone(db.execute("SELECT 1 FROM classrooms WHERE id=?", (classroom_id,)).fetchone())

    def test_anonymous_delete_is_auth_required(self) -> None:
        anonymous = ApiClient(self.server)
        status, payload = anonymous.request("DELETE", "/api/classrooms/1")
        self.assertEqual(status, 401, payload)
        self.assertEqual(payload["error"]["code"], "AUTH_REQUIRED")


if __name__ == "__main__":
    unittest.main()
