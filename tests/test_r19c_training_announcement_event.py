"""R19c A1/A2 generated-screen CRUD and branch persistence checks."""
from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import urlencode

from app import create_server
from test_app import ApiClient, TEST_PASSWORD


class R19cTrainingAnnouncementEventTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="center-edu-r19c-training-")
        self.server = create_server(Path(self.tmp.name) / "center.sqlite3", "127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.admin = ApiClient(self.server)
        self.assertEqual(
            self.admin.request("POST", "/api/auth/login", {"login": "admin", "password": TEST_PASSWORD})[0],
            200,
        )
        self.server.service.db.execute(
            "INSERT OR IGNORE INTO bm_branches(id,tenant_id,code,name) VALUES(2,1,'TEST-R19C-TRAINING','TEST training branch')"
        )
        self.server.service.db.commit()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.server.service.close()
        self.tmp.cleanup()

    def test_announcement_create_update_reload_delete_and_conflict(self) -> None:
        status, created = self.admin.request("POST", "/api/generated/screens", {
            "route": "/training/announcement",
            "data": {
                "title": "TEST-R19C announcement",
                "range": "Toàn bộ trung tâm",
                "important": "Có",
                "branch_id": 2,
                "branch": "TEST training branch",
            },
        })
        self.assertEqual(status, 201, created)
        row = created["data"]
        self.assertEqual(row["data"]["branch_id"], 2)
        status, listed = self.admin.request("GET", "/api/generated/screens?route=%2Ftraining%2Fannouncement&q=TEST-R19C%20announcement")
        self.assertEqual(status, 200, listed)
        self.assertEqual(listed["data"]["records"][0]["data"]["title"], "TEST-R19C announcement")
        token = {"version": row["version"], "updated_at": row["updated_at"], "full_body": True}
        status, updated = self.admin.request("POST", f"/api/generated/screens/{row['id']}", {
            "route": "/training/announcement", "data": {"title": "TEST-R19C announcement updated", "range": "Theo lớp", "branch_id": 2}, **token,
        })
        self.assertEqual(status, 200, updated)
        stale_status, stale = self.admin.request("POST", f"/api/generated/screens/{row['id']}", {
            "route": "/training/announcement", "data": {"title": "TEST-R19C stale", "range": "Theo lớp", "branch_id": 2}, **token,
        })
        self.assertEqual(stale_status, 409, stale)
        self.assertEqual(stale["error"]["code"], "CONFLICT")
        status, reloaded = self.admin.request("GET", "/api/generated/screens?route=%2Ftraining%2Fannouncement&q=TEST-R19C%20announcement%20updated")
        self.assertEqual(status, 200, reloaded)
        self.assertEqual(reloaded["data"]["records"][0]["data"]["branch_id"], 2)
        status, deleted = self.admin.request("DELETE", f"/api/generated/screens/{row['id']}?route=%2Ftraining%2Fannouncement")
        self.assertEqual(status, 200, deleted)
        self.assertEqual(deleted["data"]["deleted"], True)
        status, after_delete = self.admin.request("GET", "/api/generated/screens?route=%2Ftraining%2Fannouncement&q=TEST-R19C%20announcement%20updated")
        self.assertEqual(status, 200, after_delete)
        self.assertEqual(after_delete["data"]["records"], [])

    def test_event_create_update_reload_delete(self) -> None:
        status, created = self.admin.request("POST", "/api/generated/screens", {
            "route": "/training/event",
            "data": {
                "title": "TEST-R19C event",
                "description": "TEST event body",
                "start_date": "2026-11-15",
                "end_date": "2026-11-16",
                "range": "Toàn trung tâm",
                "branch_id": 2,
                "branch": "TEST training branch",
            },
        })
        self.assertEqual(status, 201, created)
        row = created["data"]
        self.assertEqual(row["data"]["branch_id"], 2)
        token = {"version": row["version"], "updated_at": row["updated_at"], "full_body": True}
        status, updated = self.admin.request("POST", f"/api/generated/screens/{row['id']}", {
            "route": "/training/event", "data": {"title": "TEST-R19C event updated", "description": "TEST event body 2", "range": "Theo lớp", "branch_id": 2}, **token,
        })
        self.assertEqual(status, 200, updated)
        status, listed = self.admin.request("GET", "/api/generated/screens?route=%2Ftraining%2Fevent&q=TEST-R19C%20event%20updated")
        self.assertEqual(status, 200, listed)
        self.assertEqual(listed["data"]["records"][0]["data"]["description"], "TEST event body 2")
        status, deleted = self.admin.request("DELETE", f"/api/generated/screens/{row['id']}?route=%2Ftraining%2Fevent")
        self.assertEqual(status, 200, deleted)

    def test_generated_delete_cas_rejects_stale_token_and_accepts_current(self) -> None:
        status, created = self.admin.request("POST", "/api/generated/screens", {
            "route": "/training/announcement",
            "data": {"title": "TEST-R19C delete CAS", "range": "Toàn bộ trung tâm", "branch_id": 2},
        })
        self.assertEqual(status, 201, created)
        row = created["data"]
        stale = {"version": row["version"], "updated_at": row["updated_at"]}
        status, changed = self.admin.request("POST", f"/api/generated/screens/{row['id']}", {
            "route": "/training/announcement",
            "data": {"title": "TEST-R19C delete CAS changed", "range": "Theo lớp", "branch_id": 2},
            **stale, "full_body": True,
        })
        self.assertEqual(status, 200, changed)
        query = urlencode({"route": "/training/announcement", **stale})
        status, conflict = self.admin.request("DELETE", f"/api/generated/screens/{row['id']}?{query}")
        self.assertEqual(status, 409, conflict)
        self.assertEqual(conflict["error"]["code"], "CONFLICT")
        current = changed["data"]
        query = urlencode({"route": "/training/announcement", "version": current["version"], "updated_at": current["updated_at"]})
        status, deleted = self.admin.request("DELETE", f"/api/generated/screens/{row['id']}?{query}")
        self.assertEqual(status, 200, deleted)


if __name__ == "__main__":
    unittest.main()
