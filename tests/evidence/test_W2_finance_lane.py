"""Focused W2 persistent contract checks for the finance route manifest."""
from __future__ import annotations

import csv
import io
import sqlite3
import unittest

from modules.finance_appointment import FinanceAppointment, route_contract as appointment_contract
from modules.finance_assessment import FinanceAssessment
from modules.finance_bill import FinanceBill, route_contract as bill_contract
from modules.finance_contract import FinanceContract, route_contract as contract_contract
from modules.finance_dashboard import FinanceDashboard
from modules.finance_debit_item import DebitItemRepository
from modules.finance_history_move import FinanceHistoryMove
from modules.finance_item import ensure_schema as ensure_item_schema, create_item, list_items, route_contract as item_contract
from modules.finance_points import FinancePoints, route_contract as points_contract
from modules.finance_reserve import FinanceReserve
from modules.finance_revenue import FinanceRevenue, route_contract as revenue_contract
from modules.finance import FinanceSpend
from modules.finance_transfer import FinanceTransfer, route_contract as transfer_contract
from modules.finance_wallet import ensure_schema as ensure_wallet_schema, route_contract as wallet_contract


class W2FinanceLaneContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row

    def tearDown(self) -> None:
        self.db.close()

    def test_manifest_route_contracts_cover_observed_headers_and_filters(self) -> None:
        contracts = (
            contract_contract(), bill_contract(), revenue_contract(), appointment_contract(),
            points_contract(), item_contract(), transfer_contract(), wallet_contract(),
        )
        routes = {entry.get("route", entry.get("routes", [None])[0]) for entry in contracts}
        self.assertTrue({
            "/finance/contract", "/finance/bill/index", "/finance/revenue",
            "/finance/appointment_date", "/finance/accumulate_points", "/finance/item",
            "/finance/transfer/index", "/finance/wallet_co/index",
        }.issubset(routes))
        for entry in contracts:
            self.assertTrue(entry.get("headers"))
            self.assertTrue(entry.get("filters") is not None)
            self.assertTrue(entry.get("read_roles"))

    def test_contract_bill_revenue_transfer_crud_filter_export(self) -> None:
        contract = FinanceContract(self.db)
        created_contract = contract.create({
            "contract_code": "HD-W2-001", "created_date": "02/11/2026",
            "package_name": "Tiếng Anh cơ bản 1", "total_amount": 3_000_000,
            "paid_amount": 1_000_000, "sales_owner": "Nguyễn Ngọc Mai",
            "note": "Hợp đồng kiểm tra W2",
        }, role="ADMIN", actor="Nguyễn Ngọc Mai")
        self.assertEqual(created_contract["debt_amount"], 2_000_000)
        self.assertEqual(contract.list({"payment_status": "PARTIAL"})["total"], 1)
        updated_contract = contract.update(created_contract["id"], {"paid_amount": 3_000_000}, role="STAFF", actor="Nhân viên tài chính")
        self.assertEqual(updated_contract["debt_amount"], 0)
        self.assertTrue(contract.export_csv().startswith("\ufeff"))

        bill = FinanceBill(self.db)
        created_bill = bill.create({
            "invoice_code": "HD-W2-BILL-001", "contract_code": "HD-W2-001",
            "customer_name": "Nguyễn Minh Anh", "payment_amount": 3_000_000,
            "confirmation_status": "PENDING", "payment_method": "bank_transfer",
            "invoice_date": "02/11/2026", "center": "Trung tâm CenterOnline - Demo",
        }, role="ADMIN", actor="Nguyễn Ngọc Mai")
        self.assertEqual(bill.confirm(created_bill["id"], role="ADMIN", actor="Nguyễn Ngọc Mai")["confirmation_status"], "CONFIRMED")
        self.assertEqual(len(bill.list({"confirmation_status": "CONFIRMED"})), 1)
        self.assertIn("Đã xác nhận", bill.export_csv())

        revenue = FinanceRevenue(self.db)
        revenue.create({"code": "KT-W2-001", "name": "Phí kiểm tra", "price": 100_000, "discount_type": "FIXED", "discount_value": 0, "amount_due": 100_000, "center": "Trung tâm CenterOnline - Demo"}, role="ADMIN", actor="Nguyễn Ngọc Mai")
        self.assertEqual(len(revenue.list({"q": "kiểm tra"})), 1)
        self.assertIn("Theo tiền", revenue.export_csv())

        transfer = FinanceTransfer(self.db)
        transfer_row = transfer.create({"transfer_code": "CN-W2-001", "transfer_date": "02/11/2026", "from_student_name": "Nguyễn Minh Anh", "to_student_name": "Trần Hoàng Nam", "contract_code": "HD-W2-001", "course_name": "IELTS Start", "amount_received": 500_000, "status": "PENDING"}, role="ADMIN", actor="Nguyễn Ngọc Mai")
        self.assertEqual(transfer.list({"status": "PENDING"})[0]["id"], transfer_row["id"])
        self.assertIn("Chưa xử lý", transfer.export_csv())

    def test_remaining_routes_persist_and_enforce_rbac(self) -> None:
        appointment = FinanceAppointment(self.db)
        row = appointment.create({"student_name": "Lê Khánh Linh", "parent_name": "Phụ huynh Lê Khánh Linh", "appointment_date": "02/11/2026", "amount": 2_000_000, "appointment_type": "Theo hóa đơn", "reference_code": "HD-W2-001"}, role="ADMIN", actor="Nguyễn Ngọc Mai")
        self.assertEqual(appointment.list({"appointment_type": "Theo hóa đơn"})["total"], 1)
        with self.assertRaises(PermissionError):
            appointment.create({"student_name": "X", "appointment_date": "02/11/2026", "reference_code": "X"}, role="TEACHER", actor="Giáo viên")

        spend = FinanceSpend(self.db)
        spend.create({
            "code": "PC-W2-001", "spend_date": "02/11/2026", "center_id": "demo",
            "center_name": "Trung tâm CenterOnline - Demo", "content": "Chi phí kiểm tra nhãn",
            "note": "", "category": "Vận hành", "amount_vnd": 120_000,
            "payment_method": "bank_transfer",
        }, role="ADMIN", actor="Nguyễn Ngọc Mai")
        self.assertIn("Chuyển khoản", spend.export_csv())

        FinanceBill(self.db).create({"invoice_code": "HD-W2-DASH-001", "customer_name": "Lê Khánh Linh", "payment_amount": 1_000_000, "confirmation_status": "CONFIRMED", "invoice_date": "02/11/2026"}, role="ADMIN", actor="Nguyễn Ngọc Mai")

        assessment = FinanceAssessment(self.db)
        assessment.create({"name": "Bảng giá IELTS", "date_apply": "02/11/2026", "course_name": "IELTS Start", "old_price": 2_500_000, "new_price": 2_700_000}, role="ADMIN", actor="Nguyễn Ngọc Mai")
        reserve = FinanceReserve(self.db)
        reserve.create({"student_name": "Phạm Gia Huy", "reserve_date": "02/11/2026", "amount_or_days": 8_000_000, "contract_code": "HD-W2-001", "course_name": "IELTS Start"}, role="ADMIN", actor="Nguyễn Ngọc Mai")
        history = FinanceHistoryMove(self.db)
        history.create({"student_name": "Võ Ngọc Mai", "original_course_name": "Tiếng Anh cơ bản 1", "destination_course_name": "IELTS Start", "remaining_amount": 2_000_000, "remaining_sessions": 8, "price_vnd": 250_000, "additional_amount": 0}, role="ADMIN", actor="Nguyễn Ngọc Mai")
        points = FinancePoints(self.db)
        point = points.create({"code": "AP-W2-001", "name": "Tích điểm tháng 11", "status": "active", "amount_per_point": 100, "conversion_rate": 10_000, "center_id": "demo", "center_name": "Trung tâm CenterOnline - Demo"}, role="ADMIN", actor="Nguyễn Ngọc Mai")
        self.assertEqual(points.get(point["id"])["code"], "AP-W2-001")
        ensure_item_schema(self.db)
        item_id = create_item(self.db, {"code": "IT-W2-001", "fullname": "Sách ngữ pháp cơ bản", "category": "Học liệu", "quantity": 3, "sale_price": 150_000, "status": "Hoạt động"}, role="ADMIN")
        self.assertEqual(list_items(self.db, {"q": "ngữ pháp"})[0]["id"], item_id)
        debit = DebitItemRepository(self.db)
        debit.create(role="ADMIN", invoice_code="HD-W2-001", invoice_date="2026-11-02", customer_name="Nguyễn Minh Anh", item_name="Sách ngữ pháp cơ bản", quantity=1, total_amount=150_000)
        ensure_wallet_schema(self.db)
        self.db.execute("INSERT INTO finance_wallets(student_name,branch,total_amount,used_amount,unused_amount,status,note,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)", ("Nguyễn Minh Anh", "Trung tâm CenterOnline - Demo", 3_000_000, 0, 3_000_000, "Kích hoạt", "", "now", "now")); self.db.commit()
        self.assertEqual(len(__import__("modules.finance_wallet", fromlist=["list_wallets"]).list_wallets(self.db, {"q": "Minh Anh"})), 1)

        dashboard = FinanceDashboard(self.db)
        summary = dashboard.summary(role="ADMIN")
        self.assertEqual(summary["route"], "/dashboard/finance")
        self.assertGreaterEqual(summary["bill_count"], 1)
        with self.assertRaises(PermissionError):
            dashboard.summary(role="STUDENT")

    def test_no_placeholder_or_english_customer_enum_in_contract_exports(self) -> None:
        for module_name in ("modules.finance_contract", "modules.finance_bill", "modules.finance_revenue", "modules.finance_transfer"):
            module = __import__(module_name, fromlist=["route_contract"])
            text = str(module.route_contract())
            self.assertNotIn("UNKNOWN", text)
            self.assertNotIn("Chưa cập nhật", text)


if __name__ == "__main__":
    unittest.main()
