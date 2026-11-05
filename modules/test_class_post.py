"""Focused tests for the persistent class-post report contract.

The reference capture exposed a read-only report (no create/edit form).  These
tests therefore exercise the durable event join, filters, and truthful empty
state; mutation/RBAC remains owned by the application service when a future
observed contract adds it.
"""

from __future__ import annotations

import sqlite3
import unittest

from report_crm_center import CrmCenterReportAdapter


class _Provider:
    def __init__(self) -> None:
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row

    def query_report(self, *, entity: str, filters: dict[str, str]):
        raise sqlite3.OperationalError(f"no such table: {entity}")


def _schema(provider: _Provider) -> None:
    db = provider.db
    db.executescript(
        """
        CREATE TABLE courses (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE classes (
            id INTEGER PRIMARY KEY, code TEXT NOT NULL, room TEXT NOT NULL DEFAULT '',
            course_id INTEGER NOT NULL, status TEXT NOT NULL
        );
        CREATE TABLE users (
            id INTEGER PRIMARY KEY, full_name TEXT NOT NULL,
            role TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE enrollments (
            id INTEGER PRIMARY KEY, class_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL, status TEXT NOT NULL
        );
        CREATE TABLE class_post_events (
            id INTEGER PRIMARY KEY, class_id INTEGER NOT NULL,
            author_id INTEGER NOT NULL, content TEXT NOT NULL,
            status TEXT NOT NULL, posted_at TEXT NOT NULL
        );
        """
    )
    db.executemany("INSERT INTO courses VALUES (?, ?)", [(1, "IELTS 6.5"), (2, "Starters")])
    db.executemany(
        "INSERT INTO classes VALUES (?, ?, ?, ?, ?)",
        [(1, "IELTS-T2", "P.101", 1, "IN_PROGRESS"),
         (2, "STARTERS-T4", "P.102", 2, "PLANNED")],
    )
    db.executemany(
        "INSERT INTO users(id, full_name, role) VALUES (?, ?, ?)",
        [(10, "Nguyễn Văn Cường", "TEACHER"), (11, "Lê Thu Hà", "STAFF")],
    )
    db.executemany(
        "INSERT INTO enrollments VALUES (?, ?, ?, ?)",
        [(1, 1, 501, "ENROLLED"), (2, 1, 502, "ENROLLED"),
         (3, 1, 503, "CANCELLED"), (4, 2, 504, "ENROLLED")],
    )
    db.executemany(
        "INSERT INTO class_post_events VALUES (?, ?, ?, ?, ?, ?)",
        [(1, 1, 10, "Bài học tuần 1", "PUBLISHED", "2026-10-01 18:00:00"),
         (2, 1, 11, "Bài học tuần 2", "PUBLISHED", "2026-10-08 18:00:00"),
         (3, 1, 10, "Bản nháp", "DRAFT", "2026-10-09 18:00:00"),
         (4, 2, 11, "Đã lưu trữ", "ARCHIVED", "2026-10-02 18:00:00")],
    )
    db.commit()


class ClassPostReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = _Provider()
        _schema(self.provider)
        self.adapter = CrmCenterReportAdapter(self.provider)

    def test_published_events_aggregate_without_counting_drafts(self) -> None:
        rows = self.adapter._local_rows("report_center_class_post_index", {})
        self.assertEqual(len(rows), 2)  # classes remain visible, even zero posts
        first = rows[0]
        self.assertEqual(first["ten_lop"], "STARTERS-T4")
        second = rows[1]
        self.assertEqual(second["ten_lop"], "IELTS-T2")
        self.assertEqual(second["so_luong_hoc_vien"], 2)
        self.assertEqual(second["so_luong_bai_ang"], 2)
        self.assertEqual(second["nguoi_ang_bai"], "Lê Thu Hà")
        self.assertEqual(second["trang_thai"], "Đang học")

    def test_filters_apply_to_class_status_and_posted_date(self) -> None:
        status_rows = self.adapter._local_rows(
            "report_center_class_post_index", {"filter_3": "Đang học"}
        )
        self.assertEqual([row["ten_lop"] for row in status_rows], ["IELTS-T2"])
        date_rows = self.adapter._local_rows(
            "report_center_class_post_index",
            {"from_date": "2026-10-08", "to_date": "2026-10-08"},
        )
        # Date filtering is event-backed; only the class with the 08 Oct post
        # remains in the grouped report.
        self.assertEqual([row["ten_lop"] for row in date_rows], ["IELTS-T2"])

    def test_class_search_matches_code_room_or_course(self) -> None:
        rows = self.adapter._local_rows(
            "report_center_class_post_index", {"chon_lop_hoc": "IELTS"}
        )
        self.assertEqual([row["ten_lop"] for row in rows], ["IELTS-T2"])

    def test_no_published_event_is_truthful_no_data(self) -> None:
        self.provider.db.execute("UPDATE class_post_events SET status='DRAFT'")
        self.provider.db.commit()
        self.assertEqual(
            self.adapter._local_rows("report_center_class_post_index", {}), []
        )
        self.assertIn("report_center_class_post_index", self.adapter.missing_entities)

    def test_missing_tables_do_not_fallback_to_generic_rows(self) -> None:
        provider = _Provider()
        adapter = CrmCenterReportAdapter(provider)
        self.assertEqual(
            list(adapter.query_report(entity="report_center_class_post_index", filters={})),
            [],
        )
        self.assertIn("report_center_class_post_index", adapter.missing_entities)


if __name__ == "__main__":
    unittest.main()
