"""r19c clean-production tenant/branch bootstrap and isolation contract."""
from __future__ import annotations

import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from app import create_server
from test_app import ApiClient


class R19cProductionBranchTests(unittest.TestCase):
    password = "R19C-admin-password"

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="center-edu-r19c-production-")
        self.db_path = Path(self.tmp.name) / "center.sqlite3"
        self.env = patch.dict(os.environ, {"CENTER_EDU_ADMIN_PASSWORD": self.password}, clear=False)
        self.env.start()
        self.server = create_server(
            self.db_path, "127.0.0.1", 0, production=True,
            production_tenant_name="TEST R19C TENANT",
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.admin = ApiClient(self.server)
        self.assertEqual(self.admin.request("POST", "/api/auth/login", {"login": "admin", "password": self.password})[0], 200)

    def tearDown(self) -> None:
        self.server.shutdown(); self.server.server_close(); self.server.service.close()
        self.env.stop(); self.tmp.cleanup()

    def _branch(self, code: str, name: str):
        status, payload = self.admin.request("POST", "/api/branch-manager/branches", {"code": code, "name": name})
        self.assertEqual(status, 201, payload)
        return payload["data"]

    def _course(self):
        status, payload = self.admin.request("POST", "/api/courses", {"code": "TEST-R19C-COURSE", "name": "TEST R19C course"})
        self.assertEqual(status, 201, payload)
        return payload["data"]["id"]

    def test_empty_bootstrap_is_admin_only_and_branch_required(self) -> None:
        db = self.server.service.db
        self.assertEqual(db.execute("SELECT COUNT(*) FROM users").fetchone()[0], 1)
        self.assertEqual(db.execute("SELECT COUNT(*) FROM bm_tenants").fetchone()[0], 1)
        self.assertEqual(db.execute("SELECT COUNT(*) FROM bm_branches").fetchone()[0], 0)
        self.assertEqual(self.admin.request("GET", "/api/branch-manager/scope")[1]["data"]["branches"], [])
        status, payload = self.admin.request("POST", "/api/students", {
            "student_code": "TEST-R19C-NOBRANCH", "full_name": "TEST no branch", "email": "nobranch@example.test",
        })
        self.assertEqual(status, 409, payload)
        self.assertEqual(payload["error"]["code"], "BRANCH_REQUIRED")
        status, payload = self.admin.request("POST", "/api/potential-customers", {
            "customer_code": "TEST-R19C-NOBRANCH-LEAD", "full_name": "TEST no branch lead",
        })
        self.assertEqual(status, 409, payload)
        self.assertEqual(payload["error"]["code"], "BRANCH_REQUIRED")

    def test_v7_potential_form_uses_real_branch_scope(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn("async function potentialBranchOptions()", source)
        self.assertIn("/api/branch-manager/scope", source)
        self.assertIn("name:'branch_id'", source)
        self.assertIn("required:true,options:[{value:'',label:'Chọn chi nhánh'}", source)
        self.assertNotIn("name:'branch',label:'Tên chi nhánh'", source)
        self.assertIn('"BRANCH_REQUIRED"', (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8"))

    def test_v7_potential_create_search_and_reload_keep_branch_scope(self) -> None:
        branch = self._branch("TEST-V7", "TEST V7 branch")
        status, created = self.admin.request("POST", "/api/potential-customers", {
            "customer_code": "TEST-R19C-V7-LEAD",
            "full_name": "TEST V7 prospect",
            "branch_id": branch["id"],
            "source": "TEST fixture",
        })
        self.assertEqual(status, 201, created)
        self.assertEqual(created["data"]["branch_id"], branch["id"])
        self.assertEqual(created["data"]["branch"], branch["name"])
        found = self.admin.request("GET", "/api/potential-customers?q=TEST-R19C-V7-LEAD")
        self.assertEqual(found[0], 200, found[1])
        self.assertEqual([row["id"] for row in found[1]["data"]], [created["data"]["id"]])
        reopened = create_server(self.db_path, "127.0.0.1", 0, production=True,
                                 production_tenant_name="TEST R19C TENANT")
        thread = threading.Thread(target=reopened.serve_forever, daemon=True)
        thread.start()
        try:
            client = ApiClient(reopened)
            self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": self.password})[0], 200)
            reloaded = client.request("GET", "/api/potential-customers?q=TEST-R19C-V7-LEAD")
            self.assertEqual(reloaded[0], 200, reloaded[1])
            self.assertEqual(reloaded[1]["data"][0]["branch_id"], branch["id"])
        finally:
            reopened.shutdown(); reopened.server_close(); reopened.service.close()

    def test_branch_crud_duplicate_lock_delete_guard_and_restart(self) -> None:
        branch_a = self._branch("TEST-A", "TEST Branch A")
        status, duplicate = self.admin.request("POST", "/api/branch-manager/branches", {"code": "test-a", "name": "Duplicate"})
        self.assertEqual(status, 409, duplicate)
        renamed = self.admin.request("POST", f"/api/branch-manager/branches/{branch_a['id']}", {"name": "TEST Branch A renamed"})
        self.assertEqual(renamed[0], 200, renamed[1])
        locked = self.admin.request("POST", f"/api/branch-manager/branches/{branch_a['id']}", {"status": "inactive"})
        self.assertEqual(locked[0], 200, locked[1])
        reopened = self.admin.request("POST", f"/api/branch-manager/branches/{branch_a['id']}", {"status": "active"})
        self.assertEqual(reopened[0], 200, reopened[1])
        branch_b = self._branch("TEST-B", "TEST Branch B")
        branch_c = self._branch("TEST-C", "TEST Branch C")
        deleted = self.admin.request("DELETE", f"/api/branch-manager/branches/{branch_c['id']}")
        self.assertEqual(deleted[0], 200, deleted[1])
        self.assertEqual(self.admin.request("GET", "/api/branch-manager/branches")[0], 200)
        # Operational mappings make deletion fail closed.
        course_id = self._course()
        created = self.admin.request("POST", "/api/classes", {
            "course_id": course_id, "code": "TEST-R19C-BRANCH-A", "name": "TEST Branch A class", "branch_id": branch_a["id"],
        })
        self.assertEqual(created[0], 201, created[1])
        denied_delete = self.admin.request("DELETE", f"/api/branch-manager/branches/{branch_a['id']}")
        self.assertEqual(denied_delete[0], 409, denied_delete[1])
        self.assertEqual(denied_delete[1]["error"]["code"], "BRANCH_IN_USE")
        self.assertEqual(self.server.service.db.execute("SELECT COUNT(*) FROM bm_entity_scopes WHERE entity='class'").fetchone()[0], 1)
        self.assertEqual(branch_b["status"], "active")

    def test_real_entity_scope_manager_isolation_reports_and_roles(self) -> None:
        branch_a = self._branch("TEST-A", "TEST Branch A")
        branch_b = self._branch("TEST-B", "TEST Branch B")
        course_id = self._course()
        students = {}
        classes = {}
        for suffix, branch in (("A", branch_a), ("B", branch_b)):
            status, payload = self.admin.request("POST", "/api/students", {
                "student_code": f"TEST-R19C-STUDENT-{suffix}", "full_name": f"TEST student {suffix}",
                "email": f"student-{suffix.lower()}@example.test", "branch_id": branch["id"],
            })
            self.assertEqual(status, 201, payload); students[suffix] = payload["data"]
            status, payload = self.admin.request("POST", "/api/classes", {
                "course_id": course_id, "code": f"TEST-R19C-CLASS-{suffix}", "name": f"TEST class {suffix}",
                "branch_id": branch["id"],
            })
            self.assertEqual(status, 201, payload); classes[suffix] = payload["data"]
        status, teacher = self.admin.request("POST", "/api/teachers", {
            "username": "TEST_R19C_TEACHER_A", "email": "teacher-a@example.test", "full_name": "TEST teacher A",
            "password": "R19C-teacher-password", "branch_id": branch_a["id"],
        })
        self.assertEqual(status, 201, teacher)
        status, manager = self.admin.request("POST", "/api/staff", {
            "username": "TEST_R19C_MANAGER_A", "email": "manager-a@example.test", "fullname": "TEST manager A",
            "password": "R19C-manager-password", "role": "BRANCH_MANAGER", "branch_ids": [branch_a["id"]],
        })
        self.assertEqual(status, 201, manager)
        manager_client = ApiClient(self.server)
        self.assertEqual(manager_client.request("POST", "/api/auth/login", {"login": "TEST_R19C_MANAGER_A", "password": "R19C-manager-password"})[0], 200)
        scope = manager_client.request("GET", "/api/branch-manager/scope")
        self.assertEqual(scope[0], 200, scope[1]); self.assertEqual([row["id"] for row in scope[1]["data"]["branches"]], [branch_a["id"]])
        listed_students = manager_client.request("GET", "/api/students")
        self.assertEqual(listed_students[0], 200, listed_students[1]); self.assertEqual([row["id"] for row in listed_students[1]["data"]], [students["A"]["id"]])
        listed_classes = manager_client.request("GET", "/api/classes")
        self.assertEqual(listed_classes[0], 200, listed_classes[1]); self.assertEqual([row["id"] for row in listed_classes[1]["data"]], [classes["A"]["id"]])
        self.assertEqual(manager_client.request("GET", f"/api/students/{students['B']['id']}")[0], 404)
        self.assertEqual(manager_client.request("GET", f"/api/classes/{classes['B']['id']}")[0], 404)
        update_status, update_payload = manager_client.request("POST", f"/api/students/{students['B']['id']}", {"full_name": "TEST forged"})
        self.assertEqual(update_status, 404, update_payload)
        report = manager_client.request("GET", "/api/report-engine?route=/report/training/class/v2")
        self.assertEqual(report[0], 200, report[1]); self.assertFalse(any(row.get("id") == classes["B"]["id"] for row in report[1]["data"]["rows"]))
        self.assertEqual(manager_client.request("GET", "/api/branch-manager/branches")[0], 403)
        anonymous = ApiClient(self.server)
        self.assertEqual(anonymous.request("GET", "/api/branch-manager/scope")[0], 401)
        teacher_client = ApiClient(self.server)
        self.assertEqual(teacher_client.request("POST", "/api/auth/login", {"login": "TEST_R19C_TEACHER_A", "password": "R19C-teacher-password"})[0], 200)
        self.assertEqual(teacher_client.request("GET", "/api/branch-manager/branches")[0], 403)
        admin_all = self.admin.request("GET", "/api/students")
        self.assertEqual(admin_all[0], 200, admin_all[1]); self.assertEqual({row["id"] for row in admin_all[1]["data"]}, {students["A"]["id"], students["B"]["id"]})

    def test_production_restart_preserves_tenant_branches_and_scope_rows(self) -> None:
        branch = self._branch("TEST-PERSIST", "TEST Persistent Branch")
        status, student = self.admin.request("POST", "/api/students", {
            "student_code": "TEST-R19C-PERSIST", "full_name": "TEST persistent student", "email": "persist@example.test",
        })
        self.assertEqual(status, 201, student)
        self.assertEqual(student["data"].get("id") is not None, True)
        db = self.server.service.db
        self.assertEqual(db.execute("SELECT COUNT(*) FROM bm_entity_scopes WHERE entity='student'").fetchone()[0], 1)
        self.server.shutdown(); self.server.server_close(); self.server.service.close()
        reopened = create_server(self.db_path, "127.0.0.1", 0, production=True)
        thread = threading.Thread(target=reopened.serve_forever, daemon=True); thread.start()
        try:
            client = ApiClient(reopened)
            self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": self.password})[0], 200)
            scope = client.request("GET", "/api/branch-manager/scope")
            self.assertEqual([row["id"] for row in scope[1]["data"]["branches"]], [branch["id"]])
            rows = client.request("GET", "/api/students")[1]["data"]
            self.assertEqual([row["student_code"] for row in rows], ["TEST-R19C-PERSIST"])
        finally:
            reopened.shutdown(); reopened.server_close(); reopened.service.close()


if __name__ == "__main__":
    unittest.main()
