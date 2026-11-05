"""W3 focused checks for the standalone CRM prospect/care contract."""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from modules.crm_domain import CRMStore
from modules.crm_routes import CRMRoutesStore, READ_ONLY_ROUTES, ROUTE_CONTRACTS, route_manifest


class W3CRMVerticalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "crm.sqlite3"
        self.db = sqlite3.connect(self.db_path)
        self.store = CRMStore(self.db)

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_persistent_prospect_and_care_workflow(self) -> None:
        prospect = self.store.create_prospect(
            role="ADMIN",
            full_name="Nguyễn Minh Anh",
            phone="0901234567",
            source="Website",
            sale_owner="Trần Thu Hà",
            interested_course="IELTS Foundation",
        )
        self.assertTrue(prospect["customer_code"].startswith("KH-TIEM-"))
        self.assertEqual(prospect["status"], "Khách hàng mới")

        appointment = self.store.create_appointment(
            role="ADMIN",
            prospect_id=prospect["id"],
            appointment_at="2026-11-15 09:30",
            action_type="Gọi",
            note="Tư vấn lộ trình và hẹn test đầu vào",
            created_by="Quản trị viên trung tâm",
        )
        self.assertEqual(appointment["status"], "Chưa xử lý")
        self.assertEqual(len(self.store.get_prospect(prospect["id"], role="ADMIN")["appointments"]), 1)

        self.store.update_appointment(appointment["id"], role="ADMIN", status="Đã xử lý")
        self.store.update_prospect(prospect["id"], role="ADMIN", status="Đủ điều kiện", care_progress="2/5")
        summary = self.store.summary(role="STAFF")
        self.assertEqual(summary["prospect_count"], 1)
        self.assertEqual(summary["appointment_statuses"]["Đã xử lý"], 1)
        self.db.close()

        reopened = sqlite3.connect(self.db_path)
        self.store = CRMStore(reopened)
        rows = self.store.list_prospects(role="STAFF", query="Minh Anh", status="Đủ điều kiện")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["care_progress"], "2/5")
        appointments = self.store.list_appointments(role="STAFF", status="Đã xử lý", date_from="2026-11-01", date_to="2026-11-30")
        self.assertEqual(len(appointments), 1)
        reopened.close()

    def test_manifest_matches_coordinator_route_order(self) -> None:
        expected = [
            "/crm/potential/index", "/crm/potential/appointment", "/crm/sale_team/index", "/crm/target/index",
            "/crm/class_enroll_trail_wait", "/crm/event2/index", "/crm/customer_test", "/crm/pending_enrollment/index",
            "/sale/potential/index", "/sale/contract", "/sale/bill/index", "/sale/class_enroll_trail_wait",
            "/sale/customer_test", "/sale/potential/appointment", "/sale/appointment_date", "/sale/pending_enrollment/index",
            "/crm/discount", "/crm/packet", "/dashboard/crm", "/dashboard/sale",
        ]
        self.assertEqual([item["route"] for item in route_manifest()], expected)

    def test_filter_export_and_fail_closed_roles(self) -> None:
        self.store.create_prospect(role="ADMIN", full_name="Lê Quốc Bảo", sale_owner="Trần Thu Hà", source="Sự kiện")
        self.store.create_prospect(role="ADMIN", full_name="Phạm Ngọc Linh", sale_owner="Nguyễn Hải Yến", source="Giới thiệu")
        self.assertEqual(len(self.store.list_prospects(role="STAFF", sale_owner="Trần Thu Hà")), 1)
        csv_text = self.store.export_prospects(role="STAFF", source="Sự kiện")
        self.assertIn("Khách hàng", csv_text)
        self.assertIn("Lê Quốc Bảo", csv_text)
        with self.assertRaises(PermissionError):
            self.store.list_prospects(role="STUDENT")
        with self.assertRaises(PermissionError):
            self.store.create_prospect(role="TEACHER", full_name="Không được tạo")

    def test_validation_and_soft_delete(self) -> None:
        prospect = self.store.create_prospect(role="ADMIN", full_name="Đỗ Mai Chi")
        with self.assertRaises(ValueError):
            self.store.create_appointment(role="ADMIN", prospect_id=prospect["id"], appointment_at="15/11/2026 09:30", action_type="Gọi", note="Sai định dạng", created_by="Admin")
        with self.assertRaises(ValueError):
            self.store.create_prospect(role="ADMIN", full_name="Sai trạng thái", status="UNKNOWN")
        self.store.delete_prospect(prospect["id"], role="ADMIN")
        self.assertEqual(self.store.list_prospects(role="ADMIN"), [])

    def test_manifest_route_crud_filter_export_and_rbac(self) -> None:
        """Every W3-owned non-core route has a durable, validated contract."""
        route_store = CRMRoutesStore(self.db)
        payloads = {
            "/crm/sale_team/index": {"full_name": "Nguyễn Thu Hà", "phone": "0901112233", "center_name": "Trung tâm Cầu Giấy", "team_name": "Nhóm Sale Hà Nội"},
            "/crm/target/index": {"year": 2026, "scope": "Toàn trung tâm", "scope_name": "Trung tâm Cầu Giấy", "revenue_target": 100000000, "contract_target": 40, "renewal_target": 12},
            "/crm/class_enroll_trail_wait": {"customer_name": "Trần Minh Đức", "status": "Chưa phê duyệt", "class_name": "IELTS Foundation"},
            "/crm/event2/index": {"title": "Ngày hội tư vấn IELTS", "description": "Tư vấn lộ trình học tập", "start_at": "2026-11-20", "status": "Đang kích hoạt"},
            "/crm/customer_test": {"customer_name": "Lê Ngọc Anh", "test_date": "2026-11-21"},
            "/crm/pending_enrollment/index": {"customer_name": "Phạm Gia Bảo", "center_name": "Trung tâm Cầu Giấy", "status": "Đang chờ", "created_by": "Quản trị viên"},
            "/sale/contract": {"code": "HD-W3-001", "customer_name": "Vũ Minh Khôi", "created_date": "2026-11-02", "course_name": "IELTS Foundation", "total_vnd": 12000000, "paid_vnd": 4000000, "created_by": "Quản trị viên", "payment_status": "Còn nợ", "contract_status": "Đang thực hiện"},
            "/sale/bill/index": {"invoice_code": "HDN-W3-001", "customer_name": "Vũ Minh Khôi", "bill_type": "Học viên", "payment_vnd": 4000000, "created_by": "Quản trị viên", "confirmation_status": "Cần xác nhận"},
            "/sale/class_enroll_trail_wait": {"customer_name": "Nguyễn Hà Linh", "status": "Chưa phê duyệt", "class_name": "IELTS Foundation"},
            "/sale/customer_test": {"customer_name": "Hoàng Minh Châu", "test_date": "2026-11-22"},
            "/sale/appointment_date": {"status": "Chưa xử lý", "student_name": "Vũ Minh Khôi", "appointment_date": "2026-11-10", "amount_vnd": 8000000, "appointment_type": "Theo hợp đồng", "reference_code": "HD-W3-001"},
            "/sale/pending_enrollment/index": {"customer_name": "Đỗ Mai Chi", "center_name": "Trung tâm Cầu Giấy", "status": "Đang chờ", "created_by": "Quản trị viên"},
            "/crm/discount": {"code": "KM-W3-001", "name": "Ưu đãi tháng 11", "start_date": "2026-11-01", "discount_type": "%", "discount_value": 10, "apply_type": "Tất cả gói và khóa", "status": "Đang hoạt động"},
            "/crm/packet": {"name": "Gói IELTS Foundation 30 buổi", "price_vnd": 15000000, "net_price_vnd": 13500000, "status": "Hoạt động"},
        }
        self.assertEqual(set(payloads), set(ROUTE_CONTRACTS) - READ_ONLY_ROUTES)
        for route, payload in payloads.items():
            created = route_store.create(route, role="ADMIN", created_by="Quản trị viên", data=payload)
            self.assertEqual(route_store.list(route, role="STAFF", query=str(next(iter(payload.values())))), [created])
            exported = route_store.export_csv(route, role="STAFF")
            if ROUTE_CONTRACTS[route]["columns"]:
                self.assertTrue(exported.splitlines()[0], route)
            updated = route_store.update(route, created["id"], role="STAFF", data={next(iter(payload)): next(iter(payload.values()))})
            self.assertEqual(updated["id"], created["id"])
        with self.assertRaises(PermissionError):
            route_store.list("/sale/contract", role="TEACHER")
        with self.assertRaises(PermissionError):
            route_store.create("/crm/discount", role="TEACHER", created_by="Giáo viên", data=payloads["/crm/discount"])
        for route in READ_ONLY_ROUTES:
            self.assertEqual(route_store.list(route, role="STAFF"), [])
            with self.assertRaises(PermissionError):
                route_store.create(route, role="ADMIN", created_by="Quản trị viên", data={"as_of": "2026-11-02"})

    def test_observed_form_aliases_and_persisted_summary(self) -> None:
        route_store = CRMRoutesStore(self.db)
        event = route_store.create(
            "/crm/event2/index", role="ADMIN", created_by="Quản trị viên",
            data={"fullname": "Ngày hội IELTS", "description": "Tư vấn lộ trình", "start_at": "01/12/2026", "number_of_people": "40", "status": "Đang kích hoạt"},
        )
        self.assertEqual(event["title"], "Ngày hội IELTS")
        self.assertEqual(event["max_people"], 40)
        discount = route_store.create(
            "/crm/discount", role="ADMIN", created_by="Quản trị viên",
            data={"code": "KM-2026-01", "discount_name": "Ưu đãi mùa đông", "start_date": "01-12-2026", "discount_type": "0", "sale": 500000, "apply_type": "0", "status": "1"},
        )
        self.assertEqual(discount["name"], "Ưu đãi mùa đông")
        self.assertEqual(discount["discount_type"], "VND")
        self.assertEqual(discount["status"], "Đang hoạt động")
        self.assertEqual(route_store.summary("/crm/discount", role="STAFF")["record_count"], 1)


if __name__ == "__main__":
    unittest.main()
