"""Focused runnable checks for the observed weekly Ca học contract."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from app import AppError, CenterEduService


class SessionSlotWeekdayTests(unittest.TestCase):
    def test_weekdays_validation_and_migration(self):
        with TemporaryDirectory(prefix="center-session-slot-") as temp:
            service = CenterEduService(Path(temp) / "test.sqlite3")
            db = service.db
            actor = db.execute("SELECT * FROM users WHERE role='ADMIN' LIMIT 1").fetchone()
            created = service.add_session_slot(actor, {
                "start_time": "08:30", "end_time": "09:30", "day_of_weeks": ["1", 2, "0", 2],
            })
            self.assertEqual(created["day_of_weeks"], [0, 1, 2])
            service.update_session_slot(actor, created["id"], {"day_of_weeks": ["6"], "start_time": "09:00"})
            self.assertEqual(service.session_slot_detail(actor, created["id"])["day_of_weeks"], [6])
            self.assertEqual(service.session_slots(actor, query=created["code"])[0]["day_of_weeks"], [6])
            legacy = service.add_session_slot(actor, {
                "code": "LEGACY-SLOT", "name": "Khung giờ lịch cũ", "start_time": "10:00", "end_time": "11:00",
            })
            self.assertEqual(legacy["day_of_weeks"], [])
            with self.assertRaises(AppError):
                service.add_session_slot(actor, {"start_time": "10:00", "end_time": "11:00", "day_of_weeks": []})
            with self.assertRaises(AppError):
                service.add_session_slot(actor, {"start_time": "10:00", "end_time": "11:00", "day_of_weeks": [7]})
            with self.assertRaises(AppError):
                service.add_session_slot(actor, {"start_time": "10:00", "end_time": "11:00", "day_of_weeks": [1.5]})
            with self.assertRaises(AppError):
                service.add_session_slot(actor, {"start_time": "10:00", "end_time": "11:00", "day_of_weeks": [True]})
            self.assertTrue(service.delete_session_slot(actor, created["id"])["deleted"])
            service.db.close()


if __name__ == "__main__":
    unittest.main()
