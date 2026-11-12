"""Focused contract checks for the CRM/CENTER report adapter.

These tests use only in-memory SQLite rows and never mutate the product runtime.
"""
import sqlite3
import csv
import io
import unittest
from report_crm_center import CrmCenterReportAdapter, _customer_care_total
from report_engine import ReportEngine


class Provider:
    def __init__(self):
        self.db = sqlite3.connect(":memory:")

    def query_report(self, *, entity, filters):
        raise sqlite3.OperationalError("no such table: " + entity)


class ReportCrmCenterTests(unittest.TestCase):
    def setUp(self):
        self.provider = Provider()
        self.provider.db.row_factory = sqlite3.Row
        self.adapter = CrmCenterReportAdapter(self.provider)

    def test_birth_day_reads_persisted_students_only(self):
        self.provider.db.execute("CREATE TABLE students (full_name TEXT, parent1_name TEXT, date_of_birth TEXT, status TEXT, class_codes TEXT)")
        self.provider.db.execute("CREATE TABLE classes (code TEXT, schedule TEXT)")
        self.provider.db.execute("INSERT INTO students VALUES ('Lan','Parent','2014-05-10','ACTIVE','')")
        rows = self.adapter._local_rows("report_center_birth_day_index", {"filter_4": "5"})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["ho_ten"], "Lan")
        self.assertEqual(rows[0]["ngay_sinh"], "2014-05-10")

    def test_class_post_has_no_cross_domain_fallback(self):
        self.assertEqual(self.adapter._local_rows("report_center_class_post_index", {}), [])

    def test_staff_birthday_api_and_export_share_staff_columns(self):
        db = self.provider.db
        db.execute("CREATE TABLE users (full_name TEXT, username TEXT, role TEXT, date_of_birth TEXT, active INTEGER)")
        db.executemany("INSERT INTO users VALUES (?,?,?,?,?)", [
            ("Lan", "lan", "TEACHER", "1990-05-10", 1),
            ("Nam", "nam", "STAFF", "1991-06-12", 1),
            ("Học viên", "hv", "STUDENT", "2014-05-10", 1),
        ])
        engine = ReportEngine(self.adapter)
        route = "/report/center/birth_day/index"
        filters = {"birthday_type": "staff", "filter_4": "5"}
        result = engine.run(route, filters=filters)
        expected = ["No.", "Họ tên", "Ngày sinh", "Chức danh", "Phòng ban", "Quà tặng", "Ngày tặng", "Trạng thái", "Hành động"]
        self.assertEqual([column["label"] for column in result["columns"]], expected)
        self.assertEqual([row["ho_ten"] for row in result["rows"]], ["Lan"])
        self.assertIsNone(result["rows"][0]["chuc_danh"])
        self.assertIsNone(result["rows"][0]["phong_ban"])
        self.assertIsNone(result["rows"][0]["trang_thai"])
        self.assertEqual(engine.run(route, filters={**filters, "given_status": "0"})["rows"], [])
        self.assertEqual(engine.run(route, filters={**filters, "tim_trong_bang": "Nam"})["rows"], [])
        exported = list(csv.reader(io.StringIO(engine.export_csv(route, filters=filters))))
        self.assertEqual(exported[0], expected)
        self.assertEqual(len(exported[1]), 9)
        self.assertEqual(len(engine.definition(route).columns), 12)

    def test_district_without_persisted_dimension_is_empty(self):
        self.provider.db.execute("CREATE TABLE potential_customers (full_name TEXT, status TEXT, created_at TEXT)")
        self.provider.db.execute("INSERT INTO potential_customers VALUES ('Lan','NEW','2026-01-01')")
        self.assertEqual(self.adapter._local_rows("report_crm_customer_care_result_by_district", {}), [])

    def test_missing_table_is_no_data_and_recorded(self):
        self.assertEqual(list(self.adapter.query_report(entity="report_center_class_post_index", filters={})), [])
        self.assertIn("report_center_class_post_index", self.adapter.missing_entities)

    def test_missing_customer_source_is_no_data_without_generic_fallback(self):
        self.assertEqual(list(self.adapter.query_report(entity="report_crm_customer_report_index", filters={})), [])
        self.assertIn("report_crm_customer_report_index", self.adapter.missing_entities)

    def test_customer_care_total_sums_persisted_groups_and_recomputes_rates(self):
        rows = [
            {"facility": "A", "so_luong_khach_hang": 2, "kh_ong_y": 1, "kh_tu_choi": 1,
             "khach_hang_moi": 0, "so_luong": 2, "ti_le": 50, "so_luong_2": 1,
             "ti_le_2": 50, "so_luong_3": 1, "ti_le_3": 50},
            {"facility": "B", "so_luong_khach_hang": 3, "kh_ong_y": 3, "kh_tu_choi": 0,
             "khach_hang_moi": 0, "so_luong": 3, "ti_le": 100, "so_luong_2": 3,
             "ti_le_2": 100, "so_luong_3": 0, "ti_le_3": 0},
        ]
        total = _customer_care_total(rows, "facility")[-1]
        self.assertEqual(total["facility"], "Tổng")
        self.assertEqual(total["so_luong_khach_hang"], 5)
        self.assertEqual(total["kh_ong_y"], 4)
        self.assertEqual(total["ti_le"], 100)
        self.assertEqual(total["ti_le_2"], 80)

    def test_customer_care_total_skips_empty_and_existing_total(self):
        self.assertEqual(_customer_care_total([], "facility"), [])
        rows = [{"facility": "Tổng", "so_luong_khach_hang": 5}]
        self.assertIs(_customer_care_total(rows, "facility"), rows)


if __name__ == "__main__":
    unittest.main()
