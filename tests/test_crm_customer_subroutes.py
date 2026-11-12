import sqlite3
import unittest

from modules import crm_routes


class Service:
    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        CREATE TABLE potential_customers(id INTEGER PRIMARY KEY,full_name TEXT,customer_code TEXT,branch TEXT,date_of_birth TEXT,phone TEXT,email TEXT,source TEXT,sale_owner TEXT,sale_assistant TEXT,status TEXT,tag TEXT,interested_course TEXT,care_course TEXT,note TEXT,deleted_at TEXT);
        CREATE TABLE users(id INTEGER PRIMARY KEY,full_name TEXT);
        CREATE TABLE potential_customer_followups(id INTEGER PRIMARY KEY,potential_customer_id INTEGER,action_type TEXT,outcome TEXT,note TEXT,next_follow_up_at TEXT,created_by INTEGER,created_at TEXT);
        """)
    generated_screen = add_generated_record = update_generated_record = delete_generated_record = export_generated_screen = lambda *a, **k: {}


class CustomerSubrouteTests(unittest.TestCase):
    def setUp(self):
        self.service = Service()
        crm_routes.register(None, self.service)
        self.actor = {"role": "ADMIN", "full_name": "QA"}

    def test_raw_crud_soft_delete(self):
        row = self.service.add_generated_record(self.actor, "/crm/customer/raw", {"data": {"full_name": "Raw QA", "source": "Form"}})
        self.assertEqual(self.service.generated_screen(self.actor, "/crm/customer/raw")["records"][0]["data"]["full_name"], "Raw QA")
        self.service.update_generated_record(self.actor, "/crm/customer/raw", row["id"], {"data": {"full_name": "Edited QA", "source": "Event"}})
        self.assertEqual(self.service.generated_screen(self.actor, "/crm/customer/raw")["records"][0]["data"]["full_name"], "Edited QA")
        self.service.delete_generated_record(self.actor, "/crm/customer/raw", row["id"])
        self.assertEqual(self.service.generated_screen(self.actor, "/crm/customer/raw")["records"], [])

    def test_history_join_sequence_and_read_only(self):
        self.service.db.execute("INSERT INTO users VALUES(1,'Staff QA')")
        self.service.db.execute("INSERT INTO potential_customers(id,full_name,customer_code,branch,date_of_birth,phone,email,source,sale_owner,sale_assistant,status,tag,interested_course,care_course,note,deleted_at) VALUES(1,'Student QA','C-1','Center QA','2000-01-01','0900','a@b','Form','Sale QA','Assistant QA','CONTACTED','Tag QA','Course QA','Care QA','Note QA',NULL)")
        self.service.db.execute("INSERT INTO potential_customer_followups VALUES(1,1,'CALL','OK','Called','2026-11-15 10:00',1,'2026-11-10 09:00')")
        self.service.db.execute("INSERT INTO potential_customer_followups VALUES(2,1,'MESSAGE','OK','Messaged',NULL,1,'2026-11-10 09:00')")
        rows = self.service.generated_screen(self.actor, "/crm/opportunity_history")["records"]
        self.assertEqual([row["data"]["care_number"] for row in rows], [2, 1])
        self.assertEqual(rows[0]["data"]["performed_by"], "Staff QA")
        self.assertNotIn("care_status", rows[0]["data"])
        with self.assertRaises(PermissionError):
            self.service.add_generated_record(self.actor, "/crm/opportunity_history", {"data": {}})


if __name__ == "__main__":
    unittest.main()
