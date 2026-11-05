"""Focused W1 contract checks for the home/training route lane."""
from __future__ import annotations

import csv
import io
import os
import sqlite3
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path

from modules.training_routes import (
    MANAGE_ROLES,
    ROUTE_CONTRACTS,
    TrainingRoutesStore,
    route_manifest,
)


class W1TrainingRoutesTests(unittest.TestCase):
    def setUp(self) -> None:
        # File-backed, per-test DB proves persistence while preventing state
        # leakage when this module runs inside the combined evidence suite.
        handle = tempfile.NamedTemporaryFile(prefix="w1-training-test-", suffix=".sqlite3", delete=False)
        self.db_path = handle.name
        handle.close()
        self.db = sqlite3.connect(self.db_path)
        self.store = TrainingRoutesStore(self.db)

    def tearDown(self) -> None:
        self.db.close()
        try:
            os.unlink(self.db_path)
        except FileNotFoundError:
            pass

    def test_manifest_covers_all_owned_routes_and_reference_labels(self) -> None:
        expected = {
            "/", "/dashboard/training", "/training/announcement", "/training/absent-v2",
            "/training/event", "/training/post", "/training/course", "/training/class",
            "/training/timetable", "/training/attendance", "/training/daily-evaluation-v2",
            "/training/test", "/training/homework", "/training/elearn/topic",
            "/training/elearn/exam_first_test", "/training/class_enroll_trail_wait",
            "/training/confirm", "/training/customer_test", "/training/pending_enrollment/index",
        }
        self.assertEqual(set(ROUTE_CONTRACTS), expected)
        self.assertEqual(set(item["route"] for item in route_manifest()), expected)
        self.assertEqual(
            [item["label"] for item in ROUTE_CONTRACTS["/training/course"]["columns"]],
            ["No.", "Tên khóa học", "Số buổi / Số giờ", "Học phí", "Bài đánh giá hàng ngày", "Bài kiểm tra", "Môn học", "Trạng thái", "Hành động"],
        )

    def test_course_and_pending_rows_persist_filter_export_and_restart(self) -> None:
        self.store.seed_natural()
        courses = self.store.list("/training/course", role="ADMIN")
        self.assertEqual(len(courses), 3)
        self.assertEqual(courses[0]["name"], "Tiếng Anh thiếu nhi")
        filtered = self.store.list("/training/course", role="STAFF", query="IELTS")
        self.assertEqual([row["code"] for row in filtered], ["IELTS-MUC-TIEU"])
        exported = self.store.export_csv("/training/course", role="STAFF", query="IELTS")
        rows = list(csv.reader(io.StringIO(exported.lstrip("\ufeff"))))
        self.assertEqual(rows[0][1], "Tên khóa học")
        self.assertIn("IELTS mục tiêu 6.5", rows[1])
        pending = self.store.list("/training/pending_enrollment/index", role="ADMIN")
        self.assertEqual(pending[0]["status"], "Đang chờ")
        with tempfile.NamedTemporaryFile(suffix=".sqlite3") as handle:
            path = handle.name
        try:
            first = sqlite3.connect(path)
            first_store = TrainingRoutesStore(first)
            first_store.seed_natural("/training/course")
            first.close()
            restarted_db = sqlite3.connect(path)
            restarted = TrainingRoutesStore(restarted_db)
            self.assertEqual(len(restarted.list("/training/course", role="ADMIN")), 3)
            restarted_db.close()
        finally:
            os.unlink(path)

    def test_crud_rbac_and_unknown_values_fail_closed(self) -> None:
        with self.assertRaises(PermissionError):
            self.store.create("/training/course", role="TEACHER", created_by="Giáo viên", data={"code": "X", "name": "Không được tạo"})
        created = self.store.create(
            "/training/course", role="ADMIN", created_by="Quản trị viên trung tâm",
            data={"code": "TA-GIAO-TIEP", "name": "Tiếng Anh giao tiếp", "sessions_count": 30, "hours": 45, "fee_method": "Theo khóa", "fee": 5400000, "status": "Hoạt động"},
        )
        self.assertEqual(created["code"], "TA-GIAO-TIEP")
        duplicate = self.store.duplicate("/training/course", created["id"], role="STAFF")
        self.assertEqual(duplicate["code"], "TA-GIAO-TIEP-SAO")
        self.assertEqual(duplicate["name"], "Tiếng Anh giao tiếp (bản sao)")
        duplicate_again = self.store.duplicate("/training/course", created["id"], role="STAFF")
        self.assertEqual(duplicate_again["code"], "TA-GIAO-TIEP-2")
        updated = self.store.update("/training/course", created["id"], role="STAFF", data={"subject": "Giao tiếp"})
        self.assertEqual(updated["subject"], "Giao tiếp")
        with self.assertRaises(ValueError):
            self.store.update("/training/course", created["id"], role="STAFF", data={"status": "UNKNOWN"})
        self.store.delete("/training/course", created["id"], role="ADMIN")
        self.store.delete("/training/course", duplicate["id"], role="ADMIN")
        self.store.delete("/training/course", duplicate_again["id"], role="ADMIN")
        self.assertEqual(self.store.list("/training/course", role="ADMIN"), [])

    def test_teaching_route_accepts_vietnamese_status_and_rejects_english_placeholder(self) -> None:
        row = self.store.create(
            "/training/attendance", role="TEACHER", created_by="Trần Minh Anh",
            data={"student_name": "Nguyễn Minh Anh", "class_name": "TA-NEN-TANG-01", "session_date": "03/11/2026", "status": "Có mặt", "note": "Tham gia đầy đủ"},
        )
        self.assertEqual(row["session_date"], "2026-11-03")
        with self.assertRaises(ValueError):
            self.store.create(
                "/training/attendance", role="TEACHER", created_by="Trần Minh Anh",
                data={"student_name": "Lê Hoàng Nam", "class_name": "TA-NEN-TANG-01", "session_date": "2026-11-04", "status": "UNKNOWN"},
            )

    def test_backend_register_attaches_persistent_store_and_manifest(self) -> None:
        from modules.training_routes import register

        target = SimpleNamespace(db=self.db)
        result = register(target, target)
        self.assertEqual(result["name"], "training_routes")
        self.assertEqual(result["schema"], "training_route_records")
        self.assertEqual(result["status"], "PERSISTENT_SQLITE_CONTRACT")
        self.assertIs(target.training_routes_store.db, self.db)
        self.assertEqual({item["route"] for item in target.training_route_manifest}, set(ROUTE_CONTRACTS))
        self.assertIs(target.training_route_contracts, ROUTE_CONTRACTS)

    def test_frontend_autoload_registers_all_owned_routes(self) -> None:
        source = (Path(__file__).parents[2] / "static" / "modules" / "training_routes.js").read_text(encoding="utf-8")
        self.assertIn("export function register", source)
        # The module receives the host registry as an injected object (with a
        # globalThis fallback), so assert the public seam and registration loop
        # instead of requiring one literal global expression in source.
        self.assertIn("registerScreen", source)
        self.assertIn("TRAINING_ROUTES.forEach", source)
        for route in ROUTE_CONTRACTS:
            self.assertIn(repr(route), source)


if __name__ == "__main__":
    unittest.main()
