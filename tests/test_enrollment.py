from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from app import create_server, password_hash
from test_app import ApiClient, TEST_PASSWORD


class EnrollmentAndTeacherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.server = create_server(Path(self.tmp.name) / "r19.sqlite3", "127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.admin = ApiClient(self.server)
        status, payload = self.admin.request("POST", "/api/auth/login", {"login": "admin", "password": TEST_PASSWORD})
        self.assertEqual(status, 200, payload)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.server.service.close()
        self.tmp.cleanup()

    def _student(self, suffix="A"):
        status, payload = self.admin.request("POST", "/api/students", {
            "student_code": f"TEST_R19_STUDENT_{suffix}", "full_name": f"TEST_R19 Student {suffix}",
            "email": f"test_r19_student_{suffix.lower()}@example.test", "phone": "0900000019",
        })
        self.assertEqual(status, 201, payload)
        return payload["data"]

    def _class_id(self):
        status, payload = self.admin.request("GET", "/api/classes")
        self.assertEqual(status, 200, payload)
        self.assertTrue(payload["data"])
        return payload["data"][0]["id"]

    def test_create_duplicate_status_reenroll_read_reload_and_class_codes_unchanged(self):
        student = self._student()
        class_id = self._class_id()
        before = self.admin.request("GET", f"/api/students/{student['id']}")[1]["data"]["class_codes"]
        status, payload = self.admin.request("POST", f"/api/classes/{class_id}/enrollments", {
            "student_id": student["id"], "start_date": "2026-11-13", "sessions_count": 12,
            "schedule": "Tue/Thu 18:30", "note": "TEST_R19 enrollment",
        })
        self.assertEqual(status, 201, payload)
        self.assertEqual(payload["data"]["status"], "ENROLLED")
        status, duplicate = self.admin.request("POST", f"/api/classes/{class_id}/enrollments", {"student_id": student["id"]})
        self.assertEqual(status, 409, duplicate)
        self.assertEqual(duplicate["error"]["code"], "DUPLICATE_ENROLLMENT")
        status, listed = self.admin.request("GET", f"/api/classes/{class_id}/students?status=ENROLLED")
        self.assertEqual(status, 200, listed)
        row = next(item for item in listed["data"]["rows"] if item["student_id"] == student["id"])
        self.assertEqual(row["sessions_count"], 12)
        self.assertEqual(self.admin.request("POST", f"/api/classes/{class_id}/enrollments/{student['id']}", {"status": "DROPPED"})[0], 200)
        self.assertEqual(self.admin.request("POST", f"/api/classes/{class_id}/enrollments", {"student_id": student["id"]})[0], 201)
        restarted = ApiClient(self.server)
        self.assertEqual(restarted.request("POST", "/api/auth/login", {"login": "admin", "password": TEST_PASSWORD})[0], 200)
        status, listed = restarted.request("GET", f"/api/classes/{class_id}/students?status=ENROLLED")
        self.assertEqual(status, 200, listed)
        self.assertTrue(any(item["student_id"] == student["id"] for item in listed["data"]["rows"]))
        after = self.admin.request("GET", f"/api/students/{student['id']}")[1]["data"]["class_codes"]
        self.assertEqual(before, after)

    def test_teacher_is_real_user_and_selectable(self):
        status, payload = self.admin.request("POST", "/api/teachers", {
            "full_name": "TEST_R19 Teacher", "username": "TEST_R19_teacher",
            "email": "test_r19_teacher@example.test", "password": TEST_PASSWORD,
            "phone": "0900000019", "nationality": "Vietnamese",
        })
        self.assertEqual(status, 201, payload)
        teacher_id = payload["data"]["id"]
        self.assertIn(teacher_id, [row["id"] for row in self.admin.request("GET", "/api/teachers?q=TEST_R19")[1]["data"]])
        teacher = ApiClient(self.server)
        status, login = teacher.request("POST", "/api/auth/login", {"login": "TEST_R19_teacher", "password": TEST_PASSWORD})
        self.assertEqual(status, 200, login)
        self.assertEqual(login["user"]["role"], "TEACHER")
        status, _headers, js = self.admin.request_raw("GET", "/app.js")
        self.assertEqual(status, 200)
        self.assertIn(b"/api/teachers", js)
        self.assertIn(b"name=\"password\"", js)
        self.assertIn(b"class-students", js)
        self.assertIn("Học viên".encode(), js)
        self.assertIn("Bảo lưu".encode(), js)
        self.assertIn("Chuyển lớp".encode(), js)
        status, _headers, training = self.admin.request_raw("GET", "/modules/training_routes.js")
        self.assertEqual(status, 200)
        self.assertIn(b"/training/class/student/list/", training)
        self.assertIn(b"Gi\xc3\xa1o vi\xc3\xaan", training)

    def test_teacher_owns_class_and_sees_only_enrolled_students(self):
        status, payload = self.admin.request("POST", "/api/teachers", {
            "full_name": "TEST_R19 Assigned Teacher", "username": "TEST_R19_assigned_teacher",
            "email": "test_r19_assigned_teacher@example.test", "password": TEST_PASSWORD,
        })
        self.assertEqual(status, 201, payload)
        teacher_id = payload["data"]["id"]
        course_id = self.admin.request("GET", "/api/courses")[1]["data"][0]["id"]
        status, created_class = self.admin.request("POST", "/api/classes", {
            "course_id": course_id, "code": "TEST_R19_TEACHER_CLASS", "name": "TEST R19 teacher class",
            "status": "OPEN", "teacher_id": teacher_id,
        })
        self.assertEqual(status, 201, created_class)
        class_id = created_class["data"]["id"]
        enrolled = self._student("OWNED")
        outside = self._student("OUTSIDE")
        status, _ = self.admin.request("POST", f"/api/classes/{class_id}/enrollments", {"student_id": enrolled["id"]})
        self.assertEqual(status, 201)
        teacher = ApiClient(self.server)
        status, login = teacher.request("POST", "/api/auth/login", {
            "login": "TEST_R19_assigned_teacher", "password": TEST_PASSWORD,
        })
        self.assertEqual(status, 200, login)
        status, rows = teacher.request("GET", "/api/students")
        self.assertEqual(status, 200, rows)
        ids = {row["id"] for row in rows["data"]}
        self.assertIn(enrolled["id"], ids)
        self.assertNotIn(outside["id"], ids)
        status, class_rows = teacher.request("GET", f"/api/classes/{class_id}/students?status=ENROLLED")
        self.assertEqual(status, 200, class_rows)
        self.assertEqual([row["student_id"] for row in class_rows["data"]["rows"]], [enrolled["id"]])

    def test_teacher_and_student_cannot_mutate_enrollment(self):
        class_id = self._class_id()
        student = self._student("DENY")
        teacher = ApiClient(self.server)
        self.assertEqual(teacher.request("POST", "/api/auth/login", {"login": "teacher", "password": TEST_PASSWORD})[0], 200)
        status, _ = teacher.request("POST", f"/api/classes/{class_id}/enrollments", {"student_id": student["id"]})
        self.assertEqual(status, 403)
        student_client = ApiClient(self.server)
        self.assertEqual(student_client.request("POST", "/api/auth/login", {"login": "student", "password": TEST_PASSWORD})[0], 200)
        status, _ = student_client.request("POST", f"/api/classes/{class_id}/enrollments", {"student_id": student["id"]})
        self.assertEqual(status, 403)

    def test_branch_manager_enrollment_scope_denies_other_branch(self):
        db = self.server.service.db
        db.execute("INSERT OR IGNORE INTO bm_branches(id,tenant_id,code,name) VALUES(2,1,'B2','TEST branch B')")
        db.execute(
            "INSERT INTO users(username,email,full_name,password_hash,role) VALUES(?,?,?,?,?)",
            ("TEST_R19_manager", "test_r19_manager@example.test", "TEST R19 manager", password_hash(TEST_PASSWORD), "BRANCH_MANAGER"),
        )
        manager_id = db.execute("SELECT id FROM users WHERE username='TEST_R19_manager'").fetchone()[0]
        db.execute("INSERT INTO bm_user_roles(user_id,tenant_id,role) VALUES(?,?,?)", (manager_id, 1, "BRANCH_MANAGER"))
        db.execute("INSERT INTO bm_manager_assignments(tenant_id,branch_id,user_id,role) VALUES(?,?,?,?)", (1, 1, manager_id, "BRANCH_MANAGER"))
        db.commit()
        course_id = self.admin.request("GET", "/api/courses")[1]["data"][0]["id"]
        status, class_a = self.admin.request("POST", "/api/classes", {
            "course_id": course_id, "code": "TEST_R19_BRANCH_A_CLASS", "name": "TEST branch A class",
            "status": "OPEN", "branch_id": 1,
        })
        self.assertEqual(status, 201, class_a)
        status, class_b = self.admin.request("POST", "/api/classes", {
            "course_id": course_id, "code": "TEST_R19_BRANCH_B_CLASS", "name": "TEST branch B class",
            "status": "OPEN", "branch_id": 2,
        })
        self.assertEqual(status, 201, class_b)
        student_a = self._student("BRANCHA")
        student_b = self._student("BRANCHB")
        # Admin create defaults have no scope; map exact fixtures to branches.
        db.execute("INSERT OR REPLACE INTO bm_entity_scopes(entity,entity_id,tenant_id,branch_id) VALUES('student',?,?,1)", (student_a["id"], 1))
        db.execute("INSERT OR REPLACE INTO bm_entity_scopes(entity,entity_id,tenant_id,branch_id) VALUES('student',?,?,2)", (student_b["id"], 1))
        db.commit()
        manager = ApiClient(self.server)
        status, login = manager.request("POST", "/api/auth/login", {"login": "TEST_R19_manager", "password": TEST_PASSWORD})
        self.assertEqual(status, 200, login)
        status, classes = manager.request("GET", "/api/classes")
        self.assertEqual(status, 200, classes)
        visible_class_ids = {row["id"] for row in classes["data"]}
        self.assertIn(class_a["data"]["id"], visible_class_ids)
        self.assertNotIn(class_b["data"]["id"], visible_class_ids)
        status, hidden = manager.request("GET", f"/api/classes/{class_b['data']['id']}/students")
        self.assertEqual(status, 404, hidden)
        status, hidden_student = manager.request("GET", f"/api/students/{student_b['id']}")
        self.assertEqual(status, 404, hidden_student)
        status, denied = manager.request("POST", f"/api/classes/{class_b['data']['id']}/enrollments", {"student_id": student_b["id"]})
        self.assertEqual(status, 404, denied)


if __name__ == "__main__":
    unittest.main()
