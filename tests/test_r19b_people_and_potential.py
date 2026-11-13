"""r19b people/CRM contracts: real persistence, scope and CAS behavior."""
from __future__ import annotations

import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app import create_server, password_hash
from test_app import ApiClient, TEST_PASSWORD


class R19bPeopleAndPotentialTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.server = create_server(Path(self.tmp.name) / "r19b.sqlite3", "127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.admin = ApiClient(self.server)
        status, payload = self.admin.request(
            "POST", "/api/auth/login", {"login": "admin", "password": TEST_PASSWORD}
        )
        self.assertEqual(status, 200, payload)

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.server.service.close()
        self.tmp.cleanup()

    def _student_id(self) -> int:
        return int(self.admin.request("GET", "/api/students")[1]["data"][0]["id"])

    def test_parent_create_read_update_reload_and_cas(self) -> None:
        student_id = self._student_id()
        body = {
            "fullname": "TEST_R19B Parent",
            "username": "TEST_R19B_parent",
            "password": "test-r19b-parent",
            "code": "TEST-R19B-PARENT",
            "email": "test-r19b-parent@example.test",
            "phone": "0900000199",
            "student_ids": [student_id],
            "note": "TEST fixture",
        }
        status, created = self.admin.request("POST", "/api/parents", body)
        self.assertEqual(status, 201, created)
        row = created["data"]
        parent_id = row["id"]
        self.assertEqual(row["student_ids"], [student_id])
        status, read = self.admin.request("GET", f"/api/parents/{parent_id}")
        self.assertEqual(status, 200, read)
        self.assertEqual(read["data"]["fullname"], body["fullname"])
        status, missing_token = self.admin.request(
            "POST", f"/api/parents/{parent_id}", {"fullname": "TEST missing token"}
        )
        self.assertEqual(status, 428, missing_token)
        update = {"fullname": "TEST_R19B Parent Updated", "version": row["version"]}
        status, changed = self.admin.request("POST", f"/api/parents/{parent_id}", update)
        self.assertEqual(status, 200, changed)
        self.assertEqual(changed["data"]["fullname"], update["fullname"])
        status, stale = self.admin.request(
            "POST", f"/api/parents/{parent_id}", {"fullname": "TEST stale", "version": row["version"]}
        )
        self.assertEqual(status, 409, stale)
        self.assertIn("tải lại", stale["error"]["message"])
        status, duplicate = self.admin.request("POST", "/api/parents", {**body, "code": "TEST-R19B-PARENT-2"})
        self.assertEqual(status, 409, duplicate)
        # A fresh GET is the reload/persistence proof.
        status, reloaded = self.admin.request("GET", f"/api/parents?q=TEST_R19B")
        self.assertEqual(status, 200, reloaded)
        self.assertEqual(reloaded["data"][0]["id"], parent_id)

    def test_staff_create_login_duplicate_denial_and_cas(self) -> None:
        body = {
            "fullname": "TEST_R19B Staff",
            "username": "TEST_R19B_staff",
            "password": "test-r19b-staff",
            "code": "TEST-R19B-STAFF",
            "email": "test-r19b-staff@example.test",
            "department": "CM",
        }
        status, created = self.admin.request("POST", "/api/staff", body)
        self.assertEqual(status, 201, created)
        row = created["data"]
        staff_id = row["id"]
        staff_login = ApiClient(self.server)
        status, login = staff_login.request("POST", "/api/auth/login", {"login": body["username"], "password": body["password"]})
        self.assertEqual(status, 200, login)
        self.assertEqual(login["user"]["role"], "STAFF")
        status, listed = self.admin.request("GET", "/api/staff?q=TEST_R19B_staff")
        self.assertEqual(status, 200, listed)
        self.assertEqual(listed["data"][0]["version"], row["version"])
        status, duplicate = self.admin.request("POST", "/api/staff", body)
        self.assertEqual(status, 409, duplicate)
        status, missing_token = self.admin.request("POST", f"/api/staff/{staff_id}", {"fullname": "TEST"})
        self.assertEqual(status, 428, missing_token)
        status, changed = self.admin.request("POST", f"/api/staff/{staff_id}", {"fullname": "TEST_R19B Staff Updated", "version": row["version"]})
        self.assertEqual(status, 200, changed)
        status, stale = self.admin.request("POST", f"/api/staff/{staff_id}", {"fullname": "TEST stale", "version": row["version"]})
        self.assertEqual(status, 409, stale)
        status, denied = staff_login.request("POST", "/api/staff", {**body, "username": "TEST_R19B_staff_denied", "email": "denied@example.test"})
        self.assertEqual(status, 403, denied)

    def test_teacher_update_requires_token_and_parallel_cas(self) -> None:
        status, created = self.admin.request("POST", "/api/teachers", {
            "full_name": "TEST_R19B Teacher", "username": "TEST_R19B_teacher",
            "email": "test-r19b-teacher@example.test", "password": "test-r19b-teacher",
        })
        self.assertEqual(status, 201, created)
        row = created["data"]
        teacher_id = row["id"]
        status, missing = self.admin.request("POST", f"/api/teachers/{teacher_id}", {"full_name": "TEST"})
        self.assertEqual(status, 428, missing)
        token = {"version": row["version"], "updated_at": row["updated_at"], "full_body": True}

        def save(index: int) -> int:
            client = ApiClient(self.server)
            self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": TEST_PASSWORD})[0], 200)
            return client.request("POST", f"/api/teachers/{teacher_id}", {
                "full_name": f"TEST_R19B Teacher {index}", "email": row["email"], **token,
            })[0]

        with ThreadPoolExecutor(max_workers=4) as pool:
            statuses = list(pool.map(save, range(4)))
        self.assertEqual(statuses.count(200), 1, statuses)
        self.assertEqual(statuses.count(409), 3, statuses)

    def test_potential_create_branch_scope_and_cas(self) -> None:
        body = {
            "full_name": "TEST_R19B Lead",
            "customer_code": "TEST-R19B-LEAD",
            "phone": "0900000200",
            "email": "test-r19b-lead@example.test",
            "branch_id": 1,
            "note": "TEST fixture",
        }
        status, created = self.admin.request("POST", "/api/potential-customers", body)
        self.assertEqual(status, 201, created)
        row = created["data"]
        self.assertEqual(row["branch_id"], 1)
        status, listed = self.admin.request("GET", "/api/potential-customers?q=TEST-R19B-LEAD")
        self.assertEqual(status, 200, listed)
        self.assertEqual(listed["data"][0]["id"], row["id"])
        status, missing = self.admin.request("POST", f"/api/potential-customers/{row['id']}", {"full_name": "TEST", "full_body": True})
        self.assertEqual(status, 428, missing)
        token = {"version": row["version"], "updated_at": row["updated_at"], "full_body": True}
        status, changed = self.admin.request("POST", f"/api/potential-customers/{row['id']}", {**body, "full_name": "TEST_R19B Lead Updated", **token})
        self.assertEqual(status, 200, changed)
        status, stale = self.admin.request("POST", f"/api/potential-customers/{row['id']}", {**body, "full_name": "TEST stale", **token})
        self.assertEqual(status, 409, stale)

    def test_potential_parallel_full_body_updates_have_one_winner(self) -> None:
        status, created = self.admin.request("POST", "/api/potential-customers", {
            "full_name": "TEST_R19B Parallel Lead", "customer_code": "TEST-R19B-PARALLEL",
        })
        self.assertEqual(status, 201, created)
        row = created["data"]
        token = {"version": row["version"], "updated_at": row["updated_at"], "full_body": True}

        def save(index: int) -> int:
            client = ApiClient(self.server)
            self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": TEST_PASSWORD})[0], 200)
            return client.request("POST", f"/api/potential-customers/{row['id']}", {
                "full_name": f"TEST_R19B Parallel Lead {index}",
                "customer_code": row["customer_code"], "status": "QUALIFIED", **token,
            })[0]

        with ThreadPoolExecutor(max_workers=4) as pool:
            statuses = list(pool.map(save, range(4)))
        self.assertEqual(statuses.count(200), 1, statuses)
        self.assertEqual(statuses.count(409), 3, statuses)

    def test_staff_branch_manager_requires_existing_branch(self) -> None:
        status, invalid = self.admin.request("POST", "/api/staff", {
            "fullname": "TEST_R19B Manager", "username": "TEST_R19B_manager",
            "password": "test-r19b-manager", "code": "TEST-R19B-MANAGER",
            "email": "test-r19b-manager@example.test", "role": "BRANCH_MANAGER", "branch_id": 99999,
        })
        self.assertIn(status, (403, 404), invalid)
        db = self.server.service.db
        db.execute("INSERT OR IGNORE INTO bm_branches(id,tenant_id,code,name) VALUES(2,1,'TEST-B2','TEST Branch 2')")
        db.commit()
        status, created = self.admin.request("POST", "/api/staff", {
            "fullname": "TEST_R19B Manager", "username": "TEST_R19B_manager",
            "password": "test-r19b-manager", "code": "TEST-R19B-MANAGER",
            "email": "test-r19b-manager@example.test", "role": "BRANCH_MANAGER", "branch_ids": [1, 2],
        })
        self.assertEqual(status, 201, created)
        manager_id = created["data"]["id"]
        assignments = db.execute("SELECT branch_id FROM bm_manager_assignments WHERE user_id=? ORDER BY branch_id", (manager_id,)).fetchall()
        self.assertEqual([row[0] for row in assignments], [1, 2])


if __name__ == "__main__":
    unittest.main()
