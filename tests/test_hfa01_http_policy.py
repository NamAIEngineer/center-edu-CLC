from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from app import create_server
from test_app import ApiClient, TEST_PASSWORD


class Hfa01HttpPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.server = create_server(Path(self.tmp.name) / "center.sqlite3", "127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        db = self.server.service.db
        db.execute(
            "INSERT INTO timetable_sessions(class_id,session_date,start_time,end_time,room,status) "
            "VALUES(?,?,?,?,?,?)",
            (1, "2026-11-05", "09:00", "10:00", "TEST-HFA01", "CANCELLED"),
        )
        db.commit()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.server.service.close()
        self.tmp.cleanup()

    def login(self, username: str) -> ApiClient:
        client = ApiClient(self.server)
        status, payload = client.request(
            "POST", "/api/auth/login", {"login": username, "password": TEST_PASSWORD}
        )
        self.assertEqual(status, 200, payload)
        return client

    def test_hfa01_denied_roles_cannot_call_hidden_route(self) -> None:
        body = {"class_url": "/training/class/ENG-FND-01", "cancelled_session_date": "2026-11-05"}
        anonymous = ApiClient(self.server)
        status, payload = anonymous.request("POST", "/api/center-tool/restore-cancelled", body)
        self.assertEqual(status, 401, payload)
        self.assertEqual(payload["error"]["code"], "AUTH_REQUIRED")
        for username in ("teacher", "student"):
            client = self.login(username)
            status, payload = client.request("POST", "/api/center-tool/restore-cancelled", body)
            self.assertEqual(status, 403, (username, payload))
            self.assertEqual(payload["error"]["code"], "FORBIDDEN")
            status, payload = client.request(
                "POST",
                "/api/center-tool/change-start-date",
                {"class_url": "/training/class/ENG-FND-01", "new_start_date": "2026-11-08"},
            )
            self.assertEqual(status, 403, (username, payload))
            self.assertEqual(payload["error"]["code"], "FORBIDDEN")

    def test_admin_can_execute_hfa01_fixture_action(self) -> None:
        admin = self.login("admin")
        status, payload = admin.request(
            "POST",
            "/api/center-tool/restore-cancelled",
            {"class_url": "/training/class/ENG-FND-01", "cancelled_session_date": "2026-11-05"},
        )
        self.assertEqual(status, 200, payload)
        self.assertEqual(payload["data"]["status"], "SCHEDULED")


if __name__ == "__main__":
    unittest.main()
