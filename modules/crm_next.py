"""CRM/Sale appointment-date local contract.

This module is intentionally isolated from ``app.py``.  The application registry can
wire the repository into the HTTP layer without importing any browser or reference
runtime.  It mirrors the observed ``/sale/appointment_date`` and
``/finance/appointment_date`` table contract and keeps persistence in SQLite.
"""
from __future__ import annotations

import csv
import io
import sqlite3
from datetime import date, datetime
from typing import Any, Iterable

ROUTE_ALIASES = ("/sale/appointment_date", "/finance/appointment_date")
ROLES = frozenset({"ADMIN", "STAFF", "TEACHER", "STUDENT"})
WRITE_ROLES = frozenset({"ADMIN", "STAFF"})
STATUSES = ("Chưa xử lý", "Đã xử lý", "Đã hủy")
APPOINTMENT_TYPES = ("Theo hóa đơn", "Theo hợp đồng")

TABLE_HEADERS = (
    "Trạng thái", "Học viên", "Phụ huynh", "Ngày hẹn", "Số tiền", "Ghi chú",
    "Kiểu/Mã", "Hợp đồng liên quan", "Công cụ",
)

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
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_finance_appointments_date
  ON finance_appointments(appointment_date);
CREATE INDEX IF NOT EXISTS idx_finance_appointments_status
  ON finance_appointments(status);
"""


class AppointmentRepository:
    """Durable CRUD/query boundary for payment appointments.

    The caller owns the connection lifecycle.  No credentials or session state are
    accepted by this class; role checks are explicit and fail closed.
    """

    def __init__(self, connection: sqlite3.Connection):
        self.db = connection
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def seed_demo(self, *, count: int = 12, actor: str = "Center Administrator") -> int:
        """Create idempotent synthetic appointments for rich local demo mode."""
        existing = self.db.execute("SELECT COUNT(*) FROM finance_appointments").fetchone()[0]
        if existing >= count:
            return existing
        for index in range(existing + 1, count + 1):
            self.create(
                role="ADMIN",
                student_name=f"Nguyễn Học viên {index:02d}",
                parent_name=f"Phụ huynh {index:02d}",
                appointment_date=f"2026-11-{min(index, 28):02d}",
                reference_code=f"HD-DEMO-{index:03d}",
                contract_code=f"HD-DEMO-{index:03d}",
                amount=1_000_000 + index * 75_000,
                note="Dữ liệu demo tổng hợp",
                appointment_type="Theo hợp đồng" if index % 2 else "Theo hóa đơn",
                created_by=actor,
            )
        return self.db.execute("SELECT COUNT(*) FROM finance_appointments").fetchone()[0]

    @staticmethod
    def _write_allowed(role: str) -> None:
        if role not in ROLES:
            raise ValueError("unknown role")
        if role not in WRITE_ROLES:
            raise PermissionError("appointment write requires ADMIN or STAFF")

    @staticmethod
    def _day(value: Any, label: str, *, required: bool = False) -> str | None:
        text = "" if value is None else str(value).strip()
        if not text:
            if required:
                raise ValueError(f"{label} là bắt buộc")
            return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(text, fmt).date().isoformat()
            except ValueError:
                continue
        raise ValueError(f"{label} phải theo dạng YYYY-MM-DD hoặc DD/MM/YYYY")

    @staticmethod
    def _amount(value: Any) -> int:
        try:
            amount = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Số tiền phải là số nguyên") from exc
        if amount < 0:
            raise ValueError("Số tiền không được âm")
        return amount

    def list(self, *, role: str, query: str = "", from_date: str = "",
             to_date: str = "", appointment_type: str = "Tất cả",
             limit: int = 10, offset: int = 0) -> list[dict[str, Any]]:
        if role not in ROLES:
            raise PermissionError("appointment read denied")
        limit = max(1, min(int(limit), 100))
        clauses, args = ["1=1"], []
        if query.strip():
            q = f"%{query.strip()}%"
            clauses.append("(student_name LIKE ? OR parent_name LIKE ? OR reference_code LIKE ? OR contract_code LIKE ?)")
            args.extend([q, q, q, q])
        start = self._day(from_date, "Từ ngày")
        end = self._day(to_date, "Đến ngày")
        if start and end and start > end:
            raise ValueError("Khoảng ngày lọc không hợp lệ")
        if start:
            clauses.append("appointment_date >= ?"); args.append(start)
        if end:
            clauses.append("appointment_date <= ?"); args.append(end)
        if appointment_type and appointment_type != "Tất cả":
            if appointment_type not in APPOINTMENT_TYPES:
                raise ValueError("Kiểu hẹn không hợp lệ")
            clauses.append("appointment_type = ?"); args.append(appointment_type)
        sql = "SELECT * FROM finance_appointments WHERE " + " AND ".join(clauses)
        sql += " ORDER BY appointment_date DESC, id DESC LIMIT ? OFFSET ?"
        args.extend([limit, max(0, int(offset))])
        return [dict(r) for r in self.db.execute(sql, args).fetchall()]

    def create(self, *, role: str, student_name: str, appointment_date: str,
               reference_code: str, amount: int = 0, parent_name: str = "",
               note: str = "", appointment_type: str = "Theo hóa đơn",
               contract_code: str = "", created_by: str = "system") -> dict[str, Any]:
        self._write_allowed(role)
        if not str(student_name or "").strip() or not str(reference_code or "").strip():
            raise ValueError("student_name, appointment_date and reference_code are required")
        day = self._day(appointment_date, "Ngày hẹn", required=True)
        if appointment_type not in APPOINTMENT_TYPES:
            raise ValueError("Kiểu hẹn không hợp lệ")
        cur = self.db.execute(
            "INSERT INTO finance_appointments(status,student_name,parent_name,appointment_date,amount,note,appointment_type,reference_code,contract_code,created_by) VALUES(?,?,?,?,?,?,?,?,?,?)",
            ("Chưa xử lý", str(student_name).strip(), str(parent_name or "").strip(), day, self._amount(amount), str(note or "").strip(), appointment_type, str(reference_code).strip(), str(contract_code or "").strip(), str(created_by or "").strip() or "system"),
        )
        self.db.commit()
        return dict(self.db.execute("SELECT * FROM finance_appointments WHERE id=?", (cur.lastrowid,)).fetchone())

    def update(self, appointment_id: int, *, role: str, **changes: Any) -> dict[str, Any]:
        self._write_allowed(role)
        allowed = {"status", "student_name", "parent_name", "appointment_date", "amount", "note", "appointment_type", "reference_code", "contract_code"}
        unknown = sorted(set(changes) - allowed)
        if unknown:
            raise ValueError("Trường lịch hẹn không được hỗ trợ: " + ", ".join(unknown))
        values = dict(changes)
        if not values:
            raise ValueError("no editable fields")
        current = self.db.execute("SELECT * FROM finance_appointments WHERE id=?", (int(appointment_id),)).fetchone()
        if current is None:
            raise KeyError("appointment not found")
        merged = dict(current)
        merged.update(values)
        merged["student_name"] = str(merged.get("student_name") or "").strip()
        merged["reference_code"] = str(merged.get("reference_code") or "").strip()
        if not merged["student_name"] or not merged["reference_code"]:
            raise ValueError("student_name and reference_code are required")
        merged["appointment_date"] = self._day(merged.get("appointment_date"), "Ngày hẹn", required=True)
        if merged.get("status") not in STATUSES:
            raise ValueError("Trạng thái không hợp lệ")
        if merged.get("appointment_type") not in APPOINTMENT_TYPES:
            raise ValueError("Kiểu hẹn không hợp lệ")
        merged["amount"] = self._amount(merged.get("amount"))
        merged["parent_name"] = str(merged.get("parent_name") or "").strip()
        merged["note"] = str(merged.get("note") or "").strip()
        merged["contract_code"] = str(merged.get("contract_code") or "").strip()
        columns = ("status", "student_name", "parent_name", "appointment_date", "amount", "note", "appointment_type", "reference_code", "contract_code")
        assignments = ", ".join(f"{column}=?" for column in columns) + ", updated_at=CURRENT_TIMESTAMP"
        args = [merged[column] for column in columns] + [appointment_id]
        cur = self.db.execute(f"UPDATE finance_appointments SET {assignments} WHERE id=?", args)
        if cur.rowcount != 1: raise KeyError("appointment not found")
        self.db.commit()
        return dict(self.db.execute("SELECT * FROM finance_appointments WHERE id=?", (appointment_id,)).fetchone())

    def export_csv(self, *, role: str, **filters: Any) -> str:
        rows = self.list(role=role, limit=10000, **filters)
        out = io.StringIO(); writer = csv.writer(out); writer.writerow(TABLE_HEADERS)
        for row in rows:
            writer.writerow([row["status"], row["student_name"], row["parent_name"], row["appointment_date"], f"{row['amount']:,} VND", row["note"], f"{row['appointment_type']} / {row['reference_code']}", row["contract_code"], "..."])
        return out.getvalue()


def route_contract() -> dict[str, Any]:
    return {"routes": ROUTE_ALIASES, "headers": TABLE_HEADERS, "filters": ["query", "from_date", "to_date", "appointment_type"], "page_sizes": [10, 25, 50, 100], "write_roles": sorted(WRITE_ROLES)}
