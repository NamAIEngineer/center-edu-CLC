"""Staff-table counts come from persisted call outcomes, not demo totals."""
import sqlite3
import unittest
from modules import center_lane


class StaffCallProjectionTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        center_lane.ensure_schema(self.db)
        self.db.execute("CREATE TABLE call_history(staff_name TEXT, status TEXT)")
        center_lane.create_record(self.db, "/callcenter/staff", {"staff_name": "Trần Minh Tú", "extension": "101"})

    def tearDown(self):
        self.db.close()

    def test_counts_follow_persisted_outcomes_and_exclude_other_staff(self):
        self.db.executemany("INSERT INTO call_history VALUES(?,?)", [
            ("Trần Minh Tú", "CONNECTED"), ("Trần Minh Tú", "FAILED"),
            ("Trần Minh Tú", "MISSED"), ("Trần Minh Tú", "FOLLOW_UP"),
            ("Nhân viên khác", "CONNECTED"),
        ])
        row = center_lane.list_records(self.db, "/callcenter/staff")[0]["data"]
        self.assertEqual((row["total_calls"], row["processed_calls"], row["successful_calls"], row["failed_calls"]), (4, 2, 1, 1))

    def test_no_calls_is_zero_and_projection_does_not_persist_totals(self):
        row = center_lane.list_records(self.db, "/callcenter/staff")[0]["data"]
        self.assertEqual(row["total_calls"], 0)
        stored = self.db.execute("SELECT data_json FROM w6_route_records").fetchone()[0]
        self.assertNotIn("total_calls", stored)

    def test_unavailable_ledger_does_not_claim_zero(self):
        self.db.execute("DROP TABLE call_history")
        row = center_lane.list_records(self.db, "/callcenter/staff")[0]["data"]
        self.assertNotIn("total_calls", row)


if __name__ == "__main__":
    unittest.main()
