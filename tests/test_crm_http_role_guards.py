"""Structured HTTP role guards for CRM/Sale route adapters."""
from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import quote

from app import create_server
from test_app import ApiClient, TEST_PASSWORD


CRM_ROUTES = (
    "/crm/class_enroll_trail_wait",
    "/crm/customer_test",
    "/crm/pending_enrollment/index",
    "/crm/sale_team/index",
    "/sale/class_enroll_trail_wait",
    "/sale/customer_test",
    "/sale/pending_enrollment/index",
)
DASHBOARD_ROUTES = ("/dashboard/crm", "/dashboard/sale")


class CrmHttpRoleGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.server = create_server(Path(self.tmp.name) / "crm-role.sqlite3", "127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.server.service.close()
        self.tmp.cleanup()

    def _login(self, login: str) -> ApiClient:
        client = ApiClient(self.server)
        status, payload = client.request("POST", "/api/auth/login", {"login": login, "password": TEST_PASSWORD})
        self.assertEqual(status, 200, payload)
        return client

    def test_anonymous_is_auth_required_for_all_nine_controls(self) -> None:
        anonymous = ApiClient(self.server)
        for route in CRM_ROUTES + DASHBOARD_ROUTES:
            status, payload = anonymous.request("GET", f"/api/generated/screens?route={quote(route)}")
            self.assertEqual(status, 401, (route, payload))
            self.assertEqual(payload["error"]["code"], "AUTH_REQUIRED")

    def test_teacher_get_and_write_are_structured_403_without_socket_drop(self) -> None:
        teacher = self._login("teacher")
        for route in CRM_ROUTES + DASHBOARD_ROUTES:
            status, payload = teacher.request("GET", f"/api/generated/screens?route={quote(route)}")
            self.assertEqual(status, 403, (route, payload))
            self.assertEqual(payload["error"]["code"], "FORBIDDEN")
            status, payload = teacher.request("POST", "/api/generated/screens", {"route": route, "data": {}})
            self.assertEqual(status, 403, (route, payload))
            self.assertEqual(payload["error"]["code"], "FORBIDDEN")

    def test_admin_read_contract_remains_available_and_dashboards_stay_read_only(self) -> None:
        admin = self._login("admin")
        for route in CRM_ROUTES + DASHBOARD_ROUTES:
            status, payload = admin.request("GET", f"/api/generated/screens?route={quote(route)}")
            self.assertEqual(status, 200, (route, payload))
        for route in DASHBOARD_ROUTES:
            status, payload = admin.request("POST", "/api/generated/screens", {"route": route, "data": {}})
            self.assertEqual(status, 403, (route, payload))
            self.assertEqual(payload["error"]["code"], "FORBIDDEN")

    def test_generated_crm_delete_requires_updated_at_token(self) -> None:
        admin = self._login("admin")
        route = "/crm/customer/raw"
        status, created = admin.request("POST", "/api/generated/screens", {
            "route": route,
            "data": {"full_name": "TEST-R19C CRM delete CAS", "source": "Form"},
        })
        self.assertEqual(status, 201, created)
        row = created["data"]
        status, payload = admin.request("DELETE", f"/api/generated/screens/{row['id']}?route={quote(route)}")
        self.assertEqual(status, 428, payload)
        self.assertEqual(payload["error"]["code"], "CONCURRENCY_TOKEN_REQUIRED")
        status, payload = admin.request("DELETE", f"/api/generated/screens/{row['id']}?route={quote(route)}&updated_at=stale")
        self.assertEqual(status, 409, payload)
        self.assertEqual(payload["error"]["code"], "CONFLICT")
        status, deleted = admin.request("DELETE", f"/api/generated/screens/{row['id']}?route={quote(route)}&updated_at={quote(row['updated_at'])}")
        self.assertEqual(status, 200, deleted)


if __name__ == "__main__":
    unittest.main()
