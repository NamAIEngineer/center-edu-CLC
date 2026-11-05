"""Focused W6 tests for the persistent survey contract."""

from __future__ import annotations

import csv
import io
import sqlite3
import unittest

from modules import survey


class W6SurveyContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, full_name TEXT NOT NULL)")
        self.db.execute("INSERT INTO users(id,full_name) VALUES(1,'Nguyễn Ngọc Mai')")
        survey.ensure_schema(self.db)
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()

    def test_crud_builder_response_filter_and_export(self) -> None:
        created = survey.create_survey(
            self.db,
            {"name": "Khảo sát mức độ hài lòng tháng Mười Một", "due_date": "15/11/2026", "status": "Bản nháp", "description": "Ý kiến sau buổi học."},
            created_by=1,
        )
        self.assertEqual(created["status"], "DRAFT")
        self.assertEqual(created["due_date"], "2026-11-15")
        page = survey.create_page(self.db, created["id"], {"title": "Trải nghiệm lớp học", "position": 0})
        page_id = page["pages"][0]["id"]
        detail = survey.create_question(
            self.db,
            page_id,
            {"kind": "RATING", "label": "Bạn đánh giá giáo viên thế nào?", "position": 0, "required": True},
        )
        question_id = detail["pages"][0]["questions"][0]["id"]
        submitted = survey.submit_response(
            self.db,
            created["id"],
            {"respondent_name": "Trần Minh Anh", "respondent_role": "Nhân viên", "answers": {str(question_id): "5"}},
        )
        self.assertEqual(submitted["response_count"], 1)
        updated = survey.update_survey(self.db, created["id"], {"name": "Khảo sát trải nghiệm lớp học", "status": "Đã phát hành"})
        self.assertEqual(updated["status"], "PUBLISHED")
        rows = survey.list_surveys(self.db, {"q": "trải nghiệm", "status": "Đã phát hành"})
        self.assertEqual(len(rows), 1)
        csv_text = survey.export_csv(rows)
        parsed = list(csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff"))))
        self.assertEqual(parsed[0]["Tên khảo sát"], "Khảo sát trải nghiệm lớp học")
        self.assertEqual(parsed[0]["Người tạo"], "Nguyễn Ngọc Mai")

    def test_rbac_and_validation_fail_closed(self) -> None:
        self.assertFalse(survey.can("STUDENT", "read"))
        with self.assertRaises(PermissionError):
            survey.list_surveys(self.db, role="STUDENT")
        with self.assertRaises(survey.SurveyError):
            survey.create_survey(self.db, {"name": "", "due_date": "31/02/2026"}, created_by=1)
        with self.assertRaises(survey.SurveyError):
            survey.normalize_date("2026-11-01-extra")

    def test_register_initializes_schema_and_returns_host_metadata(self) -> None:
        class Service:
            db = self.db

        metadata = survey.register(Service(), Service())
        self.assertEqual(metadata["status"], "PERSISTENT_LOCAL_CONTRACT")
        self.assertEqual(metadata["routes"], ("/survey", "/survey/create_survey"))
        self.assertEqual(
            self.db.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='surveys'").fetchone()[0],
            1,
        )


if __name__ == "__main__":
    unittest.main()
