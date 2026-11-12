import tempfile
import unittest
from pathlib import Path

from app import AppError, CenterEduService


class Hfa01CenterToolTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.service = CenterEduService(Path(self.tempdir.name) / "hfa01.db")
        self.admin = self.service.user_by_login("admin")
        course_id = self.service.db.execute("SELECT id FROM courses ORDER BY id LIMIT 1").fetchone()[0]
        self.service.db.execute(
            "UPDATE classes SET start_date=?,end_date=? WHERE id=1",
            ("2026-11-01", "2026-11-30"),
        )
        self.service.db.execute(
            "INSERT INTO timetable_sessions(class_id,session_date,start_time,end_time,room,teacher_id,status) VALUES(?,?,?,?,?,?,?)",
            (1, "2026-11-05", "09:00", "10:00", "TEST-ROOM", None, "CANCELLED"),
        )
        self.service.db.commit()

    def tearDown(self):
        self.service.close()
        self.tempdir.cleanup()

    def test_restore_cancelled_session_persists_and_audits(self):
        row = self.service.restore_cancelled_session(
            self.admin,
            {"class_url": "/training/class/ENG-FND-01", "cancelled_session_date": "2026-11-05"},
        )
        self.assertEqual(row["status"], "SCHEDULED")
        persisted = self.service.db.execute("SELECT status FROM timetable_sessions WHERE id=?", (row["id"],)).fetchone()[0]
        self.assertEqual(persisted, "SCHEDULED")
        self.assertIsNotNone(self.service.db.execute("SELECT 1 FROM audit_events WHERE action='RESTORE_CANCELLED' AND entity_id=?", (str(row["id"]),)).fetchone())

    def test_change_start_date_shifts_class_and_sessions(self):
        second = self.service.db.execute(
            "INSERT INTO timetable_sessions(class_id,session_date,start_time,end_time,room,teacher_id,status) VALUES(?,?,?,?,?,?,?)",
            (1, "2026-11-13", "09:00", "10:00", "TEST-ROOM", None, "SCHEDULED"),
        )
        self.service.db.commit()
        result = self.service.change_class_start_date(
            self.admin,
            {"class_url": "https://local.invalid/training/class/ENG-FND-01", "new_start_date": "2026-11-08"},
        )
        self.assertEqual(result["start_date"], "2026-11-08")
        self.assertEqual(self.service.db.execute("SELECT session_date FROM timetable_sessions WHERE id=?", (second.lastrowid,)).fetchone()[0], "2026-11-20")

    def test_invalid_and_no_match_fail_without_mutation(self):
        before = self.service.db.execute("SELECT start_date FROM classes WHERE id=1").fetchone()[0]
        with self.assertRaises(AppError) as invalid:
            self.service.change_class_start_date(self.admin, {"class_url": "", "new_start_date": "2026-11-08"})
        self.assertEqual(invalid.exception.status, 400)
        with self.assertRaises(AppError) as missing:
            self.service.restore_cancelled_session(self.admin, {"class_url": "/training/class/NO-SUCH", "cancelled_session_date": "2026-11-05"})
        self.assertEqual(missing.exception.status, 404)
        self.assertEqual(self.service.db.execute("SELECT start_date FROM classes WHERE id=1").fetchone()[0], before)


if __name__ == "__main__":
    unittest.main()
