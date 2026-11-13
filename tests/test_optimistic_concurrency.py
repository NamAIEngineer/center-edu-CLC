"""Evidence for stale form rejection and atomic compare-and-update."""
from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from app import CenterEduService, create_server
from test_app import ApiClient, TEST_PASSWORD


class OptimisticConcurrencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.server = create_server(Path(self.tmp.name) / "concurrency.sqlite3", "127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.admin = ApiClient(self.server)
        self.assertEqual(self.admin.request("POST", "/api/auth/login", {"login": "admin", "password": TEST_PASSWORD})[0], 200)

    def tearDown(self) -> None:
        self.server.shutdown(); self.server.server_close(); self.server.service.close(); self.tmp.cleanup()

    def _student(self) -> dict:
        return self.admin.request("GET", "/api/students?q=HV-0001")[1]["data"][0]

    def test_student_tokenless_full_body_rejected_and_stale_form_conflicts(self) -> None:
        first = self._student()
        body = {"student_code": first["student_code"], "full_name": "TEST-CONCURRENCY-A", "email": first["email"], "phone": first["phone"], "full_body": True}
        status, payload = self.admin.request("POST", f"/api/students/{first['id']}", body)
        self.assertEqual(status, 428, payload)
        self.assertEqual(payload["error"]["code"], "CONCURRENCY_TOKEN_REQUIRED")
        token = {"version": first["version"], "updated_at": first["updated_at"], "full_body": True}
        status, saved = self.admin.request("POST", f"/api/students/{first['id']}", {**body, **token})
        self.assertEqual(status, 200, saved)
        stale = {**body, "full_name": "TEST-CONCURRENCY-STALE", **token}
        status, conflict = self.admin.request("POST", f"/api/students/{first['id']}", stale)
        self.assertEqual(status, 409, conflict)
        self.assertEqual(conflict["error"]["code"], "CONFLICT")
        self.assertIn("tải lại", conflict["error"]["message"])
        self.assertEqual(conflict["error"]["details"]["retry"], "reload")

    def test_tokenless_narrow_student_patch_merges_without_clobbering_other_fields(self) -> None:
        """Legacy narrow writes are explicit PATCH-style merges, never full replacement."""
        current = self._student()
        original_name = current["full_name"]
        original_phone = current["phone"]
        status, updated = self.admin.request(
            "POST",
            f"/api/students/{current['id']}",
            {"phone": "0900000099"},
        )
        self.assertEqual(status, 200, updated)
        self.assertEqual(updated["data"]["phone"], "0900000099")
        self.assertEqual(updated["data"]["full_name"], original_name)
        self.assertNotEqual(updated["data"]["phone"], original_phone)
        self.assertEqual(self.admin.request("GET", f"/api/students/{current['id']}")[1]["data"]["full_name"], original_name)

    def test_tokenless_narrow_generated_screen_patch_merges_without_clobbering_other_fields(self) -> None:
        created = self.admin.request("POST", "/api/generated/screens", {"route": "/setup/criteria", "data": {"name": "TEST-CONCURRENCY-PATCH", "assessment_type": "Bằng số", "value": "1", "center": "TEST"}})
        self.assertEqual(created[0], 201, created[1])
        row = created[1]["data"]
        status, updated = self.admin.request("POST", f"/api/generated/screens/{row['id']}", {"route": "/setup/criteria", "data": {"value": "99"}, "patch": True})
        self.assertEqual(status, 200, updated)
        self.assertEqual(updated["data"]["data"]["value"], "99")
        self.assertEqual(updated["data"]["data"]["name"], "TEST-CONCURRENCY-PATCH")
        self.assertEqual(self.admin.request("DELETE", f"/api/generated/screens/{row['id']}?route=%2Fsetup%2Fcriteria")[0], 200)

    def test_n_parallel_student_updates_have_one_winner(self) -> None:
        current = self._student()
        token = {"version": current["version"], "updated_at": current["updated_at"], "full_body": True}
        def save(index: int) -> int:
            client = ApiClient(self.server)
            self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": TEST_PASSWORD})[0], 200)
            body = {"student_code": current["student_code"], "full_name": f"TEST-CONCURRENT-{index}", "email": current["email"], "phone": current["phone"], **token}
            return client.request("POST", f"/api/students/{current['id']}", body)[0]
        barrier = threading.Barrier(6)
        def run(index: int) -> int:
            barrier.wait(); return save(index)
        with __import__("concurrent.futures").futures.ThreadPoolExecutor(max_workers=6) as pool:
            statuses = list(pool.map(run, range(6)))
        self.assertEqual(statuses.count(200), 1, statuses)
        self.assertEqual(statuses.count(409), 5, statuses)

    def test_generated_screen_stale_token_conflicts(self) -> None:
        created = self.admin.request("POST", "/api/generated/screens", {"route": "/setup/criteria", "data": {"name": "TEST-CONCURRENCY", "assessment_type": "Bằng số", "value": "1", "center": "TEST"}})
        self.assertEqual(created[0], 201, created[1])
        row = created[1]["data"]
        token = {"version": row["version"], "updated_at": row["updated_at"], "full_body": True}
        tokenless = {"route": "/setup/criteria", "data": {"name": "TEST-CONCURRENCY-TOKENLESS", "assessment_type": "Bằng số", "value": "2", "center": "TEST"}, "full_body": True}
        status, payload = self.admin.request("POST", f"/api/generated/screens/{row['id']}", tokenless)
        self.assertEqual(status, 428, payload)
        self.assertEqual(payload["error"]["code"], "CONCURRENCY_TOKEN_REQUIRED")
        self.assertEqual(self.admin.request("POST", f"/api/generated/screens/{row['id']}", {"route": "/setup/criteria", "data": {"name": "TEST-CONCURRENCY-A", "assessment_type": "Bằng số", "value": "2", "center": "TEST"}, **token})[0], 200)
        status, payload = self.admin.request("POST", f"/api/generated/screens/{row['id']}", {"route": "/setup/criteria", "data": {"name": "TEST-CONCURRENCY-STALE", "assessment_type": "Bằng số", "value": "3", "center": "TEST"}, **token})
        self.assertEqual(status, 409, payload)
        self.assertEqual(payload["error"]["code"], "CONFLICT")
        self.assertEqual(self.admin.request("DELETE", f"/api/generated/screens/{row['id']}?route=%2Fsetup%2Fcriteria")[0], 200)

    def test_n_parallel_generated_updates_have_one_winner(self) -> None:
        created = self.admin.request("POST", "/api/generated/screens", {"route": "/setup/criteria", "data": {"name": "TEST-CONCURRENCY-PARALLEL", "assessment_type": "Bằng số", "value": "1", "center": "TEST"}})
        self.assertEqual(created[0], 201, created[1])
        row = created[1]["data"]
        token = {"version": row["version"], "updated_at": row["updated_at"], "full_body": True}
        barrier = threading.Barrier(6)
        def save(index: int) -> int:
            client = ApiClient(self.server)
            self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": TEST_PASSWORD})[0], 200)
            barrier.wait()
            body = {"route": "/setup/criteria", "data": {"name": f"TEST-CONCURRENCY-PARALLEL-{index}", "assessment_type": "Bằng số", "value": str(index), "center": "TEST"}, **token}
            return client.request("POST", f"/api/generated/screens/{row['id']}", body)[0]
        with __import__("concurrent.futures").futures.ThreadPoolExecutor(max_workers=6) as pool:
            statuses = list(pool.map(save, range(6)))
        self.assertEqual(statuses.count(200), 1, statuses)
        self.assertEqual(statuses.count(409), 5, statuses)
        self.assertEqual(self.admin.request("DELETE", f"/api/generated/screens/{row['id']}?route=%2Fsetup%2Fcriteria")[0], 200)

    def test_n_parallel_class_updates_have_one_winner(self) -> None:
        course_id = self.admin.request("GET", "/api/courses")[1]["data"][0]["id"]
        created_status, created = self.admin.request("POST", "/api/classes", {
            "course_id": course_id, "code": "TEST-CONCURRENCY-CLASS", "name": "TEST concurrency class",
            "status": "OPEN", "teacher_id": "",
        })
        self.assertEqual(created_status, 201, created)
        row = created["data"]
        token = {"version": row["version"], "updated_at": row["updated_at"], "full_body": True}
        barrier = threading.Barrier(6)

        def save(index: int) -> int:
            client = ApiClient(self.server)
            self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": TEST_PASSWORD})[0], 200)
            barrier.wait()
            body = {"course_id": course_id, "code": "TEST-CONCURRENCY-CLASS", "name": f"TEST class winner {index}", "status": "OPEN", "teacher_id": "", **token}
            return client.request("POST", f"/api/classes/{row['id']}", body)[0]

        with __import__("concurrent.futures").futures.ThreadPoolExecutor(max_workers=6) as pool:
            statuses = list(pool.map(save, range(6)))
        self.assertEqual(statuses.count(200), 1, statuses)
        self.assertEqual(statuses.count(409), 5, statuses)

    def test_n_parallel_finance_bill_updates_have_one_winner(self) -> None:
        created_status, created = self.admin.request("POST", "/api/finance/bills", {
            "invoice_code": "TEST-CONCURRENCY-BILL", "confirmation_status": "PENDING",
            "payment_amount": 100, "invoice_date": "2026-11-13", "note": "QA disposable fixture",
        })
        self.assertEqual(created_status, 201, created)
        row = created["data"]
        token = {"version": row["version"], "updated_at": row["updated_at"], "full_body": True}
        barrier = threading.Barrier(6)

        def save(index: int) -> int:
            client = ApiClient(self.server)
            self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": TEST_PASSWORD})[0], 200)
            barrier.wait()
            body = {
                "invoice_code": "TEST-CONCURRENCY-BILL", "confirmation_status": "PENDING",
                "payment_amount": 100 + index, "invoice_date": "2026-11-13", "note": f"TEST bill winner {index}",
                **token,
            }
            return client.request("POST", f"/api/finance/bills/{row['id']}", body)[0]

        with __import__("concurrent.futures").futures.ThreadPoolExecutor(max_workers=6) as pool:
            statuses = list(pool.map(save, range(6)))
        self.assertEqual(statuses.count(200), 1, statuses)
        self.assertEqual(statuses.count(409), 5, statuses)


if __name__ == "__main__":
    unittest.main()
