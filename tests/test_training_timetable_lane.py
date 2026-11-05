"""Focused timetable route evidence: matrix contract plus persistent service seam."""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
import json
import subprocess
import textwrap

from app import AppError, CenterEduService


class TrainingTimetableLaneTests(unittest.TestCase):
    def test_matrix_frontend_contract_has_observed_columns_states_and_focus(self):
        source = (Path(__file__).parents[1] / "static/modules/training_routes.js").read_text(encoding="utf-8")
        for marker in ("timetableMatrix", "Phòng học Ca học", "Ma trận thời khóa biểu theo phòng học", "Đang tải dữ liệu…", "Không thể tải dữ liệu thời khóa biểu.", "Chưa có dữ liệu", "scope = 'col'", "scope = 'row'"):
            self.assertIn(marker, source)

    def test_timetable_controls_have_query_wiring_and_nonempty_only(self):
        source = (Path(__file__).parents[1] / "static/modules/training_routes.js").read_text(encoding="utf-8")
        for marker in (
            "timetableQueryFromControls", "data-filter-key", "queryKey: 'teacher'",
            "queryKey: 'course'", "queryKey: 'class_code'", "queryKey: 'time'",
            "queryKey: 'room'", "/api/timetable${query ?",
            "else if (value) {\n      filters[key] = value;\n    }",
        ):
            self.assertIn(marker, source)
        self.assertIn("localOnly: true, name: 'week'", source)
        self.assertIn("localOnly: true, name: 'day'", source)
        self.assertNotIn("queryKey: 'week'", source)
        self.assertNotIn("queryKey: 'day'", source)

    def test_timetable_projection_deduplicates_observed_room_headers(self):
        source = Path(__file__).parents[1] / "static/modules/training_routes.js"
        script = textwrap.dedent(f"""
            import {{ timetableRoomHeaders }} from {json.dumps(source.as_uri())};
            const headers = timetableRoomHeaders([
              ['session_date', 'Ngày'], ['room_session', 'Phòng học Ca học'],
              ['a', 'A01'], ['sky-1', 'phòng học Sky, giáo viên Hà Anh'],
              ['sky-2', 'phòng học Sky, giáo viên Hà Anh'], ['a-2', 'A01'],
              ['outside', 'Phòng ngoài'],
            ]);
            const expected = ['A01', 'phòng học Sky, giáo viên Hà Anh', 'Phòng ngoài'];
            if (JSON.stringify(headers) !== JSON.stringify(expected)) process.exit(1);
        """)
        result = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("sessions.map((row) => [row.room", source.read_text(encoding="utf-8"))

    def test_persisted_create_update_cancel_and_restart(self):
        with tempfile.TemporaryDirectory(prefix="timetable-lane-") as root:
            path = Path(root) / "center.sqlite3"
            service = CenterEduService(path)
            try:
                admin = service.db.execute("SELECT * FROM users WHERE username='admin'").fetchone()
                course = service.db.execute("SELECT id FROM courses ORDER BY id LIMIT 1").fetchone()
                created = service.create_class_workflow(admin, {"course_id": course["id"], "code": "TT-LANE", "name": "Lớp thời khóa biểu", "sessions": []})
                class_id = created["class"]["id"]
                row = service.add_timetable(admin, {"class_id": class_id, "session_date": "2026-11-04", "start_time": "18:30", "end_time": "20:00", "room": "A01"})
                self.assertEqual(row["room"], "A01")
                with self.assertRaises(AppError) as duplicate:
                    service.add_timetable(admin, {"class_id": class_id, "session_date": "2026-11-04", "start_time": "18:30", "end_time": "20:00", "room": "A02"})
                self.assertEqual(duplicate.exception.code, "DUPLICATE_TIMETABLE")
                updated = service.update_timetable(admin, row["id"], {"room": "A02", "end_time": "20:15"})
                self.assertEqual((updated["room"], updated["end_time"]), ("A02", "20:15"))
                cancelled = service.cancel_timetable(admin, row["id"])
                self.assertEqual(cancelled["status"], "CANCELLED")
            finally:
                service.close()
            reopened = CenterEduService(path)
            try:
                stored = reopened.db.execute("SELECT room,status FROM timetable_sessions WHERE class_id=?", (class_id,)).fetchone()
                self.assertEqual(dict(stored), {"room": "A02", "status": "CANCELLED"})
            finally:
                reopened.close()

    def test_validation_and_atomicity(self):
        with tempfile.TemporaryDirectory(prefix="timetable-invalid-") as root:
            service = CenterEduService(Path(root) / "center.sqlite3")
            try:
                admin = service.db.execute("SELECT * FROM users WHERE username='admin'").fetchone()
                course = service.db.execute("SELECT id FROM courses ORDER BY id LIMIT 1").fetchone()
                created = service.create_class_workflow(admin, {"course_id": course["id"], "code": "TT-INVALID", "sessions": []})
                with self.assertRaises(AppError):
                    service.add_timetable(admin, {"class_id": created["class"]["id"], "session_date": "2026-11-05", "start_time": "21:00", "end_time": "20:00"})
                self.assertEqual(service.db.execute("SELECT COUNT(*) FROM timetable_sessions WHERE class_id=?", (created["class"]["id"],)).fetchone()[0], 0)
            finally:
                service.close()


if __name__ == "__main__":
    unittest.main()
