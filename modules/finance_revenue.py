"""Persistent CRUD contract for ``/finance/revenue`` (Khoản thu tài chính)."""
from __future__ import annotations

import csv
import io
import sqlite3
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from modules.finance import _attach_store, _register_metadata

ROUTE = "/finance/revenue"
READ_ROLES = frozenset(("ADMIN", "STAFF"))
WRITE_ROLES = frozenset(("ADMIN", "STAFF"))
STATUSES = ("ACTIVE", "INACTIVE")
STATUS_LABELS = {"ACTIVE": "Kích hoạt", "INACTIVE": "Tạm khóa"}
DISCOUNT_TYPES = ("", "FIXED", "PERCENT")
DISCOUNT_LABELS = {"": "Không giảm", "FIXED": "Theo tiền", "PERCENT": "%"}
TABLE_HEADERS = ("No.", "Mã", "Tên", "Trạng thái", "Giá", "Kiểu giảm", "Giá trị giảm", "Giá phải thu", "Trung tâm", "Ghi chú", "Công cụ")
FILTERS = ("q", "status", "center")

SCHEMA = """
CREATE TABLE IF NOT EXISTS finance_revenues (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 code TEXT NOT NULL UNIQUE,
 name TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'ACTIVE',
 price INTEGER,
 discount_type TEXT NOT NULL DEFAULT '',
 discount_value INTEGER,
 amount_due INTEGER,
 center TEXT NOT NULL DEFAULT '',
 note TEXT NOT NULL DEFAULT '',
 created_by TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_finance_revenues_status_w2 ON finance_revenues(status);
CREATE INDEX IF NOT EXISTS idx_finance_revenues_center_w2 ON finance_revenues(center);
"""


def _money(value: Any, field: str, *, default: int | None = None) -> int | None:
    if value in (None, ""):
        return default
    try:
        amount = Decimal(str(value).replace(",", "").replace(" VND", "").strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field} không hợp lệ") from exc
    if amount < 0 or amount != amount.quantize(Decimal("1")):
        raise ValueError(f"{field} phải là số nguyên không âm")
    return int(amount)


class FinanceRevenue:
    def __init__(self, db: sqlite3.Connection):
        self.db = db; self.db.row_factory = sqlite3.Row; self.db.executescript(SCHEMA); self.db.commit()

    @staticmethod
    def _read(role: str) -> None:
        if role not in READ_ROLES: raise PermissionError("Khoản thu không dành cho vai trò này")

    @staticmethod
    def _write(role: str) -> None:
        if role not in WRITE_ROLES: raise PermissionError("Chỉ ADMIN hoặc STAFF được quản lý khoản thu")

    @staticmethod
    def _normalize(payload: Mapping[str, Any], current: Mapping[str, Any] | None = None) -> dict[str, Any]:
        value = dict(current or {}); value.update(payload)
        code = str(value.get("code") or "").strip().upper(); name = str(value.get("name") or value.get("fullname") or "").strip()
        status = str(value.get("status") or "ACTIVE").strip().upper(); discount_type = str(value.get("discount_type") or "").strip().upper()
        if not code or not name: raise ValueError("Mã và tên khoản thu là bắt buộc")
        if status not in STATUSES: raise ValueError("Trạng thái khoản thu không hợp lệ")
        if discount_type not in DISCOUNT_TYPES: raise ValueError("Kiểu giảm không hợp lệ")
        discount_value = _money(value.get("discount_value"), "Giá trị giảm")
        if discount_type == "PERCENT" and discount_value is not None and discount_value > 100: raise ValueError("Phần trăm giảm không được lớn hơn 100")
        return {"code": code, "name": name, "status": status, "price": _money(value.get("price") or value.get("total_price"), "Giá"), "discount_type": discount_type, "discount_value": discount_value, "amount_due": _money(value.get("amount_due") or value.get("net_price"), "Giá phải thu"), "center": str(value.get("center") or "").strip(), "note": str(value.get("note") or "").strip()}

    def list(self, filters: Mapping[str, Any] | None = None, *, role: str = "ADMIN") -> list[dict[str, Any]]:
        self._read(role); filters = filters or {}; clauses, args = ["1=1"], []
        if filters.get("q"):
            q = f"%{str(filters['q']).strip()}%"; clauses.append("(code LIKE ? OR name LIKE ? OR note LIKE ?)"); args.extend([q, q, q])
        if filters.get("status"):
            status = str(filters["status"]).strip().upper()
            if status not in STATUSES: raise ValueError("Trạng thái khoản thu không hợp lệ")
            clauses.append("status=?"); args.append(status)
        if filters.get("center"): clauses.append("center LIKE ?"); args.append(f"%{str(filters['center']).strip()}%")
        return [dict(row) for row in self.db.execute("SELECT * FROM finance_revenues WHERE " + " AND ".join(clauses) + " ORDER BY id DESC", args).fetchall()]

    def get(self, revenue_id: int, *, role: str = "ADMIN") -> dict[str, Any]:
        self._read(role); row = self.db.execute("SELECT * FROM finance_revenues WHERE id=?", (int(revenue_id),)).fetchone()
        if row is None: raise KeyError("Khoản thu không tồn tại")
        return dict(row)

    def create(self, payload: Mapping[str, Any], *, role: str, actor: str) -> dict[str, Any]:
        self._write(role); data = self._normalize(payload); now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        try:
            cur = self.db.execute("INSERT INTO finance_revenues(code,name,status,price,discount_type,discount_value,amount_due,center,note,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (data["code"], data["name"], data["status"], data["price"], data["discount_type"], data["discount_value"], data["amount_due"], data["center"], data["note"], str(actor or "").strip(), now, now)); self.db.commit()
        except sqlite3.IntegrityError as exc: self.db.rollback(); raise ValueError("Mã khoản thu đã tồn tại") from exc
        return self.get(cur.lastrowid, role=role)

    def update(self, revenue_id: int, payload: Mapping[str, Any], *, role: str, actor: str) -> dict[str, Any]:
        self._write(role); current = self.get(revenue_id, role=role); data = self._normalize(payload, current)
        self.db.execute("UPDATE finance_revenues SET code=?,name=?,status=?,price=?,discount_type=?,discount_value=?,amount_due=?,center=?,note=?,updated_at=? WHERE id=?", (data["code"], data["name"], data["status"], data["price"], data["discount_type"], data["discount_value"], data["amount_due"], data["center"], data["note"], datetime.utcnow().isoformat(timespec="seconds") + "Z", int(revenue_id))); self.db.commit(); return self.get(revenue_id, role=role)

    def delete(self, revenue_id: int, *, role: str) -> None:
        self._write(role); self.get(revenue_id, role=role); self.db.execute("DELETE FROM finance_revenues WHERE id=?", (int(revenue_id),)); self.db.commit()

    def export_csv(self, filters: Mapping[str, Any] | None = None, *, role: str = "ADMIN") -> str:
        out = io.StringIO(); writer = csv.writer(out); writer.writerow(TABLE_HEADERS)
        for i, row in enumerate(self.list(filters, role=role), 1):
            writer.writerow([i, row["code"], row["name"], STATUS_LABELS.get(row["status"], ""), f'{row["price"]:,} VND' if row["price"] is not None else "", DISCOUNT_LABELS.get(row["discount_type"], ""), f'{row["discount_value"]:,} ' + ("%" if row["discount_type"] == "PERCENT" else "VND") if row["discount_value"] is not None else "", f'{row["amount_due"]:,} VND' if row["amount_due"] is not None else "", row["center"], row["note"], ""])
        return "\ufeff" + out.getvalue()


def route_contract() -> dict[str, Any]:
    return {"route": ROUTE, "headers": TABLE_HEADERS, "filters": FILTERS, "status_options": [(k, v) for k, v in STATUS_LABELS.items()], "discount_options": [(k, v) for k, v in DISCOUNT_LABELS.items()], "read_roles": sorted(READ_ROLES), "write_roles": sorted(WRITE_ROLES)}


def register(app_or_router: Any = None, service: Any = None) -> dict[str, Any]:
    target = service if service is not None else app_or_router
    _attach_store(target, "finance_revenue_store", FinanceRevenue)
    return _register_metadata(app_or_router, service, name="finance_revenue", routes=(ROUTE,), schema="finance_revenues")


__all__ = ["FinanceRevenue", "ROUTE", "TABLE_HEADERS", "FILTERS", "STATUSES", "STATUS_LABELS", "DISCOUNT_TYPES", "DISCOUNT_LABELS", "route_contract", "register"]
