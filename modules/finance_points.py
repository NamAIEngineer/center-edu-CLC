"""Persistent local contract for finance accumulate-points settings."""
from __future__ import annotations
import csv, io, sqlite3
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from modules.finance import _attach_store, _register_metadata

ROUTE = "/finance/accumulate_points"
COLUMNS = ("No.", "Mã tích điểm", "Tên", "Trạng thái", "Số tiền tích 1 điểm", "Tỉ lệ quy đổi", "Trung tâm áp dụng", "Công cụ")
STATUSES = ("active", "inactive")
STATUS_LABELS = {"active": "Hoạt động", "inactive": "Ngừng hoạt động"}
ROLE_WRITE = frozenset(("ADMIN", "STAFF"))
ROLE_READ = frozenset(("ADMIN", "STAFF", "TEACHER"))


def _amount(v: Any) -> int:
    try: n = Decimal(str(v).replace(",", "").replace(" VND", "").strip())
    except (InvalidOperation, ValueError): raise ValueError("Số tiền không hợp lệ")
    if n < 0 or n != n.quantize(Decimal("1")): raise ValueError("Số tiền phải là số nguyên không âm")
    return int(n)


class FinancePoints:
    def __init__(self, db: sqlite3.Connection):
        self.db = db; self.db.row_factory = sqlite3.Row; self.ensure_schema()

    def ensure_schema(self):
        self.db.execute("""CREATE TABLE IF NOT EXISTS finance_point_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('active','inactive')), amount_per_point INTEGER NOT NULL CHECK(amount_per_point>=0),
            conversion_rate INTEGER NOT NULL CHECK(conversion_rate>=0), center_id TEXT NOT NULL, center_name TEXT NOT NULL,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_finance_point_rules_status ON finance_point_rules(status)"); self.db.commit()

    def seed_demo(self, count: int = 10, center_id: str = "demo", center_name: str = "Trung tâm CenterOnline - Demo") -> int:
        current = self.db.execute("SELECT COUNT(*) FROM finance_point_rules").fetchone()[0]
        for i in range(current, count):
            self.create({"code": f"ap-demo-{i+1:03d}", "name": ("Mã khuyến mãi hè" if i == 0 else f"Chương trình tích điểm {i+1}"), "status": "active" if i % 4 else "inactive", "amount_per_point": 100 + i * 50, "conversion_rate": 10000 + i * 1000, "center_id": center_id, "center_name": center_name}, role="ADMIN", actor="system-seed")
        return self.db.execute("SELECT COUNT(*) FROM finance_point_rules").fetchone()[0]

    def list(self, q: str = "", *, status: str | None = None, center_id: str | None = None, page: int = 1, page_size: int = 10, role: str = "ADMIN") -> dict[str, Any]:
        if role not in ROLE_READ: raise PermissionError("Thiết lập tích điểm không dành cho vai trò này")
        page, page_size = max(int(page), 1), min(max(int(page_size), 5), 50); where, args = ["1=1"], []
        if q: where.append("(code LIKE ? OR name LIKE ? OR center_name LIKE ?)"); qq = f"%{q}%"; args += [qq, qq, qq]
        if status:
            status = str(status).strip().lower()
            if status not in STATUSES: raise ValueError("Trạng thái không hợp lệ")
            where.append("status = ?"); args.append(status)
        if center_id: where.append("center_id = ?"); args.append(center_id)
        base = " FROM finance_point_rules WHERE " + " AND ".join(where)
        total = self.db.execute("SELECT COUNT(*)" + base, args).fetchone()[0]
        rows = self.db.execute("SELECT *" + base + " ORDER BY id DESC LIMIT ? OFFSET ?", args + [page_size, (page - 1) * page_size]).fetchall()
        return {"items": [dict(r) for r in rows], "total": total, "page": page, "page_size": page_size, "pages": (total + page_size - 1) // page_size}

    def create(self, payload: Mapping[str, Any], *, role: str, actor: str) -> dict[str, Any]:
        if role not in ROLE_WRITE: raise PermissionError("Chỉ ADMIN hoặc STAFF được tạo mã tích điểm")
        code, name, center_id, center_name = [str(payload.get(k) or "").strip() for k in ("code", "name", "center_id", "center_name")]
        status = str(payload.get("status") or "active").strip(); amount, rate = _amount(payload.get("amount_per_point")), _amount(payload.get("conversion_rate"))
        if not code or not name or not center_id or not center_name: raise ValueError("Thiếu trường bắt buộc")
        if status not in STATUSES: raise ValueError("Trạng thái không hợp lệ")
        now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        self.db.execute("INSERT INTO finance_point_rules(code,name,status,amount_per_point,conversion_rate,center_id,center_name,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)", (code,name,status,amount,rate,center_id,center_name,now,now)); self.db.commit()
        return dict(self.db.execute("SELECT * FROM finance_point_rules WHERE code=?", (code,)).fetchone())

    def update(self, rule_id: int, payload: Mapping[str, Any], *, role: str, actor: str) -> dict[str, Any]:
        if role not in ROLE_WRITE: raise PermissionError("Chỉ ADMIN hoặc STAFF được sửa mã tích điểm")
        row = self.db.execute("SELECT * FROM finance_point_rules WHERE id=?", (int(rule_id),)).fetchone()
        if not row: raise KeyError("Mã tích điểm không tồn tại")
        x = dict(row); x.update(payload); status = str(x.get("status") or "active")
        if status not in STATUSES: raise ValueError("Trạng thái không hợp lệ")
        self.db.execute("UPDATE finance_point_rules SET name=?,status=?,amount_per_point=?,conversion_rate=?,center_id=?,center_name=?,updated_at=? WHERE id=?", (str(x.get("name") or "").strip(), status, _amount(x.get("amount_per_point")), _amount(x.get("conversion_rate")), str(x.get("center_id") or ""), str(x.get("center_name") or ""), datetime.utcnow().isoformat(timespec="seconds") + "Z", int(rule_id))); self.db.commit()
        return dict(self.db.execute("SELECT * FROM finance_point_rules WHERE id=?", (int(rule_id),)).fetchone())

    def export_csv(self, *, role: str = "ADMIN", **filters: Any) -> str:
        rows = self.list(**filters, page=1, page_size=50, role=role)["items"]; out = io.StringIO(); w = csv.writer(out); w.writerow(COLUMNS)
        for i, r in enumerate(rows, 1): w.writerow([i,r["code"],r["name"],"Hoạt động" if r["status"] == "active" else "Ngừng hoạt động",f'{r["amount_per_point"]:,} VND',f'{r["conversion_rate"]:,} VND',r["center_name"],""])
        return out.getvalue()

    def get(self, rule_id: int, *, role: str = "ADMIN") -> dict[str, Any]:
        if role not in ("ADMIN", "STAFF", "TEACHER"):
            raise PermissionError("Thiết lập tích điểm không dành cho vai trò này")
        row = self.db.execute("SELECT * FROM finance_point_rules WHERE id=?", (int(rule_id),)).fetchone()
        if row is None:
            raise KeyError("Mã tích điểm không tồn tại")
        return dict(row)


def route_contract() -> dict[str, Any]:
    return {
        "route": ROUTE,
        "headers": COLUMNS,
        "filters": ("q", "status", "center_id"),
        "tabs": ("Thiết lập tích điểm", "Thống kê tích điểm"),
        "status_options": [(key, value) for key, value in STATUS_LABELS.items()],
        "page_sizes": (5, 10, 25, 50),
        "read_roles": ("ADMIN", "STAFF", "TEACHER"),
        "write_roles": tuple(sorted(ROLE_WRITE)),
    }

def register(app_or_router: Any = None, service: Any = None) -> dict[str, Any]:
    target = service if service is not None else app_or_router
    _attach_store(target, "finance_points_store", FinancePoints)
    return _register_metadata(app_or_router, service, name="finance_points", routes=(ROUTE,), schema="finance_point_rules")


__all__ = ["FinancePoints", "ROUTE", "COLUMNS", "STATUSES", "STATUS_LABELS", "route_contract", "register"]
