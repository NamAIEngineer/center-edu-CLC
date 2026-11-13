"""Route-owned HFA02 contract checks against a disposable SQLite service."""
from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import urlencode

from app import CenterEduService, create_server
from test_app import ApiClient, TEST_PASSWORD


class Hfa02CustomerCareTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.service = CenterEduService(Path(self.tmp.name) / "hfa02.db")
        self.admin = self.service.user_by_login("admin")
        self.service.db.execute("DELETE FROM w6_route_records WHERE route='/cso/customer-care'")
        self.service.db.commit()

    def tearDown(self) -> None:
        self.service.close()
        self.tmp.cleanup()

    def _create(self, name: str, *, action: str, result: str, purpose: str, date: str) -> dict:
        return self.service.add_generated_record(self.admin, "/cso/customer-care", {"data": {
            "student_name": name, "class_name": "Lớp Tiếng Anh giao tiếp A1",
            "staff_name": "Nguyễn Ngọc Mai", "care_round": "Lần 01", "content": name,
            "action": action, "purpose": purpose, "result": result, "care_date": date,
            "status": "Chưa xử lý", "note": "",
        }})

    def test_contract_has_observed_columns_and_multiselect_filters(self) -> None:
        spec = self.service.generated_screen(self.admin, "/cso/customer-care")["spec"]
        self.assertEqual(len(spec["columns"]), 13)
        multi = [item for item in spec["filters"] if item.get("multiple")]
        self.assertEqual(len(multi), 3)
        self.assertEqual({item["name"] for item in spec["filters"] if item["name"].endswith("_search")}, set())

    def test_filters_use_or_within_and_across(self) -> None:
        self._create("TEST-HFA02-A", action="Gọi điện", result="Đồng ý", purpose="Khảo sát", date="2026-11-10")
        self._create("TEST-HFA02-B", action="Nhắn tin", result="Từ chối", purpose="Bán thêm", date="2026-11-11")
        both_actions = self.service.generated_screen(self.admin, "/cso/customer-care", filters={"action": ["Gọi điện", "Nhắn tin"]})
        self.assertEqual(len(both_actions["records"]), 2)
        conjunction = self.service.generated_screen(self.admin, "/cso/customer-care", filters={"action": ["Gọi điện", "Khảo sát"], "result": ["Đồng ý"]})
        self.assertEqual([row["data"]["student_name"] for row in conjunction["records"]], ["TEST-HFA02-A"])

    def test_paired_search_controls_filter_their_domain_field(self) -> None:
        self._create("TEST-HFA02-SEARCH-A", action="Gọi điện", result="Đồng ý", purpose="Khảo sát", date="2026-11-10")
        self._create("TEST-HFA02-SEARCH-B", action="Nhắn tin", result="Từ chối", purpose="Bán thêm", date="2026-11-11")
        filtered = self.service.generated_screen(self.admin, "/cso/customer-care", filters={
            "action_search": "gọi", "result_search": "đồng",
        })
        self.assertEqual([row["data"]["student_name"] for row in filtered["records"]], ["TEST-HFA02-SEARCH-A"])

    def test_update_reload_and_filtered_export_persist(self) -> None:
        row = self._create("TEST-HFA02-PERSIST", action="Gọi điện", result="Đồng ý", purpose="Khảo sát", date="2026-11-10")
        self.service.update_generated_record(self.admin, "/cso/customer-care", row["id"], {"data": {"status": "Đã xong"}})
        reloaded = self.service.generated_screen(self.admin, "/cso/customer-care", query="TEST-HFA02-PERSIST")["records"]
        self.assertEqual(reloaded[0]["data"]["status"], "Đã xong")
        exported = self.service.export_generated_screen(self.admin, "/cso/customer-care", filters={"action": ["Gọi điện"]})
        self.assertEqual(exported[0]["Học viên"], "TEST-HFA02-PERSIST")


if __name__ == "__main__":
    unittest.main()


class Hfa02CustomerCareHttpSearchTests(unittest.TestCase):
    """Ensure transport forwards the three paired search controls."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.server = create_server(Path(self.tmp.name) / "hfa02-http.db", "127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.admin = ApiClient(self.server)
        status, payload = self.admin.request("POST", "/api/auth/login", {
            "login": "admin", "password": TEST_PASSWORD,
        })
        self.assertEqual(status, 200, payload)

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.server.service.close()
        self.tmp.cleanup()

    def _create(self, name: str, action: str, result: str, purpose: str) -> int:
        status, payload = self.admin.request("POST", "/api/generated/screens", {"route": "/cso/customer-care", "data": {
            "student_name": name, "class_name": "Lớp Tiếng Anh giao tiếp A1",
            "staff_name": "Nguyễn Ngọc Mai", "care_round": "Lần 01", "content": name,
            "action": action, "purpose": purpose, "result": result, "care_date": "2026-11-10",
            "status": "Chưa xử lý", "note": "",
        }})
        self.assertEqual(status, 201, payload)
        return payload["data"]["id"]

    def _delete(self, record_id: int) -> int:
        status, payload = self.admin.request("GET", "/api/generated/screens?route=%2Fcso%2Fcustomer-care")
        row = next(item for item in payload["data"]["records"] if item["id"] == record_id)
        query = urlencode({"route": "/cso/customer-care", "version": row["version"], "updated_at": row["updated_at"]})
        return self.admin.request_raw("DELETE", f"/api/generated/screens/{record_id}?{query}")[0]

    def test_search_controls_round_trip_over_get_and_export(self) -> None:
        first = self._create("TEST-HFA02-HTTP-A", "Gọi điện", "Đồng ý", "Khảo sát")
        second = self._create("TEST-HFA02-HTTP-B", "Nhắn tin", "Từ chối", "Bán thêm")
        query = urlencode({"action_search": "gọi", "result_search": "đồng", "purpose_search": "khảo"})
        status, payload = self.admin.request("GET", f"/api/generated/screens?route=%2Fcso%2Fcustomer-care&{query}")
        self.assertEqual(status, 200, payload)
        self.assertEqual([row["id"] for row in payload["data"]["records"]], [first])
        status, headers, body = self.admin.request_raw("GET", f"/api/export/generated-screen?route=%2Fcso%2Fcustomer-care&{query}")
        self.assertEqual(status, 200)
        self.assertIn("text/csv", headers["Content-Type"])
        self.assertIn(b"TEST-HFA02-HTTP-A", body)
        self.assertNotIn(b"TEST-HFA02-HTTP-B", body)
        self.assertEqual(self._delete(first), 200)
        self.assertEqual(self._delete(second), 200)

    def test_multiselect_export_joins_values_and_includes_both_rows(self) -> None:
        first = self._create("TEST-HFA02-EXPORT-A", "Gọi điện", "Đồng ý", "Khảo sát")
        second = self._create("TEST-HFA02-EXPORT-B", "Nhắn tin", "Từ chối", "Bán thêm")
        query = urlencode({"action": "Gọi điện,Nhắn tin"})
        status, headers, body = self.admin.request_raw("GET", f"/api/export/generated-screen?route=%2Fcso%2Fcustomer-care&{query}")
        self.assertEqual(status, 200)
        self.assertIn("text/csv", headers["Content-Type"])
        self.assertIn(b"TEST-HFA02-EXPORT-A", body)
        self.assertIn(b"TEST-HFA02-EXPORT-B", body)
        lines = body.decode("utf-8-sig").splitlines()
        self.assertEqual(sum("TEST-HFA02-EXPORT-A" in line for line in lines), 1)
        self.assertEqual(sum("TEST-HFA02-EXPORT-B" in line for line in lines), 1)
        for record_id in (first, second):
            self.assertEqual(self._delete(record_id), 200)

    def test_missing_delete_id_returns_not_found_json(self) -> None:
        status, headers, body = self.admin.request_raw("DELETE", "/api/generated/screens/987654321?route=%2Fcso%2Fcustomer-care")
        self.assertEqual(status, 404)
        self.assertIn("application/json", headers.get("Content-Type", ""))
        payload = __import__("json").loads(body.decode("utf-8"))
        self.assertEqual(payload["error"]["code"], "NOT_FOUND")
