"""Focused W4 checks for the training and teacher report adapters.

These tests exercise the adapters against the product's persistent rich-demo
SQLite domain.  They do not call the shared controller or mutate reference
inventory state; HTTP wiring remains a coordinator-owned integration step.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from app import CenterEduService
from modules.report_teacher import teacher_hours_rows, teacher_rest_learning_rows
from modules.report_training import training_report_rows


MANIFEST = (
    "/report/training/attendance",
    "/report/teacher/sth/index",
    "/report/training/test",
    "/report/training/daily_evaluation/index",
    "/report/training/class/v2",
    "/report/training/tuition_class/index",
    "/report/training/allocation_student/index",
    "/report/training/change_class/index",
    "/report/training/reserve_training/index",
    "/report/training/homework_ratio/index",
    "/report/training/attendance_center/index",
    "/report/training/using_course/index",
    "/report/training/enroll/index",
    "/report/training/allocation_hours/index",
    "/report/training/schedule/index",
    "/report/training/diligence/index",
    "/report/training/register_learning",
    "/report/training/student_pause",
    "/report/training/student_training_v2",
    "/report/training/due_date_student",
    "/report/training/absent/classes",
    "/report/teacher/rest_learning",
    "/report/training/top_notebook",
    "/report/training/student_drop/index",
    "/report/training/new_enrollment/index",
    "/report/training/require_support/index",
    "/report/training/instead_teacher",
    "/report/training/examination_month/index",
)

ENTITY_BY_ROUTE = {
    route: route.removeprefix("/").replace("/", "_")
    for route in MANIFEST
}


class W4ReportTrainingTeacherTest(unittest.TestCase):
    def setUp(self) -> None:
        self._old_rich = os.environ.get("CENTER_EDU_RICH_DEMO")
        os.environ["CENTER_EDU_RICH_DEMO"] = "1"
        self.tmp = tempfile.NamedTemporaryFile(prefix="center-edu-w4-", suffix=".sqlite3", delete=False)
        self.tmp.close()
        self.service = CenterEduService(Path(self.tmp.name))

    def tearDown(self) -> None:
        self.service.close()
        for suffix in ("", "-wal", "-shm"):
            try:
                Path(self.tmp.name + suffix).unlink()
            except FileNotFoundError:
                pass
        if self._old_rich is None:
            os.environ.pop("CENTER_EDU_RICH_DEMO", None)
        else:
            os.environ["CENTER_EDU_RICH_DEMO"] = self._old_rich

    def test_test_report_joins_real_students_and_applies_filter(self):
        rows = training_report_rows(self.service.db, "report_training_test", {})
        self.assertGreater(len(rows), 0)
        self.assertTrue(rows[0]["ho_ten"])
        self.assertEqual(rows[0]["tieu_chi"], "Foundation checkpoint")
        self.assertIn(rows[0]["trang_thai"], {"Bản nháp", "Đang mở", "Đã đóng"})
        filtered = training_report_rows(self.service.db, "report_training_test", {"student_query": rows[0]["ho_ten"].split()[-1]})
        self.assertGreaterEqual(len(filtered), 1)
        self.assertTrue(all(rows[0]["ho_ten"].split()[-1] in item["ho_ten"] for item in filtered))

    def test_teacher_hours_aggregates_duration_and_reference_date_column(self):
        rows = teacher_hours_rows(self.service.db)
        self.assertGreater(len(rows), 0)
        row = next(item for item in rows if item["tong_so_ca_day"] > 0)
        self.assertGreater(row["tong_so_gio_day"], 0)
        self.assertGreaterEqual(row["day_chinh"], 0)
        self.assertIn("01_11_2026", row)
        self.assertGreaterEqual(row["01_11_2026"], 0)
        by_date = teacher_hours_rows(self.service.db, {"from_date": "2026-11-01", "to_date": "2026-11-01"})
        self.assertTrue(by_date)
        self.assertTrue(all(item["01_11_2026"] == item["tong_so_gio_day"] for item in by_date))

    def test_teacher_rest_learning_uses_absence_source_and_vietnamese_filter(self):
        rows = teacher_rest_learning_rows(self.service.db)
        self.assertGreater(len(rows), 0)
        self.assertTrue(all(item["trang_thai_nghi"] in {"Vắng có phép", "Vắng không phép"} for item in rows))
        excused = teacher_rest_learning_rows(self.service.db, {"filter_1": "Vắng có phép"})
        self.assertGreater(len(excused), 0)
        self.assertTrue(all(item["trang_thai_nghi"] == "Vắng có phép" for item in excused))
        self.assertIsNone(excused[0]["so_tien_khong_hoc_bu"])

    def test_manifest_entities_never_crash_or_emit_placeholder_values(self):
        for route in MANIFEST:
            entity = ENTITY_BY_ROUTE[route]
            rows = training_report_rows(self.service.db, entity, {})
            self.assertIsInstance(rows, list, route)
            for row in rows:
                for value in row.values():
                    if isinstance(value, str):
                        self.assertNotIn("UNKNOWN", value.upper(), route)
                        self.assertNotEqual(value, "Chưa cập nhật", route)
                        self.assertNotIn(value, {"PRESENT", "ABSENT", "EXCUSED", "LATE", "ACTIVE", "PAUSED", "DROPPED", "ENROLLED", "OPEN", "CLOSED", "DRAFT", "PUBLISHED"}, route)

    def test_coordinator_autoload_routes_report_engine_to_owned_adapter(self):
        self.assertEqual(self.service.module_registry["report_training"]["status"], "ADAPTER_READY")
        self.assertEqual(self.service.module_registry["report_teacher"]["status"], "ADAPTER_READY")
        result = self.service.report_engine_v2.run("/report/training/attendance")
        self.assertEqual(result["data_status"], "OBSERVED")
        self.assertGreater(len(result["rows"]), 0)
        self.assertTrue(any(row.get("Mã học sinh") or row.get("ma_hoc_sinh") for row in result["rows"]))


if __name__ == "__main__":
    unittest.main()
