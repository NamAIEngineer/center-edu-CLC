"""W4 evidence checks for the CRM and Center report lane.

The checks use a temporary rich-demo SQLite database.  They exercise the
adapter through the service report engine and inspect the owned frontend
metadata without touching the shared shell.
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from app import CenterEduService


ROUTES = (
    "/report/crm/contract/index",
    "/report/crm/bill/index",
    "/report/center/birth_day/index",
    "/report/center/access_history",
    "/report/center/staff_teacher",
    "/report/center/class_post/index",
    "/report/crm/customer_care/index",
    "/report/crm/customer_care_result_by_center",
    "/report/crm/customer_care_result_by_district",
    "/report/crm/customer_care_result_by_dob",
    "/report/crm/customer_care_result_by_source",
    "/report/crm/customer_care_result_by_sale",
    "/report/crm/customer_care_result",
    "/report/crm/customer_report/index",
    "/report/crm/customer_trailer",
)


class W4ReportCrmCenterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.previous = os.environ.get("CENTER_EDU_RICH_DEMO")
        os.environ["CENTER_EDU_RICH_DEMO"] = "1"
        self.tempdir = tempfile.TemporaryDirectory()
        self.service = CenterEduService(Path(self.tempdir.name) / "w4.sqlite3")

    def tearDown(self) -> None:
        self.service.close()
        self.tempdir.cleanup()
        if self.previous is None:
            os.environ.pop("CENTER_EDU_RICH_DEMO", None)
        else:
            os.environ["CENTER_EDU_RICH_DEMO"] = self.previous

    def test_all_routes_have_observed_contract_or_truthful_no_data(self) -> None:
        for route in ROUTES:
            with self.subTest(route=route):
                report = self.service.report_engine_v2.run(route, limit=5)
                self.assertEqual(report["route"], route)
                self.assertIn(report["data_status"], {"OBSERVED", "PARTIAL", "NO_DATA"})
                payload = json.dumps(report, ensure_ascii=False)
                self.assertNotIn("UNKNOWN", payload)
                self.assertNotIn("Chưa cập nhật", payload)

    def test_finance_backed_rows_use_vietnamese_customer_labels(self) -> None:
        contract = self.service.report_engine_v2.run("/report/crm/contract/index", limit=1)
        bill = self.service.report_engine_v2.run("/report/crm/bill/index", limit=1)
        self.assertTrue(contract["rows"])
        self.assertTrue(bill["rows"])
        self.assertIn(contract["rows"][0]["o_tuong_kh"], {"Học viên đang học", "Khách hàng tiềm năng"})
        self.assertNotIn(contract["rows"][0]["ma_hop_ong"], {"DEMO-CONTRACT-005"})
        self.assertEqual(bill["rows"][0]["khach_hang"], "Võ Ngọc Mai")
        self.assertNotIn("Demo Customer", json.dumps(bill, ensure_ascii=False))
        self.assertNotIn("Academic Team", json.dumps(bill, ensure_ascii=False))
        self.assertNotIn("Center Administrator", json.dumps(contract, ensure_ascii=False))

    def test_owned_frontend_exposes_route_actions_and_register_hook(self) -> None:
        root = Path(__file__).parents[2]
        source = (root / "static" / "modules" / "report_crm_center.js").read_text(encoding="utf-8")
        self.assertIn("export async function register", source)
        self.assertIn("report-action", source)
        for route in ROUTES:
            self.assertIn(route, source)


if __name__ == "__main__":
    unittest.main()
