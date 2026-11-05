import os
import tempfile
import unittest
from pathlib import Path

from app import CenterEduService


ROUTES = (
    "/report/finance/revenue_center/by_month/center/index",
    "/report/finance/class_revenue_tracking/index",
    "/report/finance/class_revenue_tracking_new/index",
    "/report/finance/revenue_center",
    "/report/finance/revenue_center/by_month/sale_team/index",
    "/report/finance/revenue_center/by_month/sale/index",
    "/report/finance/revenue_source/index",
    "/report/finance/debt",
    "/report/finance/student_finance",
    "/report/finance/revenue_item/index",
    "/report/finance/revenue_item/export",
    "/report/finance/inventory_item/index",
    "/report/finance/payment/index",
    "/report/crm/contract/index",
    "/report/crm/bill/index",
    "/report/finance/reserve",
    "/report/center/student_statistical/index",
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
    "/report/crm/customer_statistic/index",
    "/report/crm/customer_trailer",
)


class W5ReportManifestTest(unittest.TestCase):
    def test_owned_backend_and_frontend_register_hooks_exist(self):
        root = Path(__file__).parents[2]
        finance_py = (root / "modules" / "finance_report_adapter.py").read_text(encoding="utf-8")
        crm_py = (root / "modules" / "report_crm_center.py").read_text(encoding="utf-8")
        finance_js = (root / "static" / "modules" / "report_finance.js").read_text(encoding="utf-8")
        payment_js = (root / "static" / "modules" / "report_finance_payment.js").read_text(encoding="utf-8")
        crm_js = (root / "static" / "modules" / "report_crm_center.js").read_text(encoding="utf-8")
        self.assertIn("def register(", finance_py)
        self.assertIn("def register(", crm_py)
        self.assertIn("export async function register", finance_js)
        self.assertIn("export async function register", payment_js)
        self.assertIn("export async function register", crm_js)
        self.assertIn("registerScreen", finance_js)
        self.assertIn("registerScreen", crm_js)

    def test_all_owned_routes_execute_without_generic_rows(self):
        old = os.environ.get("CENTER_EDU_RICH_DEMO")
        os.environ["CENTER_EDU_RICH_DEMO"] = "1"
        try:
            with tempfile.TemporaryDirectory() as td:
                service = CenterEduService(Path(td) / "w5-manifest.sqlite3")
                try:
                    for route in ROUTES:
                        with self.subTest(route=route):
                            report = service.report_engine_v2.run(route, limit=10)
                            self.assertIn(report["data_status"], {"OBSERVED", "PARTIAL", "NO_DATA"})
                            self.assertNotEqual(report["data_status"], "UNKNOWN")
                            self.assertEqual(report["route"], route)
                            if route.endswith("/export"):
                                exported = service.report_engine_v2.export_csv(route)
                                self.assertTrue(exported.splitlines()[0])
                finally:
                    service.close()
        finally:
            if old is None:
                os.environ.pop("CENTER_EDU_RICH_DEMO", None)
            else:
                os.environ["CENTER_EDU_RICH_DEMO"] = old


if __name__ == "__main__":
    unittest.main()
