from __future__ import annotations

import tempfile
import threading
import unittest
import json
from pathlib import Path
from urllib.parse import quote

from app import create_server
from test_app import ApiClient, TEST_PASSWORD


class HeaderApiRowsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.server = create_server(Path(self.tmp.name) / "center.sqlite3", "127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.client = ApiClient(self.server)
        status, payload = self.client.request(
            "POST", "/api/auth/login",
            {"login": "admin", "password": TEST_PASSWORD},
        )
        self.assertEqual(status, 200, payload)

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.server.service.close()
        self.tmp.cleanup()

    def test_notification_and_calendar_rows_use_real_sqlite_columns(self) -> None:
        row = self.server.service.appointment_store.create(
            role="ADMIN",
            student_name="TEST_HEADER_API_STUDENT",
            parent_name="TEST_HEADER_API_PARENT",
            appointment_date="2026-11-12",
            reference_code="TEST_HEADER_API_REF",
            amount=0,
            note="QA disposable fixture",
            created_by="TEST_HEADER_API",
        )

        for tab in (
            "Thông báo", "Sự kiện", "Xin nghỉ", "Hỗ trợ KH", "Lịch hẹn trễ",
            "Ghi danh mới", "Nhận KH", "Hợp đồng", "Hóa đơn", "Ghi danh",
            "Lớp sắp KT", "Bình luận", "HV hết hạn bảo lưu",
        ):
            status, payload = self.client.request("GET", "/api/notifications?tab=" + quote(tab))
            self.assertEqual(status, 200, (tab, payload))
            self.assertEqual(payload["data"]["tab"], tab)

        status, payload = self.client.request("GET", "/api/notifications?tab=" + quote("Lịch hẹn trễ"))
        self.assertEqual(status, 200, payload)
        self.assertEqual(payload["data"]["items"][0]["title"], "TEST_HEADER_API_STUDENT")

        status, payload = self.client.request("GET", "/api/appointments-upcoming")
        self.assertEqual(status, 200, payload)
        self.assertEqual(payload["data"]["items"][0]["id"], row["id"])
        self.assertEqual(payload["data"]["items"][0]["name"], "TEST_HEADER_API_STUDENT")

    def test_classroom_all_filter_and_profile_persist_on_disposable_db(self) -> None:
        status, payload = self.client.request("GET", "/api/classrooms?q=TEST_NO_MATCH&status=")
        self.assertEqual(status, 200, payload)
        self.assertEqual(payload["data"], [])
        status, payload = self.client.request("GET", "/api/classrooms?q=TEST_NO_MATCH&status=T%E1%BA%A5t%20c%E1%BA%A3")
        self.assertEqual(status, 200, payload)
        self.assertEqual(payload["data"], [])

        valid_png = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        status, payload = self.client.request("POST", "/api/profile", {
            "fullname": "TEST_PROFILE_ADMIN",
            "nickname": "TEST EN",
            "dob": "2000-01-02",
            "gender": "F",
            "address": "TEST PROFILE ADDRESS",
            "skype": "test-skype",
            "facebook": "test-facebook",
            "zalo": "test-zalo",
            "note": "QA disposable fixture",
            "phone": "0900000002",
            "avatar_data": valid_png,
        })
        self.assertEqual(status, 200, payload)
        self.assertEqual(payload["data"]["full_name"], "TEST_PROFILE_ADMIN")
        self.assertEqual(payload["data"]["english_name"], "TEST EN")
        self.assertEqual(payload["data"]["phone"], "0900000002")
        self.assertEqual(payload["data"]["avatar_data"], valid_png)
        status, payload = self.client.request("GET", "/api/auth/me")
        self.assertEqual(status, 200, payload)
        self.assertEqual(payload["user"]["address"], "TEST PROFILE ADDRESS")
        self.assertEqual(payload["user"]["note"], "QA disposable fixture")
        self.assertEqual(payload["user"]["phone"], "0900000002")
        self.assertEqual(payload["user"]["avatar_data"], valid_png)

        status, payload = self.client.request("POST", "/api/profile", {
            "fullname": "TEST_PROFILE_ADMIN",
            "phone": "abc",
        })
        self.assertEqual(status, 400, payload)
        self.assertEqual(payload["error"]["code"], "VALIDATION_ERROR")

    def test_finance_bill_no_match_search_uses_bill_note_column(self) -> None:
        status, payload = self.client.request(
            "GET", "/api/finance/bills?q=TEST_NO_SUCH_BILL_20261111",
        )
        self.assertEqual(status, 200, payload)
        self.assertEqual(payload["data"], [])

        status, payload = self.client.request("POST", "/api/profile", {
            "fullname": "TEST_PROFILE_ADMIN",
            "phone": "0900000002",
            "avatar_data": "data:image/png;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==",
        })
        self.assertEqual(status, 400, payload)
        self.assertEqual(payload["error"]["code"], "VALIDATION_ERROR")

        status, payload = self.client.request("POST", "/api/profile", {
            "fullname": "TEST_PROFILE_ADMIN",
            "phone": "0900000002",
            "avatar_data": "data:image/svg+xml;base64,PHN2Zz4=",
        })
        self.assertEqual(status, 400, payload)
        self.assertEqual(payload["error"]["code"], "VALIDATION_ERROR")

    def test_teacher_report_class_scope_excludes_other_teacher(self) -> None:
        admin = self.client
        courses = admin.request("GET", "/api/courses")[1]["data"]
        teachers = admin.request("GET", "/api/teachers")[1]["data"]
        self.assertGreaterEqual(len(teachers), 1)
        teacher_a = teachers[0]["id"]
        teacher_b = self.server.service.db.execute(
            "SELECT id FROM users WHERE role='TEACHER' AND id<>? ORDER BY id LIMIT 1", (teacher_a,)
        ).fetchone()
        if teacher_b is None:
            cur = self.server.service.db.execute(
                "INSERT INTO users(username,email,full_name,password_hash,role) VALUES(?,?,?,?,?)",
                ("TEST_REPORT_TEACHER_B", "TEST_REPORT_TEACHER_B@example.test", "Test report teacher B", "x", "TEACHER"),
            )
            self.server.service.db.commit()
            teacher_b = (cur.lastrowid,)
        course_id = courses[0]["id"]
        db = self.server.service.db
        db.execute("INSERT INTO classes(course_id,code,teacher_id,status) VALUES(?,?,?,'OPEN')", (course_id, "TEST_REPORT_CLASS_A", teacher_a))
        db.execute("INSERT INTO classes(course_id,code,teacher_id,status) VALUES(?,?,?,'OPEN')", (course_id, "TEST_REPORT_CLASS_B", teacher_b[0]))
        db.commit()
        teacher = ApiClient(self.server)
        self.assertEqual(teacher.request("POST", "/api/auth/login", {"login": "teacher", "password": TEST_PASSWORD})[0], 200)
        status, payload = teacher.request("GET", "/api/report-engine?route=%2Freport%2Ftraining%2Fclass%2Fv2")
        self.assertEqual(status, 200, payload)
        codes = {row["code"] for row in payload["data"]["rows"]}
        self.assertIn("TEST_REPORT_CLASS_A", codes)
        self.assertNotIn("TEST_REPORT_CLASS_B", codes)

    def test_teacher_report_ui_adapter_class_scope_excludes_other_teacher(self) -> None:
        courses = self.client.request("GET", "/api/courses")[1]["data"]
        teachers = self.client.request("GET", "/api/teachers")[1]["data"]
        teacher_a = teachers[0]["id"]
        teacher_b = self.server.service.db.execute(
            "SELECT id FROM users WHERE role='TEACHER' AND id<>? ORDER BY id LIMIT 1", (teacher_a,)
        ).fetchone()
        if teacher_b is None:
            cur = self.server.service.db.execute(
                "INSERT INTO users(username,email,full_name,password_hash,role) VALUES(?,?,?,?,?)",
                ("TEST_REPORT_UI_TEACHER_B", "TEST_REPORT_UI_TEACHER_B@example.test", "Test report UI teacher B", "x", "TEACHER"),
            )
            self.server.service.db.commit()
            teacher_b = (cur.lastrowid,)
        db = self.server.service.db
        db.execute("INSERT INTO classes(course_id,code,teacher_id,status) VALUES(?,?,?,'OPEN')", (courses[0]["id"], "TEST_REPORT_UI_CLASS_A", teacher_a))
        db.execute("INSERT INTO classes(course_id,code,teacher_id,status) VALUES(?,?,?,'OPEN')", (courses[0]["id"], "TEST_REPORT_UI_CLASS_B", teacher_b[0]))
        db.commit()
        teacher = ApiClient(self.server)
        self.assertEqual(teacher.request("POST", "/api/auth/login", {"login": "teacher", "password": TEST_PASSWORD})[0], 200)
        status, payload = teacher.request("GET", "/api/reports/run?route=%2Freport%2Ftraining%2Fclass%2Fv2")
        self.assertEqual(status, 200, payload)
        self.assertNotIn("TEST_REPORT_UI_CLASS_B", json.dumps(payload, ensure_ascii=False))

    def test_teacher_report_adapter_denies_finance_route(self) -> None:
        teacher = ApiClient(self.server)
        self.assertEqual(teacher.request("POST", "/api/auth/login", {"login": "teacher", "password": TEST_PASSWORD})[0], 200)
        status, payload = teacher.request("GET", "/api/reports/run?route=%2Freport%2Ffinance%2Fdebt")
        self.assertEqual(status, 403, payload)
        self.assertEqual(payload["error"]["code"], "ROLE_FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
