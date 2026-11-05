"""Persistent contract for ``/finance/transfer/index``."""
from __future__ import annotations

import csv
import io
import sqlite3
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from modules.finance import _attach_store, _register_metadata

ROUTE = "/finance/transfer/index"
READ_ROLES = frozenset(("ADMIN", "STAFF"))
WRITE_ROLES = frozenset(("ADMIN", "STAFF"))
STATUSES = ("PENDING", "PROCESSED", "CANCELLED")
STATUS_LABELS = {"PENDING": "Chưa xử lý", "PROCESSED": "Đã xử lý", "CANCELLED": "Đã hủy"}
TABLE_HEADERS = ("No.", "Mã chuyển nhượng", "Ngày chuyển nhượng", "Học viên chuyển", "Hợp đồng", "Khóa học", "Học viên nhận", "Số tiền nhận", "Ghi chú", "Action")
FILTERS = ("q",)

SCHEMA = """
CREATE TABLE IF NOT EXISTS finance_transfers (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 transfer_code TEXT NOT NULL UNIQUE,
 transfer_date TEXT NOT NULL,
 from_student_id INTEGER,
 from_student_name TEXT NOT NULL DEFAULT '',
 contract_id INTEGER,
 contract_code TEXT NOT NULL DEFAULT '',
 course_id INTEGER,
 course_name TEXT NOT NULL DEFAULT '',
 to_student_id INTEGER,
 to_student_name TEXT NOT NULL DEFAULT '',
 amount_received INTEGER NOT NULL DEFAULT 0 CHECK(amount_received >= 0),
 note TEXT NOT NULL DEFAULT '',
 status TEXT NOT NULL DEFAULT 'PENDING',
 created_by TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_finance_transfers_w2_date ON finance_transfers(transfer_date);
CREATE INDEX IF NOT EXISTS idx_finance_transfers_w2_status ON finance_transfers(status);
"""


def _day(value: Any) -> str:
    text = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError("Ngày chuyển nhượng không hợp lệ")


def _money(value: Any) -> int:
    try:
        n = Decimal(str(value or 0).replace(",", "").replace(" VND", "").strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Số tiền nhận không hợp lệ") from exc
    if n < 0 or n != n.quantize(Decimal("1")):
        raise ValueError("Số tiền nhận phải là số nguyên không âm")
    return int(n)


class FinanceTransfer:
    def __init__(self, db: sqlite3.Connection):
        self.db = db; self.db.row_factory = sqlite3.Row; self.db.executescript(SCHEMA)
        # The main application already owns a leaner finance_transfers table.
        # Add only the display columns this repository needs, preserving all
        # existing rows and constraints during coordinator wiring.
        existing = {row[1] for row in self.db.execute("PRAGMA table_info(finance_transfers)").fetchall()}
        additions = {
            "from_student_name": "TEXT NOT NULL DEFAULT ''", "contract_code": "TEXT NOT NULL DEFAULT ''",
            "course_name": "TEXT NOT NULL DEFAULT ''", "to_student_name": "TEXT NOT NULL DEFAULT ''",
        }
        for column, definition in additions.items():
            if column not in existing:
                self.db.execute(f"ALTER TABLE finance_transfers ADD COLUMN {column} {definition}")
        self.db.commit()

    @staticmethod
    def _read(role: str) -> None:
        if role not in READ_ROLES: raise PermissionError("Chuyển nhượng không dành cho vai trò này")

    @staticmethod
    def _write(role: str) -> None:
        if role not in WRITE_ROLES: raise PermissionError("Chỉ ADMIN hoặc STAFF được quản lý chuyển nhượng")

    def list(self, filters: Mapping[str, Any] | None = None, *, role: str = "ADMIN") -> list[dict[str, Any]]:
        self._read(role); filters = filters or {}; where, args = ["1=1"], []
        if filters.get("q"):
            q = f"%{str(filters['q']).strip()}%"; where.append("(transfer_code LIKE ? OR from_student_name LIKE ? OR to_student_name LIKE ? OR contract_code LIKE ? OR course_name LIKE ? OR note LIKE ?)"); args.extend([q] * 6)
        if filters.get("status"):
            status = str(filters["status"]).strip().upper()
            if status not in STATUSES: raise ValueError("Trạng thái chuyển nhượng không hợp lệ")
            where.append("status=?"); args.append(status)
        rows = self.db.execute("SELECT * FROM finance_transfers WHERE " + " AND ".join(where) + " ORDER BY transfer_date DESC,id DESC", args).fetchall()
        return [dict(row) for row in rows]

    def get(self, transfer_id: int, *, role: str = "ADMIN") -> dict[str, Any]:
        self._read(role); row = self.db.execute("SELECT * FROM finance_transfers WHERE id=?", (int(transfer_id),)).fetchone()
        if row is None: raise KeyError("Chuyển nhượng không tồn tại")
        return dict(row)

    def create(self, payload: Mapping[str, Any], *, role: str, actor: str) -> dict[str, Any]:
        self._write(role); code = str(payload.get("transfer_code") or "").strip().upper()
        if not code: raise ValueError("Mã chuyển nhượng là bắt buộc")
        status = str(payload.get("status") or "PENDING").strip().upper()
        if status not in STATUSES: raise ValueError("Trạng thái chuyển nhượng không hợp lệ")
        from_name = str(payload.get("from_student_name") or "").strip(); to_name = str(payload.get("to_student_name") or "").strip()
        if not from_name or not to_name: raise ValueError("Học viên chuyển và học viên nhận là bắt buộc")
        if from_name == to_name: raise ValueError("Học viên chuyển và học viên nhận phải khác nhau")
        now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        try:
            cur = self.db.execute("INSERT INTO finance_transfers(transfer_code,transfer_date,from_student_id,from_student_name,contract_id,contract_code,course_id,course_name,to_student_id,to_student_name,amount_received,note,status,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (code, _day(payload.get("transfer_date")), payload.get("from_student_id") or None, from_name, payload.get("contract_id") or None, str(payload.get("contract_code") or "").strip(), payload.get("course_id") or None, str(payload.get("course_name") or "").strip(), payload.get("to_student_id") or None, to_name, _money(payload.get("amount_received")), str(payload.get("note") or "").strip(), status, str(actor or "").strip(), now, now))
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            self.db.rollback(); raise ValueError("Mã chuyển nhượng đã tồn tại") from exc
        return self.get(cur.lastrowid, role=role)

    def update(self, transfer_id: int, payload: Mapping[str, Any], *, role: str, actor: str) -> dict[str, Any]:
        self._write(role); current = self.get(transfer_id, role=role); value = dict(current); value.update(payload)
        code = str(value.get("transfer_code") or "").strip().upper(); status = str(value.get("status") or "PENDING").strip().upper()
        if not code or status not in STATUSES: raise ValueError("Mã hoặc trạng thái chuyển nhượng không hợp lệ")
        from_name = str(value.get("from_student_name") or "").strip(); to_name = str(value.get("to_student_name") or "").strip()
        if not from_name or not to_name: raise ValueError("Học viên chuyển và học viên nhận là bắt buộc")
        if from_name == to_name: raise ValueError("Học viên chuyển và học viên nhận phải khác nhau")
        self.db.execute("UPDATE finance_transfers SET transfer_code=?,transfer_date=?,from_student_id=?,from_student_name=?,contract_id=?,contract_code=?,course_id=?,course_name=?,to_student_id=?,to_student_name=?,amount_received=?,note=?,status=?,updated_at=? WHERE id=?", (code, _day(value.get("transfer_date")), value.get("from_student_id") or None, from_name, value.get("contract_id") or None, str(value.get("contract_code") or "").strip(), value.get("course_id") or None, str(value.get("course_name") or "").strip(), value.get("to_student_id") or None, to_name, _money(value.get("amount_received")), str(value.get("note") or "").strip(), status, datetime.utcnow().isoformat(timespec="seconds") + "Z", int(transfer_id)))
        self.db.commit(); return self.get(transfer_id, role=role)

    def export_csv(self, filters: Mapping[str, Any] | None = None, *, role: str = "ADMIN") -> str:
        out = io.StringIO(); writer = csv.writer(out); writer.writerow(TABLE_HEADERS + ("Trạng thái",))
        for i, row in enumerate(self.list(filters, role=role), 1):
            writer.writerow([i, row["transfer_code"], row["transfer_date"], row["from_student_name"], row["contract_code"], row["course_name"], row["to_student_name"], f'{row["amount_received"]:,} VND', row["note"], "", STATUS_LABELS.get(row["status"], "")])
        return "\ufeff" + out.getvalue()


def route_contract() -> dict[str, Any]:
    return {"route": ROUTE, "headers": TABLE_HEADERS, "filters": FILTERS, "tabs": ("Chuyển nhượng hợp đồng", "Chuyển nhượng khoản thu vật phẩm", "Danh sách hợp đồng chênh lệch phí khi chuyển lớp"), "status_options": [(k, v) for k, v in STATUS_LABELS.items()], "read_roles": sorted(READ_ROLES), "write_roles": sorted(WRITE_ROLES)}


def register(app_or_router: Any = None, service: Any = None) -> dict[str, Any]:
    target = service if service is not None else app_or_router
    _attach_store(target, "finance_transfer_store", FinanceTransfer)
    return _register_metadata(app_or_router, service, name="finance_transfer", routes=(ROUTE,), schema="finance_transfers")


__all__ = ["FinanceTransfer", "ROUTE", "TABLE_HEADERS", "FILTERS", "STATUSES", "STATUS_LABELS", "route_contract", "register"]
