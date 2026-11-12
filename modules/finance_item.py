"""Persistent local contract for the Finance / Vật phẩm screen.

The application registry can mount these helpers against its SQLite connection.
This module intentionally has no Flask imports or global database ownership.
"""
from __future__ import annotations

import csv
import io
import sqlite3
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from modules.finance import _register_metadata

ROUTE = "/finance/item"
ENTITY = "finance_items"
TABS = ("Danh mục vật phẩm", "Vật phẩm", "Phiếu nhập kho", "Phiếu xuất kho")
COLUMNS = (
    "No.", "Mã vật phẩm", "Danh mục", "Tên vật phẩm", "Khóa học áp dụng",
    "Đơn vị tính", "Trung tâm áp dụng", "Số lượng còn", "Giá bán",
    "Điều chỉnh giá", "Trạng thái", "Công cụ",
)
STATUS_LABELS = {"Hoạt động": "Hoạt động", "Tạm khóa": "Tạm khóa"}
FILTERS = (
    {"name": "q", "kind": "text", "placeholder": "Tìm trong bảng..."},
    {"name": "status", "kind": "select", "placeholder": "Chọn trạng thái",
     "options": ("Hoạt động", "Tạm khóa")},
    {"name": "page_size", "kind": "page_size", "options": (5, 10, 25, 50)},
)
RBAC = {
    "ADMIN": frozenset(("read", "create", "update", "delete", "export")),
    "STAFF": frozenset(("read", "create", "update", "export")),
    "TEACHER": frozenset(("read",)),
    "STUDENT": frozenset(),
}
SCHEMA = """
CREATE TABLE IF NOT EXISTS finance_items (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 code TEXT NOT NULL UNIQUE,
 category TEXT NOT NULL DEFAULT '',
 fullname TEXT NOT NULL,
 description TEXT NOT NULL DEFAULT '',
 image_logo TEXT NOT NULL DEFAULT '',
 unit TEXT NOT NULL DEFAULT 'cái',
 course_ids TEXT NOT NULL DEFAULT '',
 branch TEXT NOT NULL DEFAULT '',
 quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
 sale_price INTEGER NOT NULL DEFAULT 0 CHECK(sale_price >= 0),
 price_adjustment INTEGER NOT NULL DEFAULT 0,
 status TEXT NOT NULL DEFAULT 'Hoạt động' CHECK(status IN ('Hoạt động','Tạm khóa')),
 start_date TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_finance_items_status ON finance_items(status);
CREATE INDEX IF NOT EXISTS idx_finance_items_code ON finance_items(code);
"""


def can(role: str, action: str) -> bool:
    return action in RBAC.get(str(role or "").upper(), frozenset())


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(finance_items)")}
    if "image_logo" not in columns:
        conn.execute("ALTER TABLE finance_items ADD COLUMN image_logo TEXT NOT NULL DEFAULT ''")
    conn.commit()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate(payload: Mapping[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    for key, label in (("code", "Mã vật phẩm"), ("fullname", "Tên vật phẩm")):
        if not str(payload.get(key, "")).strip(): errors[key] = f"{label} là bắt buộc"
    if str(payload.get("status", "Hoạt động")) not in ("Hoạt động", "Tạm khóa"):
        errors["status"] = "Trạng thái không hợp lệ"
    image = str(payload.get("image_logo", "") or "")
    # The shared JSON body reader caps requests at 1 MB; keep encoded image
    # below that boundary, with room for the other form fields and JSON syntax.
    if image and (len(image) > 800_000 or not image.startswith(("data:image/png;base64,", "data:image/jpeg;base64,", "data:image/webp;base64,"))):
        errors["image_logo"] = "Ảnh không hợp lệ hoặc vượt quá giới hạn tải lên"
    try:
        if int(payload.get("quantity", 0)) < 0: errors["quantity"] = "Số lượng không âm"
        if int(payload.get("sale_price", 0)) < 0: errors["sale_price"] = "Giá bán không âm"
    except (TypeError, ValueError):
        errors["quantity"] = "Số lượng và giá bán phải là số"
    return errors


def seed(conn: sqlite3.Connection, count: int = 10) -> int:
    """Idempotently seed synthetic inventory rows for a local demo database."""
    ensure_schema(conn)
    existing = conn.execute("SELECT COUNT(*) FROM finance_items").fetchone()[0]
    added = 0
    for i in range(existing + 1, max(count, existing) + 1):
        conn.execute(
            "INSERT OR IGNORE INTO finance_items "
            "(code,category,fullname,description,unit,course_ids,branch,quantity,sale_price,price_adjustment,status,start_date,created_at,updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (f"IT-DEMO-{i:03d}", "Học liệu" if i % 2 else "Thiết bị",
             f"Vật phẩm demo {i}", "Dữ liệu tổng hợp cho môi trường demo", "cái",
             "", "Trung tâm Demo", 5 + i, 50000 * i, 0,
             "Hoạt động" if i % 5 else "Tạm khóa", "2026-11-01", _now(), _now()),
        )
        added += 1
    conn.commit()
    return added


def list_items(conn: sqlite3.Connection, filters: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    filters = filters or {}
    clauses, values = [], []
    q = str(filters.get("q", "")).strip()
    if q:
        clauses.append("(code LIKE ? OR fullname LIKE ? OR category LIKE ? OR description LIKE ?)")
        values.extend([f"%{q}%"] * 4)
    if str(filters.get("status", "")).strip():
        clauses.append("status = ?"); values.append(str(filters["status"]))
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    rows = conn.execute(f"SELECT * FROM finance_items{where} ORDER BY id DESC", values).fetchall()
    return [dict(row) for row in rows]


def create_item(conn: sqlite3.Connection, payload: Mapping[str, Any], role: str = "ADMIN") -> int:
    if not can(role, "create"): raise PermissionError("FORBIDDEN")
    errors = validate(payload)
    if errors: raise ValueError(errors)
    now = _now()
    cur = conn.execute(
        "INSERT INTO finance_items (code,category,fullname,description,image_logo,unit,course_ids,branch,quantity,sale_price,price_adjustment,status,start_date,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        tuple(payload.get(k, "") for k in ("code", "category", "fullname", "description", "image_logo", "unit", "course_ids", "branch"))
        + (int(payload.get("quantity", 0)), int(payload.get("sale_price", 0)), int(payload.get("price_adjustment", 0)), payload.get("status", "Hoạt động"), payload.get("start_date", ""), now, now),
    )
    conn.commit(); return int(cur.lastrowid)


def update_item(conn: sqlite3.Connection, item_id: int, payload: Mapping[str, Any], role: str = "ADMIN") -> None:
    if not can(role, "update"): raise PermissionError("FORBIDDEN")
    if conn.execute("SELECT 1 FROM finance_items WHERE id=?", (int(item_id),)).fetchone() is None:
        raise KeyError("Vật phẩm không tồn tại")
    errors = validate(payload)
    if errors: raise ValueError(errors)
    fields = ("code", "category", "fullname", "description", "image_logo", "unit", "course_ids", "branch", "quantity", "sale_price", "price_adjustment", "status", "start_date")
    conn.execute("UPDATE finance_items SET " + ",".join(f"{k}=?" for k in fields) + ",updated_at=? WHERE id=?", tuple(payload.get(k, "") for k in fields) + (_now(), item_id))
    conn.commit()


def export_csv(rows: Iterable[Mapping[str, Any]]) -> str:
    out = io.StringIO(newline=""); writer = csv.writer(out); writer.writerow(COLUMNS)
    for no, row in enumerate(rows, 1):
        writer.writerow((no, row.get("code", ""), row.get("category", ""), row.get("fullname", ""), row.get("course_ids", ""), row.get("unit", ""), row.get("branch", ""), row.get("quantity", 0), row.get("sale_price", 0), row.get("price_adjustment", 0), row.get("status", ""), ""))
    return "\ufeff" + out.getvalue()


def route_contract() -> dict[str, Any]:
    return {
        "route": ROUTE, "entity": ENTITY, "tabs": TABS, "headers": COLUMNS,
        "filters": FILTERS, "rbac": {key: sorted(value) for key, value in RBAC.items()},
        "read_roles": sorted(role for role, actions in RBAC.items() if "read" in actions),
        "write_roles": sorted(role for role, actions in RBAC.items() if "create" in actions),
        "status_options": [("Hoạt động", "Hoạt động"), ("Tạm khóa", "Tạm khóa")],
        "page_sizes": (5, 10, 25, 50),
        "api_hooks": ("GET /api/finance/items", "POST /api/finance/items", "PATCH /api/finance/items/<id>", "GET /api/export/finance-items"),
    }


CONTRACT = {"route": ROUTE, "entity": ENTITY, "tabs": TABS, "columns": COLUMNS, "filters": FILTERS, "schema": SCHEMA, "rbac": RBAC, "maturity": "SOURCE_PRESENT", "api_hooks": ("GET /api/finance/items", "POST /api/finance/items", "PATCH /api/finance/items/<id>", "GET /api/export/finance-items")}


def register(app_or_router: Any = None, service: Any = None) -> dict[str, Any]:
    target = service if service is not None else app_or_router
    connection = getattr(target, "db", None)
    if connection is not None:
        ensure_schema(connection)
    return _register_metadata(app_or_router, service, name="finance_item", routes=(ROUTE,), schema=ENTITY)
