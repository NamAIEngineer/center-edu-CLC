from __future__ import annotations

import sqlite3
import unittest

from modules.finance_report_adapter import FinanceReportProvider
from modules.report_engine import ReportEngine


class FinanceReportSemanticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """
            CREATE TABLE students (id INTEGER PRIMARY KEY, student_code TEXT, full_name TEXT);
            CREATE TABLE classes (id INTEGER PRIMARY KEY, code TEXT);
            CREATE TABLE users (id INTEGER PRIMARY KEY, full_name TEXT);
            CREATE TABLE finance_contracts (
                id INTEGER PRIMARY KEY, contract_code TEXT, customer_type TEXT,
                student_id INTEGER, class_id INTEGER, package_name TEXT,
                created_date TEXT, expiry_date TEXT, total_amount REAL,
                paid_amount REAL, debt_amount REAL, sales_owner TEXT,
                created_by INTEGER, payment_status TEXT, contract_status TEXT,
                note TEXT
            );
            CREATE TABLE finance_bills (
                id INTEGER PRIMARY KEY, invoice_code TEXT, contract_code TEXT,
                invoice_date TEXT, created_at TEXT
            );
            INSERT INTO students VALUES (1, 'HS-001', 'Nguyễn Minh Anh');
            INSERT INTO classes VALUES (1, 'ENG-01');
            INSERT INTO users VALUES (1, 'Nhân viên');
            INSERT INTO finance_contracts VALUES
                (1, 'HD-001', 'STUDENT', 1, 1, 'IELTS', '2026-11-01',
                 '2027-01-01', 1000000, 500000, 500000, 'Sale', 1,
                 'PARTIAL', 'ACTIVE', '');
            INSERT INTO finance_bills VALUES
                (1, 'INV-OLD', 'HD-001', '2026-11-02', '2026-11-02'),
                (2, 'INV-NEW', 'HD-001', '2026-11-03', '2026-11-03');
            """
        )

    def tearDown(self) -> None:
        self.db.close()

    def test_student_finance_resolves_latest_persisted_invoice(self) -> None:
        rows = list(FinanceReportProvider(self.db).query_report(
            entity="report_finance_student_finance", filters={}
        ))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["invoice_code"], "INV-NEW")
        self.assertNotEqual(rows[0]["invoice_code"], rows[0]["contract_code"])

    def test_student_finance_keeps_invoice_missing_when_bill_source_absent(self) -> None:
        self.db.execute("DROP TABLE finance_bills")
        rows = list(FinanceReportProvider(self.db).query_report(
            entity="report_finance_student_finance", filters={}
        ))
        self.assertEqual(rows[0]["invoice_code"], None)

    def test_contract_status_is_presentation_only(self) -> None:
        rows = list(FinanceReportProvider(self.db).query_report(
            entity="report_crm_contract_index", filters={}
        ))
        self.assertEqual(rows[0]["payment_status"], "Còn nợ")
        self.assertEqual(rows[0]["contract_status"], "Hoạt động")
        self.assertEqual(
            tuple(self.db.execute(
                "SELECT payment_status,contract_status FROM finance_contracts WHERE contract_code=?",
                ("HD-001",),
            ).fetchone()),
            ("PARTIAL", "ACTIVE"),
        )

    def test_vietnamese_status_filters_match_stored_enums(self) -> None:
        rows = list(FinanceReportProvider(self.db).query_report(
            entity="report_crm_contract_index",
            filters={"payment_status": "Còn nợ", "contract_status": "Đang thực hiện"},
        ))
        self.assertEqual([row["contract_code"] for row in rows], ["HD-001"])

    def test_source_report_requires_persisted_source_dimension(self) -> None:
        rows = list(FinanceReportProvider(self.db).query_report(
            entity="report_finance_revenue_source_index", filters={}
        ))
        self.assertEqual(rows, [])

    def test_student_finance_summary_uses_filtered_contracts_and_stable_student_id(self) -> None:
        self.db.execute("INSERT INTO students VALUES (2, 'HS-002', 'Trần B')")
        self.db.execute("INSERT INTO finance_contracts VALUES (2, 'HD-002', 'STUDENT', 2, 1, 'TOEIC', '2026-12-01', '2027-01-01', 2000000, 1200000, 800000, 'Sale', 1, 'PARTIAL', 'ACTIVE', '')")
        provider = FinanceReportProvider(self.db)
        summary = provider.query_report_summary(entity="report_finance_student_finance", filters={"payment_status": "Còn nợ"})
        self.assertEqual(summary["total_amount"], 3000000)
        self.assertEqual(summary["paid_amount"], 1700000)
        self.assertEqual(summary["debt_amount"], 1300000)
        self.assertEqual(summary["student_count"], 2)

    def test_summary_excludes_unsupported_fields_and_generic_provider_unchanged(self) -> None:
        provider = FinanceReportProvider(self.db)
        summary = provider.query_report_summary(entity="report_finance_debt", filters={})
        self.assertNotIn("bad_debt", summary)
        self.assertNotIn("refund", summary)
        self.assertNotIn("unused_amount", summary)
        class Generic:
            def query_report(self, *, entity, filters): return [{"x": 1}]
        engine = ReportEngine(Generic())
        route = next(iter(engine.definitions))
        self.assertNotIn("summary", engine.run(route))


if __name__ == "__main__":
    unittest.main()
