"""R19c K1 class lifecycle contract on a disposable runtime."""
from __future__ import annotations

import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app import create_server, password_hash
from test_app import ApiClient, TEST_PASSWORD


class R19cClassManagementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="center-edu-r19c-class-")
        self.server = create_server(Path(self.tmp.name) / "center.sqlite3", "127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.admin = ApiClient(self.server)
        self.assertEqual(self.admin.request("POST", "/api/auth/login", {"login": "admin", "password": TEST_PASSWORD})[0], 200)

    def tearDown(self) -> None:
        self.server.shutdown(); self.server.server_close(); self.server.service.close(); self.tmp.cleanup()

    def _class(self, code: str):
        course_id = self.admin.request("GET", "/api/courses")[1]["data"][0]["id"]
        status, payload = self.admin.request("POST", "/api/classes", {
            "course_id": course_id, "code": code, "name": "TEST K1 class", "status": "OPEN",
            "start_date": "2026-11-13", "end_date": "2026-12-13",
        })
        self.assertEqual(status, 201, payload)
        return payload["data"]

    def test_close_requires_date_token_audits_and_survives_restart(self) -> None:
        row = self._class("TEST-R19C-CLOSE")
        status, payload = self.admin.request("POST", f"/api/classes/{row['id']}/close", {"apply_from": "2026-11-20"})
        self.assertEqual(status, 428, payload)
        status, payload = self.admin.request("POST", f"/api/classes/{row['id']}/close", {
            "apply_from": "2026-11-20", "version": row["version"], "updated_at": row["updated_at"],
        })
        self.assertEqual(status, 200, payload)
        self.assertEqual(payload["data"]["status"], "COMPLETED")
        self.assertEqual(payload["data"]["status_apply_from"], "2026-11-20")
        audits = self.server.service.db.execute("SELECT action,entity,entity_id FROM audit_events WHERE entity='class' AND entity_id=? ORDER BY id DESC LIMIT 1", (row["id"],)).fetchone()
        self.assertEqual(tuple(audits), ("CLOSE", "class", str(row["id"])))
        db_path = Path(self.tmp.name) / "center.sqlite3"
        self.server.shutdown(); self.server.server_close(); self.server.service.close()
        reopened = create_server(db_path, "127.0.0.1", 0)
        reopened_thread = threading.Thread(target=reopened.serve_forever, daemon=True)
        reopened_thread.start()
        try:
            client = ApiClient(reopened)
            self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": TEST_PASSWORD})[0], 200)
            status, reloaded = client.request("GET", f"/api/classes/{row['id']}")
            self.assertEqual(status, 200, reloaded)
            self.assertEqual(reloaded["data"]["status"], "COMPLETED")
            self.assertEqual(reloaded["data"]["status_apply_from"], "2026-11-20")
        finally:
            reopened.shutdown(); reopened.server_close(); reopened.service.close()

    def test_cancel_stale_token_conflicts_and_modal_is_read_only(self) -> None:
        row = self._class("TEST-R19C-CANCEL")
        stale = {"apply_from": "2026-11-21", "version": row["version"], "updated_at": row["updated_at"]}
        status, _ = self.admin.request("POST", f"/api/classes/{row['id']}", {
            "course_id": row["course_id"], "code": row["code"], "name": "TEST K1 changed",
            "status": "OPEN", "version": row["version"], "updated_at": row["updated_at"], "full_body": True,
        })
        self.assertEqual(status, 200)
        status, payload = self.admin.request("POST", f"/api/classes/{row['id']}/cancel", stale)
        self.assertEqual(status, 409, payload)
        self.assertEqual(payload["error"]["code"], "CONFLICT")
        status, modal = self.admin.request("GET", f"/api/classes/{row['id']}/modal-cancel")
        self.assertEqual(status, 200, modal)
        self.assertEqual(modal["data"]["action"], "cancel")
        self.assertEqual(modal["data"]["class"]["status"], "OPEN")

    def test_teacher_cannot_close_class(self) -> None:
        row = self._class("TEST-R19C-RBAC")
        teacher_id = self.server.service.db.execute("SELECT id FROM users WHERE role='TEACHER' ORDER BY id LIMIT 1").fetchone()[0]
        self.server.service.db.execute("UPDATE classes SET teacher_id=? WHERE id=?", (teacher_id, row["id"]))
        self.server.service.db.commit()
        teacher = ApiClient(self.server)
        self.assertEqual(teacher.request("POST", "/api/auth/login", {"login": "teacher", "password": TEST_PASSWORD})[0], 200)
        status, payload = teacher.request("POST", f"/api/classes/{row['id']}/close", {"apply_from": "2026-11-22", "version": row["version"], "updated_at": row["updated_at"]})
        self.assertEqual(status, 403, payload)

    def test_parallel_same_token_has_one_class_update_winner(self) -> None:
        row = self._class("TEST-R19C-CAS")
        token = {"version": row["version"], "updated_at": row["updated_at"], "full_body": True}
        barrier = threading.Barrier(8)

        def save(index: int) -> int:
            client = ApiClient(self.server)
            self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": TEST_PASSWORD})[0], 200)
            barrier.wait()
            body = {"course_id": row["course_id"], "code": row["code"], "name": f"TEST-R19C-CAS-{index}", "status": "OPEN", **token}
            return client.request("POST", f"/api/classes/{row['id']}", body)[0]

        with ThreadPoolExecutor(max_workers=8) as pool:
            statuses = list(pool.map(save, range(8)))
        self.assertEqual(statuses.count(200), 1, statuses)
        self.assertEqual(statuses.count(409), 7, statuses)

    def test_cancel_persists_and_timetable_route_remains_readable(self) -> None:
        row = self._class("TEST-R19C-CANCEL-PERSIST")
        status, payload = self.admin.request("POST", f"/api/classes/{row['id']}/cancel", {
            "apply_from": "2026-11-23", "version": row["version"], "updated_at": row["updated_at"],
        })
        self.assertEqual(status, 200, payload)
        self.assertEqual(payload["data"]["status"], "CANCELLED")
        self.assertEqual(payload["data"]["status_apply_from"], "2026-11-23")
        status, workflow = self.admin.request("POST", "/api/classes/workflow", {
            "course_id": row["course_id"], "code": "TEST-R19C-TIMETABLE", "name": "TEST R19C timetable",
            "status": "OPEN", "sessions": [{"session_date": "2026-11-24", "start_time": "18:00", "end_time": "19:00", "room": "TEST-R19C"}], "student_ids": [],
        })
        self.assertEqual(status, 201, workflow)
        status, timetable = self.admin.request("GET", "/api/timetable?class_code=TEST-R19C-TIMETABLE")
        self.assertEqual(status, 200, timetable)
        self.assertEqual(len(timetable["data"]), 1)
        session_id = timetable["data"][0]["id"]
        status, detail = self.admin.request("GET", f"/api/timetable/{session_id}")
        self.assertEqual(status, 200, detail)
        self.assertEqual(detail["data"]["class_code"], "TEST-R19C-TIMETABLE")

    def test_branch_manager_cannot_close_class_outside_assigned_branch(self) -> None:
        db = self.server.service.db
        db.execute("INSERT OR IGNORE INTO bm_branches(id,tenant_id,code,name) VALUES(2,1,'R19C-B2','TEST R19C branch B')")
        db.execute(
            "INSERT INTO users(username,email,full_name,password_hash,role) VALUES(?,?,?,?,?)",
            ("TEST_R19C_MANAGER", "test_r19c_manager@example.test", "TEST R19C manager", password_hash(TEST_PASSWORD), "BRANCH_MANAGER"),
        )
        manager_id = db.execute("SELECT id FROM users WHERE username='TEST_R19C_MANAGER'").fetchone()[0]
        db.execute("INSERT INTO bm_user_roles(user_id,tenant_id,role) VALUES(?,?,?)", (manager_id, 1, "BRANCH_MANAGER"))
        db.execute("INSERT INTO bm_manager_assignments(tenant_id,branch_id,user_id,role) VALUES(?,?,?,?)", (1, 1, manager_id, "BRANCH_MANAGER"))
        db.commit()
        course_id = self.admin.request("GET", "/api/courses")[1]["data"][0]["id"]
        status, created = self.admin.request("POST", "/api/classes", {
            "course_id": course_id, "code": "TEST-R19C-BRANCH-B", "name": "TEST R19C branch B class", "status": "OPEN", "branch_id": 2,
        })
        self.assertEqual(status, 201, created)
        manager = ApiClient(self.server)
        self.assertEqual(manager.request("POST", "/api/auth/login", {"login": "TEST_R19C_MANAGER", "password": TEST_PASSWORD})[0], 200)
        status, payload = manager.request("POST", f"/api/classes/{created['data']['id']}/close", {
            "apply_from": "2026-11-24", "version": created["data"]["version"], "updated_at": created["data"]["updated_at"],
        })
        self.assertEqual(status, 404, payload)

    def test_detail_route_contract_is_present_without_unsupported_buttons(self) -> None:
        source = Path(__file__).resolve().parents[1] / "static" / "app.js"
        text = source.read_text(encoding="utf-8")
        self.assertIn("K1 deep link", text)
        self.assertIn("Chương trình học, bộ kỹ năng và bài kiểm tra: Chưa triển khai", text)


if __name__ == "__main__":
    unittest.main()
