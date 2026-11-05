"""Course pricing assessment domain for the CENTER EDU local rebuild.

The reference DOM exposes a pricing list with a small create form.  Its private
API is not available, so this module owns an explicit SQLite contract derived
from the observed fields.  It deliberately keeps role checks and validation at
the domain boundary instead of relying on the browser.
"""
from __future__ import annotations

import csv
import io
import sqlite3
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from modules.finance import _attach_store, _register_metadata

ROUTE = "/finance/assessment"
READ_ROLES = frozenset(("ADMIN", "STAFF", "TEACHER"))
WRITE_ROLES = frozenset(("ADMIN", "STAFF"))
STATUSES = ("ACTIVE", "INACTIVE")
TABLE_HEADERS = ("No.", "Tên", "Ngày áp dụng", "Nhân viên định giá", "Khóa học liên quan")


def _day(value: Any) -> str:
    text = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError("Ngày áp dụng không hợp lệ")


def _money(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        amount = Decimal(str(value).replace(",", "").replace(" VND", "").strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Giá định giá không hợp lệ") from exc
    if amount < 0:
        raise ValueError("Giá định giá không được âm")
    return float(amount)


class FinanceAssessment:
    """Persistent CRUD/query/export boundary for course price assessments."""

    def __init__(self, db: sqlite3.Connection, *, now: date | None = None):
        self.db = db
        self.db.row_factory = sqlite3.Row
        self.now = now or date.today()
        self.ensure_schema()

    def ensure_schema(self) -> None:
        self.db.execute(
            """CREATE TABLE IF NOT EXISTS finance_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                date_apply TEXT NOT NULL,
                pricing_staff TEXT NOT NULL,
                course_id INTEGER,
                course_name TEXT NOT NULL DEFAULT '',
                old_price REAL,
                new_price REAL,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )"""
        )
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_finance_assessments_date ON finance_assessments(date_apply)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_finance_assessments_status ON finance_assessments(status)")
        self.db.commit()

    def _assert_read(self, role: str) -> None:
        if role not in READ_ROLES:
            raise PermissionError("Định giá không dành cho vai trò này")

    def _assert_write(self, role: str) -> None:
        if role not in WRITE_ROLES:
            raise PermissionError("Chỉ ADMIN hoặc STAFF được quản lý định giá")

    def seed_demo(self, *, count: int = 12, actor: str = "Center Administrator") -> int:
        existing = self.db.execute("SELECT COUNT(*) FROM finance_assessments").fetchone()[0]
        if existing >= count:
            return existing
        names = ("Tăng giá đầu năm", "Ưu đãi khóa IELTS", "Bảng giá tiếng Anh trẻ em", "Gói học phí mùa hè")
        courses = ("Tiếng Anh cơ bản 1", "IELTS Start", "Tiếng Anh trẻ em", "AA")
        for index in range(existing, count):
            self.create({
                "assessment_code": f"DG-DEMO-{index + 1:03d}",
                "name": names[index % len(names)],
                "date_apply": f"2026-{(index % 9) + 1:02d}-{(index % 25) + 1:02d}",
                "course_name": courses[index % len(courses)],
                "old_price": 2_500_000 + index * 100_000,
                "new_price": 2_700_000 + index * 100_000,
                "status": STATUSES[index % len(STATUSES)],
            }, role="ADMIN", actor=actor)
        return self.db.execute("SELECT COUNT(*) FROM finance_assessments").fetchone()[0]

    @staticmethod
    def _row(row: sqlite3.Row) -> dict[str, Any]:
        value = dict(row)
        # Keep display fields explicit so the UI/export layer never needs to
        # infer a course label from a private reference response.
        value["assessment_name"] = value["name"]
        value["employee_name"] = value["pricing_staff"]
        return value

    def list(self, filters: Mapping[str, Any] | None = None, *, role: str = "ADMIN", page: int = 1, page_size: int = 10) -> dict[str, Any]:
        self._assert_read(role)
        filters = filters or {}
        page = max(int(page), 1)
        page_size = min(max(int(page_size), 1), 100)
        where, args = ["1=1"], []
        if filters.get("q"):
            needle = f"%{str(filters['q']).strip()}%"
            # Rich-demo responses pass through the customer-facing seed
            # sanitizer, which presents ``DG-DEMO-009`` as ``DG-009`` while
            # the durable code remains ``DG-DEMO-009`` for stable joins.
            # Search both representations so a code copied from the UI is
            # round-trippable without mutating storage identifiers.
            where.append("(assessment_code LIKE ? OR REPLACE(assessment_code, 'DG-DEMO-', 'DG-') LIKE ? OR name LIKE ? OR pricing_staff LIKE ? OR course_name LIKE ?)")
            args.extend([needle, needle, needle, needle, needle])
        if filters.get("status"):
            status = str(filters["status"]).strip().upper()
            if status not in STATUSES:
                raise ValueError("Trạng thái định giá không hợp lệ")
            where.append("status = ?"); args.append(status)
        base = " FROM finance_assessments WHERE " + " AND ".join(where)
        total = self.db.execute("SELECT COUNT(*)" + base, args).fetchone()[0]
        rows = self.db.execute(
            "SELECT *" + base + " ORDER BY date_apply DESC, id DESC LIMIT ? OFFSET ?",
            args + [page_size, (page - 1) * page_size],
        ).fetchall()
        return {
            "items": [self._row(row) for row in rows], "total": total, "page": page,
            "page_size": page_size, "pages": (total + page_size - 1) // page_size,
        }

    def get(self, assessment_id: int, *, role: str = "ADMIN") -> dict[str, Any]:
        self._assert_read(role)
        row = self.db.execute("SELECT * FROM finance_assessments WHERE id = ?", (int(assessment_id),)).fetchone()
        if row is None:
            raise KeyError("Định giá không tồn tại")
        return self._row(row)

    def create(self, payload: Mapping[str, Any], *, role: str, actor: str) -> dict[str, Any]:
        self._assert_write(role)
        name = str(payload.get("name") or payload.get("fullname") or "").strip()
        if not name:
            raise ValueError("Tên định giá là bắt buộc")
        date_apply = _day(payload.get("date_apply"))
        status = str(payload.get("status") or "ACTIVE").strip().upper()
        if status not in STATUSES:
            raise ValueError("Trạng thái định giá không hợp lệ")
        code = str(payload.get("assessment_code") or "").strip() or f"DG-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        try:
            cur = self.db.execute(
                """INSERT INTO finance_assessments
                (assessment_code,name,date_apply,pricing_staff,course_id,course_name,old_price,new_price,status,created_by,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (code, name, date_apply, actor, payload.get("course_id"), str(payload.get("course_name") or "").strip(),
                 _money(payload.get("old_price")), _money(payload.get("new_price")), status, actor, now, now),
            )
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            self.db.rollback()
            raise ValueError("Mã định giá đã tồn tại") from exc
        return self.get(cur.lastrowid, role=role)

    def update(self, assessment_id: int, payload: Mapping[str, Any], *, role: str, actor: str) -> dict[str, Any]:
        self._assert_write(role)
        current = self.get(assessment_id, role=role)
        merged = dict(current); merged.update(payload)
        name = str(merged.get("name") or merged.get("fullname") or "").strip()
        if not name:
            raise ValueError("Tên định giá là bắt buộc")
        status = str(merged.get("status") or "ACTIVE").strip().upper()
        if status not in STATUSES:
            raise ValueError("Trạng thái định giá không hợp lệ")
        self.db.execute(
            """UPDATE finance_assessments SET name=?,date_apply=?,course_id=?,course_name=?,old_price=?,new_price=?,status=?,updated_at=? WHERE id=?""",
            (name, _day(merged.get("date_apply")), merged.get("course_id"), str(merged.get("course_name") or "").strip(),
             _money(merged.get("old_price")), _money(merged.get("new_price")), status,
             datetime.utcnow().isoformat(timespec="seconds") + "Z", int(assessment_id)),
        )
        self.db.commit()
        return self.get(assessment_id, role=role)

    def export_csv(self, filters: Mapping[str, Any] | None = None, *, role: str = "ADMIN") -> str:
        rows = self.list(filters, role=role, page=1, page_size=10000)["items"]
        out = io.StringIO(); writer = csv.writer(out); writer.writerow(TABLE_HEADERS)
        for index, row in enumerate(rows, 1):
            writer.writerow([index, row["name"], row["date_apply"], row["pricing_staff"], row["course_name"]])
        return "\ufeff" + out.getvalue()


__all__ = ["FinanceAssessment", "ROUTE", "TABLE_HEADERS", "READ_ROLES", "WRITE_ROLES", "register"]


def route_contract() -> dict[str, Any]:
    return {
        "route": ROUTE, "headers": TABLE_HEADERS,
        "filters": ("q", "status"),
        "tabs": ("Ưu đãi - Khuyến mãi", "Gói học phí", "Định giá", "Định giá gói học phí"),
        "page_sizes": (5, 10, 25, 50), "read_roles": sorted(READ_ROLES), "write_roles": sorted(WRITE_ROLES),
    }


def register(app_or_router: Any = None, service: Any = None) -> dict[str, Any]:
    target = service if service is not None else app_or_router
    _attach_store(target, "finance_assessment_store", FinanceAssessment)
    return _register_metadata(app_or_router, service, name="finance_assessment", routes=(ROUTE,), schema="finance_assessments")
