"""Persisted daily-evaluation detail, criterion CRUD, and CAS proof."""
from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import urlencode

from app import create_server
from test_app import ApiClient, TEST_PASSWORD


class DailyEvaluationDetailTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="center-edu-daily-evaluation-")
        self.server = create_server(Path(self.tmp.name) / "center.sqlite3", "127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.client = ApiClient(self.server)
        self.assertEqual(self.client.request("POST", "/api/auth/login", {"login": "admin", "password": TEST_PASSWORD})[0], 200)

    def tearDown(self) -> None:
        self.server.shutdown(); self.server.server_close(); self.server.service.close(); self.tmp.cleanup()

    def test_detail_criterion_crud_reload_and_delete_cas(self) -> None:
        status, created = self.client.request("POST", "/api/generated/screens", {"route": "/setup/daily-evaluation", "data": {"name": "TEST daily evaluation", "status": "Hoạt động", "course_ids": ["1"], "criteria": '[{"name":"Điểm danh","assessment_type":"Nhập điểm","max_value":10,"status":"Hoạt động"}]'}})
        self.assertEqual(status, 201, created)
        row = created["data"]
        self.assertEqual(row["data"]["criteria_count"], 1)
        listed = self.client.request("GET", "/api/generated/screens?route=%2Fsetup%2Fdaily-evaluation&q=TEST%20daily%20evaluation")[1]
        self.assertEqual(listed["data"]["records"][0]["data"]["course_count"], 1)
        token = {"version": row["version"], "updated_at": row["updated_at"], "full_body": True}
        status, updated = self.client.request("POST", f"/api/generated/screens/{row['id']}", {"route": "/setup/daily-evaluation", "data": {"name": "TEST daily evaluation", "status": "Hoạt động", "course_ids": ["1"], "criteria": '[{"name":"Điểm danh","assessment_type":"Nhập điểm","max_value":10,"status":"Đã khóa"},{"name":"Bài tập","assessment_type":"Bằng số","value":"Đạt","status":"Hoạt động"}]'}, **token})
        self.assertEqual(status, 200, updated)
        self.assertEqual(updated["data"]["data"]["criteria_count"], 2)
        stale_status, stale = self.client.request("POST", f"/api/generated/screens/{row['id']}", {"route": "/setup/daily-evaluation", "data": {"name": "stale", "criteria": "[]"}, **token})
        self.assertEqual(stale_status, 409, stale)
        self.assertEqual(stale["error"]["code"], "CONFLICT")
        current = updated["data"]
        query = urlencode({"route": "/setup/daily-evaluation", "version": current["version"], "updated_at": current["updated_at"]})
        self.assertEqual(self.client.request("DELETE", f"/api/generated/screens/{row['id']}?{query}")[0], 200)
        after = self.client.request("GET", "/api/generated/screens?route=%2Fsetup%2Fdaily-evaluation&q=TEST%20daily%20evaluation")[1]
        self.assertEqual(after["data"]["records"], [])


if __name__ == "__main__":
    unittest.main()
