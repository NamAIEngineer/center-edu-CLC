import json
import os
import tempfile
import unittest
from pathlib import Path

from app import CenterEduService


class W5CrmCenterReportTest(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.get("CENTER_EDU_RICH_DEMO")
        os.environ["CENTER_EDU_RICH_DEMO"] = "1"
        self.tmp = tempfile.TemporaryDirectory()
        self.service = CenterEduService(Path(self.tmp.name) / "w5.sqlite3")

    def tearDown(self):
        self.service.close()
        self.tmp.cleanup()
        if self._old is None:
            os.environ.pop("CENTER_EDU_RICH_DEMO", None)
        else:
            os.environ["CENTER_EDU_RICH_DEMO"] = self._old

    def test_center_and_crm_routes_use_domain_rows(self):
        for route in (
            "/report/center/staff_teacher",
            "/report/center/student_statistical/index",
            "/report/crm/customer_care/index",
            "/report/crm/customer_report/index",
            "/report/crm/customer_statistic/index",
            "/report/crm/customer_trailer",
            "/report/crm/customer_care_result_by_source",
        ):
            report = self.service.report_engine_v2.run(route, limit=10)
            self.assertIn(report["data_status"], {"OBSERVED", "PARTIAL"}, route)
            self.assertTrue(report["rows"], route)
            self.assertNotIn("UNKNOWN", json.dumps(report, ensure_ascii=False), route)

    def test_rich_demo_class_posts_are_event_backed(self):
        report = self.service.report_engine_v2.run("/report/center/class_post/index")
        self.assertEqual(report["data_status"], "OBSERVED")
        self.assertEqual(len(report["rows"]), 25)
        self.assertNotIn("UNKNOWN", json.dumps(report, ensure_ascii=False))

    def test_empty_database_class_posts_are_explicit_no_data(self):
        old = os.environ.pop("CENTER_EDU_RICH_DEMO", None)
        empty_tmp = tempfile.TemporaryDirectory()
        try:
            empty_service = CenterEduService(Path(empty_tmp.name) / "empty.sqlite3")
            report = empty_service.report_engine_v2.run("/report/center/class_post/index")
            self.assertEqual(report["rows"], [])
            self.assertEqual(report["data_status"], "NO_DATA")
            empty_service.close()
        finally:
            empty_tmp.cleanup()
            if old is not None:
                os.environ["CENTER_EDU_RICH_DEMO"] = old

    def test_customer_status_is_vietnamese_in_projection(self):
        report = self.service.report_engine_v2.run("/report/crm/customer_report/index", limit=3)
        payload = json.dumps(report, ensure_ascii=False)
        self.assertNotIn('"status": "CONVERTED"', payload)
        self.assertNotIn('"status": "LOST"', payload)

    def test_access_history_is_event_backed(self):
        report = self.service.report_engine_v2.run("/report/center/access_history")
        self.assertEqual(report["data_status"], "NO_DATA")
        self.assertEqual(report["rows"], [])

    def test_autoload_registers_crm_center_adapter(self):
        self.assertEqual(self.service.module_registry["report_crm_center"]["status"], "ADAPTER_READY")
        self.assertEqual(self.service.module_registry["finance_report_adapter"]["status"], "ADAPTER_READY")


if __name__ == "__main__":
    unittest.main()
