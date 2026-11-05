"""Persistent local contract for ``/finance/bill/debit_item/index``.

Disjoint module: app integration may import ``DebitItemRepository`` and expose the
listed route.  It does not depend on the reference site or browser state.
"""
from __future__ import annotations

import csv
import io
import sqlite3
from typing import Any

from modules.finance import _attach_store, _register_metadata

ROUTE = "/finance/bill/debit_item/index"
ROLES = frozenset({"ADMIN", "STAFF", "TEACHER", "STUDENT"})
WRITE_ROLES = frozenset({"ADMIN", "STAFF"})
STATUSES = frozenset({"Chưa trả", "Đã trả"})
TABLE_HEADERS = ("No.", "Hóa đơn", "Ngày xuất HĐ", "Khách hàng", "Vật phẩm nợ", "Số lượng", "Tổng tiền", "Trạng thái", "Action")

SCHEMA = """
CREATE TABLE IF NOT EXISTS finance_debit_items (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 invoice_code TEXT NOT NULL,
 invoice_date TEXT NOT NULL,
 customer_name TEXT NOT NULL,
 item_name TEXT NOT NULL,
 quantity INTEGER NOT NULL CHECK(quantity > 0),
 total_amount INTEGER NOT NULL CHECK(total_amount >= 0),
 status TEXT NOT NULL DEFAULT 'Chưa trả' CHECK(status IN ('Chưa trả','Đã trả')),
 created_by TEXT NOT NULL DEFAULT 'system',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_debit_item_date ON finance_debit_items(invoice_date);
CREATE INDEX IF NOT EXISTS idx_debit_item_status ON finance_debit_items(status);
"""


class DebitItemRepository:
    """SQLite-backed CRUD, filtering, status updates and CSV export."""

    def __init__(self, connection: sqlite3.Connection, *, seed: bool = False):
        self.db = connection
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        if seed:
            self.seed_demo(minimum=10)

    @staticmethod
    def _read(role: str) -> None:
        if role not in ROLES:
            raise PermissionError("debit item read denied")

    @staticmethod
    def _write(role: str) -> None:
        if role not in WRITE_ROLES:
            raise PermissionError("debit item write requires ADMIN or STAFF")

    def seed_demo(self, *, minimum: int = 10) -> int:
        current = self.db.execute("SELECT COUNT(*) FROM finance_debit_items").fetchone()[0]
        created = 0
        names = ("Ipad", "iPhone", "Sách ngữ pháp cơ bản")
        for i in range(current, max(current, minimum)):
            self.db.execute(
                "INSERT INTO finance_debit_items(invoice_code,invoice_date,customer_name,item_name,quantity,total_amount,status,created_by) VALUES(?,?,?,?,?,?,?,?)",
                (f"DEMO-HD-{53+i:03d}", f"2026-{(i % 9) + 1:02d}-{(i % 27) + 1:02d}", f"Học viên Demo {i+1}", names[i % len(names)], (i % 3) + 1, ((i % 5) + 1) * 500000, "Đã trả" if i % 4 == 0 else "Chưa trả", "seed"),
            )
            created += 1
        self.db.commit()
        return created

    def list(self, *, role: str, query: str = "", status: str = "Tất cả", from_date: str = "", to_date: str = "", item_name: str = "Tất cả", limit: int = 10, offset: int = 0) -> list[dict[str, Any]]:
        self._read(role)
        clauses, args = ["1=1"], []
        if query.strip():
            q = f"%{query.strip()}%"; clauses.append("(invoice_code LIKE ? OR customer_name LIKE ? OR item_name LIKE ?)"); args.extend([q, q, q])
        if status != "Tất cả":
            if status not in STATUSES: raise ValueError("unsupported status")
            clauses.append("status = ?"); args.append(status)
        if from_date: clauses.append("invoice_date >= ?"); args.append(from_date)
        if to_date: clauses.append("invoice_date <= ?"); args.append(to_date)
        if item_name != "Tất cả": clauses.append("item_name = ?"); args.append(item_name)
        limit = max(1, min(int(limit), 100)); offset = max(0, int(offset))
        args.extend([limit, offset])
        rows = self.db.execute("SELECT * FROM finance_debit_items WHERE " + " AND ".join(clauses) + " ORDER BY invoice_date DESC,id DESC LIMIT ? OFFSET ?", args).fetchall()
        return [dict(r) for r in rows]

    def create(self, *, role: str, invoice_code: str, invoice_date: str, customer_name: str, item_name: str, quantity: int, total_amount: int, status: str = "Chưa trả", created_by: str = "system") -> dict[str, Any]:
        self._write(role)
        if not all(str(v).strip() for v in (invoice_code, invoice_date, customer_name, item_name)): raise ValueError("invoice_code, invoice_date, customer_name and item_name are required")
        if status not in STATUSES: raise ValueError("unsupported status")
        quantity, total_amount = int(quantity), int(total_amount)
        if quantity <= 0 or total_amount < 0: raise ValueError("quantity or total_amount invalid")
        cur = self.db.execute("INSERT INTO finance_debit_items(invoice_code,invoice_date,customer_name,item_name,quantity,total_amount,status,created_by) VALUES(?,?,?,?,?,?,?,?)", (invoice_code.strip(), invoice_date.strip(), customer_name.strip(), item_name.strip(), quantity, total_amount, status, created_by.strip() or "system"))
        self.db.commit(); return dict(self.db.execute("SELECT * FROM finance_debit_items WHERE id=?", (cur.lastrowid,)).fetchone())

    def update(self, item_id: int, *, role: str, **changes: Any) -> dict[str, Any]:
        self._write(role)
        allowed = {"invoice_code", "invoice_date", "customer_name", "item_name", "quantity", "total_amount", "status"}
        vals = {k: v for k, v in changes.items() if k in allowed}
        if not vals: raise ValueError("no editable fields")
        if "status" in vals and vals["status"] not in STATUSES: raise ValueError("unsupported status")
        if "quantity" in vals and int(vals["quantity"]) <= 0: raise ValueError("quantity invalid")
        if "total_amount" in vals and int(vals["total_amount"]) < 0: raise ValueError("total_amount invalid")
        keys = list(vals); assignments = ", ".join(f"{k}=?" for k in keys) + ", updated_at=CURRENT_TIMESTAMP"
        cur = self.db.execute(f"UPDATE finance_debit_items SET {assignments} WHERE id=?", [vals[k] for k in keys] + [item_id])
        if cur.rowcount != 1: raise KeyError("debit item not found")
        self.db.commit(); return dict(self.db.execute("SELECT * FROM finance_debit_items WHERE id=?", (item_id,)).fetchone())

    def export_csv(self, *, role: str, **filters: Any) -> str:
        rows = self.list(role=role, limit=10000, **filters); out = io.StringIO(); writer = csv.writer(out); writer.writerow(TABLE_HEADERS)
        for i, row in enumerate(rows, 1): writer.writerow([i, row["invoice_code"], row["invoice_date"], row["customer_name"], row["item_name"], row["quantity"], f"{row['total_amount']:,}", row["status"], "..."])
        return out.getvalue()


def route_contract() -> dict[str, Any]:
    return {"route": ROUTE, "tab": "Vật phẩm nợ", "headers": TABLE_HEADERS, "filters": ["query", "status", "from_date", "to_date", "item_name"], "status_options": ["Tất cả", "Chưa trả", "Đã trả"], "page_sizes": [10, 20, 50, 100], "read_roles": sorted(ROLES), "write_roles": sorted(WRITE_ROLES)}


def register(app_or_router: Any = None, service: Any = None) -> dict[str, Any]:
    target = service if service is not None else app_or_router
    _attach_store(target, "finance_debit_item_store", DebitItemRepository)
    return _register_metadata(app_or_router, service, name="finance_debit_item", routes=(ROUTE,), schema="finance_debit_items")
