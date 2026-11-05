"""Compatibility coverage for the legacy call-center history API path."""

from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from app import create_server
from test_app import ApiClient


class CallcenterHistoryAliasTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "center.sqlite3"
        self.server = create_server(self.db_path, "127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.server.service.close()
        self.tmp.cleanup()

    def login(self, login: str) -> ApiClient:
        client = ApiClient(self.server)
        status, payload = client.request(
            "POST", "/api/auth/login", {"login": login, "password": "ChangeMe!CenterEdu2026"}
        )
        self.assertEqual(status, 200, payload)
        return client

    def test_alias_requires_auth_and_preserves_role_boundary(self) -> None:
        anonymous = ApiClient(self.server)
        status, payload = anonymous.request("GET", "/api/callcenter/history")
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"]["code"], "AUTH_REQUIRED")

        for login in ("student", "teacher"):
            client = self.login(login)
            status, payload = client.request("GET", "/api/callcenter/history")
            self.assertEqual(status, 403, (login, payload))
            self.assertEqual(payload["error"]["code"], "FORBIDDEN")

    def test_alias_returns_same_filtered_contract_as_canonical_endpoint(self) -> None:
        staff = self.login("staff")
        status, created = staff.request(
            "POST", "/api/call-history",
            {
                "full_name": "Alias Filter Contact",
                "phone": "0900000001",
                "status": "CONNECTED",
                "call_type": "OUTBOUND",
                "party_role": "STUDENT",
                "staff_name": "Staff Alias",
                "called_at": "2026-11-05 09:30",
            },
        )
        self.assertEqual(status, 201, created)
        query = "/api/callcenter/history?status=CONNECTED&staff_name=Alias%20&date_from=2026-11-05&date_to=2026-11-05"
        alias_status, alias_payload = staff.request("GET", query)
        canonical_status, canonical_payload = staff.request(
            "GET", "/api/call-history?status=CONNECTED&staff_name=Alias%20&date_from=2026-11-05&date_to=2026-11-05"
        )
        self.assertEqual(alias_status, 200)
        self.assertEqual(canonical_status, 200)
        self.assertEqual(alias_payload, canonical_payload)
        self.assertEqual(len(alias_payload["data"]), 1)
        self.assertEqual(alias_payload["data"][0]["full_name"], "Alias Filter Contact")

    def test_alias_data_persists_across_server_restart(self) -> None:
        admin = self.login("admin")
        status, _ = admin.request(
            "POST", "/api/call-history", {"full_name": "Restart Contact", "status": "MISSED"}
        )
        self.assertEqual(status, 201)
        self.server.shutdown()
        self.server.server_close()
        self.server.service.close()

        self.server = create_server(self.db_path, "127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        restarted = self.login("admin")
        status, payload = restarted.request("GET", "/api/callcenter/history?status=MISSED")
        self.assertEqual(status, 200)
        self.assertEqual([row["full_name"] for row in payload["data"]], ["Restart Contact"])


if __name__ == "__main__":
    unittest.main()
