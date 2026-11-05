"""Persistent local contract for the Finance ``Ví CO`` screen.

The reference exposes a read/export list.  Its private wallet API is not
available, so this module keeps an explicit local ledger contract derived from
the observed table shape.  Synthetic rows are used only in rich demo mode.
"""
from __future__ import annotations

import csv
import io
import sqlite3
from datetime import datetime, timezone
from typing import Any, Mapping

from modules.finance import _register_metadata

ROUTE = "/finance/wallet_co/index"
READ_ROLES = frozenset(("ADMIN", "STAFF", "TEACHER", "STUDENT"))
TABLE_HEADERS = (
    "No.", "Tên học viên", "Trung tâm/chi nhánh", "Tổng tiền",
    "Đã dùng", "Chưa dùng", "Trạng thái", "Công cụ",
)
STATUSES = ("Kích hoạt", "Tạm khóa")
SCHEMA = """
CREATE TABLE IF NOT EXISTS finance_wallets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_name TEXT NOT NULL,
  branch TEXT NOT NULL DEFAULT '',
  total_amount INTEGER NOT NULL DEFAULT 0 CHECK(total_amount >= 0),
  used_amount INTEGER NOT NULL DEFAULT 0 CHECK(used_amount >= 0),
  unused_amount INTEGER NOT NULL DEFAULT 0 CHECK(unused_amount >= 0),
  status TEXT NOT NULL DEFAULT 'Kích hoạt' CHECK(status IN ('Kích hoạt','Tạm khóa')),
  note TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_finance_wallets_student ON finance_wallets(student_name);
CREATE INDEX IF NOT EXISTS idx_finance_wallets_status ON finance_wallets(status);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def _money(value: Any) -> int:
    try:
        amount = int(str(value or 0).replace(",", "").replace(" VND", "").strip())
    except (TypeError, ValueError) as exc:
        raise ValueError("Số tiền ví không hợp lệ") from exc
    if amount < 0:
        raise ValueError("Số tiền ví không được âm")
    return amount


def _validate(payload: Mapping[str, Any]) -> dict[str, Any]:
    student_name = str(payload.get("student_name") or "").strip()
    if not student_name:
        raise ValueError("Tên học viên là bắt buộc")
    status = str(payload.get("status") or "Kích hoạt").strip()
    if status not in STATUSES:
        raise ValueError("Trạng thái ví không hợp lệ")
    total = _money(payload.get("total_amount"))
    used = _money(payload.get("used_amount"))
    unused = _money(payload.get("unused_amount", total - used))
    if used > total or unused != total - used:
        raise ValueError("Tổng tiền phải bằng đã dùng + chưa dùng")
    return {
        "student_name": student_name,
        "branch": str(payload.get("branch") or "").strip(),
        "total_amount": total,
        "used_amount": used,
        "unused_amount": unused,
        "status": status,
        "note": str(payload.get("note") or "").strip(),
    }


def seed(conn: sqlite3.Connection, count: int = 20) -> int:
    ensure_schema(conn)
    current = conn.execute("SELECT COUNT(*) FROM finance_wallets").fetchone()[0]
    names = (
        "Trần Hoàng Anh", "Nguyễn Minh Anh", "Lê Khánh Linh", "Phạm Gia Huy",
        "Võ Ngọc Mai", "Đặng Nhật Minh", "Bùi Thu Hà", "Phan Đức Anh",
        "Hoàng Yến Nhi", "Đỗ Quang Huy", "Nguyễn Thảo Vy", "Trần Gia Bảo",
        "Lê Minh Khang", "Phạm Ngọc Hân", "Vũ Thanh Tùng", "Đinh Hà My",
        "Nguyễn Hải Đăng", "Trương Tú Anh", "Huỳnh Anh Khoa", "Mai Phương Thảo",
    )
    branches = ("Trung tâm CenterOnline - Demo", "Cơ sở Quận 1", "Cơ sở Cầu Giấy", "Cơ sở Bình Thạnh")
    for index in range(current, count):
        total = 3_000_000 + index * 125_000
        used = (index % 4) * 250_000
        payload = {
            "student_name": names[index % len(names)],
            "branch": branches[index % len(branches)],
            "total_amount": total,
            "used_amount": used,
            "unused_amount": total - used,
            "status": "Kích hoạt" if index % 5 else "Tạm khóa",
            "note": "Dữ liệu tổng hợp cho môi trường demo",
        }
        row = _validate(payload)
        now = _now()
        conn.execute(
            "INSERT INTO finance_wallets(student_name,branch,total_amount,used_amount,unused_amount,status,note,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (row["student_name"], row["branch"], row["total_amount"], row["used_amount"], row["unused_amount"], row["status"], row["note"], now, now),
        )
    conn.commit()
    return conn.execute("SELECT COUNT(*) FROM finance_wallets").fetchone()[0]


def list_wallets(conn: sqlite3.Connection, filters: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    filters = filters or {}
    clauses, values = [], []
    query = str(filters.get("q") or "").strip()
    if query:
        clauses.append("(student_name LIKE ? OR branch LIKE ? OR note LIKE ?)")
        values.extend([f"%{query}%"] * 3)
    status = str(filters.get("status") or "").strip()
    if status:
        if status not in STATUSES:
            raise ValueError("Trạng thái ví không hợp lệ")
        clauses.append("status=?"); values.append(status)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    rows = conn.execute(f"SELECT * FROM finance_wallets{where} ORDER BY id DESC", values).fetchall()
    return [dict(row) for row in rows]


def export_csv(rows: list[Mapping[str, Any]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(TABLE_HEADERS)
    for number, row in enumerate(rows, 1):
        writer.writerow((
            number, row.get("student_name", ""), row.get("branch", ""),
            f"{int(row.get('total_amount') or 0):,} VND",
            f"{int(row.get('used_amount') or 0):,} VND",
            f"{int(row.get('unused_amount') or 0):,} VND",
            row.get("status", ""), "",
        ))
    return "\ufeff" + output.getvalue()


def route_contract() -> dict[str, Any]:
    return {
        "route": ROUTE, "entity": "finance_wallets", "headers": TABLE_HEADERS,
        "filters": ("q", "status"), "tabs": ("Ví CO",), "page_sizes": (5, 10, 25, 50),
        "status_options": [("", "Tất cả"), ("Kích hoạt", "Kích hoạt"), ("Tạm khóa", "Tạm khóa")],
        "rbac": {"read": sorted(READ_ROLES), "write": []},
        "read_roles": sorted(READ_ROLES), "write_roles": [],
    }


CONTRACT = {
    "route": ROUTE,
    "entity": "finance_wallets",
    "columns": TABLE_HEADERS,
    "filters": ("q", "status"),
    "page_sizes": (5, 10, 25, 50),
    "rbac": {"read": sorted(READ_ROLES), "write": []},
    "maturity": "SOURCE_PRESENT",
}


def register(app_or_router: Any = None, service: Any = None) -> dict[str, Any]:
    target = service if service is not None else app_or_router
    connection = getattr(target, "db", None)
    if connection is not None:
        ensure_schema(connection)
    return _register_metadata(app_or_router, service, name="finance_wallet", routes=(ROUTE,), schema="finance_wallets")

