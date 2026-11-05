"""Focused W2 training wizard checks.

These tests stay lane local: the Python contract/normalizer is tested with an
isolated SQLite store, while the browser module is checked for its public
renderer and workflow transport markers.  They do not touch the reference
site, primary runtime, or shared app.py/static/app.js files.
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from app import AppError, CenterEduService
from modules.training_routes import (
    CLASS_CREATE_CONTRACT,
    CLASS_CREATE_ROUTE,
    CLASS_CREATE_STEPS,
    TrainingRoutesStore,
    class_workflow_payload,
)


class TrainingSupervisionTests(unittest.TestCase):
    def test_observed_wizard_contract_is_explicit(self) -> None:
        self.assertEqual(CLASS_CREATE_ROUTE, "/training/class/create")
        self.assertEqual([step["label"] for step in CLASS_CREATE_STEPS], ["Lớp học", "Lịch học", "Học viên"])
        self.assertEqual(CLASS_CREATE_CONTRACT["submit"], "/api/classes/workflow")
        self.assertIn("cm_ids[]", CLASS_CREATE_CONTRACT["unknowns"])
        self.assertIn("cm_second_ids[]", CLASS_CREATE_CONTRACT["unknowns"])
        self.assertIn("daily_evaluation_id", CLASS_CREATE_CONTRACT["unknowns"])
        self.assertNotIn("fullname", CLASS_CREATE_CONTRACT["unknowns"])
        self.assertEqual(CLASS_CREATE_CONTRACT["name_transport"]["payload"], "name")
        self.assertEqual(CLASS_CREATE_CONTRACT["source"], "observed DOM + local workflow adapter")

    def test_workflow_payload_maps_observed_fields_and_dates(self) -> None:
        payload = class_workflow_payload(
            {
                "fullname": "Lớp tối",
                "course_id": "7",
                "code": "  ta-demo-01 ",
                "number_of_session": "40",
                "number_of_session_vietnam_teacher": "20",
                "number_of_session_foreign_teacher": "20",
                "number_of_hours": "80",
                "max_student": "12",
                "max_student_per_session": "6",
                "open_at": "03/11/2026",
                "close_at": "2026-12-31",
                "type_cost": "1",
                "note": "Ghi chú cục bộ",
                "sessions": [{"session_date": "04/11/2026", "start_time": "18:30", "end_time": "20:00", "room": "A01"}],
                "student_ids": [3, "4"],
            }
        )
        self.assertEqual(payload["code"], "TA-DEMO-01")
        self.assertEqual(payload["start_date"], "2026-11-03")
        self.assertEqual(payload["end_date"], "2026-12-31")
        self.assertEqual(payload["payment_method"], "Theo buổi")
        self.assertEqual(payload["sessions"][0]["session_date"], "2026-11-04")
        self.assertEqual(payload["student_ids"], [3, 4])
        self.assertEqual(payload["name"], "Lớp tối")
        self.assertNotIn("fullname", payload)
        self.assertNotIn("cm_ids[]", payload)

    def test_distinct_fullnames_never_collapse_on_coordinator_wire(self) -> None:
        base = {"course_id": 1, "code": "ALPHA-BETA", "student_ids": [], "sessions": []}
        alpha = class_workflow_payload({**base, "fullname": "  Lớp Alpha  "})
        beta = class_workflow_payload({**base, "fullname": "Lớp Beta"})
        self.assertEqual(alpha["name"], "Lớp Alpha")
        self.assertEqual(beta["name"], "Lớp Beta")
        self.assertNotEqual(alpha["name"], beta["name"])
        self.assertNotEqual(alpha, beta)

    def test_empty_and_overlong_fullname_are_explicit(self) -> None:
        with self.assertRaisesRegex(ValueError, "Tên lớp là bắt buộc"):
            class_workflow_payload({"course_id": 1, "code": "NO-NAME", "fullname": "   "})
        with self.assertRaisesRegex(ValueError, "Tên lớp không được dài quá 160"):
            class_workflow_payload({"course_id": 1, "code": "LONG-NAME", "fullname": "x" * 161})

    def test_fullname_normalizer_rejects_non_text_values(self) -> None:
        for value in ({"unexpected": True}, 42, ["Tên lớp"]):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "Tên lớp phải là văn bản"):
                    class_workflow_payload({"course_id": 1, "code": "BAD-NAME", "fullname": value})

    def test_workflow_payload_rejects_invalid_or_unsafe_steps(self) -> None:
        invalid = (
            ({"course_id": 1, "code": ""}, "Mã lớp"),
            ({"course_id": 1, "code": "A", "open_at": "2026-12-02", "close_at": "2026-12-01"}, "Ngày kết thúc"),
            ({"course_id": 1, "code": "A", "sessions": [{"session_date": "2026-11-03", "start_time": "20:00", "end_time": "19:00"}]}, "Buổi học"),
            ({"course_id": 1, "code": "A", "student_ids": [1, 1]}, "Danh sách học viên"),
            ({"course_id": 1, "code": "A", "max_student": "-1"}, "không được âm"),
        )
        for data, message in invalid:
            with self.subTest(data=data):
                with self.assertRaisesRegex(ValueError, message):
                    class_workflow_payload(data)

    def test_training_store_persists_class_route_contract_without_unknown_rows(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".sqlite3") as handle:
            db = sqlite3.connect(handle.name)
            store = TrainingRoutesStore(db)
            # Route-owned generic records remain separate from the host's
            # classes workflow; no synthetic class is inserted by this test.
            self.assertEqual(store.list("/training/class", role="ADMIN"), [])
            db.close()
            restarted = sqlite3.connect(handle.name)
            restarted_store = TrainingRoutesStore(restarted)
            self.assertEqual(restarted_store.list("/training/class", role="ADMIN"), [])
            restarted.close()

    def test_local_workflow_endpoint_persists_class_schedule_and_enrollment(self) -> None:
        # Isolated service/SQLite only.  This exercises the existing host
        # transaction that the wizard submits; it does not start or touch the
        # preserved primary listener.
        with tempfile.TemporaryDirectory(prefix="w2-training-runtime-") as root:
            db_path = Path(root) / "center.sqlite3"
            service = CenterEduService(db_path)
            actor = service.db.execute("SELECT * FROM users WHERE username='admin'").fetchone()
            course = service.db.execute("SELECT id FROM courses ORDER BY id LIMIT 1").fetchone()
            student = service.db.execute("SELECT id FROM students ORDER BY id LIMIT 1").fetchone()
            payload = class_workflow_payload(
                {
                    "course_id": course["id"],
                    "code": "W2-RUNTIME-01",
                    "number_of_session": 1,
                    "open_at": "03/11/2026",
                    "sessions": [{"session_date": "04/11/2026", "start_time": "18:30", "end_time": "20:00"}],
                    "student_ids": [student["id"]],
                }
            )
            result = service.create_class_workflow(actor, payload)
            class_id = result["class"]["id"]
            self.assertEqual(result["class"]["code"], "W2-RUNTIME-01")
            self.assertEqual(len(result["sessions"]), 1)
            self.assertEqual(len(result["enrollments"]), 1)
            service.close()
            reopened = CenterEduService(db_path)
            try:
                row = reopened.db.execute("SELECT code FROM classes WHERE id=?", (class_id,)).fetchone()
                session = reopened.db.execute("SELECT class_id FROM timetable_sessions WHERE class_id=?", (class_id,)).fetchone()
                enrollment = reopened.db.execute("SELECT student_id FROM enrollments WHERE class_id=?", (class_id,)).fetchone()
                self.assertEqual(row["code"], "W2-RUNTIME-01")
                self.assertEqual(session["class_id"], class_id)
                self.assertEqual(enrollment["student_id"], student["id"])
            finally:
                reopened.close()

    def test_name_readback_boundary_is_explicit_for_coordinator_integration(self) -> None:
        """Exercise name transport/readback without editing the host service.

        The lane owns the wire contract; app.py owns the durable classes schema
        and handler.  This test passes before and after coordinator integration,
        while making the current missing-column state observable instead of
        treating a 2xx response as proof of name persistence.
        """
        with tempfile.TemporaryDirectory(prefix="w2-training-name-readback-") as root:
            db_path = Path(root) / "center.sqlite3"
            service = CenterEduService(db_path)
            actor = service.db.execute("SELECT * FROM users WHERE username='admin'").fetchone()
            course = service.db.execute("SELECT id FROM courses ORDER BY id LIMIT 1").fetchone()
            payload = class_workflow_payload(
                {
                    "fullname": "Lớp Alpha",
                    "course_id": course["id"],
                    "code": "NAME-READBACK-01",
                    "sessions": [],
                    "student_ids": [],
                }
            )
            self.assertEqual(payload["name"], "Lớp Alpha")
            result = service.create_class_workflow(actor, payload)
            class_id = result["class"]["id"]
            columns = {row["name"] for row in service.db.execute("PRAGMA table_info(classes)").fetchall()}
            if "name" in columns:
                self.assertEqual(result["class"].get("name"), "Lớp Alpha")
            else:
                self.assertNotIn("name", result["class"])
            service.close()

            reopened = CenterEduService(db_path)
            try:
                columns = {row["name"] for row in reopened.db.execute("PRAGMA table_info(classes)").fetchall()}
                row = reopened.db.execute("SELECT * FROM classes WHERE id=?", (class_id,)).fetchone()
                self.assertIsNotNone(row)
                if "name" in columns:
                    self.assertEqual(row["name"], "Lớp Alpha")
                else:
                    self.assertNotIn("name", columns)
            finally:
                reopened.close()

    def test_service_rejects_invalid_class_names_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="w2-training-name-validation-") as root:
            service = CenterEduService(Path(root) / "center.sqlite3")
            try:
                actor = service.db.execute("SELECT * FROM users WHERE username='admin'").fetchone()
                course = service.db.execute("SELECT id FROM courses ORDER BY id LIMIT 1").fetchone()
                initial_classes = service.db.execute("SELECT COUNT(*) FROM classes").fetchone()[0]
                initial_audits = service.db.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
                invalid_names = ({"unexpected": True}, "x" * 161)
                for index, name in enumerate(invalid_names, start=1):
                    with self.subTest(name_type=type(name).__name__):
                        with self.assertRaises(AppError) as raised:
                            service.create_class_workflow(
                                actor,
                                {
                                    "course_id": course["id"],
                                    "code": f"INVALID-NAME-{index}",
                                    "name": name,
                                    "sessions": [],
                                    "student_ids": [],
                                },
                            )
                        self.assertEqual(raised.exception.status, 400)
                        self.assertEqual(raised.exception.code, "VALIDATION_ERROR")
                        self.assertEqual(
                            service.db.execute("SELECT COUNT(*) FROM classes").fetchone()[0],
                            initial_classes,
                        )
                        self.assertEqual(
                            service.db.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0],
                            initial_audits,
                        )

                created = service.create_class_workflow(
                    actor,
                    {
                        "course_id": course["id"],
                        "code": "NAME-UPDATE-VALID",
                        "name": "Tên giữ nguyên",
                        "sessions": [],
                        "student_ids": [],
                    },
                )
                class_id = created["class"]["id"]
                for name in ({"unexpected": True}, "x" * 161):
                    with self.subTest(update_name_type=type(name).__name__):
                        with self.assertRaises(AppError) as raised:
                            service.update_class(actor, class_id, {"name": name})
                        self.assertEqual(raised.exception.status, 400)
                        stored = service.db.execute("SELECT name FROM classes WHERE id=?", (class_id,)).fetchone()
                        self.assertEqual(stored["name"], "Tên giữ nguyên")
            finally:
                service.close()

    def test_frontend_contract_and_transport_are_present(self) -> None:
        source = (Path(__file__).parents[1] / "static" / "modules" / "training_routes.js").read_text(encoding="utf-8")
        for marker in (
            "'/training/class/create'",
            "CLASS_CREATE_STEPS",
            "classWorkflowPayload",
            "payloadName: 'name'",
            "assertClassWorkflowName",
            "Tên lớp chưa được hệ thống hỗ trợ lưu",
            "saveClassWorkflow",
            "renderClassCreate",
            "'/api/classes/workflow'",
            "Tạo lớp học",
            "Tìm kiếm khách hàng tiềm năng",
            "Lớp học",
            "Lịch học",
            "Học viên",
        ):
            self.assertIn(marker, source)

    def test_frontend_javascript_syntax(self) -> None:
        source_path = Path(__file__).parents[1] / "static" / "modules" / "training_routes.js"
        result = subprocess.run(["node", "--check", str(source_path)], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_frontend_rejects_success_when_name_is_dropped(self) -> None:
        source_path = Path(__file__).parents[1] / "static" / "modules" / "training_routes.js"
        script = textwrap.dedent(
            f"""
            import {{ classWorkflowPayload, saveClassWorkflow }} from {json.dumps(source_path.as_uri())};
            const input = {{ fullname: 'Lớp Alpha', course_id: 1, code: 'ALPHA', sessions: [], student_ids: [] }};
            const payload = classWorkflowPayload(input);
            if (payload.name !== 'Lớp Alpha' || payload.fullname !== undefined) process.exit(2);
            let invalidNameRejected = false;
            try {{ classWorkflowPayload({{ ...input, fullname: {{ unexpected: true }} }}); }}
            catch (error) {{ invalidNameRejected = /Tên lớp phải là văn bản/.test(String(error.message)); }}
            if (!invalidNameRejected) process.exit(5);
            let rejected = false;
            try {{
              await saveClassWorkflow(input, async (_path, options) => {{
                const posted = JSON.parse(options.body);
                if (posted.name !== 'Lớp Alpha') process.exit(3);
                return {{ ok: true, status: 201, json: async () => ({{ ok: true, data: {{ class: {{ code: 'ALPHA' }} }} }}) }};
              }});
            }} catch (error) {{
              rejected = /chưa được hệ thống hỗ trợ lưu/.test(String(error.message));
            }}
            if (!rejected) process.exit(4);
            """
        )
        result = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_class_list_projection_filters_and_summary_use_persisted_fields(self) -> None:
        source_path = Path(__file__).parents[1] / "static" / "modules" / "training_routes.js"
        script = textwrap.dedent(
            f"""
            import {{ classListProjection, classListQuery, summarizeClassStatuses }} from {json.dumps(source_path.as_uri())};
            const projection = classListProjection({{
              id: 9, name: 'Tên lớp đã lưu', code: 'CLASS-09', course_name: 'Khóa học A', student_count: 5,
              start_date: '2026-11-04', end_date: '2027-02-02', schedule: 'Thứ 2 · 18:30',
              primary_manager: '', secondary_manager: '', teacher: 'Giáo viên A', completed_sessions: 3, sessions_count: 12,
            }});
            if (projection.name !== 'Tên lớp đã lưu' || projection.code !== 'CLASS-09') process.exit(2);
            if (projection.period !== 'Từ 04/11/2026 đến 02/02/2027' || projection.teacher !== 'Giáo viên A') process.exit(3);
            if (projection.manager !== '' || projection.sessionProgress !== '3/12') process.exit(4);
            const query = new URLSearchParams(classListQuery({{ q: 'Lớp A & B', status: 'IN_PROGRESS', course_id: 2, start_from: '2026-11-01' }}));
            if (query.get('q') !== 'Lớp A & B' || query.get('status') !== 'IN_PROGRESS') process.exit(5);
            if (query.get('course_id') !== '2' || query.get('start_from') !== '2026-11-01') process.exit(6);
            const scheduleOnlyQuery = new URLSearchParams(classListQuery({{ q: 'Lớp 1', status: 'NO_SCHEDULE' }}));
            if (scheduleOnlyQuery.has('status') || scheduleOnlyQuery.get('q') !== 'Lớp 1') process.exit(7);
            const summary = summarizeClassStatuses([
              {{ code: 'P', status: 'PLANNED' }}, {{ code: 'O', status: 'OPEN' }},
              {{ code: 'I', status: 'IN_PROGRESS' }}, {{ code: 'C', status: 'COMPLETED' }},
              {{ code: 'X', status: 'CANCELLED' }}, {{ code: 'N', status: 'IN_PROGRESS' }},
            ], ['P', 'O', 'I', 'C', 'X'].map((class_code) => ({{ class_code }})));
            const counts = Object.fromEntries(summary.map((item) => [item.key, item.count]));
            if (counts.planned !== 1 || counts.inProgress !== 2 || counts.ending !== 0) process.exit(8);
            if (counts.completed !== 1 || counts.cancelled !== 1 || counts.noSchedule !== 1) process.exit(9);
            """
        )
        result = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_class_search_empty_server_response_is_authoritative(self) -> None:
        source_path = Path(__file__).parents[1] / "static" / "modules" / "training_routes.js"
        script = textwrap.dedent(
            f"""
            import {{ classListResponse }} from {json.dumps(source_path.as_uri())};
            const serverEmpty = classListResponse({{ ok: true, data: [] }});
            if (serverEmpty.rows.length !== 0 || serverEmpty.searchApplied !== true) process.exit(2);
            const legacyEmpty = classListResponse([]);
            if (legacyEmpty.rows.length !== 0 || legacyEmpty.searchApplied !== false) process.exit(3);
            const legacyRows = classListResponse([{{ code: 'ALPHA' }}]);
            if (legacyRows.rows.length !== 1 || legacyRows.searchApplied !== false) process.exit(4);
            const explicitLegacy = classListResponse({{ data: [], supportsSearch: false }});
            if (explicitLegacy.searchApplied !== false) process.exit(5);
            """
        )
        result = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_training_class_renderer_has_real_projection_filter_and_detail_actions(self) -> None:
        source = (Path(__file__).parents[1] / "static" / "modules" / "training_routes.js").read_text(encoding="utf-8")
        for marker in (
            "renderTrainingClassProjection",
            "classListProjection(row)",
            "classListQuery(state.filters)",
            "classListResponse",
            "summarizeClassStatuses(rows, timetableRows)",
            "api(`/api/classes/${encodeURIComponent(row.id)}`)",
            "api('/api/classes/import'",
            "'/api/export/classes'",
            "Không tìm thấy dữ liệu",
        ):
            self.assertIn(marker, source)


if __name__ == "__main__":
    unittest.main()
