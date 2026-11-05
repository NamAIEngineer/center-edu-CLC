"""Focused Finance/Sale gap checks: persistence, validation, RBAC, export, empty state."""
from __future__ import annotations

import csv
import io
import sqlite3
import unittest

from modules.crm_routes import CRMRoutesStore
from modules.finance_appointment import FinanceAppointment
from modules.finance_item import create_item, ensure_schema as ensure_item_schema, update_item
from modules.finance_points import FinancePoints
from modules.finance_transfer import FinanceTransfer


class FinanceSaleGapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row

    def tearDown(self) -> None:
        self.db.close()

    def test_finance_empty_state_is_persistent_and_truthful(self) -> None:
        points = FinancePoints(self.db)
        self.assertEqual(points.list(role="ADMIN")["items"], [])
        self.assertEqual(points.list(status="active")["total"], 0)
        with self.assertRaises(ValueError):
            points.list(status="UNKNOWN")

    def test_finance_update_validation_and_rbac_fail_closed(self) -> None:
        appointments = FinanceAppointment(self.db)
        row = appointments.create({
            "student_name": "Nguyễn Minh Anh", "appointment_date": "2026-11-03",
            "reference_code": "HD-GAP-001", "amount": 500000,
        }, role="ADMIN", actor="Quản trị viên")
        with self.assertRaises(PermissionError):
            appointments.update(row["id"], {"status": "Đã xử lý"}, role="TEACHER", actor="Giáo viên")
        with self.assertRaises(ValueError):
            appointments.update(row["id"], {"student_name": "", "reference_code": ""}, role="STAFF", actor="Nhân viên")

        transfers = FinanceTransfer(self.db)
        transfer = transfers.create({
            "transfer_code": "CN-GAP-001", "transfer_date": "2026-11-03",
            "from_student_name": "Nguyễn Minh Anh", "to_student_name": "Trần Minh Đức",
        }, role="ADMIN", actor="Quản trị viên")
        with self.assertRaises(ValueError):
            transfers.update(transfer["id"], {"to_student_name": "Nguyễn Minh Anh"}, role="STAFF", actor="Nhân viên")

    def test_finance_item_missing_update_does_not_succeed(self) -> None:
        ensure_item_schema(self.db)
        with self.assertRaises(KeyError):
            update_item(self.db, 999, {"code": "IT-GAP", "fullname": "Sách", "status": "Hoạt động"}, role="ADMIN")
        item_id = create_item(self.db, {"code": "IT-GAP-001", "fullname": "Sách", "status": "Hoạt động"}, role="ADMIN")
        self.assertEqual(self.db.execute("SELECT id FROM finance_items WHERE id=?", (item_id,)).fetchone()[0], item_id)

    def test_sale_route_crud_filter_export_soft_delete_and_rbac(self) -> None:
        sale = CRMRoutesStore(self.db)
        route = "/sale/pending_enrollment/index"
        data = {"customer_name": "Lê Khánh Linh", "center_name": "Trung tâm Cầu Giấy", "status": "Đang chờ", "created_by": "Nhân viên Sale", "course_name": "IELTS Foundation"}
        row = sale.create(route, role="ADMIN", created_by="Quản trị viên", data=data)
        self.assertEqual(sale.list(route, role="STAFF", filters={"status": "Đang chờ"})[0]["id"], row["id"])
        updated = sale.update(route, row["id"], role="STAFF", data={"status": "Đã vào lớp"})
        self.assertEqual(updated["status"], "Đã vào lớp")
        exported = sale.export_csv(route, role="STAFF", filters={"status": "Đã vào lớp"})
        self.assertIn("Lê Khánh Linh", exported)
        with self.assertRaises(PermissionError):
            sale.create(route, role="TEACHER", created_by="Giáo viên", data=data)
        sale.delete(route, row["id"], role="ADMIN")
        self.assertEqual(sale.list(route, role="ADMIN"), [])


if __name__ == "__main__":
    unittest.main()
