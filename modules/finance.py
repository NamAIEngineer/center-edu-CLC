"""Finance module contracts for CENTER EDU rebuild.

This file is intentionally app-framework agnostic. The host registers ``FinanceSpend``
with its SQLite connection and HTTP router. It owns the spend (phiếu chi) domain only;
no authorization or persistence bypass is performed here.
"""
from __future__ import annotations

import csv
import io
import sqlite3
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping

SPEND_ROUTE = "/finance/spend/index"
SPEND_COLUMNS = (
    "No.", "Mã phiếu chi", "Ngày lập phiếu", "Trung tâm áp dụng", "Nội dung",
    "Ghi chú", "Danh mục", "Số tiền", "Phương thức thanh toán", "Người lập phiếu", "Công cụ",
)
SPEND_FILTERS = ("center_id", "category", "q", "from_date", "to_date")
SPEND_CATEGORIES = ("CSVC", "Lương", "Marketing", "Vận hành", "Khác")
PAYMENT_METHODS = ("cash", "bank_transfer", "card")
PAYMENT_METHOD_LABELS = {
    "cash": "Tiền mặt",
    "bank_transfer": "Chuyển khoản",
    "card": "Thẻ",
}
ROLE_WRITE = frozenset(("ADMIN", "STAFF"))


def _money(value: Any) -> int:
    try:
        amount = Decimal(str(value).replace(",", "").replace(" VND", "").strip())
    except (InvalidOperation, ValueError):
        raise ValueError("Số tiền không hợp lệ")
    if amount < 0 or amount != amount.quantize(Decimal("1")):
        raise ValueError("Số tiền phải là số nguyên không âm")
    return int(amount)


def _iso_day(value: Any) -> str:
    text = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError("Ngày lập phiếu không hợp lệ")


def _text(value: Any, field: str, *, required: bool = False, max_length: int = 300) -> str:
    text = str(value or "").strip()
    if required and not text:
        raise ValueError(f"{field} là bắt buộc")
    if len(text) > max_length:
        raise ValueError(f"{field} quá dài")
    return text


def _validated_payload(payload: Mapping[str, Any], *, existing: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Normalize one spend payload before it reaches SQLite.

    The HTTP handler translates ``ValueError`` into a 400 response.  Keeping
    this boundary in the finance module prevents invalid categories, methods,
    dates, and negative amounts from entering the persistent ledger through a
    future caller that does not use the current browser form.
    """
    merged = dict(existing or {})
    merged.update(payload)
    spend_date = _iso_day(merged.get("spend_date"))
    center_id = _text(merged.get("center_id"), "Mã trung tâm", required=True, max_length=80)
    center_name = _text(merged.get("center_name"), "Trung tâm áp dụng", required=True, max_length=200)
    content = _text(merged.get("content"), "Nội dung", required=True, max_length=500)
    category = _text(merged.get("category"), "Danh mục", required=True, max_length=40)
    method = _text(merged.get("payment_method"), "Phương thức thanh toán", required=True, max_length=30)
    if category not in SPEND_CATEGORIES:
        raise ValueError("Danh mục không hợp lệ")
    if method not in PAYMENT_METHODS:
        raise ValueError("Phương thức thanh toán không hợp lệ")
    note = _text(merged.get("note"), "Ghi chú", max_length=500)
    amount = _money(merged.get("amount_vnd"))
    return {
        "code": _text(merged.get("code"), "Mã phiếu chi", required=True, max_length=80),
        "spend_date": spend_date,
        "center_id": center_id,
        "center_name": center_name,
        "content": content,
        "note": note,
        "category": category,
        "amount_vnd": amount,
        "payment_method": method,
    }


def payment_method_label(value: Any) -> str:
    """Return the Vietnamese display label for a stored method value."""
    return PAYMENT_METHOD_LABELS.get(str(value or ""), "")


class FinanceSpend:
    """Persistent spend service. The caller supplies the host SQLite connection."""

    def __init__(self, db: sqlite3.Connection, *, now: date | None = None):
        self.db = db
        self.db.row_factory = sqlite3.Row
        self.now = now or date.today()
        self.ensure_schema()

    def ensure_schema(self) -> None:
        self.db.execute(
            """CREATE TABLE IF NOT EXISTS finance_spends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                spend_date TEXT NOT NULL,
                center_id TEXT NOT NULL,
                center_name TEXT NOT NULL,
                content TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL,
                amount_vnd INTEGER NOT NULL CHECK(amount_vnd >= 0),
                payment_method TEXT NOT NULL,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )"""
        )
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_finance_spends_date ON finance_spends(spend_date)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_finance_spends_category ON finance_spends(category)")
        self.db.commit()

    def seed_demo(self, *, count: int = 24, center_id: str = "demo", center_name: str = "Trung tâm CenterOnline - Demo", actor: str = "Center Administrator") -> int:
        """Idempotently provide realistic local demo rows; never copies reference data."""
        existing = self.db.execute("SELECT COUNT(*) FROM finance_spends").fetchone()[0]
        if existing >= count:
            return existing
        for i in range(existing, count):
            d = date(self.now.year, max(1, (i % 12) + 1), min(28, (i % 25) + 1)).isoformat()
            self.create({
                "code": f"PC-demo-{self.now.strftime('%Y%m%d')}-{i + 1:04d}",
                "spend_date": d, "center_id": center_id, "center_name": center_name,
                "content": ("Chi phí cơ sở vật chất" if i % 3 == 0 else "Vận hành trung tâm"),
                "note": "Dữ liệu demo tổng hợp", "category": SPEND_CATEGORIES[i % len(SPEND_CATEGORIES)],
                "amount_vnd": (i + 1) * 1_250_000, "payment_method": PAYMENT_METHODS[i % len(PAYMENT_METHODS)],
                "created_by": actor,
            }, role="ADMIN", actor=actor)
        return self.db.execute("SELECT COUNT(*) FROM finance_spends").fetchone()[0]

    def list(self, filters: Mapping[str, Any] | None = None, *, page: int = 1, page_size: int = 10) -> dict[str, Any]:
        filters = filters or {}
        page = max(int(page), 1); page_size = min(max(int(page_size), 1), 100)
        where, args = ["1=1"], []
        if filters.get("center_id"):
            where.append("center_id = ?"); args.append(str(filters["center_id"]))
        if filters.get("category"):
            category = str(filters["category"]).strip()
            if category not in SPEND_CATEGORIES:
                raise ValueError("Danh mục lọc không hợp lệ")
            where.append("category = ?"); args.append(category)
        if filters.get("q"):
            where.append("(code LIKE ? OR content LIKE ? OR note LIKE ? OR created_by LIKE ?)")
            q = f"%{filters['q']}%"; args.extend([q, q, q, q])
        if filters.get("from_date"):
            where.append("spend_date >= ?"); args.append(_iso_day(filters["from_date"]))
        if filters.get("to_date"):
            where.append("spend_date <= ?"); args.append(_iso_day(filters["to_date"]))
        if filters.get("from_date") and filters.get("to_date"):
            start = _iso_day(filters["from_date"]); end = _iso_day(filters["to_date"])
            if start > end:
                raise ValueError("Khoảng ngày lọc không hợp lệ")
        base = " FROM finance_spends WHERE " + " AND ".join(where)
        total = self.db.execute("SELECT COUNT(*)" + base, args).fetchone()[0]
        rows = self.db.execute("SELECT *" + base + " ORDER BY spend_date DESC, id DESC LIMIT ? OFFSET ?", args + [page_size, (page - 1) * page_size]).fetchall()
        return {"items": [dict(r) for r in rows], "total": total, "page": page, "page_size": page_size, "pages": (total + page_size - 1) // page_size}

    def create(self, payload: Mapping[str, Any], *, role: str, actor: str) -> dict[str, Any]:
        if role not in ROLE_WRITE: raise PermissionError("Khoản chi chỉ dành cho ADMIN hoặc STAFF")
        data = _validated_payload(payload)
        now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        try:
            self.db.execute("INSERT INTO finance_spends(code,spend_date,center_id,center_name,content,note,category,amount_vnd,payment_method,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (data["code"], data["spend_date"], data["center_id"], data["center_name"], data["content"], data["note"], data["category"], data["amount_vnd"], data["payment_method"], _text(actor, "Người lập phiếu", required=True, max_length=200), now, now)); self.db.commit()
        except sqlite3.IntegrityError as exc:
            self.db.rollback()
            raise ValueError("Mã phiếu chi đã tồn tại") from exc
        return dict(self.db.execute("SELECT * FROM finance_spends WHERE code = ?", (data["code"],)).fetchone())

    def update(self, spend_id: int, payload: Mapping[str, Any], *, role: str, actor: str) -> dict[str, Any]:
        if role not in ROLE_WRITE: raise PermissionError("Khoản chi chỉ dành cho ADMIN hoặc STAFF")
        current = self.db.execute("SELECT * FROM finance_spends WHERE id = ?", (int(spend_id),)).fetchone()
        if not current: raise KeyError("Khoản chi không tồn tại")
        data = _validated_payload(payload, existing=current)
        self.db.execute("UPDATE finance_spends SET spend_date=?,center_id=?,center_name=?,content=?,note=?,category=?,amount_vnd=?,payment_method=?,updated_at=? WHERE id=?", (data["spend_date"], data["center_id"], data["center_name"], data["content"], data["note"], data["category"], data["amount_vnd"], data["payment_method"], datetime.utcnow().isoformat(timespec="seconds") + "Z", int(spend_id))); self.db.commit()
        return dict(self.db.execute("SELECT * FROM finance_spends WHERE id = ?", (int(spend_id),)).fetchone())

    def export_csv(self, filters: Mapping[str, Any] | None = None) -> str:
        rows = self.list(filters, page=1, page_size=10000)["items"]; out = io.StringIO(); w = csv.writer(out); w.writerow(SPEND_COLUMNS)
        for i, r in enumerate(rows, 1): w.writerow([i, r["code"], r["spend_date"], r["center_name"], r["content"], r["note"], r["category"], f'{r["amount_vnd"]:,} VND', payment_method_label(r["payment_method"]), r["created_by"], ""])
        return out.getvalue()


def _register_metadata(app_or_router: Any = None, service: Any = None, *, name: str, routes: Iterable[str], schema: str) -> dict[str, Any]:
    """Register a finance module with the coordinator autoload seam.

    The host owns HTTP dispatch and authentication.  A module hook only records
    its bounded route/schema metadata; this keeps optional imports side-effect
    free while giving the host a durable registry entry.
    """
    target = service or app_or_router
    metadata = {
        "routes": list(routes),
        "source": f"modules.{name}",
        "status": "PERSISTENT_LOCAL_CONTRACT",
        "schema": schema,
    }
    registrar = getattr(target, "register_module", None)
    if callable(registrar):
        return registrar(name, metadata=metadata)
    return {"name": name, "registered": True, **metadata}


def _attach_store(target: Any, attribute: str, factory: Any) -> Any:
    """Attach one SQLite-backed store to the host service, idempotently."""
    connection = getattr(target, "db", None)
    if connection is None or not callable(factory):
        return None
    current = getattr(target, attribute, None)
    if current is None or getattr(current, "db", None) is not connection:
        current = factory(connection)
        setattr(target, attribute, current)
    return current


def register(app_or_router: Any = None, service: Any = None) -> dict[str, Any]:
    return _register_metadata(
        app_or_router,
        service,
        name="finance",
        routes=(SPEND_ROUTE,),
        schema="finance_spends",
    )


__all__ = ["FinanceSpend", "SPEND_ROUTE", "SPEND_COLUMNS", "SPEND_FILTERS", "SPEND_CATEGORIES", "PAYMENT_METHODS", "PAYMENT_METHOD_LABELS", "payment_method_label", "register"]
