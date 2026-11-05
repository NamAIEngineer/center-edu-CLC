"""Persistent contract for ``/finance/appointment_date``."""
from __future__ import annotations

import csv
import io
import sqlite3
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from modules.finance import _attach_store, _register_metadata

ROUTE = "/finance/appointment_date"
ROUTE_ALIASES = ("/finance/appointment_date", "/sale/appointment_date")
READ_ROLES = frozenset(("ADMIN", "STAFF", "TEACHER", "STUDENT"))
WRITE_ROLES = frozenset(("ADMIN", "STAFF"))
STATUSES = ("Chưa xử lý", "Đã xử lý", "Đã hủy")
APPOINTMENT_TYPES = ("Theo hóa đơn", "Theo hợp đồng")
TABLE_HEADERS = ("Trạng thái", "Học viên", "Phụ huynh", "Ngày hẹn", "Số tiền", "Ghi chú", "Kiểu/Mã", "Hợp đồng liên quan", "Công cụ")
FILTERS = ("q", "date_from", "date_to", "appointment_type")

SCHEMA = """
CREATE TABLE IF NOT EXISTS finance_appointments (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 status TEXT NOT NULL DEFAULT 'Chưa xử lý',
 student_name TEXT NOT NULL,
 parent_name TEXT NOT NULL DEFAULT '',
 appointment_date TEXT NOT NULL,
 amount INTEGER NOT NULL DEFAULT 0 CHECK(amount >= 0),
 note TEXT NOT NULL DEFAULT '',
 appointment_type TEXT NOT NULL DEFAULT 'Theo hóa đơn',
 reference_code TEXT NOT NULL,
 contract_code TEXT NOT NULL DEFAULT '',
 created_by TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_finance_appointments_w2_date ON finance_appointments(appointment_date);
CREATE INDEX IF NOT EXISTS idx_finance_appointments_w2_type ON finance_appointments(appointment_type);
"""


def _day(value: Any) -> str:
    text = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try: return datetime.strptime(text, fmt).date().isoformat()
        except ValueError: continue
    raise ValueError("Ngày hẹn không hợp lệ")


def _money(value: Any) -> int:
    try: n = Decimal(str(value or 0).replace(",", "").replace(" VND", "").strip())
    except (InvalidOperation, ValueError) as exc: raise ValueError("Số tiền không hợp lệ") from exc
    if n < 0 or n != n.quantize(Decimal("1")): raise ValueError("Số tiền phải là số nguyên không âm")
    return int(n)


class FinanceAppointment:
    def __init__(self, db: sqlite3.Connection):
        self.db = db; self.db.row_factory = sqlite3.Row; self.db.executescript(SCHEMA); self.db.commit()

    @staticmethod
    def _read(role: str) -> None:
        if role not in READ_ROLES: raise PermissionError("Lịch hẹn đóng tiền không dành cho vai trò này")

    @staticmethod
    def _write(role: str) -> None:
        if role not in WRITE_ROLES: raise PermissionError("Chỉ ADMIN hoặc STAFF được quản lý lịch hẹn")

    def list(self, filters: Mapping[str, Any] | None = None, *, role: str = "ADMIN", page: int = 1, page_size: int = 10) -> dict[str, Any]:
        self._read(role); filters = filters or {}; page, page_size = max(int(page), 1), min(max(int(page_size), 1), 100); where, args = ["1=1"], []
        if filters.get("q"):
            q = f"%{str(filters['q']).strip()}%"; where.append("(student_name LIKE ? OR parent_name LIKE ? OR reference_code LIKE ? OR contract_code LIKE ?)"); args.extend([q] * 4)
        for key, op in (("date_from", ">="), ("date_to", "<=")):
            if filters.get(key): where.append(f"appointment_date {op} ?"); args.append(_day(filters[key]))
        if filters.get("appointment_type"):
            value = str(filters["appointment_type"]).strip()
            if value not in APPOINTMENT_TYPES: raise ValueError("Kiểu hẹn không hợp lệ")
            where.append("appointment_type=?"); args.append(value)
        base = " FROM finance_appointments WHERE " + " AND ".join(where); total = self.db.execute("SELECT COUNT(*)" + base, args).fetchone()[0]
        rows = self.db.execute("SELECT *" + base + " ORDER BY appointment_date DESC,id DESC LIMIT ? OFFSET ?", args + [page_size, (page - 1) * page_size]).fetchall()
        return {"items": [dict(row) for row in rows], "total": int(total), "page": page, "page_size": page_size, "pages": (int(total) + page_size - 1) // page_size}

    def get(self, appointment_id: int, *, role: str = "ADMIN") -> dict[str, Any]:
        self._read(role); row = self.db.execute("SELECT * FROM finance_appointments WHERE id=?", (int(appointment_id),)).fetchone()
        if row is None: raise KeyError("Lịch hẹn không tồn tại")
        return dict(row)

    def create(self, payload: Mapping[str, Any], *, role: str, actor: str) -> dict[str, Any]:
        self._write(role); student = str(payload.get("student_name") or "").strip(); reference = str(payload.get("reference_code") or payload.get("contract_code") or "").strip(); appointment_type = str(payload.get("appointment_type") or "Theo hóa đơn").strip()
        if not student or not reference: raise ValueError("Học viên và mã tham chiếu là bắt buộc")
        if appointment_type not in APPOINTMENT_TYPES: raise ValueError("Kiểu hẹn không hợp lệ")
        status = str(payload.get("status") or "Chưa xử lý").strip()
        if status not in STATUSES: raise ValueError("Trạng thái lịch hẹn không hợp lệ")
        now = datetime.utcnow().isoformat(timespec="seconds") + "Z"; cur = self.db.execute("INSERT INTO finance_appointments(status,student_name,parent_name,appointment_date,amount,note,appointment_type,reference_code,contract_code,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (status, student, str(payload.get("parent_name") or "").strip(), _day(payload.get("appointment_date")), _money(payload.get("amount")), str(payload.get("note") or "").strip(), appointment_type, reference, str(payload.get("contract_code") or "").strip(), str(actor or "").strip(), now, now)); self.db.commit(); return self.get(cur.lastrowid, role=role)

    def update(self, appointment_id: int, payload: Mapping[str, Any], *, role: str, actor: str) -> dict[str, Any]:
        self._write(role); current = self.get(appointment_id, role=role); value = dict(current); value.update(payload); return self._update_values(appointment_id, value, role=role)

    def _update_values(self, appointment_id: int, value: Mapping[str, Any], *, role: str) -> dict[str, Any]:
        status = str(value.get("status") or "Chưa xử lý").strip(); appointment_type = str(value.get("appointment_type") or "Theo hóa đơn").strip()
        if status not in STATUSES or appointment_type not in APPOINTMENT_TYPES: raise ValueError("Trạng thái hoặc kiểu hẹn không hợp lệ")
        student_name = str(value.get("student_name") or "").strip()
        reference_code = str(value.get("reference_code") or value.get("contract_code") or "").strip()
        if not student_name or not reference_code:
            raise ValueError("Học viên và mã tham chiếu là bắt buộc")
        self.db.execute("UPDATE finance_appointments SET status=?,student_name=?,parent_name=?,appointment_date=?,amount=?,note=?,appointment_type=?,reference_code=?,contract_code=?,updated_at=? WHERE id=?", (status, student_name, str(value.get("parent_name") or "").strip(), _day(value.get("appointment_date")), _money(value.get("amount")), str(value.get("note") or "").strip(), appointment_type, reference_code, str(value.get("contract_code") or "").strip(), datetime.utcnow().isoformat(timespec="seconds") + "Z", int(appointment_id))); self.db.commit(); return self.get(appointment_id, role=role)

    def export_csv(self, filters: Mapping[str, Any] | None = None, *, role: str = "ADMIN") -> str:
        rows = self.list(filters, role=role, page=1, page_size=10000)["items"]; out = io.StringIO(); writer = csv.writer(out); writer.writerow(TABLE_HEADERS)
        for row in rows: writer.writerow([row["status"], row["student_name"], row["parent_name"], row["appointment_date"], f'{row["amount"]:,} VND', row["note"], f'{row["appointment_type"]} / {row["reference_code"]}', row["contract_code"], ""])
        return "\ufeff" + out.getvalue()


def route_contract() -> dict[str, Any]:
    return {"routes": ROUTE_ALIASES, "headers": TABLE_HEADERS, "filters": FILTERS, "status_options": STATUSES, "appointment_type_options": APPOINTMENT_TYPES, "page_sizes": (10, 25, 50, 100), "read_roles": sorted(READ_ROLES), "write_roles": sorted(WRITE_ROLES)}


def register(app_or_router: Any = None, service: Any = None) -> dict[str, Any]:
    target = service if service is not None else app_or_router
    _attach_store(target, "finance_appointment_contract_store", FinanceAppointment)
    return _register_metadata(app_or_router, service, name="finance_appointment", routes=ROUTE_ALIASES, schema="finance_appointments")


__all__ = ["FinanceAppointment", "ROUTE", "ROUTE_ALIASES", "TABLE_HEADERS", "FILTERS", "STATUSES", "APPOINTMENT_TYPES", "route_contract", "register"]
