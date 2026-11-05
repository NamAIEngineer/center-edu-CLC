"""Focused contract checks for the CRM/CENTER report adapter.

These tests use only in-memory SQLite rows and never mutate the product runtime.
"""
import sqlite3
import unittest
from report_crm_center import CrmCenterReportAdapter


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


if __name__ == "__main__":
    unittest.main()
