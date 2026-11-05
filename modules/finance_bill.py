"""Persistent contract for ``/finance/bill/index``.

The service layer may use its existing ``finance_bills`` table directly.  This
repository mirrors that shape, adds strict validation, and keeps all display
labels Vietnamese at the route boundary.  It is safe to initialise against an
empty SQLite database or an existing Center EDU database.
"""
from __future__ import annotations

import csv
import io
import sqlite3
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from modules.finance import _attach_store, _register_metadata

ROUTE = "/finance/bill/index"
READ_ROLES = frozenset(("ADMIN", "STAFF"))
WRITE_ROLES = frozenset(("ADMIN", "STAFF"))
CONFIRMATION_STATUSES = ("PENDING", "CONFIRMED", "REJECTED")
CONFIRMATION_LABELS = {
    "PENDING": "Cần xác nhận", "CONFIRMED": "Đã xác nhận", "REJECTED": "Không đồng ý",
}
PAYMENT_METHOD_LABELS = {
    "cash": "Tiền mặt", "bank_transfer": "Chuyển khoản", "card": "Quẹt thẻ",
    "wallet": "Ví CO", "installment": "Trả góp", "": "",
}
TABLE_HEADERS = (
    "No.", "Mã hóa đơn", "Mã hợp đồng", "Lớp học", "Đối tượng", "Khách hàng",
    "Thanh toán", "Nhân viên sale", "Người tạo", "Trạng thái xác nhận",
    "Hình thức thanh toán", "Ghi chú", "Công cụ",
)
FILTERS = ("q", "creator", "date_from", "date_to", "center", "branch", "employee", "confirmation_status")

SCHEMA = """
CREATE TABLE IF NOT EXISTS finance_bills (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  invoice_code TEXT NOT NULL UNIQUE,
  contract_code TEXT NOT NULL DEFAULT '',
  class_code TEXT NOT NULL DEFAULT '',
  subject TEXT NOT NULL DEFAULT '',
  customer_name TEXT NOT NULL DEFAULT '',
  payment_amount INTEGER,
  sales_owner TEXT NOT NULL DEFAULT '',
  created_by TEXT NOT NULL DEFAULT '',
  center TEXT NOT NULL DEFAULT '',
  branch TEXT NOT NULL DEFAULT '',
  employee TEXT NOT NULL DEFAULT '',
  confirmation_status TEXT NOT NULL DEFAULT 'PENDING',
  payment_method TEXT NOT NULL DEFAULT '',
  note TEXT NOT NULL DEFAULT '',
  invoice_date TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_finance_bills_date_w2 ON finance_bills(invoice_date);
CREATE INDEX IF NOT EXISTS idx_finance_bills_status_w2 ON finance_bills(confirmation_status);
"""


def _text(value: Any, field: str, *, required: bool = False, limit: int = 300) -> str:
    result = str(value or "").strip()
    if required and not result:
        raise ValueError(f"{field} là bắt buộc")
    if len(result) > limit:
        raise ValueError(f"{field} quá dài")
    return result


def _day(value: Any, field: str, *, required: bool = False) -> str | None:
    text = str(value or "").strip()
    if not text:
        if required:
            raise ValueError(f"{field} là bắt buộc")
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"{field} không hợp lệ")


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


def confirmation_label(value: Any) -> str:
    return CONFIRMATION_LABELS.get(str(value or ""), "")


def payment_method_label(value: Any) -> str:
    return PAYMENT_METHOD_LABELS.get(str(value or ""), str(value or ""))


class FinanceBill:
    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.db.commit()

    @staticmethod
    def _read(role: str) -> None:
        if role not in READ_ROLES:
            raise PermissionError("Hóa đơn không dành cho vai trò này")

    @staticmethod
    def _write(role: str) -> None:
        if role not in WRITE_ROLES:
            raise PermissionError("Chỉ ADMIN hoặc STAFF được quản lý hóa đơn")

    def _normalize(self, payload: Mapping[str, Any], current: Mapping[str, Any] | None = None) -> dict[str, Any]:
        value = dict(current or {}); value.update(payload)
        status = str(value.get("confirmation_status") or "PENDING").strip().upper()
        if status not in CONFIRMATION_STATUSES:
            raise ValueError("Trạng thái xác nhận không hợp lệ")
        return {
            "invoice_code": _text(value.get("invoice_code"), "Mã hóa đơn", required=True, limit=80).upper(),
            "contract_code": _text(value.get("contract_code"), "Mã hợp đồng", limit=80),
            "class_code": _text(value.get("class_code"), "Lớp học", limit=120),
            "subject": _text(value.get("subject"), "Đối tượng", limit=120),
            "customer_name": _text(value.get("customer_name"), "Khách hàng", limit=240),
            "payment_amount": _money(value.get("payment_amount"), "Thanh toán"),
            "sales_owner": _text(value.get("sales_owner"), "Nhân viên sale", limit=180),
            "center": _text(value.get("center"), "Trung tâm", limit=180),
            "branch": _text(value.get("branch"), "Chi nhánh", limit=180),
            "employee": _text(value.get("employee"), "Nhân viên", limit=180),
            "confirmation_status": status,
            "payment_method": _text(value.get("payment_method"), "Hình thức thanh toán", limit=60),
            "note": _text(value.get("note"), "Ghi chú", limit=1000),
            "invoice_date": _day(value.get("invoice_date"), "Ngày hóa đơn"),
        }

    def list(self, filters: Mapping[str, Any] | None = None, *, role: str = "ADMIN") -> list[dict[str, Any]]:
        self._read(role); filters = filters or {}; where, args = ["1=1"], []
        if filters.get("q"):
            q = f"%{str(filters['q']).strip()}%"; where.append("(invoice_code LIKE ? OR contract_code LIKE ? OR class_code LIKE ? OR subject LIKE ? OR customer_name LIKE ? OR sales_owner LIKE ? OR note LIKE ?)"); args.extend([q] * 7)
        if filters.get("creator"):
            where.append("CAST(created_by AS TEXT) LIKE ?"); args.append(f"%{str(filters['creator']).strip()}%")
        if filters.get("confirmation_status"):
            status = str(filters["confirmation_status"]).strip().upper()
            if status not in CONFIRMATION_STATUSES:
                raise ValueError("Trạng thái xác nhận không hợp lệ")
            where.append("confirmation_status = ?"); args.append(status)
        for key, op in (("date_from", ">="), ("date_to", "<=")):
            if filters.get(key):
                where.append(f"invoice_date {op} ?"); args.append(_day(filters[key], key, required=True))
        for key in ("center", "branch", "employee"):
            if filters.get(key):
                where.append(f"{key} LIKE ?"); args.append(f"%{str(filters[key]).strip()}%")
        rows = self.db.execute("SELECT * FROM finance_bills WHERE " + " AND ".join(where) + " ORDER BY COALESCE(invoice_date, created_at) DESC, id DESC", args).fetchall()
        return [dict(row) for row in rows]

    def get(self, bill_id: int, *, role: str = "ADMIN") -> dict[str, Any]:
        self._read(role); row = self.db.execute("SELECT * FROM finance_bills WHERE id = ?", (int(bill_id),)).fetchone()
        if row is None:
            raise KeyError("Hóa đơn không tồn tại")
        return dict(row)

    def create(self, payload: Mapping[str, Any], *, role: str, actor: str) -> dict[str, Any]:
        self._write(role); data = self._normalize(payload)
        try:
            cur = self.db.execute("""INSERT INTO finance_bills(invoice_code,contract_code,class_code,subject,customer_name,payment_amount,sales_owner,created_by,center,branch,employee,confirmation_status,payment_method,note,invoice_date) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (data["invoice_code"], data["contract_code"], data["class_code"], data["subject"], data["customer_name"], data["payment_amount"], data["sales_owner"], _text(actor, "Người tạo", required=True, limit=180), data["center"], data["branch"], data["employee"], data["confirmation_status"], data["payment_method"], data["note"], data["invoice_date"]))
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            self.db.rollback(); raise ValueError("Mã hóa đơn đã tồn tại") from exc
        return self.get(cur.lastrowid, role=role)

    def update(self, bill_id: int, payload: Mapping[str, Any], *, role: str, actor: str) -> dict[str, Any]:
        self._write(role); current = self.get(bill_id, role=role); data = self._normalize(payload, current)
        self.db.execute("""UPDATE finance_bills SET invoice_code=?,contract_code=?,class_code=?,subject=?,customer_name=?,payment_amount=?,sales_owner=?,center=?,branch=?,employee=?,confirmation_status=?,payment_method=?,note=?,invoice_date=?,updated_at=CURRENT_TIMESTAMP WHERE id=?""", (data["invoice_code"], data["contract_code"], data["class_code"], data["subject"], data["customer_name"], data["payment_amount"], data["sales_owner"], data["center"], data["branch"], data["employee"], data["confirmation_status"], data["payment_method"], data["note"], data["invoice_date"], int(bill_id)))
        self.db.commit(); return self.get(bill_id, role=role)

    def confirm(self, bill_id: int, *, role: str, actor: str) -> dict[str, Any]:
        self._write(role); current = self.get(bill_id, role=role)
        if current["confirmation_status"] == "REJECTED":
            raise ValueError("Hóa đơn đã bị từ chối")
        self.db.execute("UPDATE finance_bills SET confirmation_status='CONFIRMED',updated_at=CURRENT_TIMESTAMP WHERE id=?", (int(bill_id),)); self.db.commit()
        return self.get(bill_id, role=role)

    def export_csv(self, filters: Mapping[str, Any] | None = None, *, role: str = "ADMIN") -> str:
        out = io.StringIO(); writer = csv.writer(out); writer.writerow(TABLE_HEADERS)
        for index, row in enumerate(self.list(filters, role=role), 1):
            writer.writerow([index, row["invoice_code"], row["contract_code"], row["class_code"], row["subject"], row["customer_name"], f"{int(row['payment_amount'] or 0):,} VND" if row["payment_amount"] is not None else "", row["sales_owner"], row["created_by"], confirmation_label(row["confirmation_status"]), payment_method_label(row["payment_method"]), row["note"], ""])
        return "\ufeff" + out.getvalue()


def route_contract() -> dict[str, Any]:
    return {"route": ROUTE, "headers": TABLE_HEADERS, "filters": FILTERS, "tabs": ("Hóa đơn đóng tiền", "Hóa đơn đóng tiền trước", "Hóa đơn online"), "confirmation_status_options": [(k, v) for k, v in CONFIRMATION_LABELS.items()], "read_roles": sorted(READ_ROLES), "write_roles": sorted(WRITE_ROLES)}


def register(app_or_router: Any = None, service: Any = None) -> dict[str, Any]:
    target = service if service is not None else app_or_router
    _attach_store(target, "finance_bill_store", FinanceBill)
    return _register_metadata(app_or_router, service, name="finance_bill", routes=(ROUTE,), schema="finance_bills")


__all__ = ["FinanceBill", "ROUTE", "TABLE_HEADERS", "FILTERS", "CONFIRMATION_STATUSES", "CONFIRMATION_LABELS", "PAYMENT_METHOD_LABELS", "confirmation_label", "payment_method_label", "route_contract", "register"]
