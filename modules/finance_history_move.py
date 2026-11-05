"""Persistent contract for ``/finance/history_move_student``.

The reference exposes a transfer-difference ledger.  The private API is not
available, so this module keeps the observed columns and Vietnamese status
values in a local SQLite table.  HTTP/router registration remains a coordinator
integration point because this worker cannot edit ``app.py``.
"""
from __future__ import annotations

import csv
import io
import sqlite3
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from modules.finance import _attach_store, _register_metadata

ROUTE = "/finance/history_move_student"
READ_ROLES = frozenset(("ADMIN", "STAFF", "TEACHER"))
WRITE_ROLES = frozenset(("ADMIN", "STAFF"))
STATUSES = ("Chưa thực hiện-Đã xếp lớp", "Đã xử lý", "Đã hủy")
TABLE_HEADERS = (
    "Học viên", "Khóa học ban đầu", "Khóa học chuyển đến", "Lớp học ban đầu",
    "Lớp học chuyển đến", "Còn lại", "Số buổi", "Giá tiền", "Tiền trả thêm",
    "Trạng thái", "Hành động",
)
SCHEMA = """
CREATE TABLE IF NOT EXISTS finance_history_moves (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_name TEXT NOT NULL,
  original_course_name TEXT NOT NULL,
  destination_course_name TEXT NOT NULL,
  original_class_name TEXT NOT NULL DEFAULT '',
  destination_class_name TEXT NOT NULL DEFAULT '',
  remaining_amount INTEGER NOT NULL DEFAULT 0 CHECK(remaining_amount >= 0),
  remaining_sessions INTEGER NOT NULL DEFAULT 0 CHECK(remaining_sessions >= 0),
  price_vnd INTEGER NOT NULL DEFAULT 0 CHECK(price_vnd >= 0),
  additional_amount INTEGER NOT NULL DEFAULT 0 CHECK(additional_amount >= 0),
  status TEXT NOT NULL DEFAULT 'Chưa thực hiện-Đã xếp lớp',
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_finance_history_moves_status ON finance_history_moves(status);
CREATE INDEX IF NOT EXISTS idx_finance_history_moves_student ON finance_history_moves(student_name);
"""


def _money(value: Any) -> int:
    try:
        amount = Decimal(str(value or 0).replace(",", "").replace(" VND", "").strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Số tiền không hợp lệ") from exc
    if amount < 0 or amount != amount.quantize(Decimal("1")):
        raise ValueError("Số tiền phải là số nguyên không âm")
    return int(amount)


def _text(value: Any, field: str, *, required: bool = False, limit: int = 200) -> str:
    result = str(value or "").strip()
    if required and not result:
        raise ValueError(f"{field} là bắt buộc")
    if len(result) > limit:
        raise ValueError(f"{field} quá dài")
    return result


class FinanceHistoryMove:
    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.db.commit()

    @staticmethod
    def _check_read(role: str) -> None:
        if role not in READ_ROLES:
            raise PermissionError("Lịch sử chuyển lớp không dành cho vai trò này")

    @staticmethod
    def _check_write(role: str) -> None:
        if role not in WRITE_ROLES:
            raise PermissionError("Chỉ ADMIN hoặc STAFF được quản lý lịch sử chuyển lớp")

    @staticmethod
    def _normalize(payload: Mapping[str, Any], existing: Mapping[str, Any] | None = None) -> dict[str, Any]:
        value = dict(existing or {}); value.update(payload)
        status = _text(value.get("status") or STATUSES[0], "Trạng thái")
        if status == "Tất cả":
            status = STATUSES[0]
        if status not in STATUSES:
            raise ValueError("Trạng thái chuyển lớp không hợp lệ")
        return {
            "student_name": _text(value.get("student_name"), "Học viên", required=True),
            "original_course_name": _text(value.get("original_course_name"), "Khóa học ban đầu", required=True),
            "destination_course_name": _text(value.get("destination_course_name"), "Khóa học chuyển đến", required=True),
            "original_class_name": _text(value.get("original_class_name"), "Lớp học ban đầu"),
            "destination_class_name": _text(value.get("destination_class_name"), "Lớp học chuyển đến"),
            "remaining_amount": _money(value.get("remaining_amount")),
            "remaining_sessions": _money(value.get("remaining_sessions")),
            "price_vnd": _money(value.get("price_vnd")),
            "additional_amount": _money(value.get("additional_amount")),
            "status": status,
        }

    def seed_demo(self, count: int = 8, actor: str = "Center Administrator") -> int:
        current = self.db.execute("SELECT COUNT(*) FROM finance_history_moves").fetchone()[0]
        for index in range(current, count):
            self.create({
                "student_name": f"Nguyễn Học viên chuyển lớp {index + 1:02d}",
                "original_course_name": "Tiếng Anh cơ bản 1",
                "destination_course_name": "IELTS Start",
                "original_class_name": f"Lớp CB1-{index + 1:02d}",
                "destination_class_name": f"Lớp IELTS-{index + 1:02d}",
                "remaining_amount": 2_000_000 + index * 100_000,
                "remaining_sessions": 8 + index,
                "price_vnd": 250_000,
                "additional_amount": index * 50_000,
                "status": STATUSES[index % len(STATUSES)],
            }, role="ADMIN", actor=actor)
        return self.db.execute("SELECT COUNT(*) FROM finance_history_moves").fetchone()[0]

    def list(self, filters: Mapping[str, Any] | None = None, *, role: str = "ADMIN", page: int = 1, page_size: int = 10) -> dict[str, Any]:
        self._check_read(role)
        filters = filters or {}
        page = max(int(page), 1); page_size = min(max(int(page_size), 1), 100)
        where, args = ["1=1"], []
        query = str(filters.get("q") or "").strip()
        if query:
            needle = f"%{query}%"
            where.append("(student_name LIKE ? OR original_course_name LIKE ? OR destination_course_name LIKE ? OR original_class_name LIKE ? OR destination_class_name LIKE ?)")
            args.extend([needle] * 5)
        status = str(filters.get("status") or "").strip()
        if status and status != "Tất cả":
            if status not in STATUSES:
                raise ValueError("Trạng thái lọc không hợp lệ")
            where.append("status = ?"); args.append(status)
        base = " FROM finance_history_moves WHERE " + " AND ".join(where)
        total = self.db.execute("SELECT COUNT(*)" + base, args).fetchone()[0]
        rows = self.db.execute("SELECT *" + base + " ORDER BY id DESC LIMIT ? OFFSET ?", args + [page_size, (page - 1) * page_size]).fetchall()
        return {"items": [dict(row) for row in rows], "total": total, "page": page, "page_size": page_size, "pages": (total + page_size - 1) // page_size}

    def create(self, payload: Mapping[str, Any], *, role: str, actor: str) -> dict[str, Any]:
        self._check_write(role); data = self._normalize(payload)
        now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        cur = self.db.execute(
            "INSERT INTO finance_history_moves(student_name,original_course_name,destination_course_name,original_class_name,destination_class_name,remaining_amount,remaining_sessions,price_vnd,additional_amount,status,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            tuple(data[key] for key in ("student_name", "original_course_name", "destination_course_name", "original_class_name", "destination_class_name", "remaining_amount", "remaining_sessions", "price_vnd", "additional_amount", "status")) + (_text(actor, "Người tạo", required=True), now, now),
        )
        self.db.commit()
        return dict(self.db.execute("SELECT * FROM finance_history_moves WHERE id=?", (cur.lastrowid,)).fetchone())

    def update(self, move_id: int, payload: Mapping[str, Any], *, role: str, actor: str) -> dict[str, Any]:
        self._check_write(role)
        current = self.db.execute("SELECT * FROM finance_history_moves WHERE id=?", (int(move_id),)).fetchone()
        if current is None:
            raise KeyError("Lịch sử chuyển lớp không tồn tại")
        data = self._normalize(payload, current)
        self.db.execute(
            "UPDATE finance_history_moves SET student_name=?,original_course_name=?,destination_course_name=?,original_class_name=?,destination_class_name=?,remaining_amount=?,remaining_sessions=?,price_vnd=?,additional_amount=?,status=?,updated_at=? WHERE id=?",
            tuple(data[key] for key in ("student_name", "original_course_name", "destination_course_name", "original_class_name", "destination_class_name", "remaining_amount", "remaining_sessions", "price_vnd", "additional_amount", "status")) + (datetime.utcnow().isoformat(timespec="seconds") + "Z", int(move_id)),
        )
        self.db.commit()
        return dict(self.db.execute("SELECT * FROM finance_history_moves WHERE id=?", (int(move_id),)).fetchone())

    def export_csv(self, filters: Mapping[str, Any] | None = None, *, role: str = "ADMIN") -> str:
        rows = self.list(filters, role=role, page=1, page_size=10000)["items"]
        out = io.StringIO(); writer = csv.writer(out); writer.writerow(TABLE_HEADERS)
        for row in rows:
            writer.writerow((row["student_name"], row["original_course_name"], row["destination_course_name"], row["original_class_name"], row["destination_class_name"], f'{row["remaining_amount"]:,} VND', row["remaining_sessions"], f'{row["price_vnd"]:,} VND', f'{row["additional_amount"]:,} VND', row["status"], ""))
        return "\ufeff" + out.getvalue()


def route_contract() -> dict[str, Any]:
    return {"route": ROUTE, "headers": TABLE_HEADERS, "filters": ("q", "status"), "tabs": ("Chuyển nhượng hợp đồng", "Chuyển nhượng khoản thu vật phẩm", "Danh sách hợp đồng chênh lệch phí khi chuyển lớp"), "status_options": ("Tất cả",) + STATUSES, "read_roles": sorted(READ_ROLES), "write_roles": sorted(WRITE_ROLES)}


def register(app_or_router: Any = None, service: Any = None) -> dict[str, Any]:
    target = service if service is not None else app_or_router
    _attach_store(target, "finance_history_move_store", FinanceHistoryMove)
    return _register_metadata(app_or_router, service, name="finance_history_move", routes=(ROUTE,), schema="finance_history_moves")


__all__ = ["FinanceHistoryMove", "ROUTE", "READ_ROLES", "WRITE_ROLES", "STATUSES", "TABLE_HEADERS", "route_contract", "register"]
