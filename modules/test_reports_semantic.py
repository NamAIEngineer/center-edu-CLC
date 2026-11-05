"""Bounded semantic checks for the owned training and teacher report lane."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from app import CenterEduService
from modules.report_crm_center import normalize_row
from modules.report_teacher import teacher_hours_rows, teacher_rest_learning_rows
from modules.report_training import training_report_rows


class ReportSemanticTest(unittest.TestCase):
    def setUp(self) -> None:
        self._old_rich = os.environ.get("CENTER_EDU_RICH_DEMO")
        os.environ["CENTER_EDU_RICH_DEMO"] = "1"
        self.path = Path(tempfile.mktemp(prefix="center-report-semantic-", suffix=".sqlite3"))
        self.service = CenterEduService(self.path)

    def tearDown(self) -> None:
        self.service.close()
        for suffix in ("", "-wal", "-shm"):
            try:
                Path(str(self.path) + suffix).unlink()
            except FileNotFoundError:
                pass
        if self._old_rich is None:
            os.environ.pop("CENTER_EDU_RICH_DEMO", None)
        else:
            os.environ["CENTER_EDU_RICH_DEMO"] = self._old_rich

    def test_test_report_uses_student_identity_and_filter_aliases(self):
        rows = training_report_rows(self.service.db, "report_training_test", {})
        self.assertTrue(rows)
        self.assertTrue(rows[0]["ho_ten"])
        self.assertTrue(rows[0]["tieu_chi"])
        self.assertIn(rows[0]["nhan_xet"], {"Đã chấm", "Chưa chấm"})
        self.assertNotEqual(rows[0]["ho_ten"], rows[0].get("class_code"))
        class_code = self.service.db.execute("SELECT code FROM classes ORDER BY id LIMIT 1").fetchone()[0]
        filtered = training_report_rows(self.service.db, "report_training_test", {"filter_2": class_code})
        self.assertTrue(filtered)
        self.assertTrue(all(row["class_code"] == class_code for row in filtered))

    def test_teacher_hours_uses_persisted_teacher_identity(self):
        rows = teacher_hours_rows(self.service.db)
        self.assertTrue(rows)
        self.assertTrue(rows[0]["giao_vien"])
        self.assertGreaterEqual(rows[0]["tong_so_ca_day"], 0)
        self.assertNotIn(rows[0]["giao_vien"], {"UNKNOWN", "Chưa cập nhật"})

    def test_crm_customer_report_uses_persisted_customer_identity_and_vi_status(self):
        adapter = self.service.report_engine_v2.provider.crm_adapter
        rows = list(adapter.query_report(entity="report_crm_customer_report_index", filters={}))
        self.assertTrue(rows)
        self.assertTrue(rows[0]["full_name"])
        self.assertTrue(rows[0]["customer_code"])
        self.assertNotIn(rows[0].get("status"), {"UNKNOWN", "NEW", "LEAD", "STUDENT"})
        self.assertNotIn("Chưa cập nhật", rows[0].values())

    def test_crm_normalizer_drops_internal_unknown_markers(self):
        row = normalize_row({"status": "UNKNOWN", "role": "STAFF", "action_type": "CALL"})
        self.assertEqual(row["status"], "")
        self.assertEqual(row["role"], "Nhân viên")
        self.assertEqual(row["action_type"], "Gọi")

    def test_rest_learning_applies_class_and_class_end_date_filters(self):
        all_rows = teacher_rest_learning_rows(self.service.db)
        self.assertTrue(all_rows)
        class_code = all_rows[0]["lop"]
        class_rows = teacher_rest_learning_rows(self.service.db, {"filter_6": class_code})
        self.assertTrue(class_rows)
        self.assertTrue(all(row["lop"] == class_code for row in class_rows))
        end_date = all_rows[0]["ngay_ket_thuc"]
        bounded = teacher_rest_learning_rows(self.service.db, {"from_date_enroll": end_date, "to_date_enroll": end_date})
        self.assertTrue(bounded)
        self.assertTrue(all(row["ngay_ket_thuc"] == end_date for row in bounded))

    def test_rest_learning_exposes_complete_observed_row_shape(self):
        row = teacher_rest_learning_rows(self.service.db)[0]
        expected = {
            "no", "hoc_vien", "phu_huynh", "lop", "ngay_ket_thuc", "ngay_ket_thuc_trong_lop",
            "tong_so_buoi_nghi", "co_phep", "khong_phep", "trang_thai_hoc_vien",
            "so_buoi_khong_hoc_bu", "so_tien_khong_hoc_bu", "ngay", "ca_hoc", "bai_hoc",
            "ghi_chu", "trang_thai_nghi", "ghi_chu_hoc_bu", "thong_tin_hoc_bu",
            "trang_thai_buoi_hoc_bu", "iem_danh", "cong_cu",
        }
        self.assertEqual(set(row), expected)
        self.assertIn(row["trang_thai_nghi"], {"Vắng có phép", "Vắng không phép"})

    def test_new_enrollment_projects_observed_columns_from_persisted_student_data(self):
        result = self.service.report_engine_v2.run("/report/training/new_enrollment/index")
        self.assertTrue(result["rows"])
        row = result["rows"][0]
        self.assertEqual(result["data_status"], "OBSERVED")
        self.assertEqual(row["trung_tam"], "Trung tâm CenterOnline - Demo")
        self.assertTrue(row["ma_hoc_vien"])
        self.assertTrue(row["ho_ten"])
        self.assertTrue(any(item["lop_ang_hoc"] for item in result["rows"]))
        self.assertTrue(any(item["ngay_bat_au"] is not None for item in result["rows"]))

    def test_missing_sources_and_malformed_numeric_filters_fail_closed(self):
        import sqlite3
        empty = sqlite3.connect(":memory:")
        try:
            self.assertEqual(training_report_rows(empty, "report_training_test"), [])
            self.assertEqual(teacher_hours_rows(empty), [])
            with self.assertRaises(ValueError):
                training_report_rows(self.service.db, "report_training_test", {"teacher_id": "bad-id"})
        finally:
            empty.close()


if __name__ == "__main__":
    unittest.main()
