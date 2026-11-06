import http.client
import json
import os
import socket
import sqlite3
import subprocess
import time
import tempfile
import threading
import unittest
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app import CenterEduService, connect, create_server, password_hash, password_matches


class ApiClient:
    def __init__(self, server):
        self.server = server
        self.cookies = {}
        self.csrf = ""

    def request(self, method, path, body=None):
        headers = {"Content-Type": "application/json"}
        if self.cookies:
            headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
        if method != "GET" and self.csrf:
            headers["X-CSRF-Token"] = self.csrf
        for attempt in range(20):
            conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
            try:
                conn.request(method, path, body=json.dumps(body or {}), headers=headers)
                break
            except ConnectionRefusedError:
                conn.close()
                if attempt == 19:
                    raise
                time.sleep(0.02)
        response = conn.getresponse()
        payload = json.loads(response.read().decode())
        for value in response.getheaders():
            if value[0].lower() == "set-cookie":
                token = value[1].split(";", 1)[0]
                key, val = token.split("=", 1)
                self.cookies[key] = val
        conn.close()
        if payload.get("csrf_token"):
            self.csrf = payload["csrf_token"]
        return response.status, payload

    def request_raw(self, method, path):
        headers = {}
        if self.cookies:
            headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
        if method != "GET" and self.csrf:
            headers["X-CSRF-Token"] = self.csrf
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        conn.request(method, path, headers=headers)
        response = conn.getresponse()
        body = response.read()
        headers = dict(response.getheaders())
        conn.close()
        return response.status, headers, body


class CenterEduApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "center.sqlite3"
        self.server = create_server(self.db_path, "127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.server.service.close()
        self.tmp.cleanup()

    def test_health_and_public_shell(self):
        client = ApiClient(self.server)
        status, health = client.request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertTrue(health["ok"])
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        conn.request("GET", "/")
        response = conn.getresponse()
        self.assertEqual(response.status, 200)
        self.assertIn(b"CENTER", response.read())
        conn.close()
        status, _headers, index = client.request_raw("GET", "/")
        self.assertIn(b"nav-config.js", index)
        self.assertIn(b"reference-nav", index)
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        conn.request("GET", "/dashboard/training")
        response = conn.getresponse()
        self.assertEqual(response.status, 200)
        self.assertIn(b"CENTER", response.read())
        conn.close()
        status, _headers, css = client.request_raw("GET", "/app.css")
        self.assertEqual(status, 200)
        self.assertIn(b"*[hidden]{display:none!important}", css)
        status, _headers, js = client.request_raw("GET", "/app.js")
        self.assertEqual(status, 200)
        self.assertIn(b"training-dashboard", js)
        for marker in (
            b"attachTableFilters",
            b"attachServerTableFilters",
            b"'/api/evaluations'",
            b"'/api/tests'",
            b"'/api/homework'",
            b"'/api/trial-registrations'",
            b"'/api/enrollment-confirmations'",
            b"'/api/customer-tests'",
            b"'/api/pending-enrollments'",
            b"export-pending",
            b"/api/export/pending-enrollments",
            b"if(registry.render)",
            b"trial-status-filter",
            b"confirmation-status-filter",
            b"customer-test-query",
            b"pending-status-filter",
            b"training_dashboard",
            b"upload-finance-contracts",
            b"renew-finance-contracts",
            b"dashboard-branch-filter",
            b"dashboard-date-filter",
            b"dashboard-query-filter",
            b"q.set('date',v['dashboard-date-filter'])",
            b"q.set('q',v['dashboard-query-filter'])",
            b"'training_dashboard'",
            b"timetable-day-filter",
            b"timetable-teacher-filter",
            b"timetable-course-filter",
            b"timetable-class-filter",
            b"timetable-room-filter",
            b"timetable-time-filter",
            b"timetable-status-filter",
            b"timetable-filter-clear",
            b"contains('timetable-teacher-filter','teacher')",
            b"contains('timetable-course-filter','course_name')",
            b"contains('timetable-class-filter','class_code')",
            b"contains('timetable-room-filter','room')",
            b"class-manager-filter",
            b"class-teacher-filter",
            b"q.set('manager',manager)",
            b"q.set('teacher',teacher)",
            b"class_code:$('#timetable-class-filter')?.value||''",
            b"/api/export/timetable'+(params.toString()",
            b"student-detail",
            b"student-edit",
            b"'/api/students'",
            b"'/api/courses'",
            b"'/api/classes'",
            b"q.set('q',v['student-query'])",
            b"q.set('q',v['course-query'])",
            b"q.set('q',v['class-query'])",
            b"q.set('manager',v['class-manager-filter'])",
            b"q.set('teacher',v['class-teacher-filter'])",
            b"name=\"teacher_id\"",
            b"x.attendance_total==null",
            b"x.evaluation_count==null",
            b"x.test_count==null",
            b"x.homework_count==null",
            b"const edit=wrap.querySelector('.course-detail-edit')",
            b"if(edit) edit.onclick",
            b"`/api/courses/${id}/tests`",
            b"`/api/courses/${id}/classes`",
            b"params.set('q', query)",
            b"/api/export/courses' + (params.toString()",
            b"student-parent-filter",
            b"student-status-filter",
            b"student-class-filter",
            b"student-referral-filter",
            b"student-year-filter",
            b"student-school-filter",
            b"label:'No.'",
            "label:'Học viên'".encode(),
            "label:'Tài khoản'".encode(),
            "label:'Phụ huynh'".encode(),
            b"label:'Sales rep'",
            "label:'Lớp học'".encode(),
            "label:'Nguồn giới thiệu'".encode(),
            "label:'Ghi chú'".encode(),
            # The table page-size controls are generated by dataTable at
            # render time. Assert the owning contract and default sizes rather
            # than a stale HTML literal that no longer exists in the source.
            b"pageSizes:Array.isArray(options.pageSizes)",
            b"[10,25,50,100]",
            b"pageSizes.map(size=>`<option value=\"${size}\"",
            b"/api/students/import",
            b"/api/students/preview",
            b"/api/students/template",
            b"studentImportPreview",
            b"confirm-student-import",
            b"/api/export/students",
            b"classrooms",
            b"/api/classrooms",
            b"classroom-status-filter",
            b"export-classrooms",
            b"table-page-size",
            b"pageSizes.map(size=>`<option value=\"${size}\"",
            b"/api/finance/revenue-summary",
            b"finance-bill-confirm",
            b"const saleOwners=[...new Set(list.map(x=>String(x.sale_name||x.sale_owner||'').trim()).filter(Boolean))]",
            b"route === '/crm/potential/appointment' || route === '/sale/potential/appointment'",
        ):
            self.assertIn(marker, js)

    def test_reference_deep_links_serve_shell_and_report_engine_is_truthful(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        for route in ("/training/class", "/finance/bill/index", "/report/finance/revenue_center", "/center/student/index"):
            status, _headers, body = client.request_raw("GET", route)
            self.assertEqual(status, 200)
            self.assertIn(b"CENTER EDU", body)
        status, payload = client.request("GET", "/api/report-engine?route=/report/finance/revenue_center")
        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["route"], "/report/finance/revenue_center")
        self.assertEqual(payload["data"]["source"], "local-sqlite")
        self.assertIn("rows", payload["data"])
        status, headers, body = client.request_raw("GET", "/api/export/report-engine?route=/report/finance/revenue_center")
        self.assertEqual(status, 200)
        self.assertIn("text/csv", headers["Content-Type"])
        self.assertIn(b"status", body)

    def test_generated_screen_create_update_export_delete_and_persistence(self):
        """Exercise the evidence-derived generic screen contract end to end."""
        admin = ApiClient(self.server)
        self.assertEqual(admin.request("POST", "/api/auth/login", {
            "login": "admin", "password": "ChangeMe!CenterEdu2026",
        })[0], 200)
        route = "/finance/bill/index"
        status, specs = admin.request("GET", f"/api/screen-specs?route={route}")
        self.assertEqual(status, 200)
        self.assertEqual(len(specs["data"]), 1)
        self.assertTrue(any("excel" in str(button).lower() for button in specs["data"][0]["buttons"]))

        status, created = admin.request("POST", "/api/generated/screens", {
            "route": route, "data": {"ma_hoa_on": "GEN-INV-001"},
        })
        self.assertEqual(status, 201)
        record_id = created["data"]["id"]
        self.assertEqual(created["data"]["data"]["ma_hoa_on"], "GEN-INV-001")
        listed_status, listed = admin.request("GET", f"/api/generated/screens?route={route}&q=GEN-INV-001")
        self.assertEqual(listed_status, 200)
        self.assertEqual(listed["data"]["total"], 1)
        self.assertEqual(listed["data"]["records"][0]["id"], record_id)

        second_service = CenterEduService(self.db_path)
        try:
            persisted = second_service.generated_screen(second_service.user_by_login("admin"), route, "GEN-INV-001")
            self.assertEqual(persisted["total"], 1)
            self.assertEqual(persisted["records"][0]["id"], record_id)
        finally:
            second_service.close()

        status, updated = admin.request("POST", f"/api/generated/screens/{record_id}", {
            "route": route, "data": {"ma_hoa_on": "GEN-INV-002"},
        })
        self.assertEqual(status, 200)
        self.assertEqual(updated["data"]["data"]["ma_hoa_on"], "GEN-INV-002")
        export_status, export_headers, export_body = admin.request_raw(
            "GET", f"/api/export/generated-screen?route={route}&q=GEN-INV-002"
        )
        self.assertEqual(export_status, 200)
        self.assertIn("text/csv", export_headers["Content-Type"])
        self.assertIn(b"GEN-INV-002", export_body)

        delete_status, _delete_headers, delete_body = admin.request_raw(
            "DELETE", f"/api/generated/screens/{record_id}?route={route}"
        )
        deleted = json.loads(delete_body.decode())
        self.assertEqual(delete_status, 200)
        self.assertTrue(deleted["data"]["deleted"])
        final_status, final = admin.request("GET", f"/api/generated/screens?route={route}")
        self.assertEqual(final_status, 200)
        self.assertEqual(final["data"]["total"], 0)

    def test_generated_screen_projects_legacy_form_keys_to_observed_columns(self):
        """Rich-demo training rows render observed columns after read-back."""
        previous = os.environ.get("CENTER_EDU_RICH_DEMO")
        os.environ["CENTER_EDU_RICH_DEMO"] = "1"
        try:
            service = CenterEduService(self.db_path)
            try:
                admin = service.user_by_login("admin")
                expected = {
                    "/training/announcement": ("thong_bao", "trang_thai", ("title", "thong_bao")),
                    "/training/event": ("noi_dung", "trang_thai", ("title", "noi_dung")),
                    "/training/post": ("noi_dung", "trang_thai", ("content", "noi_dung")),
                }
                for route, (display_key, status_key, raw_keys) in expected.items():
                    result = service.generated_screen(admin, route)
                    self.assertGreater(result["total"], 0, route)
                    row = result["records"][0]
                    self.assertIn("display_data", row)
                    self.assertTrue(row["display_data"].get(display_key), route)
                    self.assertTrue(row["data"].get(status_key), route)
                    self.assertTrue(any(row["data"].get(key) for key in raw_keys), route)
            finally:
                service.close()
        finally:
            if previous is None:
                os.environ.pop("CENTER_EDU_RICH_DEMO", None)
            else:
                os.environ["CENTER_EDU_RICH_DEMO"] = previous

    def test_generated_screen_rejects_unknown_route_and_field_and_enforces_rbac(self):
        admin = ApiClient(self.server)
        self.assertEqual(admin.request("POST", "/api/auth/login", {
            "login": "admin", "password": "ChangeMe!CenterEdu2026",
        })[0], 200)
        route = "/finance/revenue"
        status, unknown_route = admin.request("POST", "/api/generated/screens", {
            "route": "/does-not-exist", "data": {"code": "NOPE"},
        })
        self.assertEqual(status, 404)
        self.assertEqual(unknown_route["error"]["code"], "SCREEN_SPEC_NOT_FOUND")
        status, unknown_field = admin.request("POST", "/api/generated/screens", {
            "route": route, "data": {"not_observed": "NOPE"},
        })
        self.assertEqual(status, 400)
        self.assertEqual(unknown_field["error"]["code"], "VALIDATION_ERROR")
        status, created = admin.request("POST", "/api/generated/screens", {
            "route": route, "data": {"code": "REV-001"},
        })
        self.assertEqual(status, 201)
        record_id = created["data"]["id"]

        student = ApiClient(self.server)
        self.assertEqual(student.request("POST", "/api/auth/login", {
            "login": "student", "password": "ChangeMe!CenterEdu2026",
        })[0], 200)
        denied_create, denied_payload = student.request("POST", "/api/generated/screens", {
            "route": route, "data": {"code": "REV-STUDENT"},
        })
        self.assertEqual(denied_create, 403)
        self.assertEqual(denied_payload["error"]["code"], "FORBIDDEN")
        denied_update, denied_update_payload = student.request("POST", f"/api/generated/screens/{record_id}", {
            "route": route, "data": {"code": "REV-STUDENT-EDIT"},
        })
        self.assertEqual(denied_update, 403)
        self.assertEqual(denied_update_payload["error"]["code"], "FORBIDDEN")
        denied_delete, _denied_delete_headers, denied_delete_body = student.request_raw(
            "DELETE", f"/api/generated/screens/{record_id}?route={route}"
        )
        denied_delete_payload = json.loads(denied_delete_body.decode())
        self.assertEqual(denied_delete, 403)
        self.assertEqual(denied_delete_payload["error"]["code"], "FORBIDDEN")

    def test_sale_contract_generic_transport_is_authority_blocked(self):
        admin = ApiClient(self.server)
        self.assertEqual(admin.request("POST", "/api/auth/login", {
            "login": "admin", "password": "ChangeMe!CenterEdu2026",
        })[0], 200)
        route = "/sale/contract"
        before = admin.request("GET", f"/api/generated/screens?route={route}")[1]["data"]["total"]
        status, payload = admin.request("POST", "/api/generated/screens", {
            "route": route, "data": {"code": "GEN-AUTHORITY-LEAK"},
        })
        self.assertEqual(status, 409)
        self.assertEqual(payload["error"]["code"], "AUTHORITY_BOUNDARY")
        after = admin.request("GET", f"/api/generated/screens?route={route}")[1]["data"]["total"]
        self.assertEqual(after, before)

    def test_finance_revenue_list_uses_observed_reference_contract(self):
        """The list view keeps summary APIs while matching the observed 11/2 contract."""
        source = (Path(__file__).parent / "static" / "app.js").read_text(encoding="utf-8")
        start = source.index("async function financeRevenues(el){")
        end = source.index("function surveyFields", start)
        view = source[start:end]
        for label in ("No.", "Mã", "Tên", "Trạng thái", "Giá", "Kiểu giảm", "Giá trị giảm", "Giá phải thu", "Trung tâm", "Ghi chú", "Công cụ"):
            self.assertIn(f"label:'{label}'", view)
        self.assertIn("setAttribute('placeholder','Tìm trong bảng...')", view)
        self.assertIn("id=\"add-finance-revenue\"", view)
        self.assertNotIn("finance-revenue-status-filter", view)
        self.assertNotIn("finance-revenue-date-from", view)
        self.assertNotIn("finance-revenue-branch", view)
        self.assertNotIn("finance-revenue-summary-breakdown", view)
        admin = ApiClient(self.server)
        self.assertEqual(admin.request("POST", "/api/auth/login", {
            "login": "admin", "password": "ChangeMe!CenterEdu2026",
        })[0], 200)
        status, rows = admin.request("GET", "/api/finance/revenues?status=ACTIVE&center=HCM")
        self.assertEqual(status, 200)
        self.assertTrue(all(row["status"] == "ACTIVE" and row["center"] == "HCM" for row in rows["data"]))
        summary_status, summary = admin.request("GET", "/api/finance/revenue-summary?center=HCM")
        self.assertEqual(summary_status, 200)
        self.assertIn("totals", summary["data"])

    def test_classroom_setup_contract_filters_export_round_trip_and_rbac(self):
        """Exercise the local contract derived from the observed setup/classroom table."""
        admin = ApiClient(self.server)
        self.assertEqual(admin.request("POST", "/api/auth/login", {
            "login": "admin", "password": "ChangeMe!CenterEdu2026",
        })[0], 200)

        status, rows = admin.request("GET", "/api/classrooms?q=ROOM-A1&status=ACTIVE")
        self.assertEqual(status, 200)
        self.assertTrue(any(row["code"] == "ROOM-A1" for row in rows["data"]))

        status, created = admin.request("POST", "/api/classrooms", {
            "code": "ROOM-B2", "name": "Phòng học B2", "capacity": 24,
            "description": "Phòng tầng hai", "status": "ACTIVE",
        })
        self.assertEqual(status, 201)
        classroom_id = created["data"]["id"]
        self.assertEqual(created["data"]["capacity"], 24)
        audit_rows = admin.request("GET", "/api/audit")[1]["data"]
        self.assertTrue(any(row["entity"] == "classroom" and row["action"] == "CREATE" and row["entity_id"] == str(classroom_id) for row in audit_rows))

        status, detail = admin.request("GET", f"/api/classrooms/{classroom_id}")
        self.assertEqual(status, 200)
        self.assertEqual(detail["data"]["name"], "Phòng học B2")

        status, updated = admin.request("POST", f"/api/classrooms/{classroom_id}", {
            "code": "ROOM-B2", "name": "Phòng học B2 mới", "capacity": 26,
            "description": "Đã cập nhật", "status": "INACTIVE",
        })
        self.assertEqual(status, 200)
        self.assertEqual(updated["data"]["capacity"], 26)
        self.assertEqual(updated["data"]["status"], "INACTIVE")
        audit_rows = admin.request("GET", "/api/audit")[1]["data"]
        self.assertTrue(any(row["entity"] == "classroom" and row["action"] == "UPDATE" and row["entity_id"] == str(classroom_id) for row in audit_rows))

        export_status, export_headers, export_body = admin.request_raw(
            "GET", "/api/export/classrooms?status=INACTIVE"
        )
        self.assertEqual(export_status, 200)
        self.assertIn("text/csv", export_headers["Content-Type"])
        self.assertIn(b"ROOM-B2", export_body)

        student = ApiClient(self.server)
        self.assertEqual(student.request("POST", "/api/auth/login", {
            "login": "student", "password": "ChangeMe!CenterEdu2026",
        })[0], 200)
        denied_status, denied = student.request("GET", "/api/classrooms")
        self.assertEqual(denied_status, 403)
        self.assertEqual(denied["error"]["code"], "FORBIDDEN")

    def test_classroom_duplicate_rolls_back_row_and_audit(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {
            "login": "admin", "password": "ChangeMe!CenterEdu2026",
        })[0], 200)
        before = client.request("GET", "/api/audit")[1]["data"]
        status, payload = client.request("POST", "/api/classrooms", {
            "code": "ROOM-A1", "name": "Duplicate room", "capacity": 10,
            "description": "must rollback", "status": "ACTIVE",
        })
        self.assertEqual(status, 409)
        self.assertEqual(payload["error"]["code"], "DUPLICATE_CLASSROOM")
        after = client.request("GET", "/api/audit")[1]["data"]
        self.assertEqual(len(after), len(before))
        self.assertFalse(any(row["entity"] == "classroom" and row["action"] == "CREATE" and "Duplicate room" in row["metadata_json"] for row in after))

    def test_student_import_is_atomic_and_exposes_observed_upload_fields(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        csv_payload = (
            "student_code,identifier,full_name,english_name,email,phone,username,date_of_birth,gender,class_codes,parent1_name,school,referral_source,enrollment_year,note\n"
            "HV-CSV-01,ID-01,CSV Learner,CSV,learner@example.com,0901000001,csv-user,2010-02-03,N,ENG-FND-01,Parent One,Demo School,Website,2026,Imported\n"
        )
        status, imported = client.request("POST", "/api/students/import", {"csv": csv_payload})
        self.assertEqual(status, 201)
        self.assertEqual(imported["data"]["count"], 1)
        row = client.request("GET", "/api/students?q=HV-CSV-01")[1]["data"][0]
        self.assertEqual(row["identifier"], "ID-01")
        self.assertEqual(row["school"], "Demo School")
        self.assertEqual(row["referral_source"], "Website")

        before = client.request("GET", "/api/students")[1]["data"]
        bad_csv = "student_code,full_name,email\nHV-CSV-02,Second,second@example.com\nHV-CSV-03,MissingEmail,not-an-email\n"
        status, payload = client.request("POST", "/api/students/import", {"csv": bad_csv})
        self.assertEqual(status, 400)
        self.assertIn("row 3", payload["error"]["message"])
        after = client.request("GET", "/api/students")[1]["data"]
        self.assertEqual(len(after), len(before))
        self.assertFalse(any(row["student_code"] == "HV-CSV-02" for row in after))

    def test_student_import_preview_is_read_only_and_accepts_observed_date_format(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        csv_payload = (
            "student_code,full_name,email,date_of_birth,expected_start_date\n"
            "HV-PREVIEW-01,Preview Learner,preview@example.com,03/02/2010,15/08/2026\n"
        )
        before = client.request("GET", "/api/students?q=HV-PREVIEW-01")[1]["data"]
        status, preview = client.request("POST", "/api/students/preview", {"csv": csv_payload})
        self.assertEqual(status, 200)
        self.assertFalse(preview["data"]["mutation"])
        self.assertEqual(preview["data"]["valid_count"], 1)
        self.assertEqual(preview["data"]["errors"], [])
        self.assertEqual(preview["data"]["rows"][0]["date_of_birth"], "2010-02-03")
        self.assertEqual(preview["data"]["rows"][0]["expected_start_date"], "2026-08-15")
        after = client.request("GET", "/api/students?q=HV-PREVIEW-01")[1]["data"]
        self.assertEqual(after, before)
        template_status, headers, body = client.request_raw("GET", "/api/students/template")
        self.assertEqual(template_status, 200)
        self.assertIn("text/csv", headers["Content-Type"])
        self.assertIn(b"student_code", body)

    def test_student_import_preview_rejects_duplicate_without_partial_rows(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        csv_payload = (
            "student_code,full_name,email\n"
            "HV-DUP-01,First,first@example.com\n"
            "HV-DUP-01,Second,second@example.com\n"
        )
        status, preview = client.request("POST", "/api/students/preview", {"csv": csv_payload})
        self.assertEqual(status, 200)
        self.assertEqual(preview["data"]["valid_count"], 1)
        self.assertEqual(preview["data"]["errors"][0]["code"], "DUPLICATE_STUDENT")
        self.assertEqual(client.request("GET", "/api/students?q=HV-DUP-01")[1]["data"], [])

    def test_student_detail_update_persists_observed_metadata_fields(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        student_id = client.request("GET", "/api/students?q=HV-0001")[1]["data"][0]["id"]
        status, updated = client.request("POST", f"/api/students/{student_id}", {
            "student_code": "HV-0001", "full_name": "Demo Student Updated", "email": "student@center.edu.vn",
            "phone": "0900000000", "identifier": "ID-UPDATED", "english_name": "Demo Updated",
            "date_of_birth": "2010-02-03", "expected_start_date": "2026-08-15", "expected_sessions": 12,
            "province": "Hà Nội", "ward": "Cầu Giấy", "address": "1 Demo Street", "school": "Demo School",
            "class_name": "10A1", "birth_place": "Hà Nội", "referral_source": "Website", "enrollment_year": 2026,
            "parent1_name": "Parent One", "parent1_phone": "0901111111", "note": "Updated metadata", "status": "ACTIVE",
            "sales_rep": "Sales One",
        })
        self.assertEqual(status, 200)
        self.assertEqual(updated["data"]["identifier"], "ID-UPDATED")
        self.assertEqual(updated["data"]["expected_start_date"], "2026-08-15")
        self.assertEqual(updated["data"]["parent1_name"], "Parent One")
        self.assertEqual(updated["data"]["school"], "Demo School")
        detail = client.request("GET", f"/api/students/{student_id}")[1]["data"]
        self.assertEqual(detail["address"], "1 Demo Street")
        self.assertEqual(detail["note"], "Updated metadata")
        self.assertEqual(detail["sales_rep"], "Sales One")

    def test_student_reference_table_columns_and_sales_rep_survive_restart(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        status, created = client.request("POST", "/api/students", {
            "student_code": "HV-SALES-01", "full_name": "Sales Contract Learner",
            "email": "sales-contract@example.com", "username": "sales-contract",
            "sales_rep": "Rep A", "parent1_name": "Parent A", "class_name": "ENG-FND-01",
            "referral_source": "Website", "note": "Observed table contract",
        })
        self.assertEqual(status, 201)
        row = client.request("GET", "/api/students?q=HV-SALES-01")[1]["data"][0]
        self.assertEqual(row["sales_rep"], "Rep A")
        self.assertEqual(row["username"], "sales-contract")
        self.assertEqual(row["parent1_name"], "Parent A")

    def test_student_filter_and_csv_export_contract(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        status, filtered = client.request("GET", "/api/students?school=Demo%20School&referral_source=Website&year=2026")
        self.assertEqual(status, 200)
        self.assertTrue(any(row["student_code"] == "HV-0001" for row in filtered["data"]) is False)
        export_status, headers, body = client.request_raw("GET", "/api/export/students?school=Demo%20School&referral_source=Website&year=2026")
        self.assertEqual(export_status, 200)
        self.assertIn("text/csv", headers["Content-Type"])

    def test_security_headers_are_present_on_api_and_static_responses(self):
        client = ApiClient(self.server)
        status, headers, _body = client.request_raw("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertIn("default-src 'self'", headers["Content-Security-Policy"])
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["X-Frame-Options"], "DENY")
        self.assertEqual(headers["Referrer-Policy"], "same-origin")
        self.assertIn("camera=()", headers["Permissions-Policy"])
        status, headers, _body = client.request_raw("GET", "/app.css")
        self.assertEqual(status, 200)
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["X-Frame-Options"], "DENY")

    def test_negative_content_length_fails_closed_before_body_parse(self):
        """Malformed framing must not turn read(-1) into an unbounded body read."""
        payload = b'{"login":"admin","password":"ChangeMe!CenterEdu2026"}'
        sock = socket.create_connection(("127.0.0.1", self.server.server_port), timeout=5)
        try:
            sock.sendall(
                b"POST /api/auth/login HTTP/1.1\r\n"
                b"Host: 127.0.0.1\r\n"
                b"Connection: close\r\n"
                b"Content-Type: application/json\r\n"
                b"Content-Length: -1\r\n\r\n" + payload
            )
            sock.shutdown(socket.SHUT_WR)
            response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
        finally:
            sock.close()
        self.assertIn(b"400 Bad Request", response)
        self.assertIn(b"INVALID_CONTENT_LENGTH", response)

    def test_secure_cookie_flag_is_configurable_for_tls_deployments(self):
        os.environ["CENTER_EDU_COOKIE_SECURE"] = "1"
        try:
            conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
            conn.request("POST", "/api/auth/login", body=json.dumps({"login": "admin", "password": "ChangeMe!CenterEdu2026"}), headers={"Content-Type": "application/json"})
            response = conn.getresponse()
            response.read()
            cookie = response.getheader("Set-Cookie", "")
            conn.close()
            self.assertEqual(response.status, 200)
            self.assertIn("; Secure", cookie)
        finally:
            os.environ.pop("CENTER_EDU_COOKIE_SECURE", None)

    def test_backup_refuses_overwrite_of_existing_destination(self):
        destination = Path(self.tmp.name) / "existing-backup.sqlite3"
        destination.write_bytes(b"keep-existing-backup")
        env = os.environ.copy()
        env["CENTER_EDU_DB"] = str(self.db_path)
        script = Path(__file__).resolve().parent / "ops" / "backup.sh"
        result = subprocess.run(
            ["bash", str(script), str(destination)],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 3)
        self.assertIn("refusing overwrite", result.stderr)
        self.assertEqual(destination.read_bytes(), b"keep-existing-backup")

    def test_login_remember_identifier_never_persists_password(self):
        index = (Path(__file__).parent / "static" / "index.html").read_text()
        script = (Path(__file__).parent / "static" / "app.js").read_text()
        self.assertIn('id="remember-login"', index)
        self.assertIn("center_edu_login_identifier", script)
        self.assertIn("window.localStorage.setItem(rememberedLoginKey,login)", script)
        self.assertIn("window.localStorage.removeItem(rememberedLoginKey)", script)
        self.assertIn("addEventListener('change'", script)
        self.assertNotIn("localStorage.setItem(rememberedLoginKey,password)", script)
        self.assertNotIn("localStorage.setItem(rememberedLoginKey,f.get('password'))", script)

    def test_login_rejects_oversized_password_before_verification(self):
        client = ApiClient(self.server)
        status, payload = client.request(
            "POST",
            "/api/auth/login",
            {"login": "admin", "password": "x" * 513},
        )
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"]["code"], "INVALID_CREDENTIALS")

    def test_password_verification_fails_closed_for_malformed_hashes(self):
        encoded = password_hash("bounded-secret")
        self.assertTrue(password_matches("bounded-secret", encoded))
        self.assertFalse(password_matches("bounded-secret", None))
        self.assertFalse(password_matches("bounded-secret", "pbkdf2_sha256$0$00$00"))
        self.assertFalse(password_matches("bounded-secret", "pbkdf2_sha256$1000001$00$00"))

    def test_login_dashboard_crud_attendance_and_audit(self):
        client = ApiClient(self.server)
        status, payload = client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})
        self.assertEqual(status, 200)
        self.assertEqual(payload["user"]["role"], "ADMIN")
        status, dashboard = client.request("GET", "/api/dashboard")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(dashboard["data"]["counts"]["students"], 1)
        status, created = client.request("POST", "/api/students", {"student_code": "HV-TEST", "full_name": "Test Learner", "email": "test@example.com"})
        self.assertEqual(status, 201)
        student_id = created["data"]["id"]
        status, records = client.request("GET", "/api/students?q=Test%20Learner")
        self.assertEqual(status, 200)
        self.assertEqual(records["data"][0]["id"], student_id)
        status, course = client.request("POST", "/api/courses", {"code": "TEST-101", "name": "Test Course", "level": "Beginner"})
        self.assertEqual(status, 201)
        self.assertEqual(course["data"]["code"], "TEST-101")
        status, classes = client.request("GET", "/api/classes")
        self.assertEqual(status, 200)
        existing_class = classes["data"][0]
        # Seed student is enrolled; use it for a real attendance workflow.
        status, students = client.request("GET", "/api/students?q=Demo%20Student")
        self.assertEqual(status, 200)
        status, attendance = client.request("POST", "/api/attendance", {"class_id": existing_class["id"], "student_id": students["data"][0]["id"], "session_date": "2026-10-30", "status": "PRESENT"})
        self.assertEqual(status, 200)
        self.assertEqual(attendance["data"]["status"], "PRESENT")
        status, audit = client.request("GET", "/api/audit")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(audit["data"]), 3)

    def test_dashboard_exposes_training_rows_with_unknown_unobserved_fields(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        dashboard = client.request("GET", "/api/dashboard")[1]["data"]
        self.assertIn("training_dashboard", dashboard)
        self.assertGreaterEqual(len(dashboard["training_dashboard"]), 1)
        row = dashboard["training_dashboard"][0]
        self.assertIn("class_code", row)
        self.assertIn("session_date", row)
        self.assertIn("attendance_total", row)
        self.assertEqual(row["attendance_present"], 0)
        self.assertIsNone(row["branch"])
        self.assertIsNone(row["lesson_content"])

    def test_dashboard_server_filters_validate_and_preserve_unknown_fields(self):
        client = ApiClient(self.server)
        self.assertEqual(
            client.request("POST", "/api/auth/login", {
                "login": "admin", "password": "ChangeMe!CenterEdu2026",
            })[0],
            200,
        )

        status, by_date = client.request("GET", "/api/dashboard?date=2026-11-03")
        self.assertEqual(status, 200)
        rows = by_date["data"]["training_dashboard"]
        self.assertEqual([row["session_date"] for row in rows], ["2026-11-03"])
        self.assertIsNone(rows[0]["branch"])
        self.assertIsNone(rows[0]["lesson_content"])

        status, by_query = client.request("GET", "/api/dashboard?q=eng-fnd-01")
        self.assertEqual(status, 200)
        self.assertTrue(by_query["data"]["training_dashboard"])
        self.assertTrue(all("ENG-FND-01" in row["class_code"] for row in by_query["data"]["training_dashboard"]))

        status, no_match = client.request("GET", "/api/dashboard?q=does-not-exist")
        self.assertEqual(status, 200)
        self.assertEqual(no_match["data"]["training_dashboard"], [])

    def test_training_dashboard_has_dedicated_route_and_screen_marker(self):
        client = ApiClient(self.server)
        status, _, body = client.request_raw("GET", "/dashboard/training")
        self.assertEqual(status, 200)
        self.assertIn(b"training-dashboard", body)
        self.assertIn(b"dashboard/training", body)

        status, _ = client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})
        self.assertEqual(status, 200)
        status, invalid = client.request("GET", "/api/dashboard?date=not-a-date")
        self.assertEqual(status, 400)
        self.assertEqual(invalid["error"]["code"], "VALIDATION_ERROR")

    def test_attendance_report_preserves_known_zero_counts(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        status, report = client.request("GET", "/api/reports/attendance")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(report["data"]), 1)
        row = next(item for item in report["data"] if item["class_code"] == "ENG-FND-01")
        self.assertEqual(row["total"], 0)
        self.assertEqual(row["present"], 0)
        self.assertEqual(row["absent"], 0)
        self.assertEqual(row["late"], 0)

    def test_rbac_csrf_and_student_scope(self):
        admin = ApiClient(self.server)
        self.assertEqual(admin.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        admin.csrf = ""
        status, _ = admin.request("POST", "/api/students", {"student_code": "NO-CSRF", "full_name": "No CSRF", "email": "nocsrf@example.com"})
        self.assertEqual(status, 403)
        student = ApiClient(self.server)
        self.assertEqual(student.request("POST", "/api/auth/login", {"login": "student", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        status, _ = student.request("POST", "/api/courses", {"code": "DENIED", "name": "Denied"})
        self.assertEqual(status, 403)
        status, students = student.request("GET", "/api/students")
        self.assertEqual(status, 200)
        self.assertEqual(len(students["data"]), 1)
        own = student.request("GET", "/api/students?q=Demo%20Student")
        self.assertEqual(own[0], 200)
        self.assertEqual(len(own[1]["data"]), 1)
        missing = student.request("GET", "/api/students?q=does-not-exist")
        self.assertEqual(missing[0], 200)
        self.assertEqual(missing[1]["data"], [])

    def test_dashboard_scope_does_not_expose_staff_or_unrelated_records(self):
        admin = ApiClient(self.server)
        self.assertEqual(admin.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        course_id = admin.request("GET", "/api/courses?q=English")[1]["data"][0]["id"]
        self.assertEqual(admin.request("POST", "/api/students", {
            "student_code": "HV-0002", "full_name": "Unrelated Student", "email": "unrelated@example.com",
        })[0], 201)
        self.assertEqual(admin.request("POST", "/api/classes", {
            "course_id": course_id, "code": "ENG-FND-UNRELATED", "status": "OPEN",
        })[0], 201)

        student = ApiClient(self.server)
        self.assertEqual(student.request("POST", "/api/auth/login", {"login": "student", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        status, dashboard = student.request("GET", "/api/dashboard")
        self.assertEqual(status, 200)
        counts = dashboard["data"]["counts"]
        self.assertEqual(counts["students"], 1)
        self.assertEqual(counts["classes"], 1)
        self.assertEqual(counts["courses"], 1)
        self.assertEqual(counts["trial_registrations"], 0)
        self.assertEqual(dashboard["data"]["recent_activity"], [])

    def test_teacher_student_list_is_limited_to_assigned_enrolled_classes(self):
        admin = ApiClient(self.server)
        self.assertEqual(admin.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        course_id = admin.request("GET", "/api/courses?q=English")[1]["data"][0]["id"]
        teacher_id = admin.request("GET", "/api/classes")[1]["data"][0]["teacher_id"]
        self.assertEqual(admin.request("POST", "/api/students", {
            "student_code": "HV-0003", "full_name": "Teacher Unassigned", "email": "teacher-unassigned@example.com",
        })[0], 201)
        self.assertEqual(admin.request("POST", "/api/classes", {
            "course_id": course_id, "code": "ENG-FND-TEACHER-OTHER", "teacher_id": teacher_id, "status": "OPEN",
        })[0], 201)
        teacher = ApiClient(self.server)
        self.assertEqual(teacher.request("POST", "/api/auth/login", {"login": "teacher", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        status, students = teacher.request("GET", "/api/students")
        self.assertEqual(status, 200)
        self.assertEqual([row["student_code"] for row in students["data"]], ["HV-0001"])

    def test_student_dashboard_and_report_do_not_aggregate_peer_attendance(self):
        admin = ApiClient(self.server)
        self.assertEqual(admin.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        db = self.server.service.db
        class_id = db.execute("SELECT id FROM classes WHERE code='ENG-FND-01'").fetchone()[0]
        teacher_id = db.execute("SELECT id FROM users WHERE username='teacher'").fetchone()[0]
        db.execute("INSERT INTO students(student_code,full_name,email) VALUES(?,?,?)", ("HV-PEER", "Peer Student", "peer@example.com"))
        peer_id = db.execute("SELECT id FROM students WHERE student_code='HV-PEER'").fetchone()[0]
        db.execute("INSERT INTO enrollments(class_id,student_id,status) VALUES(?,?,?)", (class_id, peer_id, "ENROLLED"))
        db.execute("INSERT INTO attendance(class_id,student_id,session_date,status,marked_by) VALUES(?,?,?,?,?)", (class_id, peer_id, "2026-11-03", "PRESENT", teacher_id))
        db.commit()

        student = ApiClient(self.server)
        self.assertEqual(student.request("POST", "/api/auth/login", {"login": "student", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        dashboard = student.request("GET", "/api/dashboard")[1]["data"]
        training_row = next(row for row in dashboard["training_dashboard"] if row["session_date"] == "2026-11-03")
        self.assertEqual(training_row["attendance_total"], 0)
        self.assertEqual(training_row["attendance_present"], 0)
        report = student.request("GET", "/api/reports/attendance")[1]["data"]
        row = next(item for item in report if item["class_code"] == "ENG-FND-01")
        self.assertEqual(row["total"], 0)
        self.assertEqual(row["present"], 0)

    def test_student_course_list_and_detail_are_scope_limited(self):
        admin = ApiClient(self.server)
        self.assertEqual(admin.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        status, unrelated = admin.request("POST", "/api/courses", {
            "code": "PRIVATE-COURSE", "name": "Private unrelated course", "level": "Advanced",
        })
        self.assertEqual(status, 201)
        unrelated_id = unrelated["data"]["id"]

        student = ApiClient(self.server)
        self.assertEqual(student.request("POST", "/api/auth/login", {"login": "student", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        status, courses = student.request("GET", "/api/courses")
        self.assertEqual(status, 200)
        self.assertEqual([row["code"] for row in courses["data"]], ["ENG-FND"])
        self.assertEqual(student.request("GET", f"/api/courses/{unrelated_id}")[0], 404)

    def test_student_test_result_count_is_scoped_to_own_results(self):
        admin = ApiClient(self.server)
        self.assertEqual(admin.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        classroom = admin.request("GET", "/api/classes")[1]["data"][0]
        student = admin.request("GET", "/api/students?q=Demo%20Student")[1]["data"][0]
        status, created = admin.request("POST", "/api/tests", {
            "class_id": classroom["id"], "name": "Scoped result count", "test_date": "2026-11-20", "max_score": 10,
        })
        self.assertEqual(status, 201)
        test_id = created["data"]["id"]
        self.assertEqual(admin.request("POST", "/api/test-results", {
            "test_id": test_id, "student_id": student["id"], "score": 8,
        })[0], 200)

        db = self.server.service.db
        teacher_id = db.execute("SELECT id FROM users WHERE username='teacher'").fetchone()[0]
        db.execute("INSERT INTO students(student_code,full_name,email) VALUES(?,?,?)", ("HV-PEER-TEST", "Peer Test", "peer-test@example.com"))
        peer_id = db.execute("SELECT id FROM students WHERE student_code='HV-PEER-TEST'").fetchone()[0]
        db.execute("INSERT INTO enrollments(class_id,student_id,status) VALUES(?,?,?)", (classroom["id"], peer_id, "ENROLLED"))
        db.execute("INSERT INTO test_results(test_id,student_id,score,marked_by) VALUES(?,?,?,?)", (test_id, peer_id, 9, teacher_id))
        db.commit()

        student_client = ApiClient(self.server)
        self.assertEqual(student_client.request("POST", "/api/auth/login", {"login": "student", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        student_test = next(row for row in student_client.request("GET", "/api/tests")[1]["data"] if row["id"] == test_id)
        self.assertEqual(student_test["result_count"], 1)
        admin_test = next(row for row in admin.request("GET", "/api/tests")[1]["data"] if row["id"] == test_id)
        self.assertEqual(admin_test["result_count"], 2)

    def test_student_timetable_and_homework_exclude_dropped_classes(self):
        admin = ApiClient(self.server)
        self.assertEqual(admin.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        classroom = admin.request("GET", "/api/classes")[1]["data"][0]
        student = admin.request("GET", "/api/students?q=Demo%20Student")[1]["data"][0]
        self.assertEqual(admin.request("POST", "/api/timetable", {
            "class_id": classroom["id"], "session_date": "2026-11-21", "start_time": "18:30", "end_time": "20:00", "room": "Room A1",
        })[0], 201)
        self.assertEqual(admin.request("POST", "/api/homework", {
            "class_id": classroom["id"], "title": "Dropped class homework", "due_date": "2026-11-22",
        })[0], 201)
        self.assertEqual(admin.request("POST", "/api/evaluations", {
            "class_id": classroom["id"], "student_id": student["id"], "session_date": "2026-11-21", "score": 7, "status": "PUBLISHED",
        })[0], 200)
        self.assertEqual(admin.request("POST", "/api/attendance", {
            "class_id": classroom["id"], "student_id": student["id"], "session_date": "2026-11-21", "status": "PRESENT",
        })[0], 200)
        self.assertEqual(admin.request("POST", "/api/tests", {
            "class_id": classroom["id"], "name": "Dropped class test", "test_date": "2026-11-21", "max_score": 10,
        })[0], 201)
        db = self.server.service.db
        db.execute("UPDATE enrollments SET status='DROPPED' WHERE class_id=? AND student_id=?", (classroom["id"], student["id"]))
        db.commit()

        student_client = ApiClient(self.server)
        self.assertEqual(student_client.request("POST", "/api/auth/login", {"login": "student", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        timetable = student_client.request("GET", "/api/timetable")[1]["data"]
        homework = student_client.request("GET", "/api/homework")[1]["data"]
        attendance = student_client.request("GET", "/api/attendance")[1]["data"]
        evaluations = student_client.request("GET", "/api/evaluations")[1]["data"]
        tests = student_client.request("GET", "/api/tests")[1]["data"]
        dashboard = student_client.request("GET", "/api/dashboard")[1]["data"]
        self.assertFalse(any(row["session_date"] == "2026-11-21" for row in timetable))
        self.assertFalse(any(row["title"] == "Dropped class homework" for row in homework))
        self.assertFalse(any(row["session_date"] == "2026-11-21" for row in attendance))
        self.assertFalse(any(row["session_date"] == "2026-11-21" for row in evaluations))
        self.assertFalse(any(row["test_date"] == "2026-11-21" for row in tests))
        self.assertEqual(dashboard["counts"]["evaluations"], 0)
        self.assertEqual(dashboard["attendance"], [])

    def test_session_persists_when_service_restarts(self):
        client = ApiClient(self.server)
        status, _ = client.request("POST", "/api/auth/login", {"login": "staff", "password": "ChangeMe!CenterEdu2026"})
        self.assertEqual(status, 200)
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()
        self.server.service.close()
        self.server = create_server(self.db_path, "127.0.0.1", 0)
        client.server = self.server
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        status, me = client.request("GET", "/api/auth/me")
        self.assertEqual(status, 200)
        self.assertTrue(me["authenticated"])
        self.assertEqual(me["user"]["role"], "STAFF")

    def test_concurrent_authenticated_reads_keep_sqlite_session_consistent(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        cookies = dict(client.cookies)
        csrf = client.csrf

        def read_dashboard(_index):
            reader = ApiClient(self.server)
            reader.cookies = dict(cookies)
            reader.csrf = csrf
            status, payload = reader.request("GET", "/api/dashboard")
            return status, payload.get("ok"), payload.get("data", {}).get("counts", {}).get("students")

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(read_dashboard, range(24)))
        self.assertEqual({status for status, _ok, _students in results}, {200})
        self.assertEqual({ok for _status, ok, _students in results}, {True})
        self.assertEqual({students for _status, _ok, students in results}, {1})

    def test_training_workflow_routes_and_writes(self):
        client = ApiClient(self.server)
        status, _ = client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})
        self.assertEqual(status, 200)
        self.assertEqual(client.request("GET", "/api/timetable")[0], 200)
        self.assertEqual(client.request("GET", "/api/evaluations")[0], 200)
        self.assertEqual(client.request("GET", "/api/tests")[0], 200)
        self.assertEqual(client.request("GET", "/api/homework")[0], 200)
        self.assertEqual(client.request("GET", "/api/trial-registrations")[0], 200)
        self.assertEqual(client.request("GET", "/api/enrollment-confirmations")[0], 200)
        self.assertEqual(client.request("GET", "/api/customer-tests")[0], 200)
        self.assertEqual(client.request("GET", "/api/pending-enrollments")[0], 200)

        classes = client.request("GET", "/api/classes")[1]["data"]
        students = client.request("GET", "/api/students?q=Demo%20Student")[1]["data"]
        class_id = classes[0]["id"]
        student_id = students[0]["id"]
        self.assertEqual(client.request("POST", "/api/timetable", {"class_id": class_id, "session_date": "2026-11-10", "start_time": "18:30", "end_time": "20:00", "room": "Room B2"})[0], 201)
        self.assertEqual(client.request("POST", "/api/evaluations", {"class_id": class_id, "student_id": student_id, "session_date": "2026-11-10", "score": 8.5, "status": "PUBLISHED", "note": "Good progress"})[0], 200)
        test_status, test_payload = client.request("POST", "/api/tests", {"class_id": class_id, "name": "Midterm", "test_date": "2026-11-11", "max_score": 10})
        self.assertEqual(test_status, 201)
        test_id = test_payload["data"]["id"]
        self.assertEqual(client.request("POST", "/api/test-results", {"test_id": test_id, "student_id": student_id, "score": 9})[0], 200)
        self.assertEqual(client.request("POST", "/api/homework", {"class_id": class_id, "title": "Reading", "due_date": "2026-11-12", "description": "Read unit 2"})[0], 201)
        self.assertEqual(client.request("POST", "/api/trial-registrations", {"full_name": "New Trial", "trial_date": "2026-11-13"})[0], 201)
        confirmations = client.request("GET", "/api/enrollment-confirmations")[1]["data"]
        self.assertEqual(client.request("POST", "/api/enrollment-confirmations", {"id": confirmations[0]["id"], "status": "APPROVED"})[0], 200)
        self.assertEqual(client.request("POST", "/api/customer-tests", {"customer_name": "Placement", "test_date": "2026-11-14"})[0], 201)
        self.assertEqual(client.request("POST", "/api/pending-enrollments", {"customer_name": "Waiting", "course_id": classes[0]["course_id"]})[0], 201)
        dashboard = client.request("GET", "/api/dashboard")[1]["data"]
        self.assertGreaterEqual(dashboard["counts"]["timetable_sessions"], 2)
        self.assertGreaterEqual(dashboard["counts"]["evaluations"], 1)

    def test_reference_gap_contracts_course_class_and_week_grid(self):
        client = ApiClient(self.server)
        status, _ = client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})
        self.assertEqual(status, 200)
        courses = client.request("GET", "/api/courses?q=English")[1]["data"]
        self.assertEqual(len(courses), 1)
        course_id = courses[0]["id"]
        self.assertEqual(client.request("GET", f"/api/courses/{course_id}")[0], 200)
        status, duplicate = client.request("POST", f"/api/courses/{course_id}/duplicate", {})
        self.assertEqual(status, 201)
        self.assertNotEqual(duplicate["data"]["code"], courses[0]["code"])
        status, created = client.request("POST", "/api/classes", {"course_id": course_id, "code": "ENG-FND-02", "room": "Room B2", "status": "OPEN"})
        self.assertEqual(status, 201)
        class_id = created["data"]["id"]
        self.assertEqual(client.request("GET", "/api/classes?q=FND&status=OPEN")[0], 200)
        csv_payload = "course_id,code,room,status\n{},ENG-FND-CSV,Room C1,PLANNED\n".format(course_id)
        status, imported = client.request("POST", "/api/classes/import", {"csv": csv_payload})
        self.assertEqual(status, 201)
        self.assertEqual(imported["data"]["count"], 1)
        status, session = client.request("POST", "/api/timetable", {"class_id": class_id, "session_date": "2026-11-04", "start_time": "18:30", "end_time": "20:00", "room": "Room B2"})
        self.assertEqual(status, 201)
        session_id = session["data"]["id"]
        status, updated = client.request("POST", f"/api/timetable/{session_id}", {"status": "COMPLETED"})
        self.assertEqual(status, 200)
        self.assertEqual(updated["data"]["status"], "COMPLETED")
        status, week = client.request("GET", "/api/timetable/week?start=2026-11-02")
        self.assertEqual(status, 200)
        self.assertTrue(any(row["id"] == session_id for row in week["data"]))
        export_status, export_headers, export_body = client.request_raw("GET", "/api/export/classes")
        self.assertEqual(export_status, 200)
        self.assertIn("text/csv", export_headers["Content-Type"])
        self.assertIn(b"ENG-FND-02", export_body)

    def test_course_detail_tabs_read_persisted_tests_and_classes_with_scope(self):
        """Course detail tabs expose persisted rows through the actor-scoped APIs."""
        client = ApiClient(self.server)
        self.assertEqual(
            client.request(
                "POST",
                "/api/auth/login",
                {"login": "admin", "password": "ChangeMe!CenterEdu2026"},
            )[0],
            200,
        )
        course = client.request("GET", "/api/courses?q=English")[1]["data"][0]
        course_id = course["id"]

        status, classes = client.request("GET", f"/api/courses/{course_id}/classes")
        self.assertEqual(status, 200)
        self.assertTrue(any(row["code"] == "ENG-FND-01" for row in classes["data"]))

        status, tests = client.request("GET", f"/api/courses/{course_id}/tests")
        self.assertEqual(status, 200)
        self.assertTrue(any(row["name"] == "Foundation checkpoint" for row in tests["data"]))
        self.assertTrue(all(row["class_code"] for row in tests["data"]))

        # A newly persisted test must appear in the same course detail tab.
        class_id = classes["data"][0]["id"]
        status, created = client.request(
            "POST",
            "/api/tests",
            {
                "class_id": class_id,
                "name": "Course detail regression",
                "test_date": "2026-11-30",
                "max_score": 10,
            },
        )
        self.assertEqual(status, 201)
        created_id = created["data"]["id"]
        refreshed = client.request("GET", f"/api/courses/{course_id}/tests")[1]["data"]
        self.assertIn(created_id, [row["id"] for row in refreshed])

    def test_course_detail_child_endpoints_preserve_student_course_scope(self):
        """Child tabs must not disclose rows from an unrelated course."""
        admin = ApiClient(self.server)
        self.assertEqual(
            admin.request(
                "POST",
                "/api/auth/login",
                {"login": "admin", "password": "ChangeMe!CenterEdu2026"},
            )[0],
            200,
        )
        status, created_course = admin.request(
            "POST",
            "/api/courses",
            {"code": "PRIVATE-DETAIL", "name": "Private detail course"},
        )
        self.assertEqual(status, 201)
        private_course_id = created_course["data"]["id"]
        status, created_class = admin.request(
            "POST",
            "/api/classes",
            {"course_id": private_course_id, "code": "PRIVATE-DETAIL-01", "status": "OPEN"},
        )
        self.assertEqual(status, 201)
        status, _created_test = admin.request(
            "POST",
            "/api/tests",
            {
                "class_id": created_class["data"]["id"],
                "name": "Private detail test",
                "test_date": "2026-12-01",
                "max_score": 10,
            },
        )
        self.assertEqual(status, 201)

        student = ApiClient(self.server)
        self.assertEqual(
            student.request(
                "POST",
                "/api/auth/login",
                {"login": "student", "password": "ChangeMe!CenterEdu2026"},
            )[0],
            200,
        )
        self.assertEqual(student.request("GET", f"/api/courses/{private_course_id}")[0], 404)
        self.assertEqual(student.request("GET", f"/api/courses/{private_course_id}/classes")[0], 404)
        self.assertEqual(student.request("GET", f"/api/courses/{private_course_id}/tests")[0], 404)

    def test_test_result_roster_reads_enrolled_students_and_persists_scores(self):
        admin = ApiClient(self.server)
        self.assertEqual(
            admin.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0],
            200,
        )
        classroom = admin.request("GET", "/api/classes")[1]["data"][0]
        students = admin.request("GET", "/api/students")[1]["data"]
        student = students[0]
        status, created = admin.request("POST", "/api/tests", {
            "class_id": classroom["id"], "name": "Roster result workflow", "test_date": "2026-12-12", "max_score": 20,
        })
        self.assertEqual(status, 201)
        test_id = created["data"]["id"]
        status, roster = admin.request("GET", f"/api/tests/{test_id}/results")
        self.assertEqual(status, 200)
        self.assertEqual(roster["data"]["test"]["id"], test_id)
        self.assertIn(student["id"], [row["student_id"] for row in roster["data"]["results"]])
        status, saved = admin.request("POST", "/api/test-results", {
            "test_id": test_id, "student_id": student["id"], "score": 17.5, "note": "Strong work",
        })
        self.assertEqual(status, 200)
        self.assertEqual(saved["data"]["score"], 17.5)
        refreshed = admin.request("GET", f"/api/tests/{test_id}/results")[1]["data"]["results"]
        row = next(item for item in refreshed if item["student_id"] == student["id"])
        self.assertEqual(row["score"], 17.5)
        self.assertEqual(row["note"], "Strong work")

        student_client = ApiClient(self.server)
        self.assertEqual(
            student_client.request("POST", "/api/auth/login", {"login": "student", "password": "ChangeMe!CenterEdu2026"})[0],
            200,
        )
        status, own = student_client.request("GET", f"/api/tests/{test_id}/results")
        self.assertEqual(status, 200)
        self.assertEqual(len(own["data"]["results"]), 1)
        self.assertEqual(own["data"]["results"][0]["student_id"], student["id"])

    def test_class_three_step_workflow_persists_class_sessions_and_students_atomically(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        course_id = client.request("GET", "/api/courses?q=English")[1]["data"][0]["id"]
        student_id = client.request("GET", "/api/students?q=Demo%20Student")[1]["data"][0]["id"]
        status, payload = client.request("POST", "/api/classes/workflow", {
            "course_id": course_id,
            "code": "WIZARD-CLASS-01",
            "room": "Room W",
            "status": "OPEN",
            "max_students": 2,
            "sessions": [
                {"session_date": "2026-12-10", "start_time": "18:30", "end_time": "20:00"},
                {"session_date": "2026-12-12", "start_time": "09:00", "end_time": "10:30", "room": "Room W2"},
            ],
            "student_ids": [student_id],
        })
        self.assertEqual(status, 201)
        data = payload["data"]
        self.assertEqual(data["class"]["code"], "WIZARD-CLASS-01")
        self.assertEqual(len(data["sessions"]), 2)
        self.assertEqual(len(data["enrollments"]), 1)
        class_id = data["class"]["id"]
        self.assertEqual(client.request("GET", f"/api/classes/{class_id}")[1]["data"]["student_count"], 1)
        self.assertEqual(len(client.request("GET", f"/api/timetable?class_code=WIZARD-CLASS-01")[1]["data"]), 2)
        self.assertEqual(client.request("GET", f"/api/timetable/{data['sessions'][0]['id']}/students")[1]["data"][0]["id"], student_id)

    def test_class_three_step_workflow_rolls_back_on_invalid_later_step(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        course_id = client.request("GET", "/api/courses?q=English")[1]["data"][0]["id"]
        before = len(client.request("GET", "/api/classes")[1]["data"])
        status, payload = client.request("POST", "/api/classes/workflow", {
            "course_id": course_id,
            "code": "WIZARD-ROLLBACK-01",
            "sessions": [{"session_date": "2026-12-11", "start_time": "20:00", "end_time": "19:00"}],
            "student_ids": [],
        })
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["code"], "VALIDATION_ERROR")
        after = client.request("GET", "/api/classes")[1]["data"]
        self.assertEqual(len(after), before)
        self.assertFalse(any(row["code"] == "WIZARD-ROLLBACK-01" for row in after))
        self.assertFalse(any(row["entity"] == "class" and row["action"] == "CREATE" and row["metadata_json"].find("WIZARD-ROLLBACK-01") >= 0 for row in client.request("GET", "/api/audit")[1]["data"]))

    def test_class_three_step_workflow_is_staff_scoped(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "teacher", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        status, payload = client.request("POST", "/api/classes/workflow", {"course_id": 1, "code": "WIZARD-DENIED"})
        self.assertEqual(status, 403)
        self.assertEqual(payload["error"]["code"], "FORBIDDEN")

    def test_class_create_accepts_explicit_unassigned_teacher(self):
        """The create form sends an empty teacher value for an unassigned class."""
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        course_id = client.request("GET", "/api/courses?q=English")[1]["data"][0]["id"]
        status, payload = client.request("POST", "/api/classes", {
            "course_id": course_id,
            "code": "UNASSIGNED-TEACHER-01",
            "teacher_id": "",
            "status": "OPEN",
        })
        self.assertEqual(status, 201)
        self.assertIsNone(payload["data"]["teacher_id"])

    def test_class_workflow_accepts_explicit_unassigned_teacher(self):
        """The multi-step create workflow must preserve a nullable teacher FK."""
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        course_id = client.request("GET", "/api/courses?q=English")[1]["data"][0]["id"]
        status, payload = client.request("POST", "/api/classes/workflow", {
            "course_id": course_id,
            "code": "UNASSIGNED-WORKFLOW-01",
            "teacher_id": "",
            "status": "OPEN",
            "sessions": [],
            "student_ids": [],
        })
        self.assertEqual(status, 201)
        self.assertIsNone(payload["data"]["class"]["teacher_id"])

    def test_class_csv_import_is_atomic_when_a_later_row_fails(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        course_id = client.request("GET", "/api/courses?q=English")[1]["data"][0]["id"]
        before = client.request("GET", "/api/classes")[1]["data"]
        csv_payload = (
            "course_id,code,room,status\n"
            f"{course_id},ATOMIC-ONE,Room A,PLANNED\n"
            "999999,ATOMIC-TWO,Room B,PLANNED\n"
        )
        status, payload = client.request("POST", "/api/classes/import", {"csv": csv_payload})
        self.assertEqual(status, 404)
        self.assertIn("row 3", payload["error"]["message"])
        after = client.request("GET", "/api/classes")[1]["data"]
        self.assertEqual(len(after), len(before))
        self.assertFalse(any(row["code"] == "ATOMIC-ONE" for row in after))
        audit = client.request("GET", "/api/audit")[1]["data"]
        self.assertFalse(any(row["entity"] == "class" and row["action"] == "CREATE" and row["entity_id"] == "1" for row in audit))

    def test_timetable_student_list_and_cancel_workflow(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        classroom = client.request("GET", "/api/classes")[1]["data"][0]
        status, created = client.request("POST", "/api/timetable", {"class_id": classroom["id"], "session_date": "2026-12-02", "start_time": "18:30", "end_time": "20:00", "room": "Room C"})
        self.assertEqual(status, 201)
        session_id = created["data"]["id"]
        status, students = client.request("GET", f"/api/timetable/{session_id}/students")
        self.assertEqual(status, 200)
        self.assertEqual(students["data"][0]["student_code"], "HV-0001")
        status, cancelled = client.request("POST", f"/api/timetable/{session_id}/cancel", {})
        self.assertEqual(status, 200)
        self.assertEqual(cancelled["data"]["status"], "CANCELLED")
        status, cancelled_again = client.request("POST", f"/api/timetable/{session_id}/cancel", {})
        self.assertEqual(status, 200)
        self.assertEqual(cancelled_again["data"]["status"], "CANCELLED")
        status, completed = client.request("POST", f"/api/timetable/{session_id}", {"status": "COMPLETED"})
        self.assertEqual(status, 200)
        self.assertEqual(completed["data"]["status"], "COMPLETED")
        status, _ = client.request("POST", f"/api/timetable/{session_id}/cancel", {})
        self.assertEqual(status, 409)

        student = ApiClient(self.server)
        self.assertEqual(student.request("POST", "/api/auth/login", {"login": "student", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        status, _ = student.request("GET", f"/api/timetable/{session_id}/students")
        self.assertEqual(status, 403)

    def test_timetable_update_cannot_bypass_completed_cancel_guard(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        classroom = client.request("GET", "/api/classes")[1]["data"][0]
        status, created = client.request("POST", "/api/timetable", {
            "class_id": classroom["id"], "session_date": "2026-12-03",
            "start_time": "18:30", "end_time": "20:00", "room": "Room Guard",
        })
        self.assertEqual(status, 201)
        session_id = created["data"]["id"]
        status, completed = client.request("POST", f"/api/timetable/{session_id}", {"status": "COMPLETED"})
        self.assertEqual(status, 200)
        self.assertEqual(completed["data"]["status"], "COMPLETED")

        status, payload = client.request("POST", f"/api/timetable/{session_id}", {"status": "CANCELLED"})
        self.assertEqual(status, 409)
        self.assertEqual(payload["error"]["code"], "COMPLETED_SESSION_CANNOT_CANCEL")
        status, current = client.request("GET", "/api/timetable?room=Room%20Guard")
        self.assertEqual(status, 200)
        self.assertEqual(next(row for row in current["data"] if row["id"] == session_id)["status"], "COMPLETED")

    def test_enrollment_and_customer_workflows_have_detail_edit_and_cancel(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)

        confirmations = client.request("GET", "/api/enrollment-confirmations")[1]["data"]
        confirmation_id = confirmations[0]["id"]
        status, detail = client.request("GET", f"/api/enrollment-confirmations/{confirmation_id}")
        self.assertEqual(status, 200)
        self.assertEqual(detail["data"]["id"], confirmation_id)
        status, updated = client.request("POST", "/api/enrollment-confirmations", {"id": confirmation_id, "status": "REJECTED"})
        self.assertEqual(status, 200)
        self.assertEqual(updated["data"]["status"], "REJECTED")

        customer_status, customer = client.request("POST", "/api/customer-tests", {"customer_name": "Edit Me", "test_date": "2026-11-20"})
        self.assertEqual(customer_status, 201)
        customer_id = customer["data"]["id"]
        status, edited = client.request("POST", f"/api/customer-tests/{customer_id}", {"score": 8.25, "status": "SCORED", "test_date": "2026-11-20", "customer_name": "Edited Learner"})
        self.assertEqual(status, 200)
        self.assertEqual(edited["data"]["score"], 8.25)
        self.assertEqual(edited["data"]["status"], "SCORED")

        pending_status, pending = client.request("POST", "/api/pending-enrollments", {"customer_name": "Edit Pending"})
        self.assertEqual(pending_status, 201)
        pending_id = pending["data"]["id"]
        status, edited_pending = client.request("POST", f"/api/pending-enrollments/{pending_id}", {"customer_name": "Edited Pending", "status": "ASSIGNED"})
        self.assertEqual(status, 200)
        self.assertEqual(edited_pending["data"]["status"], "ASSIGNED")
        status, cancelled = client.request("POST", f"/api/pending-enrollments/{pending_id}/cancel", {})
        self.assertEqual(status, 200)
        self.assertEqual(cancelled["data"]["status"], "CANCELLED")

    def test_pending_enrollment_csv_export_uses_existing_filters(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        status, created = client.request("POST", "/api/pending-enrollments", {
            "customer_name": "Filtered Pending Export",
            "course_id": client.request("GET", "/api/courses?q=English")[1]["data"][0]["id"],
            "preferred_day": "Tue",
        })
        self.assertEqual(status, 201)
        export_status, headers, body = client.request_raw(
            "GET", "/api/export/pending-enrollments?status=WAITING&course=ENG-FND&preferred_day=Tue"
        )
        self.assertEqual(export_status, 200)
        self.assertIn("text/csv", headers["Content-Type"])
        self.assertIn(b"Filtered Pending Export", body)
        self.assertIn(b"ENG-FND", body)

        invalid_status, invalid = client.request("GET", "/api/pending-enrollments?status=UNKNOWN")
        self.assertEqual(invalid_status, 400)
        self.assertEqual(invalid["error"]["code"], "VALIDATION_ERROR")
        invalid_export_status, invalid_export = client.request_raw(
            "GET", "/api/export/pending-enrollments?date_from=2026-11-01"
        )[:2]
        self.assertEqual(invalid_export_status, 400)
        self.assertIn("application/json", invalid_export["Content-Type"])

        student = ApiClient(self.server)
        self.assertEqual(student.request("POST", "/api/auth/login", {"login": "student", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        denied_status, denied = student.request_raw("GET", "/api/export/pending-enrollments")[:2]
        self.assertEqual(denied_status, 403)
        self.assertIn("application/json", denied["Content-Type"])

    def test_legacy_database_migration_adds_nullable_metadata_columns(self):
        legacy_path = Path(self.tmp.name) / "legacy.sqlite3"
        legacy = sqlite3.connect(legacy_path)
        legacy.executescript(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                level TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL REFERENCES courses(id),
                code TEXT NOT NULL UNIQUE,
                room TEXT NOT NULL DEFAULT '',
                schedule TEXT NOT NULL DEFAULT '',
                teacher_id INTEGER REFERENCES users(id),
                status TEXT NOT NULL DEFAULT 'PLANNED',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO courses(code,name,level,description) VALUES ('LEGACY-1','Legacy course','General','kept');
            """
        )
        legacy.commit()
        legacy.close()
        db = connect(legacy_path)
        course_columns = {row[1] for row in db.execute("PRAGMA table_info(courses)")}
        class_columns = {row[1] for row in db.execute("PRAGMA table_info(classes)")}
        self.assertTrue({"sessions_count", "hours", "fee_method", "fee", "daily_evaluation", "unit", "subject"}.issubset(course_columns))
        self.assertIn("sales_rep", {row[1] for row in db.execute("PRAGMA table_info(students)")})
        self.assertTrue({"start_date", "end_date", "payment_method", "max_students", "notes"}.issubset(class_columns))
        self.assertEqual(db.execute("SELECT name FROM courses WHERE code='LEGACY-1'").fetchone()[0], "Legacy course")
        db.close()

    def test_course_and_class_metadata_round_trip_and_date_filter(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        status, created_course = client.request("POST", "/api/courses", {
            "code": "META-101", "name": "Metadata course", "level": "Advanced",
            "sessions_count": 24, "hours": 36, "fee_method": "Theo khóa", "fee": 12500000,
            "daily_evaluation": "Có", "unit": "buổi", "subject": "English",
        })
        self.assertEqual(status, 201)
        course = created_course["data"]
        self.assertEqual(course["sessions_count"], 24)
        self.assertEqual(course["hours"], 36.0)
        self.assertEqual(course["fee_method"], "Theo khóa")
        self.assertEqual(course["test_count"], 0)
        duplicate_status, duplicate = client.request("POST", f"/api/courses/{course['id']}/duplicate", {})
        self.assertEqual(duplicate_status, 201)
        self.assertEqual(duplicate["data"]["subject"], "English")

        status, created_class = client.request("POST", "/api/classes", {
            "course_id": course["id"], "code": "META-101-A", "room": "Room M",
            "start_date": "2026-11-10", "end_date": "2027-01-10", "sessions_count": 24,
            "hours": 36, "payment_method": "Theo buổi", "max_students": 18,
            "max_students_per_session": 12, "primary_manager": "Manager A",
            "secondary_manager": "Manager B", "daily_evaluation": "Có",
            "notes": "Observed create-flow fields", "status": "OPEN",
        })
        self.assertEqual(status, 201)
        classroom = created_class["data"]
        self.assertEqual(classroom["start_date"], "2026-11-10")
        self.assertEqual(classroom["payment_method"], "Theo buổi")
        self.assertEqual(classroom["max_students"], 18)
        self.assertEqual(classroom["completed_sessions"], 0)
        filtered = client.request("GET", "/api/classes?start_from=2026-11-01&start_to=2026-11-30")[1]["data"]
        self.assertTrue(any(row["id"] == classroom["id"] for row in filtered))
        excluded = client.request("GET", "/api/classes?start_from=2027-02-01")[1]["data"]
        self.assertFalse(any(row["id"] == classroom["id"] for row in excluded))
        export_status, _, export_body = client.request_raw("GET", "/api/export/classes?start_from=2026-11-01&start_to=2026-11-30")
        self.assertEqual(export_status, 200)
        self.assertIn(b"META-101-A", export_body)

    def test_course_test_count_and_class_completed_sessions_are_derived_from_persisted_workflows(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        course = client.request("GET", "/api/courses?q=English")[1]["data"][0]
        classroom = client.request("GET", "/api/classes")[1]["data"][0]
        self.assertEqual(course["test_count"], 1)
        self.assertEqual(classroom["completed_sessions"], 0)
        status, created = client.request("POST", "/api/tests", {
            "class_id": classroom["id"], "name": "Derived count", "test_date": "2026-11-15", "max_score": 10,
        })
        self.assertEqual(status, 201)
        status, session = client.request("POST", "/api/timetable", {
            "class_id": classroom["id"], "session_date": "2026-11-16", "start_time": "18:30", "end_time": "20:00",
        })
        self.assertEqual(status, 201)
        status, updated = client.request("POST", f"/api/timetable/{session['data']['id']}", {"status": "COMPLETED"})
        self.assertEqual(status, 200)
        courses = client.request("GET", "/api/courses?q=English")[1]["data"]
        classes = client.request("GET", "/api/classes")[1]["data"]
        self.assertEqual(next(row for row in courses if row["id"] == course["id"])["test_count"], 2)
        self.assertEqual(next(row for row in classes if row["id"] == classroom["id"])["completed_sessions"], 1)

    def test_search_query_contract_covers_student_phone_and_course_subject(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)

        student_status, students = client.request("GET", "/api/students?q=0900000000")
        self.assertEqual(student_status, 200)
        self.assertEqual([row["student_code"] for row in students["data"]], ["HV-0001"])

        course_status, created = client.request("POST", "/api/courses", {
            "code": "SUBJECT-101",
            "name": "General Science",
            "level": "Beginner",
            "subject": "Biology",
        })
        self.assertEqual(course_status, 201)
        subject_status, courses = client.request("GET", "/api/courses?q=Biology")
        self.assertEqual(subject_status, 200)
        self.assertIn(created["data"]["id"], [row["id"] for row in courses["data"]])

    def test_student_detail_edit_and_scope_contract(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        student = client.request("GET", "/api/students?q=Demo%20Student")[1]["data"][0]
        status, detail = client.request("GET", f"/api/students/{student['id']}")
        self.assertEqual(status, 200)
        self.assertEqual(detail["data"]["student_code"], "HV-0001")
        status, updated = client.request("POST", f"/api/students/{student['id']}", {
            "student_code": "HV-0001", "full_name": "Demo Student Updated",
            "email": "demo.student@example.com", "phone": "0900000001", "status": "PAUSED",
        })
        self.assertEqual(status, 200)
        self.assertEqual(updated["data"]["status"], "PAUSED")
        self.assertEqual(updated["data"]["full_name"], "Demo Student Updated")
        self.assertEqual(client.request("POST", f"/api/students/{student['id']}", {"status": "UNKNOWN"})[0], 400)
        student_client = ApiClient(self.server)
        self.assertEqual(student_client.request("POST", "/api/auth/login", {"login": "student", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        self.assertEqual(student_client.request("GET", f"/api/students/{student['id']}")[0], 200)

    def test_class_teacher_assignment_round_trip_and_teacher_directory_scope(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        status, teachers = client.request("GET", "/api/teachers")
        self.assertEqual(status, 200)
        # The customer-facing seed contract sanitizes fixture names.  Select
        # an actual returned teacher instead of coupling the test to the old
        # ``Demo Teacher`` label.
        teacher = teachers["data"][0]
        course_id = client.request("GET", "/api/courses?q=English")[1]["data"][0]["id"]
        status, created = client.request("POST", "/api/classes", {"course_id": course_id, "code": "TEACHER-ASSIGN-01", "teacher_id": teacher["id"], "status": "OPEN"})
        self.assertEqual(status, 201)
        self.assertEqual(created["data"]["teacher_id"], teacher["id"])
        self.assertEqual(created["data"]["teacher"], teacher["full_name"])
        status, updated = client.request("POST", f"/api/classes/{created['data']['id']}", {"teacher_id": ""})
        self.assertEqual(status, 200)
        self.assertIsNone(updated["data"]["teacher_id"])
        student_client = ApiClient(self.server)
        self.assertEqual(student_client.request("POST", "/api/auth/login", {"login": "student", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        self.assertEqual(student_client.request("GET", "/api/teachers")[0], 403)

    def test_class_screen_does_not_require_teacher_directory_for_read_only_roles(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "student", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        status, classes = client.request("GET", "/api/classes")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(classes["data"]), 1)
        self.assertEqual(client.request("GET", "/api/teachers")[0], 403)

    def test_class_search_query_covers_manager_and_teacher(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        manager_status, manager_rows = client.request("GET", "/api/classes?q=Primary")
        self.assertEqual(manager_status, 200)
        self.assertEqual(manager_rows["data"], [])
        course_id = client.request("GET", "/api/courses?q=English")[1]["data"][0]["id"]
        create_status, created = client.request("POST", "/api/classes", {
            "course_id": course_id,
            "code": "SEARCH-MANAGER-01",
            "primary_manager": "Primary Manager",
            "secondary_manager": "Backup Manager",
            "status": "OPEN",
        })
        self.assertEqual(create_status, 201)
        manager_status, manager_rows = client.request("GET", "/api/classes?q=Primary%20Manager")
        self.assertEqual(manager_status, 200)
        self.assertIn(created["data"]["id"], [row["id"] for row in manager_rows["data"]])
        teacher_name = client.request("GET", "/api/teachers")[1]["data"][0]["full_name"]
        teacher_status, teacher_rows = client.request("GET", "/api/classes?q=" + quote(teacher_name))
        self.assertEqual(teacher_status, 200)
        self.assertTrue(any(row["teacher"] == teacher_name for row in teacher_rows["data"]))
        manager_filter_status, manager_filter_rows = client.request("GET", "/api/classes?manager=Primary%20Manager")
        self.assertEqual(manager_filter_status, 200)
        self.assertEqual([row["id"] for row in manager_filter_rows["data"]], [created["data"]["id"]])
        teacher_filter_status, teacher_filter_rows = client.request("GET", "/api/classes?teacher=" + quote(teacher_name))
        self.assertEqual(teacher_filter_status, 200)
        self.assertTrue(any(row["teacher"] == teacher_name for row in teacher_filter_rows["data"]))
        export_status, _headers, export_body = client.request_raw("GET", "/api/export/classes?manager=Primary%20Manager")
        self.assertEqual(export_status, 200)
        self.assertIn(b"SEARCH-MANAGER-01", export_body)
        self.assertNotIn(b"ENG-FND-01", export_body)

    def test_class_filters_reject_unknown_status_and_reversed_dates(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        status, payload = client.request("GET", "/api/classes?status=NOT_A_STATUS")
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["code"], "VALIDATION_ERROR")

    def test_class_course_filter_rejects_malformed_and_non_positive_ids(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        for path in ("/api/classes?course_id=abc", "/api/classes?course_id=0", "/api/export/classes?course_id=abc"):
            status, payload = client.request("GET", path) if path.startswith("/api/classes?") else client.request_raw("GET", path)[:2]
            if path.startswith("/api/export/"):
                self.assertEqual(status, 400)
            else:
                self.assertEqual(status, 400)
                self.assertEqual(payload["error"]["code"], "VALIDATION_ERROR")
        status, payload = client.request("GET", "/api/classes?start_from=2026-12-01&start_to=2026-11-01")
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["code"], "VALIDATION_ERROR")

    def test_numeric_validation_rejects_non_finite_and_fractional_integer_values(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        status, payload = client.request("POST", "/api/courses", {"code": "BAD-NAN", "name": "Invalid", "fee": "NaN"})
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["code"], "VALIDATION_ERROR")
        status, payload = client.request("POST", "/api/courses", {"code": "BAD-INF", "name": "Invalid", "fee": "Infinity"})
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["code"], "VALIDATION_ERROR")
        status, payload = client.request("POST", "/api/courses", {"code": "BAD-FRACTION", "name": "Invalid", "sessions_count": 1.5})
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["code"], "VALIDATION_ERROR")

    def test_attendance_filter_contract_by_class_status_and_date(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        classroom = client.request("GET", "/api/classes")[1]["data"][0]
        student = client.request("GET", "/api/students?q=Demo%20Student")[1]["data"][0]
        for day, status in (("2026-10-30", "PRESENT"), ("2026-11-02", "ABSENT"), ("2026-11-04", "LATE")):
            self.assertEqual(client.request("POST", "/api/attendance", {
                "class_id": classroom["id"], "student_id": student["id"],
                "session_date": day, "status": status,
            })[0], 200)
        filtered = client.request("GET", "/api/attendance?status=ABSENT&date_from=2026-11-01&date_to=2026-11-03")[1]["data"]
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["status"], "ABSENT")
        self.assertEqual(filtered[0]["session_date"], "2026-11-02")
        invalid = client.request("GET", "/api/attendance?status=UNKNOWN")[0]
        self.assertEqual(invalid, 400)
        reversed_dates = client.request("GET", "/api/attendance?date_from=2026-12-01&date_to=2026-11-01")[0]
        self.assertEqual(reversed_dates, 400)

    def test_query_date_and_class_id_validation_fails_closed(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        for path in ("/api/attendance?class_id=abc", "/api/attendance?class_id=0"):
            status, payload = client.request("GET", path)
            self.assertEqual(status, 400)
            self.assertEqual(payload["error"]["code"], "VALIDATION_ERROR")
        for path in ("/api/timetable?date=not-a-date", "/api/export/timetable?date=not-a-date"):
            if path.startswith("/api/timetable?"):
                status, payload = client.request("GET", path)
            else:
                status, _headers, raw_body = client.request_raw("GET", path)
                payload = json.loads(raw_body.decode())
            self.assertEqual(status, 400)
            self.assertEqual(payload["error"]["code"], "VALIDATION_ERROR")

    def test_timetable_filters_flow_to_filtered_csv_export(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        classroom = client.request("GET", "/api/classes")[1]["data"][0]
        status, created = client.request("POST", "/api/timetable", {
            "class_id": classroom["id"], "session_date": "2026-11-10",
            "start_time": "09:30", "end_time": "11:00", "room": "Room Z",
        })
        self.assertEqual(status, 201)
        session_id = created["data"]["id"]
        self.assertEqual(client.request("POST", f"/api/timetable/{session_id}", {"status": "COMPLETED"})[0], 200)
        export_status, headers, body = client.request_raw(
            "GET", "/api/export/timetable?room=Room%20Z&status=COMPLETED&time=09:30"
        )
        self.assertEqual(export_status, 200)
        self.assertIn("text/csv", headers["Content-Type"])
        self.assertIn(b"Room Z", body)
        self.assertIn(b"COMPLETED", body)
        self.assertNotIn(b"Room A1", body)
        self.assertEqual(client.request("GET", "/api/timetable?status=NOT_A_STATUS")[0], 400)

    def test_attendance_rejects_invalid_session_date(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        classroom = client.request("GET", "/api/classes")[1]["data"][0]
        student = client.request("GET", "/api/students?q=Demo%20Student")[1]["data"][0]
        status, payload = client.request("POST", "/api/attendance", {
            "class_id": classroom["id"], "student_id": student["id"],
            "session_date": "2026-99-99", "status": "PRESENT",
        })
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["code"], "VALIDATION_ERROR")

    def test_date_and_time_validation_rejects_truncated_suffixes(self):
        """Protocol date/time fields must reject values that used to be truncated."""
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        classroom = client.request("GET", "/api/classes")[1]["data"][0]
        student = client.request("GET", "/api/students?q=Demo%20Student")[1]["data"][0]

        for payload in (
            {
                "class_id": classroom["id"],
                "student_id": student["id"],
                "session_date": "2026-11-03-extra",
                "status": "PRESENT",
            },
            {
                "class_id": classroom["id"],
                "session_date": "2026-11-03",
                "start_time": "18:30-extra",
                "end_time": "20:00",
            },
        ):
            path = "/api/attendance" if "student_id" in payload else "/api/timetable"
            status, response = client.request("POST", path, payload)
            self.assertEqual(status, 400, (path, response))
            self.assertEqual(response["error"]["code"], "VALIDATION_ERROR")

    def test_training_list_filters_and_validation_contract(self):
        client = ApiClient(self.server)
        self.assertEqual(client.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        classroom = client.request("GET", "/api/classes")[1]["data"][0]
        student = client.request("GET", "/api/students?q=Demo%20Student")[1]["data"][0]
        self.assertEqual(client.request("POST", "/api/evaluations", {
            "class_id": classroom["id"], "student_id": student["id"],
            "session_date": "2026-11-09", "score": 8, "status": "PUBLISHED",
        })[0], 200)

        cases = [
            ("/api/evaluations?class=ENG-FND&status=PUBLISHED&date_from=2026-11-09&date_to=2026-11-09", "class_code", "ENG-FND-01"),
            ("/api/tests?class=ENG-FND&status=OPEN&date_from=2026-11-05&date_to=2026-11-05", "class_code", "ENG-FND-01"),
            ("/api/homework?class=ENG-FND&status=OPEN&date_from=2026-11-06&date_to=2026-11-06", "class_code", "ENG-FND-01"),
            ("/api/trial-registrations?status=NEW&date_from=2026-11-07&date_to=2026-11-07", "status", "NEW"),
            ("/api/enrollment-confirmations?status=APPROVED&class=ENG-FND", "status", "APPROVED"),
            ("/api/customer-tests?status=SCORED&date_from=2026-11-08&date_to=2026-11-08", "status", "SCORED"),
            ("/api/pending-enrollments?status=WAITING&course=ENG-FND&preferred_day=Tue", "status", "WAITING"),
        ]
        for path, key, expected in cases:
            status, payload = client.request("GET", path)
            self.assertEqual(status, 200, path)
            self.assertTrue(payload["data"], path)
            self.assertTrue(all(row[key] == expected for row in payload["data"]), path)

        invalid_queries = [
            "/api/evaluations?status=UNKNOWN",
            "/api/tests?status=UNKNOWN",
            "/api/homework?status=UNKNOWN",
            "/api/trial-registrations?status=UNKNOWN",
            "/api/enrollment-confirmations?status=UNKNOWN",
            "/api/customer-tests?status=UNKNOWN",
            "/api/pending-enrollments?status=UNKNOWN",
            "/api/evaluations?date_from=2026-12-01&date_to=2026-11-01",
            "/api/enrollment-confirmations?date_from=not-a-date",
            "/api/enrollment-confirmations?date_from=2026-12-01&date_to=2026-11-01",
            "/api/pending-enrollments?date_from=not-a-date",
            "/api/pending-enrollments?date_from=2026-12-01&date_to=2026-11-01",
        ]
        for path in invalid_queries:
            status, payload = client.request("GET", path)
            self.assertEqual(status, 400, path)
            self.assertEqual(payload["error"]["code"], "VALIDATION_ERROR", path)

    def test_potential_customer_crm_vertical_slice(self):
        """CRM prospect list/detail/follow-up survives the normal API contract."""
        admin = ApiClient(self.server)
        self.assertEqual(admin.request("POST", "/api/auth/login", {
            "login": "admin", "password": "ChangeMe!CenterEdu2026",
        })[0], 200)
        status, created = admin.request("POST", "/api/potential-customers", {
            "full_name": "Synthetic Prospect",
            "phone": "0900000001",
            "email": "prospect@example.com",
            "source": "Website",
            "sale_owner": "Sale A",
            "sale_assistant": "Sale B",
            "interest": "IELTS",
            "note": "Initial inquiry",
        })
        self.assertEqual(status, 201)
        prospect_id = created["data"]["id"]
        self.assertTrue(created["data"]["customer_code"].startswith("KH-TIEM-"))
        self.assertEqual(created["data"]["status"], "NEW")

        status, filtered = admin.request("GET", "/api/potential-customers?q=Synthetic&status=NEW&sale_owner=Sale%20A")
        self.assertEqual(status, 200)
        self.assertEqual([row["id"] for row in filtered["data"]], [prospect_id])

        status, followup = admin.request("POST", f"/api/potential-customers/{prospect_id}/followups", {
            "action_type": "CALL", "outcome": "Reached", "note": "Discussed placement test",
            "next_follow_up_at": "2026-11-15 09:30",
        })
        self.assertEqual(status, 201)
        self.assertEqual(followup["data"]["status"], "CONTACTED")
        self.assertEqual(len(followup["data"]["followups"]), 1)
        self.assertEqual(followup["data"]["followups"][0]["action_type"], "CALL")

        status, updated = admin.request("POST", f"/api/potential-customers/{prospect_id}", {
            "full_name": "Synthetic Prospect Updated", "customer_code": created["data"]["customer_code"],
            "status": "QUALIFIED", "sale_owner": "Sale A", "sale_assistant": "Sale B",
            "source": "Website", "interest": "IELTS", "note": "Qualified",
        })
        self.assertEqual(status, 200)
        self.assertEqual(updated["data"]["status"], "QUALIFIED")
        self.assertEqual(updated["data"]["full_name"], "Synthetic Prospect Updated")

        export_status, export_headers, export_body = admin.request_raw("GET", "/api/export/potential-customers?status=QUALIFIED")
        self.assertEqual(export_status, 200)
        self.assertIn("text/csv", export_headers["Content-Type"])
        self.assertIn(b"Synthetic Prospect Updated", export_body)

        # The staff-only CRM surface must not be readable by a student.
        student = ApiClient(self.server)
        self.assertEqual(student.request("POST", "/api/auth/login", {
            "login": "student", "password": "ChangeMe!CenterEdu2026",
        })[0], 200)
        denied_status, denied = student.request("GET", "/api/potential-customers")
        self.assertEqual(denied_status, 403)
        self.assertEqual(denied["error"]["code"], "FORBIDDEN")

    def test_potential_customer_delete_contract_is_soft_and_role_csrf_guarded(self):
        """Potential delete is an isolated soft-delete contract, never generated screens."""
        admin = ApiClient(self.server)
        self.assertEqual(admin.request("POST", "/api/auth/login", {
            "login": "admin", "password": "ChangeMe!CenterEdu2026",
        })[0], 200)
        status, created = admin.request("POST", "/api/potential-customers", {"full_name": "Delete Contract Prospect"})
        self.assertEqual(status, 201)
        prospect_id = created["data"]["id"]

        # Cancel is a client-side no-op: the confirmation helper closes without
        # invoking onConfirm, and the control is wired to the narrow endpoint.
        source = Path(__file__).with_name("static").joinpath("app.js").read_text(encoding="utf-8")
        self.assertIn("delete-cancel", source)
        self.assertIn("potential-delete", source)
        self.assertIn("/api/potential-customers/${encodeURIComponent(remove.dataset.id)}", source)

        missing_csrf = admin.csrf
        admin.csrf = ""
        no_csrf_status, _no_csrf_headers, no_csrf_body = admin.request_raw("DELETE", f"/api/potential-customers/{prospect_id}")
        admin.csrf = missing_csrf
        self.assertEqual(no_csrf_status, 403)
        self.assertEqual(json.loads(no_csrf_body.decode())["error"]["code"], "CSRF_REQUIRED")

        student = ApiClient(self.server)
        self.assertEqual(student.request("POST", "/api/auth/login", {
            "login": "student", "password": "ChangeMe!CenterEdu2026",
        })[0], 200)
        denied_status, denied = student.request("DELETE", f"/api/potential-customers/{prospect_id}")
        self.assertEqual(denied_status, 403)
        self.assertEqual(denied["error"]["code"], "FORBIDDEN")

        invalid_status, invalid = admin.request("DELETE", "/api/potential-customers/not-a-number")
        self.assertEqual(invalid_status, 400)
        self.assertEqual(invalid["error"]["code"], "VALIDATION_ERROR")
        missing_status, missing = admin.request("DELETE", "/api/potential-customers/999999")
        self.assertEqual(missing_status, 404)
        self.assertEqual(missing["error"]["code"], "POTENTIAL_CUSTOMER_NOT_FOUND")

        delete_status, deleted = admin.request("DELETE", f"/api/potential-customers/{prospect_id}")
        self.assertEqual(delete_status, 200)
        self.assertEqual(deleted["data"], {"id": prospect_id, "deleted": True})
        listed_status, listed = admin.request("GET", "/api/potential-customers?q=Delete%20Contract%20Prospect")
        self.assertEqual(listed_status, 200)
        self.assertFalse(any(row["id"] == prospect_id for row in listed["data"]))
        read_status, readback = admin.request("GET", f"/api/potential-customers/{prospect_id}")
        self.assertEqual(read_status, 404)
        self.assertEqual(readback["error"]["code"], "POTENTIAL_CUSTOMER_NOT_FOUND")
        stored = self.server.service.db.execute("SELECT deleted_at FROM potential_customers WHERE id=?", (prospect_id,)).fetchone()
        self.assertIsNotNone(stored["deleted_at"])

    def test_potential_customer_follow_up_datetime_is_strict(self):
        """Persisted care scheduling accepts only the documented datetime wire format."""
        admin = ApiClient(self.server)
        self.assertEqual(admin.request("POST", "/api/auth/login", {
            "login": "admin", "password": "ChangeMe!CenterEdu2026",
        })[0], 200)
        invalid_create_status, invalid_create = admin.request("POST", "/api/potential-customers", {
            "full_name": "Invalid Create Datetime Prospect",
            "next_follow_up_at": "2026-11-15 09:30:00",
        })
        self.assertEqual(invalid_create_status, 400)
        self.assertEqual(invalid_create["error"]["code"], "VALIDATION_ERROR")
        status, created = admin.request("POST", "/api/potential-customers", {
            "full_name": "Datetime Validation Prospect",
        })
        self.assertEqual(status, 201)
        prospect_id = created["data"]["id"]
        invalid_update_status, invalid_update = admin.request("POST", f"/api/potential-customers/{prospect_id}", {
            "full_name": "Datetime Validation Prospect", "customer_code": created["data"]["customer_code"],
            "status": "NEW", "next_follow_up_at": "2026-11-15T09:30",
        })
        self.assertEqual(invalid_update_status, 400)
        self.assertEqual(invalid_update["error"]["code"], "VALIDATION_ERROR")
        for value in ("2026-11-15", "2026-11-15 9:30", "2026-11-15 09:30:00", "2026-02-30 09:30", "2026-11-15T09:30"):
            invalid_status, invalid = admin.request("POST", f"/api/potential-customers/{prospect_id}/followups", {
                "action_type": "CALL", "note": "invalid datetime", "next_follow_up_at": value,
            })
            self.assertEqual(invalid_status, 400, value)
            self.assertEqual(invalid["error"]["code"], "VALIDATION_ERROR")
        valid_status, valid = admin.request("POST", f"/api/potential-customers/{prospect_id}/followups", {
            "action_type": "CALL", "note": "valid datetime", "next_follow_up_at": "2026-11-15 09:30",
        })
        self.assertEqual(valid_status, 201)
        self.assertEqual(valid["data"]["followups"][0]["next_follow_up_at"], "2026-11-15 09:30")

    def test_potential_customer_reference_fields_and_summary_contract(self):
        """CRM list fields and status aggregates are persisted, validated and returned."""
        admin = ApiClient(self.server)
        self.assertEqual(admin.request("POST", "/api/auth/login", {
            "login": "admin", "password": "ChangeMe!CenterEdu2026",
        })[0], 200)
        status, created = admin.request("POST", "/api/potential-customers", {
            "full_name": "Nguyễn Khách Hàng", "date_of_birth": "1995-03-21",
            "branch": "Cơ sở Quận 1", "tag": "⭐", "care_course": "IELTS Foundation",
            "interested_course": "IELTS Target 6.5", "test_appointment": "2026-12-01",
            "test_score": 8.5, "trial_status": "Đã đăng ký", "care_progress": "3/5",
            "sale_owner": "Sale A", "sale_assistant": "Sale B",
        })
        self.assertEqual(status, 201)
        row = created["data"]
        for field, expected in {
            "date_of_birth": "1995-03-21", "branch": "Cơ sở Quận 1", "tag": "⭐",
            "care_course": "IELTS Foundation", "interested_course": "IELTS Target 6.5",
            "test_appointment": "2026-12-01", "test_score": 8.5,
            "trial_status": "Đã đăng ký", "care_progress": "3/5",
        }.items():
            self.assertEqual(row[field], expected, field)
        status, listed = admin.request("GET", "/api/potential-customers?sale_owner=Sale%20A")
        self.assertEqual(status, 200)
        self.assertIn("summary", listed)
        self.assertGreaterEqual(listed["summary"]["total"], 1)
        self.assertIn("successful", listed["summary"])
        export_status, export_headers, export_body = admin.request_raw("GET", "/api/export/potential-customers")
        self.assertEqual(export_status, 200)
        self.assertIn("text/csv", export_headers["Content-Type"])
        invalid, payload = admin.request("POST", "/api/potential-customers", {
            "full_name": "Invalid Score", "test_score": 11,
        })
        self.assertEqual(invalid, 400)
        self.assertEqual(payload["error"]["code"], "VALIDATION_ERROR")

    def test_sale_potential_operational_lens_contract(self):
        """Sale route exposes the observed 21-row operational lens separately."""
        admin = ApiClient(self.server)
        self.assertEqual(admin.request("POST", "/api/auth/login", {
            "login": "admin", "password": "ChangeMe!CenterEdu2026",
        })[0], 200)
        statuses = (["NEW"] * 10) + (["CONTACTED"] * 3) + (["CONVERTED"] * 7) + (["LOST"] * 1)
        for index, status in enumerate(statuses, start=1):
            created_status, created = admin.request("POST", "/api/potential-customers", {
                "full_name": f"Sale Lens Prospect {index}",
                "status": status,
                "customer_code": f"SALE-LENS-{index:03d}",
                "sale_owner": "Sale A",
                "sale_assistant": "Sale B",
            })
            self.assertEqual(created_status, 201)
        status, payload = admin.request("GET", "/api/potential-customers?scope=sale")
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["data"]), 21)
        self.assertEqual(payload["summary"]["total"], 21)
        self.assertEqual(payload["summary"]["new"], 10)
        self.assertEqual(payload["summary"]["contacted"], 3)
        self.assertEqual(payload["summary"]["successful"], 8)
        self.assertEqual(payload["summary"]["cancelled"], 1)
        export_status, export_headers, export_body = admin.request_raw("GET", "/api/export/potential-customers?scope=sale")
        self.assertEqual(export_status, 200)
        self.assertIn("text/csv", export_headers["Content-Type"])
        self.assertIn(b"SALE-LENS-021", export_body)

    def test_care_appointments_contract_filters_exports_and_rbac(self):
        """Care appointments derive only from persisted CRM follow-up dates."""
        admin = ApiClient(self.server)
        self.assertEqual(admin.request("POST", "/api/auth/login", {
            "login": "admin", "password": "ChangeMe!CenterEdu2026",
        })[0], 200)
        status, created = admin.request("POST", "/api/potential-customers", {
            "full_name": "Appointment Prospect", "sale_owner": "Sale C", "source": "Referral",
        })
        self.assertEqual(status, 201)
        prospect_id = created["data"]["id"]
        status, followup = admin.request("POST", f"/api/potential-customers/{prospect_id}/followups", {
            "action_type": "APPOINTMENT", "outcome": "Booked", "note": "Placement call",
            "next_follow_up_at": "2026-12-05 09:30",
        })
        self.assertEqual(status, 201)
        self.assertEqual(followup["data"]["followups"][0]["next_follow_up_at"], "2026-12-05 09:30")

        status, rows = admin.request("GET", "/api/care-appointments?q=Appointment&action_type=APPOINTMENT&sale_owner=Sale%20C&date_from=2026-12-01&date_to=2026-12-31")
        self.assertEqual(status, 200)
        self.assertEqual(len(rows["data"]), 1)
        self.assertEqual(rows["data"][0]["potential_customer_id"], prospect_id)
        self.assertEqual(rows["data"][0]["customer_status"], "CONTACTED")

        export_status, export_headers, export_body = admin.request_raw("GET", "/api/export/care-appointments?action_type=APPOINTMENT")
        self.assertEqual(export_status, 200)
        self.assertIn("text/csv", export_headers["Content-Type"])
        self.assertIn(b"Appointment Prospect", export_body)

        invalid_status, invalid = admin.request("GET", "/api/care-appointments?date_from=2026-12-31&date_to=2026-12-01")
        self.assertEqual(invalid_status, 400)
        self.assertEqual(invalid["error"]["code"], "VALIDATION_ERROR")

        student = ApiClient(self.server)
        self.assertEqual(student.request("POST", "/api/auth/login", {
            "login": "student", "password": "ChangeMe!CenterEdu2026",
        })[0], 200)
        denied_status, denied = student.request("GET", "/api/care-appointments")
        self.assertEqual(denied_status, 403)
        self.assertEqual(denied["error"]["code"], "FORBIDDEN")

    def test_sale_potential_appointment_local_contract(self):
        """Sale appointment route uses the seven-column local contract."""
        admin = ApiClient(self.server)
        self.assertEqual(admin.request("POST", "/api/auth/login", {
            "login": "admin", "password": "ChangeMe!CenterEdu2026",
        })[0], 200)
        created_status, created = admin.request("POST", "/api/potential-customers", {
            "full_name": "Sale Appointment Learner", "sale_owner": "Sale B", "status": "NEW",
        })
        self.assertEqual(created_status, 201)
        customer_id = created["data"]["id"]
        followup_status, _ = admin.request("POST", f"/api/potential-customers/{customer_id}/followups", {
            "action_type": "MESSAGE", "outcome": "Đã xử lý", "note": "Đã nhắn lịch học thử",
            "next_follow_up_at": "2026-12-10 14:00",
        })
        self.assertEqual(followup_status, 201)
        status, payload = admin.request("GET", "/api/care-appointments?scope=sale&status=PROCESSED&action_type=MESSAGE&date_from=2026-12-01&date_to=2026-12-31")
        self.assertEqual(status, 200)
        self.assertTrue(any(row["potential_customer_id"] == customer_id for row in payload["data"]))
        row = next(row for row in payload["data"] if row["potential_customer_id"] == customer_id)
        self.assertEqual(row["appointment_status_label"], "Đã xử lý")
        self.assertEqual(row["action_label"], "Nhắn tin")
        self.assertEqual(row["student_name"], "Sale Appointment Learner")
        self.assertEqual(row["appointment_date"], "2026-12-10 14:00")
        self.assertTrue({"student_name", "sale_name", "appointment_date", "action_label", "appointment_status_label"} <= set(row))
        invalid_status, invalid = admin.request("GET", "/api/care-appointments?scope=sale&status=NOT_A_STATUS")
        self.assertEqual(invalid_status, 400)
        self.assertEqual(invalid["error"]["code"], "VALIDATION_ERROR")

    def test_customer_test_route_filters_export_and_local_display_contract(self):
        """Customer-test routes share persistent data with route-specific columns."""
        admin = ApiClient(self.server)
        self.assertEqual(admin.request("POST", "/api/auth/login", {
            "login": "admin", "password": "ChangeMe!CenterEdu2026",
        })[0], 200)
        created_status, created = admin.request("POST", "/api/customer-tests", {
            "customer_name": "Placement Route Learner", "parent_name": "Nguyễn Thị Mai",
            "test_date": "2026-12-20", "sales_owner": "Sale B", "note": "local route contract",
        })
        self.assertEqual(created_status, 201)
        row_id = created["data"]["id"]
        status, payload = admin.request("GET", "/api/customer-tests?q=Placement%20Route&sales_owner=Sale%20B&date_from=2026-12-01&date_to=2026-12-31")
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["data"]), 1)
        row = payload["data"][0]
        self.assertEqual(row["id"], row_id)
        self.assertEqual(row["appointment_time"], row["created_at"])
        self.assertEqual(row["activity_label"], "Đã đặt lịch")
        export_status, export_headers, export_body = admin.request_raw("GET", "/api/export/customer-tests?sales_owner=Sale%20B")
        self.assertEqual(export_status, 200)
        self.assertIn("text/csv", export_headers["Content-Type"])
        self.assertIn(b"Placement Route Learner", export_body)

    def test_finance_survey_and_callcenter_contracts(self):
        """Exercise the evidence-derived Finance/Survey/Callcenter surfaces."""
        admin = ApiClient(self.server)
        login_status, login_payload = admin.request("POST", "/api/auth/login", {
            "login": "admin", "password": "ChangeMe!CenterEdu2026",
        })
        self.assertEqual(login_status, 200)
        admin_display_name = login_payload["user"]["full_name"]

        bill_payload = {
            "invoice_code": "INV-CONTRACT-001", "contract_code": "CTR-001",
            "class_code": "ENG-FND-01", "subject": "Tuition", "customer_name": "Contract Learner",
            "payment_amount": 1250000, "sales_owner": "Sale A", "center": "HCM",
            "branch": "Q1", "employee": "Staff A", "confirmation_status": "PENDING",
            "payment_method": "TRANSFER", "invoice_date": "2026-11-20", "note": "local contract",
        }
        status, created_bill = admin.request("POST", "/api/finance/bills", bill_payload)
        self.assertEqual(status, 201)
        bill_id = created_bill["data"]["id"]
        self.assertEqual(created_bill["data"]["invoice_code"], "INV-CONTRACT-001")
        filtered_status, filtered = admin.request("GET", "/api/finance/bills?creator=Center%20Administrator&confirmation_status=PENDING&date_from=2026-11-01&date_to=2026-11-30")
        self.assertEqual(filtered_status, 200)
        self.assertTrue(any(row["id"] == bill_id and row["created_by_name"] == admin_display_name for row in filtered["data"]))
        update_status, updated_bill = admin.request("POST", f"/api/finance/bills/{bill_id}", {"confirmation_status": "CONFIRMED"})
        self.assertEqual(update_status, 200)
        self.assertEqual(updated_bill["data"]["confirmation_status"], "CONFIRMED")
        duplicate_status, duplicate = admin.request("POST", "/api/finance/bills", bill_payload)
        self.assertEqual(duplicate_status, 409)
        self.assertEqual(duplicate["error"]["code"], "DUPLICATE_FINANCE_BILL")
        export_status, export_headers, export_body = admin.request_raw("GET", "/api/export/finance-bills?confirmation_status=CONFIRMED")
        self.assertEqual(export_status, 200)
        self.assertIn("text/csv", export_headers["Content-Type"])
        self.assertIn(b"INV-CONTRACT-001", export_body)

        # The reference exposes a separate confirmation action. Keep the
        # local action idempotent and fail closed for rejected bills.
        second_status, second_bill = admin.request("POST", "/api/finance/bills", {
            **bill_payload, "invoice_code": "INV-CONTRACT-002", "invoice_date": "2026-11-21",
            "branch": "Q2", "confirmation_status": "PENDING", "payment_amount": 250000,
        })
        self.assertEqual(second_status, 201)
        second_id = second_bill["data"]["id"]
        confirm_status, confirmed = admin.request("POST", f"/api/finance/bills/{second_id}/confirm", {})
        self.assertEqual(confirm_status, 200)
        self.assertEqual(confirmed["data"]["confirmation_status"], "CONFIRMED")
        repeat_status, repeated = admin.request("POST", f"/api/finance/bills/{second_id}/confirm", {})
        self.assertEqual(repeat_status, 200)
        self.assertEqual(repeated["data"]["confirmation_status"], "CONFIRMED")
        summary_status, summary = admin.request("GET", "/api/finance/revenue-summary?date_from=2026-11-20&date_to=2026-11-21&center=HCM")
        self.assertEqual(summary_status, 200)
        self.assertEqual(summary["data"]["totals"]["bill_count"], 2)
        self.assertEqual(summary["data"]["totals"]["gross_amount"], 1500000)
        self.assertEqual(summary["data"]["by_center_branch"][0]["branch"], "Q1")
        self.assertEqual(summary["data"]["by_center_branch"][1]["branch"], "Q2")

        revenue_status, revenue = admin.request("POST", "/api/finance/revenues", {
            "code": "REV-CONTRACT-001", "name": "Course fee", "status": "ACTIVE",
            "price": 1500000, "discount_type": "PERCENT", "discount_value": 10,
            "amount_due": 1350000, "center": "HCM", "note": "period local aggregation",
        })
        self.assertEqual(revenue_status, 201)
        revenue_id = revenue["data"]["id"]
        self.assertEqual(admin.request("GET", "/api/finance/revenues?status=ACTIVE&center=HCM")[0], 200)
        invalid_revenue_status, invalid_revenue = admin.request("POST", "/api/finance/revenues", {
            "code": "REV-CONTRACT-BAD", "name": "Bad", "discount_type": "PERCENT", "discount_value": 101,
        })
        self.assertEqual(invalid_revenue_status, 400)
        self.assertEqual(invalid_revenue["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(admin.request("POST", f"/api/finance/revenues/{revenue_id}", {"status": "INACTIVE"})[0], 200)
        self.assertEqual(admin.request_raw("GET", "/api/export/finance-revenues")[0], 200)

        survey_status, survey = admin.request("POST", "/api/surveys", {
            "name": "Contract survey", "due_date": "2026-12-01", "status": "DRAFT", "description": "six kinds",
        })
        self.assertEqual(survey_status, 201)
        survey_id = survey["data"]["id"]
        page_status, page = admin.request("POST", f"/api/surveys/{survey_id}/pages", {"title": "Page 1", "position": 0})
        self.assertEqual(page_status, 201)
        page_id = page["data"]["pages"][0]["id"]
        question_ids = []
        for position, kind in enumerate(("INPUT", "CHECKBOX", "DROPDOWN", "COMMENT", "RATING", "IMAGE")):
            q_status, q = admin.request("POST", f"/api/survey-pages/{page_id}/questions", {
                "kind": kind, "label": f"Question {kind}", "position": position,
                "options": ["A", "B"] if kind in {"CHECKBOX", "DROPDOWN"} else [],
                "required": kind == "INPUT",
            })
            self.assertEqual(q_status, 201)
            question_ids = [item["id"] for item in q["data"]["pages"][0]["questions"]]
        self.assertEqual(len(question_ids), 6)
        missing_required_status, missing_required = admin.request("POST", f"/api/surveys/{survey_id}/responses", {
            "respondent_name": "Missing required", "answers": {str(qid): "answer" for qid in question_ids[1:]},
        })
        self.assertEqual(missing_required_status, 400)
        self.assertEqual(missing_required["error"]["code"], "VALIDATION_ERROR")
        invalid_rating_answers = {
            str(qid): ("A" if index == 2 else ("6" if index == 4 else "answer"))
            for index, qid in enumerate(question_ids)
        }
        invalid_rating_status, invalid_rating = admin.request("POST", f"/api/surveys/{survey_id}/responses", {
            "respondent_name": "Invalid rating", "answers": invalid_rating_answers,
        })
        self.assertEqual(invalid_rating_status, 400)
        self.assertEqual(invalid_rating["error"]["code"], "VALIDATION_ERROR")
        valid_answers = {
            str(qid): ("A" if index == 2 else ("3" if index == 4 else "answer"))
            for index, qid in enumerate(question_ids)
        }
        response_status, response = admin.request("POST", f"/api/surveys/{survey_id}/responses", {
            "respondent_name": "Survey User", "answers": valid_answers,
        })
        self.assertEqual(response_status, 201)
        self.assertEqual(response["data"]["response_count"], 1)
        listed_status, listed = admin.request("GET", "/api/surveys")
        self.assertEqual(listed_status, 200)
        listed_survey = next(row for row in listed["data"] if row["id"] == survey_id)
        self.assertEqual(listed_survey["created_by_name"], admin_display_name)
        self.assertEqual(listed_survey["response_count"], 1)
        self.assertEqual(len(admin.request("GET", f"/api/surveys/{survey_id}/responses")[1]["data"]), 1)
        self.assertEqual(admin.request("POST", f"/api/surveys/{survey_id}", {"status": "CLOSED"})[0], 200)
        closed_status, closed = admin.request("POST", f"/api/surveys/{survey_id}/responses", {"answers": {}})
        self.assertEqual(closed_status, 409)
        self.assertEqual(closed["error"]["code"], "SURVEY_CLOSED")
        unknown_status, unknown = admin.request("POST", f"/api/surveys/{survey_id}/responses", {"answers": {"999999": "x"}})
        self.assertEqual(unknown_status, 409)  # closed guard runs before answer validation
        self.assertEqual(admin.request_raw("GET", "/api/export/surveys")[0], 200)

        call_status, call = admin.request("POST", "/api/call-history", {
            "phone": "0901234567", "full_name": "Call Contract", "party_role": "STUDENT",
            "call_type": "OUTBOUND", "staff_name": "Staff A", "status": "CONNECTED",
            "duration_seconds": 90, "recording_ref": "recording-local-1", "called_at": "2026-11-20 09:30",
            "note": "Follow-up",
        })
        self.assertEqual(call_status, 201)
        call_id = call["data"]["id"]
        rows_status, rows = admin.request("GET", "/api/call-history?q=Call%20Contract&date_from=2026-11-20&date_to=2026-11-20")
        self.assertEqual(rows_status, 200)
        self.assertTrue(any(row["id"] == call_id for row in rows["data"]))
        self.assertEqual(admin.request("POST", f"/api/call-history/{call_id}", {"status": "FOLLOW_UP"})[0], 200)
        invalid_call_status, invalid_call = admin.request("POST", "/api/call-history", {"full_name": "Bad", "called_at": "2026-11-20T09:30"})
        self.assertEqual(invalid_call_status, 400)
        self.assertEqual(invalid_call["error"]["code"], "VALIDATION_ERROR")
        export_status, _headers, export_body = admin.request_raw("GET", "/api/export/call-history")
        self.assertEqual(export_status, 200)
        self.assertIn(b"Call Contract", export_body)

        student = ApiClient(self.server)
        self.assertEqual(student.request("POST", "/api/auth/login", {"login": "student", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        for path in ("/api/finance/bills", "/api/finance/revenues", "/api/surveys", "/api/call-history"):
            self.assertEqual(student.request("GET", path)[0], 403)

    def test_finance_contract_domain_seed_crud_catalog_export_and_rbac(self):
        """Contracts use persistent local domain data, not a placeholder row."""
        os.environ["CENTER_EDU_RICH_DEMO"] = "1"
        try:
            self.server.service._ensure_rich_domain_backfill()
            admin = ApiClient(self.server)
            self.assertEqual(admin.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
            status, contracts = admin.request("GET", "/api/finance/contracts")
            self.assertEqual(status, 200)
            self.assertGreaterEqual(len(contracts["data"]), 40)
            self.assertTrue(all(row["contract_code"] and row["debt_amount"] is not None for row in contracts["data"]))
            self.assertEqual(admin.request("GET", "/api/finance/contract-catalog")[0], 200)
            students = admin.request("GET", "/api/students")[1]["data"]
            payload = {
                "contract_code": "CTR-RICH-001", "customer_type": "STUDENT", "account_id": students[0]["id"],
                "student_id": students[0]["id"], "item_id": 1, "created_date": "2026-11-02",
                "expiry_date": "2027-11-02", "payment_due_date": "2026-12-02", "payment_due_amount": 3000000,
                "payment_note": "Hẹn đóng", "discount_code": "WELCOME", "direct_discount": 100000,
                "total_amount": 3000000, "paid_amount": 1000000, "sales_owner": "Sale Demo",
                "payment_status": "PARTIAL", "contract_status": "ACTIVE", "note": "local contract",
            }
            created_status, created = admin.request("POST", "/api/finance/contracts", payload)
            self.assertEqual(created_status, 201)
            self.assertEqual(created["data"]["item_id"], 1)
            self.assertEqual(created["data"]["debt_amount"], 2000000)
            self.assertEqual(admin.request("GET", "/api/finance/contracts?q=CTR-RICH-001")[0], 200)
            updated_status, updated = admin.request("POST", f"/api/finance/contracts/{created['data']['id']}", {"paid_amount": 3000000, "payment_status": "PAID"})
            self.assertEqual(updated_status, 200)
            self.assertEqual(updated["data"]["debt_amount"], 0)
            export_status, headers, body = admin.request_raw("GET", "/api/export/finance-contracts")
            self.assertEqual(export_status, 200)
            self.assertIn("text/csv", headers["Content-Type"])
            self.assertIn(b"CTR-RICH-001", body)
            student = ApiClient(self.server)
            self.assertEqual(student.request("POST", "/api/auth/login", {"login": "student", "password": "ChangeMe!CenterEdu2026"})[0], 200)
            self.assertEqual(student.request("GET", "/api/finance/contracts")[0], 403)
            self.assertEqual(student.request("GET", "/api/finance/contract-catalog")[0], 403)
        finally:
            os.environ.pop("CENTER_EDU_RICH_DEMO", None)

    def test_finance_contract_filter_matrix_and_summary_are_scoped(self):
        """The contract list and summary use the same durable filtered relation."""
        os.environ["CENTER_EDU_RICH_DEMO"] = "1"
        try:
            self.server.service._ensure_rich_domain_backfill()
            admin = ApiClient(self.server)
            self.assertEqual(admin.request("POST", "/api/auth/login", {
                "login": "admin", "password": "ChangeMe!CenterEdu2026",
            })[0], 200)
            status, all_rows = admin.request("GET", "/api/finance/contracts")
            self.assertEqual(status, 200)
            self.assertGreaterEqual(len(all_rows["data"]), 40)
            sample = all_rows["data"][0]
            self.assertTrue(sample["course_id"])
            self.assertTrue(sample["created_by_name"])
            self.assertTrue(sample["expiry_date"])

            checks = {
                "q": sample["contract_code"],
                "payment_status": sample["payment_status"],
                "contract_status": sample["contract_status"],
                "course_id": str(sample["course_id"]),
                "creator": sample["created_by_name"],
                "expiry_from": "2027-01-01",
                "expiry_to": "2028-01-01",
                "branch": "Center EDU - Demo",
            }
            for key, value in checks.items():
                filtered_status, filtered = admin.request(
                    "GET", "/api/finance/contracts?" + key + "=" + quote(str(value)),
                )
                self.assertEqual(filtered_status, 200, key)
                self.assertTrue(filtered["data"], key)
                if key == "q":
                    self.assertEqual(filtered["data"][0]["contract_code"], sample["contract_code"])

            summary_status, summary = admin.request(
                "GET", "/api/finance/contracts/summary?q=" + quote(sample["contract_code"]),
            )
            self.assertEqual(summary_status, 200)
            self.assertEqual(summary["data"]["contract_count"], 1)
            self.assertGreaterEqual(summary["data"]["subtotal"], 0)
            self.assertEqual(summary["data"]["unsupported_fields"], ["refund", "bad_debt", "co_wallet"])

            unknown_branch_status, unknown_branch = admin.request(
                "GET", "/api/finance/contracts?branch=Unknown%20Branch",
            )
            self.assertEqual(unknown_branch_status, 200)
            self.assertEqual(unknown_branch["data"], [])
            invalid_status, invalid = admin.request(
                "GET", "/api/finance/contracts?payment_status=UNKNOWN",
            )
            self.assertEqual(invalid_status, 400)
            self.assertEqual(invalid["error"]["code"], "VALIDATION_ERROR")
        finally:
            os.environ.pop("CENTER_EDU_RICH_DEMO", None)

    def test_report_engine_v2_catalog_run_export_and_no_fake_rows(self):
        """All observed report routes load; populated routes expose mapped data."""
        os.environ["CENTER_EDU_RICH_DEMO"] = "1"
        try:
            self.server.service._ensure_rich_domain_backfill()
            admin = ApiClient(self.server)
            self.assertEqual(admin.request("POST", "/api/auth/login", {
                "login": "admin", "password": "ChangeMe!CenterEdu2026",
            })[0], 200)
            status, catalog = admin.request("GET", "/api/reports/catalog")
            self.assertEqual(status, 200)
            routes = [row["route"] for row in catalog["data"]]
            self.assertEqual(len(routes), 59)
            self.assertEqual(len(set(routes)), 59)

            # Legacy deep links must resolve through the canonical observed
            # report contract instead of escaping as a server-side KeyError.
            for alias, canonical in {
                "/report/finance/revenue": "/report/finance/revenue_center",
                "/report/attendance": "/report/training/attendance",
            }.items():
                alias_status, alias_payload = admin.request("GET", "/api/reports/run?route=" + quote(alias))
                self.assertEqual(alias_status, 200, alias)
                self.assertEqual(alias_payload["data"]["route"], canonical)
                export_status, export_headers, export_body = admin.request_raw(
                    "GET", "/api/reports/export?route=" + quote(alias),
                )
                self.assertEqual(export_status, 200, alias)
                self.assertIn("text/csv", export_headers["Content-Type"], alias)
                self.assertTrue(export_body.strip(), alias)

            unknown_status, unknown_payload = admin.request(
                "GET", "/api/reports/run?route=" + quote("/report/unknown")
            )
            self.assertEqual(unknown_status, 404)
            self.assertEqual(unknown_payload["error"]["code"], "NOT_FOUND")

            for route in routes:
                run_status, payload = admin.request("GET", "/api/reports/run?route=" + quote(route))
                self.assertEqual(run_status, 200, route)
                report = payload["data"]
                self.assertEqual(report["route"], route)
                # A few observed reference reports expose a chart-only shell
                # with zero table columns; preserve that observed contract.
                if route not in {
                    "/report/training/daily_evaluation/index",
                    "/report/training/student_training_v2",
                    "/report/training/top_notebook",
                }:
                    self.assertTrue(report["columns"], route)
                self.assertIn(report["data_status"], {"OBSERVED", "PARTIAL", "NO_DATA"}, route)

            for route in (
                "/report/training/attendance",
                "/report/finance/revenue_center",
                "/report/crm/contract/index",
                "/report/center/staff_teacher",
            ):
                run_status, payload = admin.request("GET", "/api/reports/run?route=" + quote(route))
                self.assertEqual(run_status, 200)
                report = payload["data"]
                self.assertTrue(report["rows"], route)
                meaningful = [
                    value for key, value in report["rows"][0].items()
                    if key not in {"no", "stt"}
                ]
                self.assertTrue(any(value not in ("", None) for value in meaningful), route)
                self.assertNotIn("UNKNOWN", json.dumps(report, ensure_ascii=False))
                export_status, headers, body = admin.request_raw(
                    "GET", "/api/reports/export?route=" + quote(route),
                )
                self.assertEqual(export_status, 200, route)
                self.assertIn("text/csv", headers["Content-Type"], route)
                self.assertTrue(body.strip(), route)

            # Empty providers must remain explicit NO_DATA, never a fabricated
            # UNKNOWN row.  This exercises the engine contract independently of
            # the HTTP adapter and local rich seed.
            from modules.report_engine import ReportEngine

            class EmptyProvider:
                def query_report(self, *, entity, filters):
                    return []

            empty_engine = ReportEngine(EmptyProvider())
            empty = empty_engine.run("/report/training/attendance")
            self.assertEqual(empty["rows"], [])
            self.assertEqual(empty["data_status"], "NO_DATA")
            self.assertNotIn("UNKNOWN", json.dumps(empty, ensure_ascii=False))
        finally:
            os.environ.pop("CENTER_EDU_RICH_DEMO", None)

    def test_session_slot_local_contract_and_call_links(self):
        admin = ApiClient(self.server)
        self.assertEqual(admin.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        status, slot = admin.request("POST", "/api/session-slots", {
            "code": "SLOT-18", "name": "Ca tối", "start_time": "18:30", "end_time": "20:00"
        })
        self.assertEqual(status, 201)
        slot_id = slot["data"]["id"]
        self.assertEqual(admin.request("GET", "/api/session-slots?status=ACTIVE")[0], 200)
        invalid_status, invalid = admin.request("POST", "/api/session-slots", {
            "code": "SLOT-BAD", "name": "Bad", "start_time": "20:00", "end_time": "19:00"
        })
        self.assertEqual(invalid_status, 400)
        self.assertEqual(invalid["error"]["code"], "VALIDATION_ERROR")
        classes = admin.request("GET", "/api/classes")[1]["data"]
        status, session = admin.request("POST", "/api/timetable", {
            "class_id": classes[0]["id"], "session_slot_id": slot_id, "session_date": "2026-12-20"
        })
        self.assertEqual(status, 201)
        self.assertEqual(session["data"]["start_time"], "18:30")
        rows = admin.request("GET", "/api/timetable?class_code=ENG-FND-01")[1]["data"]
        linked = next(row for row in rows if row["id"] == session["data"]["id"])
        self.assertEqual(linked["session_slot_code"], "SLOT-18")
        students = admin.request("GET", "/api/students")[1]["data"]
        status, call = admin.request("POST", "/api/call-history", {
            "full_name": "Linked Student Call", "student_id": students[0]["id"], "status": "CONNECTED"
        })
        self.assertEqual(status, 201)
        linked_call = admin.request("GET", "/api/call-history?q=Linked%20Student")[1]["data"][0]
        self.assertEqual(linked_call["linked_student_code"], students[0]["student_code"])
        customer = admin.request("POST", "/api/potential-customers", {"full_name": "Linked Prospect"})[1]["data"]
        status, _prospect_call = admin.request("POST", "/api/call-history", {
            "full_name": "Linked Prospect Call", "potential_customer_id": customer["id"], "status": "CONNECTED"
        })
        self.assertEqual(status, 201)
        both_status, both = admin.request("POST", "/api/call-history", {
            "full_name": "Ambiguous", "student_id": students[0]["id"], "potential_customer_id": customer["id"]
        })
        self.assertEqual(both_status, 400)
        self.assertEqual(both["error"]["code"], "VALIDATION_ERROR")
        export_status, _headers, export_body = admin.request_raw("GET", "/api/export/session-slots")
        self.assertEqual(export_status, 200)
        self.assertIn(b"SLOT-18", export_body)
        student = ApiClient(self.server)
        self.assertEqual(student.request("POST", "/api/auth/login", {"login": "student", "password": "ChangeMe!CenterEdu2026"})[0], 200)
        self.assertEqual(student.request("GET", "/api/session-slots")[0], 403)

    def test_finance_transfer_domain_filters_export_create_and_rbac(self):
        os.environ["CENTER_EDU_RICH_DEMO"] = "1"
        try:
            self.server.service._ensure_rich_domain_backfill()
            admin = ApiClient(self.server)
            self.assertEqual(admin.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
            status, rows = admin.request("GET", "/api/finance/transfers")
            self.assertEqual(status, 200)
            self.assertGreaterEqual(len(rows["data"]), 10)
            self.assertTrue(all(row["transfer_code"] and row["from_student_id"] != row["to_student_id"] for row in rows["data"]))
            students = admin.request("GET", "/api/students")[1]["data"]
            created_status, created = admin.request("POST", "/api/finance/transfers", {
                "transfer_code": "CN-TEST-001", "transfer_date": "2026-11-02",
                "from_student_id": students[0]["id"], "to_student_id": students[1]["id"],
                "amount_received": 1250000, "status": "PENDING", "note": "transfer test",
            })
            self.assertEqual(created_status, 201)
            self.assertEqual(created["data"]["transfer_code"], "CN-TEST-001")
            self.assertEqual(admin.request("GET", "/api/finance/transfers?q=CN-TEST-001")[0], 200)
            invalid_status, invalid = admin.request("POST", "/api/finance/transfers", {
                "transfer_code": "CN-TEST-BAD", "transfer_date": "2026-11-02",
                "from_student_id": students[0]["id"], "to_student_id": students[0]["id"],
            })
            self.assertEqual(invalid_status, 400)
            self.assertEqual(invalid["error"]["code"], "VALIDATION_ERROR")
            export_status, headers, body = admin.request_raw("GET", "/api/export/finance-transfers")
            self.assertEqual(export_status, 200)
            self.assertIn("text/csv", headers["Content-Type"])
            self.assertIn(b"CN-TEST-001", body)
            student = ApiClient(self.server)
            self.assertEqual(student.request("POST", "/api/auth/login", {"login": "student", "password": "ChangeMe!CenterEdu2026"})[0], 200)
            self.assertEqual(student.request("GET", "/api/finance/transfers")[0], 403)
        finally:
            os.environ.pop("CENTER_EDU_RICH_DEMO", None)

    def test_finance_spend_domain_filters_export_create_update_persistence_and_rbac(self):
        """The finance spend module is wired to the host service, not source-only."""
        os.environ["CENTER_EDU_RICH_DEMO"] = "1"
        try:
            self.server.service.finance_spend_store.seed_demo(count=12)
            admin = ApiClient(self.server)
            self.assertEqual(admin.request("POST", "/api/auth/login", {
                "login": "admin", "password": "ChangeMe!CenterEdu2026",
            })[0], 200)
            status, payload = admin.request("GET", "/api/finance/spends?page=1&page_size=10")
            self.assertEqual(status, 200)
            self.assertGreaterEqual(payload["data"]["total"], 12)
            first = payload["data"]["items"][0]
            filtered_status, filtered = admin.request("GET", f"/api/finance/spends?q={first['code']}")
            self.assertEqual(filtered_status, 200)
            self.assertEqual(filtered["data"]["total"], 1)
            create_status, created = admin.request("POST", "/api/finance/spends", {
                "code": "PC-TEST-001", "spend_date": "2026-11-02", "center_id": "demo",
                "center_name": "Trung tâm CenterOnline - Demo", "content": "Chi phí kiểm thử",
                "category": "Vận hành", "amount_vnd": 1500000, "payment_method": "bank_transfer",
                "note": "local test",
            })
            self.assertEqual(create_status, 201)
            spend_id = created["data"]["id"]
            update_status, updated = admin.request("POST", f"/api/finance/spends/{spend_id}", {
                "content": "Chi phí đã cập nhật", "amount_vnd": 1750000,
            })
            self.assertEqual(update_status, 200)
            self.assertEqual(updated["data"]["amount_vnd"], 1750000)
            export_status, headers, body = admin.request_raw("GET", "/api/export/finance-spends?q=PC-TEST-001")
            self.assertEqual(export_status, 200)
            self.assertIn("text/csv", headers["Content-Type"])
            self.assertIn("PC-TEST-001".encode(), body)
            second_service = CenterEduService(self.db_path)
            try:
                persisted = second_service.finance_spend(second_service.user_by_login("admin"), spend_id)
                self.assertEqual(persisted["content"], "Chi phí đã cập nhật")
            finally:
                second_service.close()
            student = ApiClient(self.server)
            self.assertEqual(student.request("POST", "/api/auth/login", {
                "login": "student", "password": "ChangeMe!CenterEdu2026",
            })[0], 200)
            self.assertEqual(student.request("GET", "/api/finance/spends")[0], 403)
            self.assertEqual(student.request("POST", "/api/finance/spends", {"code": "PC-DENY"})[0], 403)
        finally:
            os.environ.pop("CENTER_EDU_RICH_DEMO", None)

    def test_finance_appointment_domain_aliases_filters_export_update_and_rbac(self):
        os.environ["CENTER_EDU_RICH_DEMO"] = "1"
        try:
            self.server.service.appointment_store.seed_demo(count=6)
            admin = ApiClient(self.server)
            self.assertEqual(admin.request("POST", "/api/auth/login", {
                "login": "admin", "password": "ChangeMe!CenterEdu2026",
            })[0], 200)
            status, payload = admin.request("GET", "/api/finance/appointments?page=1&page_size=10")
            self.assertEqual(status, 200)
            self.assertGreaterEqual(payload["data"]["total"], 6)
            create_status, created = admin.request("POST", "/api/sale/appointments", {
                "student_name": "Nguyễn Appointment", "parent_name": "Phụ huynh Appointment",
                "appointment_date": "2026-11-02", "amount": 2200000,
                "appointment_type": "Theo hợp đồng", "reference_code": "HD-APPT-001",
                "contract_code": "HD-APPT-001", "note": "local appointment",
            })
            self.assertEqual(create_status, 201)
            appointment_id = created["data"]["id"]
            filtered_status, filtered = admin.request("GET", "/api/finance/appointments?q=HD-APPT-001")
            self.assertEqual(filtered_status, 200)
            self.assertEqual(filtered["data"]["total"], 1)
            update_status, updated = admin.request("POST", f"/api/finance/appointments/{appointment_id}", {"status": "Đã xử lý"})
            self.assertEqual(update_status, 200)
            self.assertEqual(updated["data"]["status"], "Đã xử lý")
            export_status, headers, body = admin.request_raw("GET", "/api/export/sale-appointments?q=HD-APPT-001")
            self.assertEqual(export_status, 200)
            self.assertIn("text/csv", headers["Content-Type"])
            self.assertIn("HD-APPT-001".encode(), body)
            student = ApiClient(self.server)
            self.assertEqual(student.request("POST", "/api/auth/login", {
                "login": "student", "password": "ChangeMe!CenterEdu2026",
            })[0], 200)
            self.assertEqual(student.request("GET", "/api/finance/appointments")[0], 200)
            self.assertEqual(student.request("POST", "/api/finance/appointments", {"student_name": "Denied"})[0], 403)
        finally:
            os.environ.pop("CENTER_EDU_RICH_DEMO", None)

    def test_finance_assessment_domain_filters_export_create_update_persistence_and_rbac(self):
        os.environ["CENTER_EDU_RICH_DEMO"] = "1"
        try:
            self.server.service.finance_assessment_store.seed_demo(count=12)
            admin = ApiClient(self.server)
            self.assertEqual(admin.request("POST", "/api/auth/login", {
                "login": "admin", "password": "ChangeMe!CenterEdu2026",
            })[0], 200)
            status, payload = admin.request("GET", "/api/finance/assessments?page=1&page_size=10")
            self.assertEqual(status, 200)
            self.assertGreaterEqual(payload["data"]["total"], 12)
            first = payload["data"]["items"][0]
            filtered_status, filtered = admin.request("GET", f"/api/finance/assessments?q={first['assessment_code']}")
            self.assertEqual(filtered_status, 200)
            self.assertEqual(filtered["data"]["total"], 1)
            create_status, created = admin.request("POST", "/api/finance/assessments", {
                "assessment_code": "DG-TEST-001", "name": "Bảng giá kiểm thử", "date_apply": "2026-11-02",
                "course_name": "IELTS Start", "old_price": 3000000, "new_price": 3200000,
            })
            self.assertEqual(create_status, 201)
            assessment_id = created["data"]["id"]
            update_status, updated = admin.request("POST", f"/api/finance/assessments/{assessment_id}", {
                "name": "Bảng giá kiểm thử đã sửa", "status": "INACTIVE",
            })
            self.assertEqual(update_status, 200)
            self.assertEqual(updated["data"]["status"], "INACTIVE")
            export_status, headers, body = admin.request_raw("GET", "/api/export/finance-assessments?q=DG-TEST-001")
            self.assertEqual(export_status, 200)
            self.assertIn("text/csv", headers["Content-Type"])
            self.assertIn("Bảng giá kiểm thử đã sửa".encode("utf-8"), body)
            second_service = CenterEduService(self.db_path)
            try:
                persisted = second_service.finance_assessment(second_service.user_by_login("admin"), assessment_id)
                self.assertEqual(persisted["status"], "INACTIVE")
            finally:
                second_service.close()
            student = ApiClient(self.server)
            self.assertEqual(student.request("POST", "/api/auth/login", {
                "login": "student", "password": "ChangeMe!CenterEdu2026",
            })[0], 200)
            self.assertEqual(student.request("GET", "/api/finance/assessments")[0], 403)
            self.assertEqual(student.request("POST", "/api/finance/assessments", {"name": "Denied", "date_apply": "2026-11-02"})[0], 403)
        finally:
            os.environ.pop("CENTER_EDU_RICH_DEMO", None)

    def test_finance_reserve_domain_filters_export_create_update_persistence_and_rbac(self):
        os.environ["CENTER_EDU_RICH_DEMO"] = "1"
        try:
            self.server.service.finance_reserve_store.seed_demo(count=12)
            admin = ApiClient(self.server)
            self.assertEqual(admin.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
            status, payload = admin.request("GET", "/api/finance/reserves?page=1&page_size=10")
            self.assertEqual(status, 200); self.assertGreaterEqual(payload["data"]["total"], 12)
            contract_status, contract = admin.request("GET", "/api/finance/reserves?mode=Theo%20h%E1%BB%A3p%20%C4%91%E1%BB%93ng")
            self.assertEqual(contract_status, 200); self.assertEqual(contract["data"]["total"], 12)
            create_status, created = admin.request("POST", "/api/finance/reserves", {
                "reserve_code": "BL-TEST-001", "student_name": "Nguyễn Bảo Lưu", "reserve_date": "2026-11-02",
                "amount_or_days": 1500000, "contract_code": "HD-TEST-001", "status": "Chờ xử lý",
            })
            self.assertEqual(create_status, 201); reserve_id = created["data"]["id"]
            update_status, updated = admin.request("POST", f"/api/finance/reserves/{reserve_id}", {"status": "Đã cộng vào ví"})
            self.assertEqual(update_status, 200); self.assertEqual(updated["data"]["status"], "Đã cộng vào ví")
            export_status, headers, body = admin.request_raw("GET", "/api/export/finance-reserves?q=BL-TEST-001")
            self.assertEqual(export_status, 200); self.assertIn("text/csv", headers["Content-Type"]); self.assertIn(b"BL-TEST-001", body)
            second_service = CenterEduService(self.db_path)
            try: self.assertEqual(second_service.finance_reserve(second_service.user_by_login("admin"), reserve_id)["status"], "Đã cộng vào ví")
            finally: second_service.close()
            student = ApiClient(self.server)
            self.assertEqual(student.request("POST", "/api/auth/login", {"login": "student", "password": "ChangeMe!CenterEdu2026"})[0], 200)
            self.assertEqual(student.request("GET", "/api/finance/reserves")[0], 403)
            self.assertEqual(student.request("POST", "/api/finance/reserves", {"student_name": "Denied", "reserve_date": "2026-11-02"})[0], 403)
        finally:
            os.environ.pop("CENTER_EDU_RICH_DEMO", None)

    def test_finance_points_domain_filters_export_create_update_persistence_and_rbac(self):
        os.environ["CENTER_EDU_RICH_DEMO"] = "1"
        try:
            self.server.service.finance_points_store.seed_demo(count=10)
            admin = ApiClient(self.server)
            self.assertEqual(admin.request("POST", "/api/auth/login", {
                "login": "admin", "password": "ChangeMe!CenterEdu2026",
            })[0], 200)
            status, payload = admin.request("GET", "/api/finance/point-rules?page=1&page_size=5")
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["page_size"], 5)
            self.assertGreaterEqual(payload["data"]["total"], 10)
            first = payload["data"]["items"][0]
            filtered_status, filtered = admin.request("GET", f"/api/finance/point-rules?q={first['code']}")
            self.assertEqual(filtered_status, 200)
            self.assertEqual(filtered["data"]["total"], 1)
            create_status, created = admin.request("POST", "/api/finance/point-rules", {
                "code": "AP-TEST-001", "name": "Tích điểm kiểm thử", "status": "active",
                "amount_per_point": 500, "conversion_rate": 12000,
                "center_id": "demo", "center_name": "Trung tâm CenterOnline - Demo",
            })
            self.assertEqual(create_status, 201)
            rule_id = created["data"]["id"]
            update_status, updated = admin.request("POST", f"/api/finance/point-rules/{rule_id}", {
                "name": "Tích điểm kiểm thử đã sửa", "status": "inactive",
            })
            self.assertEqual(update_status, 200)
            self.assertEqual(updated["data"]["status"], "inactive")
            export_status, headers, body = admin.request_raw("GET", "/api/export/finance-point-rules?q=AP-TEST-001")
            self.assertEqual(export_status, 200)
            self.assertIn("text/csv", headers["Content-Type"])
            self.assertIn("AP-TEST-001".encode(), body)
            second_service = CenterEduService(self.db_path)
            try:
                persisted = second_service.finance_point(second_service.user_by_login("admin"), rule_id)
                self.assertEqual(persisted["name"], "Tích điểm kiểm thử đã sửa")
            finally:
                second_service.close()
            student = ApiClient(self.server)
            self.assertEqual(student.request("POST", "/api/auth/login", {
                "login": "student", "password": "ChangeMe!CenterEdu2026",
            })[0], 200)
            self.assertEqual(student.request("GET", "/api/finance/point-rules")[0], 403)
            self.assertEqual(student.request("POST", "/api/finance/point-rules", {"code": "AP-DENY"})[0], 403)
        finally:
            os.environ.pop("CENTER_EDU_RICH_DEMO", None)

    def test_finance_inventory_and_debit_item_domains_are_wired(self):
        os.environ["CENTER_EDU_RICH_DEMO"] = "1"
        try:
            from modules.finance_item import seed as seed_finance_items
            self.server.service.finance_debit_item_store.seed_demo(minimum=10)
            seed_finance_items(self.server.service.db, count=10)
            admin = ApiClient(self.server)
            self.assertEqual(admin.request("POST", "/api/auth/login", {"login": "admin", "password": "ChangeMe!CenterEdu2026"})[0], 200)
            status, items = admin.request("GET", "/api/finance/items?q=IT-DEMO-001")
            self.assertEqual(status, 200); self.assertEqual(len(items["data"]), 1)
            create_status, created = admin.request("POST", "/api/finance/items", {"code":"IT-TEST-001","fullname":"Sách kiểm thử","category":"Học liệu","quantity":4,"sale_price":120000,"status":"Hoạt động"})
            self.assertEqual(create_status, 201); item_id = created["data"]["id"]
            update_status, updated = admin.request("POST", f"/api/finance/items/{item_id}", {"quantity":8,"status":"Tạm khóa"})
            self.assertEqual(update_status, 200); self.assertEqual(updated["data"]["quantity"], 8)
            export_status, headers, body = admin.request_raw("GET", "/api/export/finance-items?q=IT-TEST-001")
            self.assertEqual(export_status, 200); self.assertIn(b"IT-TEST-001", body)
            status, debit = admin.request("GET", "/api/finance/debit-items?page=1&page_size=10")
            self.assertEqual(status, 200); self.assertGreaterEqual(debit["data"]["total"], 10)
            create_status, created = admin.request("POST", "/api/finance/debit-items", {"invoice_code":"HD-DEBIT-001","invoice_date":"2026-11-02","customer_name":"Nguyễn Vật phẩm","item_name":"Ipad","quantity":1,"total_amount":900000})
            self.assertEqual(create_status, 201); debit_id = created["data"]["id"]
            update_status, updated = admin.request("POST", f"/api/finance/debit-items/{debit_id}", {"status":"Đã trả"})
            self.assertEqual(update_status, 200); self.assertEqual(updated["data"]["status"], "Đã trả")
            export_status, headers, body = admin.request_raw("GET", "/api/export/finance-debit-items?q=HD-DEBIT-001")
            self.assertEqual(export_status, 200); self.assertIn(b"HD-DEBIT-001", body)
        finally:
            os.environ.pop("CENTER_EDU_RICH_DEMO", None)

    def test_finance_wallet_domain_filters_export_and_persistence(self):
        os.environ["CENTER_EDU_RICH_DEMO"] = "1"
        try:
            from modules.finance_wallet import seed as seed_finance_wallets
            seed_finance_wallets(self.server.service.db, count=20)
            admin = ApiClient(self.server)
            self.assertEqual(admin.request("POST", "/api/auth/login", {
                "login": "admin", "password": "ChangeMe!CenterEdu2026",
            })[0], 200)
            status, payload = admin.request("GET", "/api/finance/wallets?page=1&page_size=10")
            self.assertEqual(status, 200)
            self.assertGreaterEqual(payload["data"]["total"], 20)
            self.assertEqual(len(payload["data"]["items"]), 10)
            first = payload["data"]["items"][0]
            status, filtered = admin.request("GET", f"/api/finance/wallets?q={quote(first['student_name'])}")
            self.assertEqual(status, 200)
            self.assertGreaterEqual(filtered["data"]["total"], 1)
            status, headers, body = admin.request_raw("GET", f"/api/export/finance-wallets?q={quote('Nguyễn')}")
            self.assertEqual(status, 200)
            self.assertIn("text/csv", headers["Content-Type"])
            self.assertIn("Tên học viên".encode(), body)
            student = ApiClient(self.server)
            self.assertEqual(student.request("POST", "/api/auth/login", {
                "login": "student", "password": "ChangeMe!CenterEdu2026",
            })[0], 200)
            self.assertEqual(student.request("GET", "/api/finance/wallets")[0], 200)
        finally:
            os.environ.pop("CENTER_EDU_RICH_DEMO", None)


if __name__ == "__main__":
    unittest.main()
