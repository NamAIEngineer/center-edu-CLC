"""Disposable HTTP CRUD and reload persistence for the holiday screen."""

from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import quote

from app import create_server
from test_app import ApiClient, TEST_PASSWORD


class HolidayCrudHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.server = create_server(Path(self.tmp.name) / "holiday-crud.sqlite3", "127.0.0.1", 0)
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

    def _list(self, query: str = "") -> tuple[int, dict]:
        route = quote("/center/holiday/index", safe="")
        suffix = f"&q={quote(query)}" if query else ""
        return self.admin.request("GET", f"/api/generated/screens?route={route}{suffix}")

    def test_create_search_update_reload_delete_and_missing_are_persistent(self) -> None:
        original_name = "TEST-HOLIDAY-CRUD-R16"
        updated_name = "TEST-HOLIDAY-CRUD-R16-UPDATED"
        payload = {
            "route": "/center/holiday/index",
            "data": {
                "name": original_name,
                "start_date": "2027-01-10",
                "end_date": "2027-01-11",
                "description": "TEST disposable holiday",
                "notice": "TEST only",
                "status": "Kích hoạt",
            },
        }
        status, created = self.admin.request("POST", "/api/generated/screens", payload)
        self.assertEqual(status, 201, created)
        row = created["data"]
        record_id = int(row["id"])
        self.assertEqual(row["data"]["name"], original_name)

        status, listed = self._list("TEST-HOLIDAY-CRUD-R16")
        self.assertEqual(status, 200, listed)
        self.assertEqual([item["id"] for item in listed["data"]["records"]], [record_id])

        update = {
            "route": "/center/holiday/index",
            "data": {**row["data"], "name": updated_name},
            "version": row["version"],
            "updated_at": row["updated_at"],
            "full_body": True,
        }
        status, changed = self.admin.request("POST", f"/api/generated/screens/{record_id}", update)
        self.assertEqual(status, 200, changed)
        self.assertEqual(changed["data"]["data"]["name"], updated_name)

        # A fresh GET (the browser reload contract) must read the updated row.
        status, reloaded = self._list("TEST-HOLIDAY-CRUD-R16-UPDATED")
        self.assertEqual(status, 200, reloaded)
        self.assertEqual([item["id"] for item in reloaded["data"]["records"]], [record_id])

        status, deleted = self.admin.request(
            "DELETE", f"/api/generated/screens/{record_id}?route={quote('/center/holiday/index', safe='')}"
        )
        self.assertEqual(status, 200, deleted)
        self.assertTrue(deleted["data"]["deleted"])
        status, missing = self.admin.request(
            "DELETE", f"/api/generated/screens/{record_id}?route={quote('/center/holiday/index', safe='')}"
        )
        self.assertEqual(status, 404, missing)
        self.assertEqual(missing["error"]["code"], "NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
