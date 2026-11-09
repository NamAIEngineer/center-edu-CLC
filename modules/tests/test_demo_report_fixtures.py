from __future__ import annotations

import sqlite3
import unittest

from modules.demo_report_fixtures import seed
from modules.finance_report_adapter import FinanceReportProvider


class DemoReportFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, full_name TEXT);
            INSERT INTO users VALUES (1,'admin','Admin');
            CREATE TABLE finance_bills (
              id INTEGER PRIMARY KEY, invoice_code TEXT UNIQUE, contract_code TEXT,
              class_code TEXT, subject TEXT, customer_name TEXT, payment_amount REAL,
              sales_owner TEXT, created_by INTEGER, center TEXT, branch TEXT, employee TEXT,
              confirmation_status TEXT, payment_method TEXT, note TEXT, invoice_date TEXT,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)

    def tearDown(self) -> None:
        self.db.close()

    def test_non_rich_mode_does_not_add_report_fixture_rows(self) -> None:
        self.assertEqual(seed(self.db, rich_demo=False), 0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM finance_bills").fetchone()[0], 0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM finance_report_team_memberships").fetchone()[0], 0)

    def test_rich_mode_seeds_at_most_three_persisted_months_and_team_dimension(self) -> None:
        self.assertEqual(seed(self.db, rich_demo=True), 3)
        self.assertEqual(seed(self.db, rich_demo=True), 0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM finance_bills").fetchone()[0], 3)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM finance_report_team_memberships").fetchone()[0], 3)
        rows = list(FinanceReportProvider(self.db).query_report(
            entity="report_finance_revenue_center_by_month_sale_team_index",
            filters={"year": "2026", "start_month": "1", "end_month": "11"},
        ))
        self.assertEqual(len(rows), 3)
        self.assertEqual({row["sales_team"] for row in rows}, {"Nhóm sale fixture A", "Nhóm sale fixture B", "Nhóm sale fixture C"})
        month_fields = {"thang_1", "thang_6", "thang_11", "doanh_thu_tam_tinh", "doanh_thu_tam_tinh_6", "doanh_thu_tam_tinh_11"}
        self.assertTrue(all(month_fields.issubset(row) for row in rows))
        self.assertEqual({row["thang_1"] for row in rows if row["sales_team"] == "Nhóm sale fixture A"}, {1_100_000})
        self.assertEqual({row["doanh_thu_tam_tinh_6"] for row in rows if row["sales_team"] == "Nhóm sale fixture B"}, {1_250_000})

    def test_sale_team_does_not_fall_back_to_sales_owner(self) -> None:
        self.db.execute("INSERT INTO finance_bills(invoice_code,invoice_date,payment_amount,sales_owner) VALUES('INV-1','2026-01-10',123,'Someone')")
        rows = list(FinanceReportProvider(self.db).query_report(
            entity="report_finance_revenue_center_by_month_sale_team_index", filters={}
        ))
        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
