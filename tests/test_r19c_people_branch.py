"""R19c branch selector transport and persisted scope checks."""
from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from app import create_server
from test_app import ApiClient, TEST_PASSWORD


class R19cPeopleBranchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="center-edu-r19c-people-")
        self.server = create_server(Path(self.tmp.name) / "center.sqlite3", "127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.admin = ApiClient(self.server)
        self.assertEqual(self.admin.request("POST", "/api/auth/login", {"login": "admin", "password": TEST_PASSWORD})[0], 200)
        db = self.server.service.db
        db.execute("INSERT OR IGNORE INTO bm_branches(id,tenant_id,code,name) VALUES(2,1,'TEST-R19C-B','TEST branch B')")
        db.commit()

    def tearDown(self) -> None:
        self.server.shutdown(); self.server.server_close(); self.server.service.close(); self.tmp.cleanup()

    def test_staff_branch_id_persists_and_is_returned(self) -> None:
        body = {
            "fullname": "TEST R19C scoped staff", "username": "TEST_R19C_scoped_staff",
            "password": "test-r19c-staff", "email": "test-r19c-staff@example.test",
            "code": "TEST-R19C-STAFF", "branch_id": 2,
        }
        status, created = self.admin.request("POST", "/api/staff", body)
        self.assertEqual(status, 201, created)
        self.assertEqual(created["data"]["branch_id"], 2)
        status, listed = self.admin.request("GET", "/api/staff?q=TEST_R19C_scoped_staff")
        self.assertEqual(status, 200, listed)
        self.assertEqual(listed["data"][0]["branch_id"], 2)
        scope = self.server.service.db.execute(
            "SELECT branch_id FROM bm_entity_scopes WHERE entity='staff' AND entity_id=?", (created["data"]["id"],)
        ).fetchone()
        self.assertEqual(scope[0], 2)

    def test_people_writes_require_selection_when_multiple_branches_exist(self) -> None:
        missing_staff = {
            "fullname": "TEST R19C missing branch staff", "username": "TEST_R19C_missing_staff",
            "password": "test-r19c-staff", "email": "test-r19c-missing@example.test",
            "code": "TEST-R19C-MISSING-STAFF",
        }
        status, payload = self.admin.request("POST", "/api/staff", missing_staff)
        self.assertIn(status, (400, 409), payload)
        self.assertEqual(payload["error"]["code"], "BRANCH_REQUIRED")
        student_id = self.admin.request("GET", "/api/students")[1]["data"][0]["id"]
        missing_parent = {
            "fullname": "TEST R19C missing branch parent", "username": "TEST_R19C_missing_parent",
            "password": "test-r19c-parent", "email": "test-r19c-missing-parent@example.test",
            "code": "TEST-R19C-MISSING-PARENT", "student_ids": [student_id],
        }
        status, payload = self.admin.request("POST", "/api/parents", missing_parent)
        self.assertIn(status, (400, 409), payload)
        self.assertEqual(payload["error"]["code"], "BRANCH_REQUIRED")

    def test_parent_branch_id_persists_and_update_can_move_scope(self) -> None:
        status, student_b = self.admin.request("POST", "/api/students", {
            "student_code": "TEST-R19C-PARENT-B", "full_name": "TEST parent student B",
            "email": "test-r19c-parent-b@example.test", "branch_id": 2,
        })
        self.assertEqual(status, 201, student_b)
        status, student_a = self.admin.request("POST", "/api/students", {
            "student_code": "TEST-R19C-PARENT-A", "full_name": "TEST parent student A",
            "email": "test-r19c-parent-a@example.test", "branch_id": 1,
        })
        self.assertEqual(status, 201, student_a)
        body = {
            "fullname": "TEST R19C scoped parent", "username": "TEST_R19C_parent",
            "password": "test-r19c-parent", "email": "test-r19c-parent@example.test",
            "code": "TEST-R19C-PARENT", "student_ids": [student_b["data"]["id"]], "branch_id": 2,
        }
        status, created = self.admin.request("POST", "/api/parents", body)
        self.assertEqual(status, 201, created)
        row = created["data"]
        self.assertEqual(row["branch_id"], 2)
        status, moved = self.admin.request("POST", f"/api/parents/{row['id']}", {
            "version": row["version"], "branch_id": 1,
            "student_ids": [student_a["data"]["id"]],
        })
        self.assertEqual(status, 200, moved)
        self.assertEqual(moved["data"]["branch_id"], 1)

    def test_parent_rejects_student_from_another_branch(self) -> None:
        status, student = self.admin.request("POST", "/api/students", {
            "student_code": "TEST-R19C-PARENT-MISMATCH", "full_name": "TEST mismatched student",
            "email": "test-r19c-parent-mismatch@example.test", "branch_id": 1,
        })
        self.assertEqual(status, 201, student)
        status, payload = self.admin.request("POST", "/api/parents", {
            "fullname": "TEST R19C mismatched parent", "username": "TEST_R19C_parent_mismatch",
            "password": "test-r19c-parent", "email": "test-r19c-parent-mismatch@example.test",
            "code": "TEST-R19C-PARENT-MISMATCH", "student_ids": [student["data"]["id"]], "branch_id": 2,
        })
        self.assertEqual(status, 409, payload)
        self.assertEqual(payload["error"]["code"], "BRANCH_MISMATCH")

    def test_staff_branch_assignment_does_not_hide_tenant_class_reads(self) -> None:
        course_id = self.admin.request("GET", "/api/courses")[1]["data"][0]["id"]
        for suffix, branch_id in (("A", 1), ("B", 2)):
            status, payload = self.admin.request("POST", "/api/classes", {
                "course_id": course_id, "code": f"TEST-R19C-STAFF-READ-{suffix}",
                "name": f"TEST staff read class {suffix}", "branch_id": branch_id,
            })
            self.assertEqual(status, 201, payload)
        status, staff = self.admin.request("POST", "/api/staff", {
            "fullname": "TEST R19C branch staff", "username": "TEST_R19C_branch_staff",
            "password": "test-r19c-staff", "email": "test-r19c-branch-staff@example.test",
            "code": "TEST-R19C-BRANCH-STAFF", "branch_id": 1,
        })
        self.assertEqual(status, 201, staff)
        staff_client = ApiClient(self.server)
        self.assertEqual(staff_client.request("POST", "/api/auth/login", {
            "login": "TEST_R19C_branch_staff", "password": "test-r19c-staff",
        })[0], 200)
        status, classes = staff_client.request("GET", "/api/classes")
        self.assertEqual(status, 200, classes)
        codes = {row["code"] for row in classes["data"]}
        self.assertTrue({"TEST-R19C-STAFF-READ-A", "TEST-R19C-STAFF-READ-B"}.issubset(codes))

    def test_admin_class_reads_remain_tenant_wide_with_branch_header_selection(self) -> None:
        course_id = self.admin.request("GET", "/api/courses")[1]["data"][0]["id"]
        for suffix, branch_id in (("A", 1), ("B", 2)):
            status, payload = self.admin.request("POST", "/api/classes", {
                "course_id": course_id, "code": f"TEST-R19C-ADMIN-READ-{suffix}",
                "name": f"TEST admin read class {suffix}", "branch_id": branch_id,
            })
            self.assertEqual(status, 201, payload)
        status, classes = self.admin.request("GET", "/api/classes")
        self.assertEqual(status, 200, classes)
        codes = {row["code"] for row in classes["data"]}
        self.assertTrue({"TEST-R19C-ADMIN-READ-A", "TEST-R19C-ADMIN-READ-B"}.issubset(codes))


if __name__ == "__main__":
    unittest.main()
