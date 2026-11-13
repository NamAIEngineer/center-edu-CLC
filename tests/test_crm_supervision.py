"""W4 CRM/Sale/CSO supervision checks.

These tests exercise owned domain seams with temporary SQLite state.  They do
not assert private reference API behavior; ``/sale/contract`` authority is
explicitly the integrated finance module until the coordinator wires a
different route owner.
"""
from __future__ import annotations

import sqlite3
import unittest
import csv
import io

from modules.center_lane import (
    CONTRACTS,
    archive_record,
    create_record,
    ensure_schema as ensure_cso_schema,
    export_csv as export_cso_csv,
    list_records,
    seed as seed_cso,
    update_record,
)
from modules.crm_domain import CRMStore
from modules.crm_next import AppointmentRepository
from modules.crm_routes import CRMRoutesStore, route_authority


class CRMCSOSupervisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row

    def tearDown(self) -> None:
        self.db.close()

    def test_crm_prospect_and_appointment_persist_with_negative_cases(self) -> None:
        store = CRMStore(self.db)
        prospect = store.create_prospect(
            role="ADMIN", full_name="Nguyễn Minh Anh", customer_code="KH-W4-001",
            sale_owner="Trần Thu Hà", interested_course="IELTS Foundation",
        )
        appointment = store.create_appointment(
            role="ADMIN", prospect_id=prospect["id"], appointment_at="2026-11-15 09:30",
            action_type="Gọi", note="Tư vấn lộ trình", created_by="Quản trị viên",
        )
        self.assertEqual(len(store.list_appointments(role="STAFF", sale_owner="Trần Thu Hà")), 1)
        self.assertIn("Nguyễn Minh Anh", store.export_prospects(role="STAFF"))
        self.assertIn("2026-11-15 09:30", store.export_appointments(role="STAFF"))
        with self.assertRaises(ValueError):
            store.list_appointments(role="STAFF", date_from="2026-11-30", date_to="2026-11-01")
        with self.assertRaises(ValueError):
            store.update_appointment(appointment["id"], role="ADMIN", unsupported="x")
        with self.assertRaises(PermissionError):
            store.list_prospects(role="TEACHER")
        store.delete_prospect(prospect["id"], role="ADMIN")
        self.assertEqual(store.list_prospects(role="ADMIN"), [])

    def test_cso_support_and_customer_care_use_one_persistent_contract(self) -> None:
        ensure_cso_schema(self.db)
        for route in ("/cso/support", "/cso/customer-care"):
            self.assertIn(route, CONTRACTS)
            self.assertEqual(seed_cso(self.db, route), 1)
            rows = list_records(self.db, route, role="STAFF")
            self.assertEqual(len(rows), 1)
            record_id = rows[0]["id"]
            self.assertTrue(export_cso_csv(self.db, route, role="STAFF").startswith("\ufeff"))
            if route == "/cso/support":
                updated = update_record(self.db, route, record_id, {"status": "Đang xử lý"}, role="STAFF")
            else:
                updated = update_record(self.db, route, record_id, {"status": "Đang xử lý"}, role="STAFF")
            self.assertEqual(updated["data"]["status"], "Đang xử lý")
            with self.assertRaises(PermissionError):
                create_record(self.db, route, {}, role="STUDENT")
            archive_record(self.db, route, record_id, role="ADMIN", expected_version=updated["version"], expected_updated_at=updated["updated_at"])
            self.assertEqual(list_records(self.db, route, role="STAFF"), [])

    def test_cso_export_maps_presentation_columns_to_domain_values(self) -> None:
        ensure_cso_schema(self.db)
        for route in ("/cso/support", "/cso/customer-care"):
            seed_cso(self.db, route)
            rows = list_records(self.db, route, role="STAFF")
            csv_text = export_cso_csv(self.db, route, role="STAFF")
            parsed = list(csv.reader(io.StringIO(csv_text.lstrip("\ufeff"))))
            self.assertGreaterEqual(len(parsed), 2)
            self.assertEqual(len(parsed[0]), len(parsed[1]))
            values = "|".join(parsed[1])
            if route == "/cso/support":
                self.assertIn(rows[0]["data"]["content"], values)
                self.assertIn(rows[0]["data"]["sender"], values)
                self.assertIn(rows[0]["data"]["deadline"], values)
            else:
                self.assertIn(rows[0]["data"]["student_name"], values)
                self.assertIn(rows[0]["data"]["class_name"], values)
                self.assertIn(rows[0]["data"]["care_round"], values)

    def test_route_store_rejects_reversed_ranges_and_unknown_fields(self) -> None:
        store = CRMRoutesStore(self.db)
        payload = {
            "code": "KM-W4-001", "name": "Ưu đãi tháng 11",
            "start_date": "2026-11-01", "discount_type": "%",
            "discount_value": 10, "apply_type": "Tất cả gói và khóa",
            "status": "Đang hoạt động",
        }
        row = store.create("/crm/discount", role="ADMIN", created_by="Quản trị viên", data=payload)
        self.assertEqual(store.list("/crm/discount", role="STAFF")[0]["id"], row["id"])
        with self.assertRaises(ValueError):
            store.list("/crm/discount", role="STAFF", filters={"date_from": "2026-12-01", "date_to": "2026-11-01"})
        with self.assertRaises(ValueError):
            store.create("/crm/discount", role="ADMIN", created_by="Quản trị viên", data={**payload, "unexpected": "x"})
        store.delete("/crm/discount", row["id"], role="ADMIN", expected_updated_at=row["updated_at"])
        self.assertEqual(store.list("/crm/discount", role="STAFF"), [])

    def test_sale_contract_authority_is_explicit_and_not_generic_mounted(self) -> None:
        authority = route_authority("/sale/contract")
        self.assertEqual(authority["owner"], "modules.finance_contract")
        self.assertFalse(authority["generic_store_mounted"])
        self.assertEqual(authority["status"], "SHARED_HOST_AUTHORITY")

    def test_payment_appointment_validation_is_strict_and_role_bound(self) -> None:
        appointments = AppointmentRepository(self.db)
        row = appointments.create(
            role="ADMIN", student_name="Nguyễn Minh Anh", appointment_date="15/11/2026",
            reference_code="HD-W4-001", amount=500000, appointment_type="Theo hợp đồng",
            created_by="Quản trị viên",
        )
        self.assertEqual(row["appointment_date"], "2026-11-15")
        with self.assertRaises(ValueError):
            appointments.list(role="STAFF", from_date="2026-12-01", to_date="2026-11-01")
        with self.assertRaises(ValueError):
            appointments.update(row["id"], role="STAFF", amount=-1)
        with self.assertRaises(ValueError):
            appointments.update(row["id"], role="STAFF", unsupported="x")
        with self.assertRaises(PermissionError):
            appointments.update(row["id"], role="TEACHER", status="Đã xử lý")


if __name__ == "__main__":
    unittest.main()
