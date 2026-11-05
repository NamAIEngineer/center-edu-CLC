"""Reserve (bảo lưu) local domain contract for CENTER EDU."""
from __future__ import annotations

import csv
import io
import sqlite3
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from modules.finance import _attach_store, _register_metadata

ROUTE = "/finance/reserve"
READ_ROLES = frozenset(("ADMIN", "STAFF", "TEACHER"))
WRITE_ROLES = frozenset(("ADMIN", "STAFF"))
MODES = ("Theo hợp đồng", "Theo khóa học")
STATUSES = ("Chờ xử lý", "Đã cộng vào ví", "Đã hoàn trả")
TABLE_HEADERS = ("Mã bảo lưu", "Học viên", "Ngày bảo lưu", "Số tiền/Số ngày bảo lưu", "Hợp đồng bảo lưu", "Người tạo", "Trạng thái", "Công cụ")


def _day(value: Any) -> str:
    text = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError("Ngày bảo lưu không hợp lệ")


def _amount(value: Any) -> int:
    try:
        n = Decimal(str(value or 0).replace(",", "").replace(" VND", "").strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Số tiền/Số ngày bảo lưu không hợp lệ") from exc
    if n < 0 or n != n.quantize(Decimal("1")):
        raise ValueError("Số tiền/Số ngày bảo lưu phải là số nguyên không âm")
    return int(n)


class FinanceReserve:
    def __init__(self, db: sqlite3.Connection, *, now: date | None = None):
        self.db = db; self.db.row_factory = sqlite3.Row; self.now = now or date.today(); self.ensure_schema()

    def ensure_schema(self) -> None:
        self.db.execute("""CREATE TABLE IF NOT EXISTS finance_reserves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reserve_code TEXT NOT NULL UNIQUE,
            student_name TEXT NOT NULL,
            reserve_date TEXT NOT NULL,
            amount_or_days INTEGER NOT NULL DEFAULT 0 CHECK(amount_or_days >= 0),
            contract_code TEXT NOT NULL DEFAULT '',
            course_name TEXT NOT NULL DEFAULT '',
            created_by TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Chờ xử lý',
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )""")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_finance_reserves_date ON finance_reserves(reserve_date)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_finance_reserves_status ON finance_reserves(status)")
        self.db.commit()

    def _read(self, role: str) -> None:
        if role not in READ_ROLES: raise PermissionError("Bảo lưu không dành cho vai trò này")

    def _write(self, role: str) -> None:
        if role not in WRITE_ROLES: raise PermissionError("Chỉ ADMIN hoặc STAFF được quản lý bảo lưu")

    def seed_demo(self, *, count: int = 12, actor: str = "Center Administrator") -> int:
        existing = self.db.execute("SELECT COUNT(*) FROM finance_reserves").fetchone()[0]
        if existing >= count: return existing
        for i in range(existing, count):
            self.create({
                "reserve_code": f"BL-DEMO-{i + 1:03d}", "student_name": f"Nguyễn Thị Học viên {i + 1:02d}",
                "reserve_date": f"2026-{(i % 9) + 1:02d}-{(i % 25) + 1:02d}",
                "amount_or_days": 10_000_000 + i * 750_000, "contract_code": f"HD-DEMO-{i + 1:03d}",
                "course_name": ("Tiếng Anh cơ bản 1", "IELTS Start", "AA")[i % 3],
                "status": STATUSES[i % len(STATUSES)], "note": "", "created_by": actor,
            }, role="ADMIN", actor=actor)
        return self.db.execute("SELECT COUNT(*) FROM finance_reserves").fetchone()[0]

    @staticmethod
    def _row(row: sqlite3.Row) -> dict[str, Any]: return dict(row)

    def list(self, filters: Mapping[str, Any] | None = None, *, role: str = "ADMIN", page: int = 1, page_size: int = 10) -> dict[str, Any]:
        self._read(role); filters = filters or {}; page=max(int(page),1); page_size=min(max(int(page_size),1),100)
        where, args = ["1=1"], []
        if filters.get("q"):
            q=f"%{str(filters['q']).strip()}%"; where.append("(reserve_code LIKE ? OR student_name LIKE ? OR contract_code LIKE ? OR course_name LIKE ? OR created_by LIKE ?)"); args.extend([q]*5)
        if filters.get("mode") == "Theo hợp đồng": where.append("contract_code <> ''")
        elif filters.get("mode") == "Theo khóa học": where.append("course_name <> ''")
        elif filters.get("mode"): raise ValueError("Kiểu lọc bảo lưu không hợp lệ")
        base=" FROM finance_reserves WHERE "+" AND ".join(where); total=self.db.execute("SELECT COUNT(*)"+base,args).fetchone()[0]
        rows=self.db.execute("SELECT *"+base+" ORDER BY reserve_date DESC,id DESC LIMIT ? OFFSET ?",args+[page_size,(page-1)*page_size]).fetchall()
        return {"items":[self._row(r) for r in rows],"total":total,"page":page,"page_size":page_size,"pages":(total+page_size-1)//page_size}

    def get(self, reserve_id: int, *, role: str = "ADMIN") -> dict[str, Any]:
        self._read(role); row=self.db.execute("SELECT * FROM finance_reserves WHERE id=?",(int(reserve_id),)).fetchone()
        if row is None: raise KeyError("Bảo lưu không tồn tại")
        return self._row(row)

    def create(self, payload: Mapping[str, Any], *, role: str, actor: str) -> dict[str, Any]:
        self._write(role); code=str(payload.get("reserve_code") or "").strip() or f"BL-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"; student=str(payload.get("student_name") or "").strip()
        if not student: raise ValueError("Học viên là bắt buộc")
        status=str(payload.get("status") or "Chờ xử lý").strip();
        if status not in STATUSES: raise ValueError("Trạng thái bảo lưu không hợp lệ")
        now=datetime.utcnow().isoformat(timespec="seconds")+"Z"
        try:
            cur=self.db.execute("INSERT INTO finance_reserves(reserve_code,student_name,reserve_date,amount_or_days,contract_code,course_name,created_by,status,note,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(code,student,_day(payload.get("reserve_date")),_amount(payload.get("amount_or_days")),str(payload.get("contract_code") or "").strip(),str(payload.get("course_name") or "").strip(),actor,status,str(payload.get("note") or ""),now,now)); self.db.commit()
        except sqlite3.IntegrityError as exc: self.db.rollback(); raise ValueError("Mã bảo lưu đã tồn tại") from exc
        return self.get(cur.lastrowid,role=role)

    def update(self, reserve_id: int, payload: Mapping[str, Any], *, role: str, actor: str) -> dict[str, Any]:
        self._write(role); current=self.get(reserve_id,role=role); merged=dict(current); merged.update(payload); status=str(merged.get("status") or "Chờ xử lý").strip()
        if status not in STATUSES: raise ValueError("Trạng thái bảo lưu không hợp lệ")
        self.db.execute("UPDATE finance_reserves SET student_name=?,reserve_date=?,amount_or_days=?,contract_code=?,course_name=?,status=?,note=?,updated_at=? WHERE id=?",(str(merged.get("student_name") or "").strip(),_day(merged.get("reserve_date")),_amount(merged.get("amount_or_days")),str(merged.get("contract_code") or "").strip(),str(merged.get("course_name") or "").strip(),status,str(merged.get("note") or ""),datetime.utcnow().isoformat(timespec="seconds")+"Z",int(reserve_id))); self.db.commit(); return self.get(reserve_id,role=role)

    def export_csv(self, filters: Mapping[str, Any] | None = None, *, role: str = "ADMIN") -> str:
        rows=self.list(filters,role=role,page=1,page_size=10000)["items"]; out=io.StringIO(); w=csv.writer(out); w.writerow(TABLE_HEADERS)
        for i,r in enumerate(rows,1): w.writerow([r["reserve_code"],r["student_name"],r["reserve_date"],r["amount_or_days"],r["contract_code"] or r["course_name"],r["created_by"],r["status"],""])
        return "\ufeff"+out.getvalue()

def route_contract() -> dict[str, Any]:
    return {
        "route": ROUTE, "headers": TABLE_HEADERS, "filters": ("q", "mode"),
        "tabs": ("Hoàn trả", "Bảo lưu"), "modes": MODES, "statuses": STATUSES,
        "page_sizes": (5, 10, 25, 50), "read_roles": sorted(READ_ROLES), "write_roles": sorted(WRITE_ROLES),
    }


def register(app_or_router: Any = None, service: Any = None) -> dict[str, Any]:
    target = service if service is not None else app_or_router
    _attach_store(target, "finance_reserve_store", FinanceReserve)
    return _register_metadata(app_or_router, service, name="finance_reserve", routes=(ROUTE,), schema="finance_reserves")


__all__=["FinanceReserve","ROUTE","TABLE_HEADERS","READ_ROLES","WRITE_ROLES","route_contract","register"]
