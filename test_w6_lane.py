"""Focused W6 route-group tests for persistent Center EDU contracts."""

from __future__ import annotations

import csv
import io
import sqlite3
import unittest

from modules import center_lane


GROUPS = {
    "center": ("/center/student/index", "/center/teacher", "/center/parent/index", "/center/staff", "/center/holiday/index", "/center/manager/index", "/center/options", "/center/tool/center/index", "/center/document-permission", "/center/upload_address"),
    "setup": ("/setup/classroom", "/setup/daily-evaluation", "/setup/criteria"),
    "cso": ("/cso/support", "/cso/customer-care"),
    "callcenter": ("/callcenter/extension", "/callcenter/staff", "/callcenter/get-statistic", "/callcenter/history"),
    "tenant": ("/tenant/config_excel",),
}


class W6LaneContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        center_lane.ensure_schema(self.db)

    def tearDown(self) -> None:
        self.db.close()

    def test_every_manifest_route_has_persistent_crud_filter_export(self) -> None:
        for group, routes in GROUPS.items():
            with self.subTest(group=group):
                for route in routes:
                    with self.subTest(route=route):
                        contract = center_lane.route_contract(route)
                        self.assertTrue(contract.title)
                        self.assertTrue(contract.entity)
                        self.assertEqual(center_lane.seed(self.db, route), 1)
                        rows = center_lane.list_records(self.db, route)
                        expected_rows = len(center_lane.SEED_ROWS.get(route, ())) or 1
                        self.assertEqual(len(rows), expected_rows)
                        searchable = next((str(value) for value in rows[0]["data"].values() if isinstance(value, str) and len(value) > 2), "")
                        filtered_rows = center_lane.list_records(self.db, route, {"q": searchable[: max(1, min(8, len(searchable)))]})
                        self.assertGreaterEqual(len(filtered_rows), 1)
                        self.assertLessEqual(len(filtered_rows), len(rows))
                        created_data = dict(center_lane.SEEDS.get(route, {}))
                        for field in contract.fields:
                            if field["name"] in created_data:
                                continue
                            field_type = str(field.get("type", "")).lower()
                            if field_type in {"date", "datetime", "date-text"}:
                                value = "15/11/2026"
                            elif field_type in {"number", "integer"}:
                                value = 12
                            elif field.get("options"):
                                value = field["options"][0]
                            else:
                                value = "Giá trị kiểm tra"
                            created_data[field["name"]] = value
                        created = center_lane.create_record(self.db, route, created_data)
                        updated = center_lane.update_record(self.db, route, created["id"], {next(iter(created_data)): created_data[next(iter(created_data))]})
                        self.assertEqual(updated["id"], created["id"])
                        csv_text = center_lane.export_csv(self.db, route)
                        self.assertTrue(csv_text.startswith("\ufeff"))
                        self.assertGreaterEqual(len(list(csv.reader(io.StringIO(csv_text.lstrip("\ufeff"))))), 2)

    def test_rbac_soft_delete_and_vietnamese_seed_safety(self) -> None:
        route = "/setup/classroom"
        center_lane.seed(self.db, route)
        with self.assertRaises(PermissionError):
            center_lane.list_records(self.db, route, role="STUDENT")
        row = center_lane.list_records(self.db, route)[0]
        with self.assertRaises(PermissionError):
            center_lane.archive_record(self.db, route, row["id"], role="STAFF")
        center_lane.archive_record(self.db, route, row["id"], role="ADMIN")
        self.assertEqual(center_lane.list_records(self.db, route), [])
        with self.assertRaisesRegex(KeyError, "Không tìm thấy bản ghi"):
            center_lane.archive_record(self.db, route, row["id"], role="ADMIN")
        for seed in center_lane.SEEDS.values():
            encoded = str(seed)
            self.assertNotIn("UNKNOWN", encoded)
            self.assertNotIn("Chưa cập nhật", encoded)

    def test_missing_seed_fails_closed_without_fake_row(self) -> None:
        route = "/setup/classroom"
        original = center_lane.SEEDS.pop(route)
        try:
            with self.assertRaisesRegex(ValueError, "Chưa có dữ liệu khởi tạo tự nhiên"):
                center_lane.seed(self.db, route)
            self.assertEqual(center_lane.list_records(self.db, route), [])
        finally:
            center_lane.SEEDS[route] = original

    def test_date_range_and_enum_filters_are_semantic(self) -> None:
        route = "/cso/customer-care"
        center_lane.seed(self.db, route)
        self.assertEqual(len(center_lane.list_records(self.db, route, {"date_from": "02/11/2026", "date_to": "04/11/2026"})), 1)
        self.assertEqual(len(center_lane.list_records(self.db, route, {"date_from": "04/11/2026", "date_to": "05/11/2026"})), 0)
        contract = center_lane.route_contract(route)
        purpose = next(field for field in contract.fields if field["name"] == "purpose")
        self.assertIn("Bán thêm", purpose["options"])
        self.assertNotIn("Upsale", purpose["options"])

    def test_form_normalization_rejects_bad_enum_and_accepts_date_number(self) -> None:
        classroom = center_lane.route_contract("/setup/classroom")
        normalized = center_lane.validate_data(
            classroom,
            {"code": "P-B202", "name": "Phòng học B202", "capacity": "18", "status": "Hoạt động"},
        )
        self.assertEqual(normalized["capacity"], 18)
        holiday = center_lane.route_contract("/center/holiday/index")
        normalized_holiday = center_lane.validate_data(
            holiday,
            {"name": "Nghỉ Tết", "start_date": "01/02/2027", "status": "Kích hoạt"},
        )
        self.assertEqual(normalized_holiday["start_date"], "2027-02-01")
        with self.assertRaisesRegex(ValueError, "lựa chọn không hợp lệ"):
            center_lane.validate_data(classroom, {"code": "P-B203", "name": "Phòng học B203", "status": "ACTIVE"})

    def test_register_initializes_schema_and_returns_host_metadata(self) -> None:
        class Service:
            db = self.db

        metadata = center_lane.register(Service(), Service())
        self.assertEqual(metadata["status"], "PERSISTENT_LOCAL_CONTRACT")
        self.assertIn("/setup/classroom", metadata["routes"])
        self.assertEqual(
            self.db.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='w6_route_records'").fetchone()[0],
            1,
        )


if __name__ == "__main__":
    unittest.main()
