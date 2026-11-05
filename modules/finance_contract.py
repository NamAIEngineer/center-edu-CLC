"""Persistent contract repository for ``/finance/contract``.

The HTTP shell owns authentication and route registration.  This module keeps
the observed contract table and form semantics in a small SQLite boundary so
the route can be wired without copying reference data or relying on a browser
session.  Enum values are stable storage values; ``*_LABELS`` are the only
values intended for customer-facing rendering.
"""
from __future__ import annotations

import csv
import io
import sqlite3
import unicodedata
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from modules.finance import _attach_store, _register_metadata

ROUTE = "/finance/contract"
UPLOAD_ROUTE = "/finance/contract/upload"
EXTENSION_ROUTE = "/finance/contract/get_extension_contract"
READ_ROLES = frozenset(("ADMIN", "STAFF", "TEACHER"))
WRITE_ROLES = frozenset(("ADMIN", "STAFF"))
PAYMENT_STATUSES = ("PENDING", "PARTIAL", "PAID", "OVERDUE")
CONTRACT_STATUSES = ("ACTIVE", "EXPIRED", "CANCELLED", "COMPLETED")
PAYMENT_STATUS_LABELS = {
    "PENDING": "Chưa đóng tiền", "PARTIAL": "Còn nợ", "PAID": "Đóng đủ", "OVERDUE": "Quá hạn",
}
CONTRACT_STATUS_LABELS = {
    "ACTIVE": "Đang thực hiện", "EXPIRED": "Hợp đồng hết hạn",
    "CANCELLED": "Đã hủy", "COMPLETED": "Hoàn thành",
}
TABLE_HEADERS = (
    "No.", "Mã hợp đồng", "Khách hàng", "Ngày tạo/Hết hạn", "Khóa học đăng kí",
    "Thanh toán/Còn nợ", "Nhân viên sale", "Người tạo", "Trạng thái đóng tiền",
    "Trạng thái hợp đồng", "Ghi chú", "Công cụ",
)
FILTERS = (
    "q", "date_from", "date_to", "expiry_from", "expiry_to", "course_id",
    "course_status", "discount", "branch", "payment_status", "contract_status",
    "sale", "sales_owner", "creator", "expired_date_status",
)

# The prior read-only browser DOM exposed these exact visible headings. The
# private file format and endpoint remain UNKNOWN; the local template mirrors
# the observed labels for syntax preview only. ``STT`` is display-only and is
# not part of the CSV payload.
UPLOAD_HEADERS = (
    "Mã hợp đồng", "Mã học viên", "Mã khách hàng", "Mã khóa học",
    "Số buổi đăng ký", "Mã Gói học phí", "Mã khoản thu", "Tiền trước giảm giá",
    "Mã giảm giá (khóa học)", "Tiền giảm (khóa học)", "Tiền sau giảm",
    "Mã giảm giá (toàn bộ hợp đồng)", "Tiền giảm giá (toàn bộ hợp đồng)",
    "Ngày tạo hợp đồng", "Ngày hết hạn", "Tổng tiền trước giảm giá",
    "Giảm giá trực tiếp", "Tổng tiền sau giảm giá", "Ghi chú hợp đồng",
    "Mã lớp học", "Ngày bắt đầu học",
)
UPLOAD_FIELDS = (
    "contract_code", "student_code", "customer_code", "course_code",
    "session_count", "package_code", "item_code", "pre_discount_amount",
    "course_discount_code", "course_discount_amount", "after_course_discount",
    "contract_discount_code", "contract_discount_amount", "created_date", "expiry_date",
    "gross_total_before_discount", "direct_discount", "gross_total_after_discount",
    "contract_note", "class_code", "start_date",
)
UPLOAD_MAX_BYTES = 2_000_000
UPLOAD_PROVENANCE = "LOCAL_SYNTHETIC_UPLOAD_CONTRACT_OBSERVED_COLUMNS"
UPLOAD_SAVE_BLOCKERS = (
    "finance_contract_upload_rows stores only the original 15 upload fields; it has no columns for the six newly observed fields.",
    "finance_contracts has no separate gross_total_before_discount or start_date field, and no class_code field; class_id exists but the upload-to-class mapping is not established.",
    "The local contract has no verified arithmetic mapping from the existing item, course-discount, and contract-discount values to the newly observed aggregate totals or debt amount.",
)


def _header_key(value: Any) -> str:
    """Normalize a CSV heading without changing stored customer values."""
    text = unicodedata.normalize("NFKD", str(value or "").replace("\ufeff", ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.strip().lower().replace("_", " ").split())


_UPLOAD_HEADER_MAP = {
    **{_header_key(header): field for header, field in zip(UPLOAD_HEADERS, UPLOAD_FIELDS)},
    **{_header_key(field): field for field in UPLOAD_FIELDS},
    # Common English aliases keep the local template easy to author while
    # still rejecting unknown columns rather than silently dropping data.
    "sessions": "session_count",
    "number of sessions": "session_count",
    "package": "package_code",
    "course package code": "package_code",
    "fee item code": "item_code",
    "created at": "created_date",
    "expires at": "expiry_date",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS finance_contracts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  contract_code TEXT NOT NULL UNIQUE,
  customer_type TEXT NOT NULL DEFAULT 'STUDENT',
  account_id INTEGER,
  student_id INTEGER,
  class_id INTEGER,
  course_id INTEGER,
  item_id INTEGER,
  package_name TEXT NOT NULL DEFAULT '',
  created_date TEXT NOT NULL,
  expiry_date TEXT,
  payment_due_date TEXT,
  payment_due_amount INTEGER,
  payment_note TEXT NOT NULL DEFAULT '',
  discount_code TEXT NOT NULL DEFAULT '',
  direct_discount INTEGER NOT NULL DEFAULT 0,
  total_amount INTEGER NOT NULL DEFAULT 0,
  paid_amount INTEGER NOT NULL DEFAULT 0,
  debt_amount INTEGER NOT NULL DEFAULT 0,
  sales_owner TEXT NOT NULL DEFAULT '',
  created_by TEXT NOT NULL DEFAULT '',
  payment_status TEXT NOT NULL DEFAULT 'PENDING',
  contract_status TEXT NOT NULL DEFAULT 'ACTIVE',
  note TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_finance_contract_code ON finance_contracts(contract_code);
CREATE INDEX IF NOT EXISTS idx_finance_contract_dates ON finance_contracts(created_date, expiry_date);
CREATE INDEX IF NOT EXISTS idx_finance_contract_status ON finance_contracts(payment_status, contract_status);
"""

UPLOAD_SCHEMA = """
CREATE TABLE IF NOT EXISTS finance_contract_uploads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  batch_id TEXT NOT NULL UNIQUE,
  actor TEXT NOT NULL,
  provenance TEXT NOT NULL,
  row_count INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'COMMITTED' CHECK(status IN ('COMMITTED','REJECTED')),
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS finance_contract_upload_rows (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  batch_id TEXT NOT NULL REFERENCES finance_contract_uploads(batch_id) ON DELETE CASCADE,
  row_number INTEGER NOT NULL,
  contract_code TEXT NOT NULL,
  student_code TEXT NOT NULL DEFAULT '',
  customer_code TEXT NOT NULL DEFAULT '',
  course_code TEXT NOT NULL DEFAULT '',
  session_count INTEGER NOT NULL DEFAULT 0,
  package_code TEXT NOT NULL DEFAULT '',
  item_code TEXT NOT NULL DEFAULT '',
  pre_discount_amount INTEGER NOT NULL DEFAULT 0,
  course_discount_code TEXT NOT NULL DEFAULT '',
  course_discount_amount INTEGER NOT NULL DEFAULT 0,
  after_course_discount INTEGER NOT NULL DEFAULT 0,
  contract_discount_code TEXT NOT NULL DEFAULT '',
  contract_discount_amount INTEGER NOT NULL DEFAULT 0,
  created_date TEXT NOT NULL,
  expiry_date TEXT,
  UNIQUE(batch_id, row_number)
);
CREATE INDEX IF NOT EXISTS idx_finance_contract_upload_rows_code ON finance_contract_upload_rows(contract_code);
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


def _money(value: Any, field: str, *, default: int = 0) -> int:
    if value in (None, ""):
        return default
    try:
        amount = Decimal(str(value).replace(",", "").replace(" VND", "").strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field} không hợp lệ") from exc
    if amount < 0 or amount != amount.quantize(Decimal("1")):
        raise ValueError(f"{field} phải là số nguyên không âm")
    return int(amount)


def payment_status_label(value: Any) -> str:
    return PAYMENT_STATUS_LABELS.get(str(value or ""), "")


def contract_status_label(value: Any) -> str:
    return CONTRACT_STATUS_LABELS.get(str(value or ""), "")


class FinanceContract:
    """SQLite-backed contract CRUD, filtering, summary, and CSV preview."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.db.executescript(UPLOAD_SCHEMA)
        self._converge_demo_rows()
        self.db.commit()

    @staticmethod
    def upload_template() -> str:
        """Return the local template for the observed upload table.

        The reference download body is private and was not fetched.  This
        deterministic UTF-8 CSV is therefore labelled as a local contract by
        ``UPLOAD_PROVENANCE`` and contains headings only; no customer rows are
        copied into the template.
        """
        out = io.StringIO(newline="")
        csv.writer(out).writerow(UPLOAD_HEADERS)
        return "\ufeff" + out.getvalue()

    @staticmethod
    def _upload_header_map(fieldnames: list[str] | None) -> dict[str, str]:
        names = [str(value or "").strip() for value in (fieldnames or [])]
        if not names:
            raise ValueError("Tệp CSV phải có dòng tiêu đề")
        mapped: dict[str, str] = {}
        unknown: list[str] = []
        duplicate: list[str] = []
        for name in names:
            field = _UPLOAD_HEADER_MAP.get(_header_key(name))
            if field is None:
                unknown.append(name)
            elif field in mapped.values():
                duplicate.append(name)
            else:
                mapped[name] = field
        missing = [field for field in UPLOAD_FIELDS if field not in mapped.values()]
        if unknown:
            raise ValueError("Cột CSV không được hỗ trợ: " + ", ".join(unknown))
        if duplicate:
            raise ValueError("Cột CSV bị lặp: " + ", ".join(duplicate))
        if missing:
            labels = [UPLOAD_HEADERS[UPLOAD_FIELDS.index(field)] for field in missing]
            raise ValueError("Thiếu cột CSV: " + ", ".join(labels))
        return mapped

    @staticmethod
    def _upload_session(value: Any, field: str) -> int:
        if value in (None, ""):
            return 0
        text = str(value).strip()
        try:
            result = int(text)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field} phải là số nguyên không âm") from exc
        if result < 0:
            raise ValueError(f"{field} phải là số nguyên không âm")
        return result

    @staticmethod
    def _optional_upload_money(value: Any, field: str) -> int | None:
        if value in (None, ""):
            return None
        return _money(value, field)

    def _parse_upload(self, text: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        if isinstance(text, bytes):
            if len(text) > UPLOAD_MAX_BYTES:
                raise ValueError("Tệp CSV tải lên quá lớn")
            try:
                text = text.decode("utf-8-sig")
            except UnicodeDecodeError as exc:
                raise ValueError("Tệp CSV phải dùng UTF-8") from exc
        if not isinstance(text, str) or len(text.encode("utf-8")) > UPLOAD_MAX_BYTES:
            raise ValueError("Tệp CSV tải lên quá lớn")
        reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
        mapping = self._upload_header_map(reader.fieldnames)
        rows: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        seen: set[str] = set()
        for row_number, source in enumerate(reader, start=2):
            # DictReader places surplus cells under None.  Reject them rather
            # than silently dropping an observed financial column.
            if None in source and any(str(value or "").strip() for value in (source.get(None) or [])):
                errors.append({"row": row_number, "message": "Số ô CSV vượt quá số cột tiêu đề"})
                continue
            raw = {field: source.get(header, "") for header, field in mapping.items()}
            try:
                code = _text(raw.get("contract_code"), "Mã hợp đồng", required=True, limit=80).upper()
                if code in seen:
                    raise ValueError("Mã hợp đồng bị lặp trong tệp")
                seen.add(code)
                created = _day(raw.get("created_date"), "Ngày tạo hợp đồng", required=True)
                expiry = _day(raw.get("expiry_date"), "Ngày hết hạn")
                if expiry and created and expiry < created:
                    raise ValueError("Ngày hết hạn không được trước ngày tạo hợp đồng")
                pre = _money(raw.get("pre_discount_amount"), "Tiền trước giảm giá", default=0)
                course_discount = _money(raw.get("course_discount_amount"), "Tiền giảm (khóa học)", default=0)
                contract_discount = _money(raw.get("contract_discount_amount"), "Tiền giảm giá (toàn bộ hợp đồng)", default=0)
                after = self._optional_upload_money(raw.get("after_course_discount"), "Tiền sau giảm")
                row = {
                    "contract_code": code,
                    "student_code": _text(raw.get("student_code"), "Mã học viên", limit=80),
                    "customer_code": _text(raw.get("customer_code"), "Mã khách hàng", limit=80),
                    "course_code": _text(raw.get("course_code"), "Mã khóa học", limit=80),
                    "session_count": self._upload_session(raw.get("session_count"), "Số buổi đăng ký"),
                    "package_code": _text(raw.get("package_code"), "Mã Gói học phí", limit=120),
                    "item_code": _text(raw.get("item_code"), "Mã khoản thu", limit=120),
                    "pre_discount_amount": pre,
                    "course_discount_code": _text(raw.get("course_discount_code"), "Mã giảm giá (khóa học)", limit=120),
                    "course_discount_amount": course_discount,
                    "after_course_discount": after,
                    "contract_discount_code": _text(raw.get("contract_discount_code"), "Mã giảm giá (toàn bộ hợp đồng)", limit=120),
                    "contract_discount_amount": contract_discount,
                    "created_date": created,
                    "expiry_date": expiry,
                    "gross_total_before_discount": self._optional_upload_money(raw.get("gross_total_before_discount"), "Tổng tiền trước giảm giá"),
                    "direct_discount": self._optional_upload_money(raw.get("direct_discount"), "Giảm giá trực tiếp"),
                    "gross_total_after_discount": self._optional_upload_money(raw.get("gross_total_after_discount"), "Tổng tiền sau giảm giá"),
                    "contract_note": _text(raw.get("contract_note"), "Ghi chú hợp đồng", limit=500),
                    "class_code": _text(raw.get("class_code"), "Mã lớp học", limit=80),
                    "start_date": _day(raw.get("start_date"), "Ngày bắt đầu học"),
                }
                if self.db.execute("SELECT 1 FROM finance_contracts WHERE contract_code=?", (code,)).fetchone():
                    raise ValueError("Mã hợp đồng đã tồn tại")
                rows.append(row)
            except (TypeError, ValueError) as exc:
                errors.append({"row": row_number, "message": str(exc)})
        return rows, errors

    def preview_upload(self, text: Any, *, role: str = "ADMIN") -> dict[str, Any]:
        self._write(role)
        rows, errors = self._parse_upload(text)
        return {
            "count": len(rows) + len(errors), "valid_count": len(rows), "rows": rows,
            "errors": errors, "mutation": False, "provenance": UPLOAD_PROVENANCE,
            "route": UPLOAD_ROUTE, "can_commit": False,
            "save_blockers": list(UPLOAD_SAVE_BLOCKERS),
            "validation_scope": "LOCAL_SYNTAX_AND_SAFE_TYPES_ONLY",
        }

    def commit_upload(self, text: Any, *, role: str, actor: str) -> dict[str, Any]:
        """Keep import writes blocked until all observed fields map truthfully."""
        self._write(role)
        preview = self.preview_upload(text, role=role)
        if preview["errors"]:
            raise ValueError("Tệp CSV có lỗi; chưa ghi dữ liệu")
        rows = preview["rows"]
        if not rows:
            raise ValueError("Tệp CSV phải có ít nhất một dòng dữ liệu")
        reason = "Lưu bị khóa vì lược đồ/API cục bộ chưa lưu được đủ các cột quan sát: " + " ".join(UPLOAD_SAVE_BLOCKERS)
        raise ValueError(reason)

    def upload_batch(self, batch_id: str, *, role: str = "ADMIN") -> dict[str, Any]:
        self._read(role)
        row = self.db.execute("SELECT * FROM finance_contract_uploads WHERE batch_id=?", (str(batch_id).strip(),)).fetchone()
        if row is None:
            raise KeyError("Lô upload không tồn tại")
        entries = self.db.execute("SELECT * FROM finance_contract_upload_rows WHERE batch_id=? ORDER BY row_number", (row["batch_id"],)).fetchall()
        return {"batch": dict(row), "rows": [dict(entry) for entry in entries], "provenance": row["provenance"]}

    def renewal_candidates(self, *, role: str = "ADMIN", class_id: Any = None, query: str = "") -> dict[str, Any]:
        """List local classes for the observed extension selector.

        The reference flow after selecting a class was not observed.  This
        method intentionally stops at the selector and labels its result as a
        local contract instead of inventing renewal accounting rules.
        """
        self._read(role)
        exists = self.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='classes'").fetchone()
        if not exists:
            return {"items": [], "total": 0, "data_status": "NO_DATA", "provenance": UPLOAD_PROVENANCE, "route": EXTENSION_ROUTE}
        where, args = ["1=1"], []
        if class_id not in (None, ""):
            try:
                where.append("c.id=?"); args.append(int(class_id))
            except (TypeError, ValueError) as exc:
                raise ValueError("Mã lớp học không hợp lệ") from exc
        if str(query or "").strip():
            needle = f"%{str(query).strip()}%"; where.append("(c.code LIKE ? OR co.code LIKE ? OR co.name LIKE ?)"); args.extend([needle] * 3)
        has_courses = self.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='courses'").fetchone()
        join = "LEFT JOIN courses co ON co.id=c.course_id" if has_courses else ""
        course = "co.code AS course_code,co.name AS course_name" if has_courses else "'' AS course_code,'' AS course_name"
        rows = self.db.execute(f"SELECT c.id,c.code,c.course_id,{course} FROM classes c {join} WHERE {' AND '.join(where)} ORDER BY c.code,c.id", args).fetchall()
        return {"items": [dict(row) for row in rows], "total": len(rows), "data_status": "LOCAL_SYNTHETIC", "provenance": UPLOAD_PROVENANCE, "route": EXTENSION_ROUTE}

    # Stable aliases for route adapters.  Keeping these names on the owned
    # store lets the shared HTTP layer map endpoints without reimplementing
    # CSV validation or the renewal-selector boundary.
    template_csv = upload_template
    preview = preview_upload
    get_extension_contract = renewal_candidates

    def _converge_demo_rows(self) -> None:
        """Converge known synthetic contract fixtures to natural identities."""
        rows = self.db.execute(
            "SELECT id,contract_code FROM finance_contracts WHERE contract_code GLOB 'DEMO-CONTRACT-[0-9][0-9][0-9]' ORDER BY id"
        ).fetchall()
        owners = ("Nguyễn Ngọc Mai", "Lê Hoàng Anh", "Trần Minh Tú", "Phạm Gia Huy")
        has_bills = self.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='finance_bills'").fetchone()
        for index, row in enumerate(rows, 1):
            old_code = str(row["contract_code"] or "")
            new_code = f"HD-EDU-{index:03d}"
            if old_code != new_code:
                self.db.execute("UPDATE finance_contracts SET contract_code=? WHERE id=?", (new_code, int(row["id"])))
                if has_bills:
                    self.db.execute("UPDATE finance_bills SET contract_code=? WHERE contract_code=?", (new_code, old_code))
            self.db.execute("UPDATE finance_contracts SET sales_owner=? WHERE id=? AND sales_owner='Academic Team'", (owners[(index - 1) % len(owners)], int(row["id"])))

    @staticmethod
    def _read(role: str) -> None:
        if role not in READ_ROLES:
            raise PermissionError("Hợp đồng không dành cho vai trò này")

    @staticmethod
    def _write(role: str) -> None:
        if role not in WRITE_ROLES:
            raise PermissionError("Chỉ ADMIN hoặc STAFF được quản lý hợp đồng")

    def _normalize(self, payload: Mapping[str, Any], current: Mapping[str, Any] | None = None) -> dict[str, Any]:
        value = dict(current or {})
        value.update(payload)
        total = _money(value.get("total_amount"), "Tổng tiền")
        paid = _money(value.get("paid_amount"), "Đã thanh toán")
        direct_discount = _money(value.get("direct_discount"), "Giảm giá trực tiếp")
        if paid > total:
            raise ValueError("Đã thanh toán không được lớn hơn tổng tiền")
        payment_status = str(value.get("payment_status") or "").strip().upper()
        if not payment_status:
            payment_status = "PAID" if paid == total and total else ("PARTIAL" if paid else "PENDING")
        if payment_status not in PAYMENT_STATUSES:
            raise ValueError("Trạng thái đóng tiền không hợp lệ")
        contract_status = str(value.get("contract_status") or "ACTIVE").strip().upper()
        if contract_status not in CONTRACT_STATUSES:
            raise ValueError("Trạng thái hợp đồng không hợp lệ")
        customer_type = str(value.get("customer_type") or "STUDENT").strip().upper()
        if customer_type not in {"LEAD", "STUDENT"}:
            raise ValueError("Đối tượng khách hàng không hợp lệ")
        return {
            "contract_code": _text(value.get("contract_code"), "Mã hợp đồng", required=True, limit=80),
            "customer_type": customer_type,
            "account_id": value.get("account_id") or value.get("student_id") or None,
            "student_id": value.get("student_id") or value.get("account_id") or None,
            "class_id": value.get("class_id") or None,
            "course_id": value.get("course_id") or None,
            "item_id": value.get("item_id") or None,
            "package_name": _text(value.get("package_name") or value.get("course_name"), "Khóa học đăng kí", limit=240),
            "created_date": _day(value.get("created_date"), "Ngày tạo", required=True),
            "expiry_date": _day(value.get("expiry_date"), "Ngày hết hạn"),
            "payment_due_date": _day(value.get("payment_due_date"), "Ngày hẹn đóng tiền"),
            "payment_due_amount": _money(value.get("payment_due_amount"), "Số tiền hẹn đóng", default=0),
            "payment_note": _text(value.get("payment_note"), "Ghi chú hẹn đóng tiền", limit=500),
            "discount_code": _text(value.get("discount_code"), "Ưu đãi", limit=160),
            "direct_discount": direct_discount,
            "total_amount": total,
            "paid_amount": paid,
            "debt_amount": total - paid,
            "sales_owner": _text(value.get("sales_owner"), "Nhân viên sale", limit=160),
            "payment_status": payment_status,
            "contract_status": contract_status,
            "note": _text(value.get("note"), "Ghi chú", limit=1000),
        }

    def list(self, filters: Mapping[str, Any] | None = None, *, role: str = "ADMIN", page: int = 1, page_size: int = 10) -> dict[str, Any]:
        self._read(role)
        filters = filters or {}
        page, page_size = max(int(page), 1), min(max(int(page_size), 1), 100)
        where, args = ["1=1"], []
        q = str(filters.get("q") or "").strip()
        if q:
            needle = f"%{q}%"
            where.append("(contract_code LIKE ? OR package_name LIKE ? OR sales_owner LIKE ? OR note LIKE ?)")
            args.extend([needle] * 4)
        for key in ("payment_status", "contract_status"):
            if filters.get(key):
                value = str(filters[key]).strip().upper()
                allowed = PAYMENT_STATUSES if key == "payment_status" else CONTRACT_STATUSES
                if value not in allowed:
                    raise ValueError("Bộ lọc trạng thái không hợp lệ")
                where.append(f"{key} = ?"); args.append(value)
        for key, op in (("date_from", ">="), ("date_to", "<="), ("expiry_from", ">="), ("expiry_to", "<=")):
            if filters.get(key):
                column = "created_date" if key.startswith("date_") else "expiry_date"
                where.append(f"{column} {op} ?"); args.append(_day(filters[key], key, required=True))
        if filters.get("course_id"):
            where.append("course_id = ?"); args.append(int(filters["course_id"]))
        if filters.get("sales_owner"):
            where.append("sales_owner LIKE ?"); args.append(f"%{str(filters['sales_owner']).strip()}%")
        if filters.get("creator"):
            where.append("CAST(created_by AS TEXT) LIKE ?"); args.append(f"%{str(filters['creator']).strip()}%")
        if filters.get("discount"):
            where.append("discount_code LIKE ?"); args.append(f"%{str(filters['discount']).strip()}%")
        base = " FROM finance_contracts WHERE " + " AND ".join(where)
        total = int(self.db.execute("SELECT COUNT(*)" + base, args).fetchone()[0])
        rows = self.db.execute("SELECT *" + base + " ORDER BY created_date DESC, id DESC LIMIT ? OFFSET ?", args + [page_size, (page - 1) * page_size]).fetchall()
        return {"items": [dict(row) for row in rows], "total": total, "page": page, "page_size": page_size, "pages": (total + page_size - 1) // page_size}

    def get(self, contract_id: int, *, role: str = "ADMIN") -> dict[str, Any]:
        self._read(role)
        row = self.db.execute("SELECT * FROM finance_contracts WHERE id = ?", (int(contract_id),)).fetchone()
        if row is None:
            raise KeyError("Hợp đồng không tồn tại")
        return dict(row)

    def create(self, payload: Mapping[str, Any], *, role: str, actor: str) -> dict[str, Any]:
        self._write(role); data = self._normalize(payload)
        now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        try:
            cur = self.db.execute(
                """INSERT INTO finance_contracts
                (contract_code,customer_type,account_id,student_id,class_id,course_id,item_id,package_name,created_date,expiry_date,payment_due_date,payment_due_amount,payment_note,discount_code,direct_discount,total_amount,paid_amount,debt_amount,sales_owner,created_by,payment_status,contract_status,note,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (data["contract_code"], data["customer_type"], data["account_id"], data["student_id"], data["class_id"], data["course_id"], data["item_id"], data["package_name"], data["created_date"], data["expiry_date"], data["payment_due_date"], data["payment_due_amount"], data["payment_note"], data["discount_code"], data["direct_discount"], data["total_amount"], data["paid_amount"], data["debt_amount"], data["sales_owner"], _text(actor, "Người tạo", required=True, limit=200), data["payment_status"], data["contract_status"], data["note"], now, now),
            )
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            self.db.rollback(); raise ValueError("Mã hợp đồng đã tồn tại") from exc
        return self.get(cur.lastrowid, role=role)

    def update(self, contract_id: int, payload: Mapping[str, Any], *, role: str, actor: str) -> dict[str, Any]:
        self._write(role); current = self.get(contract_id, role=role); data = self._normalize(payload, current)
        self.db.execute(
            """UPDATE finance_contracts SET contract_code=?,customer_type=?,account_id=?,student_id=?,class_id=?,course_id=?,item_id=?,package_name=?,created_date=?,expiry_date=?,payment_due_date=?,payment_due_amount=?,payment_note=?,discount_code=?,direct_discount=?,total_amount=?,paid_amount=?,debt_amount=?,sales_owner=?,payment_status=?,contract_status=?,note=?,updated_at=? WHERE id=?""",
            (data["contract_code"], data["customer_type"], data["account_id"], data["student_id"], data["class_id"], data["course_id"], data["item_id"], data["package_name"], data["created_date"], data["expiry_date"], data["payment_due_date"], data["payment_due_amount"], data["payment_note"], data["discount_code"], data["direct_discount"], data["total_amount"], data["paid_amount"], data["debt_amount"], data["sales_owner"], data["payment_status"], data["contract_status"], data["note"], datetime.utcnow().isoformat(timespec="seconds") + "Z", int(contract_id)),
        )
        self.db.commit(); return self.get(contract_id, role=role)

    def summary(self, filters: Mapping[str, Any] | None = None, *, role: str = "ADMIN") -> dict[str, int]:
        self._read(role); rows = self.list(filters, role=role, page=1, page_size=10000)["items"]
        return {"contract_count": len(rows), "subtotal": sum(int(r.get("total_amount") or 0) for r in rows), "paid": sum(int(r.get("paid_amount") or 0) for r in rows), "debt": sum(int(r.get("debt_amount") or 0) for r in rows), "refund": 0, "bad_debt": sum(int(r.get("debt_amount") or 0) for r in rows if r.get("payment_status") == "OVERDUE"), "co_wallet": 0}

    def export_csv(self, filters: Mapping[str, Any] | None = None, *, role: str = "ADMIN") -> str:
        rows = self.list(filters, role=role, page=1, page_size=10000)["items"]
        out = io.StringIO(); writer = csv.writer(out); writer.writerow(TABLE_HEADERS)
        for index, row in enumerate(rows, 1):
            writer.writerow([index, row.get("contract_code", ""), row.get("customer_name", ""), f"Tạo: {row.get('created_date', '')} HH: {row.get('expiry_date') or ''}", row.get("package_name", ""), f"{int(row.get('paid_amount') or 0):,} VND / {int(row.get('debt_amount') or 0):,} VND", row.get("sales_owner", ""), row.get("created_by", ""), payment_status_label(row.get("payment_status")), contract_status_label(row.get("contract_status")), row.get("note", ""), ""])
        return "\ufeff" + out.getvalue()


def route_contract() -> dict[str, Any]:
    return {
        "route": ROUTE,
        "routes": (ROUTE, UPLOAD_ROUTE, EXTENSION_ROUTE),
        "headers": TABLE_HEADERS,
        "filters": FILTERS,
        "upload_headers": UPLOAD_HEADERS,
        "upload_fields": UPLOAD_FIELDS,
        "upload_can_commit": False,
        "upload_save_blockers": UPLOAD_SAVE_BLOCKERS,
        "upload_template_route": f"{UPLOAD_ROUTE}/template",
        "upload_provenance": UPLOAD_PROVENANCE,
        "payment_status_options": [(k, v) for k, v in PAYMENT_STATUS_LABELS.items()],
        "contract_status_options": [(k, v) for k, v in CONTRACT_STATUS_LABELS.items()],
        "read_roles": sorted(READ_ROLES),
        "write_roles": sorted(WRITE_ROLES),
        "api_hooks": (
            "GET /api/finance/contracts",
            "POST /api/finance/contracts",
            "PATCH /api/finance/contracts/<id>",
            "POST /api/finance/contract/upload/preview",
            "POST /api/finance/contract/upload/commit",
            "GET /api/finance/contract/upload/template",
            "GET /api/finance/contract/get_extension_contract",
        ),
    }


def register(app_or_router: Any = None, service: Any = None) -> dict[str, Any]:
    target = service if service is not None else app_or_router
    _attach_store(target, "finance_contract_store", FinanceContract)
    return _register_metadata(app_or_router, service, name="finance_contract", routes=(ROUTE, UPLOAD_ROUTE, EXTENSION_ROUTE), schema="finance_contracts,finance_contract_uploads,finance_contract_upload_rows")


__all__ = [
    "FinanceContract", "ROUTE", "UPLOAD_ROUTE", "EXTENSION_ROUTE", "TABLE_HEADERS", "FILTERS",
    "UPLOAD_HEADERS", "UPLOAD_FIELDS", "UPLOAD_MAX_BYTES", "UPLOAD_PROVENANCE", "PAYMENT_STATUSES",
    "CONTRACT_STATUSES", "PAYMENT_STATUS_LABELS", "CONTRACT_STATUS_LABELS", "payment_status_label",
    "contract_status_label", "route_contract", "register",
    "UPLOAD_SAVE_BLOCKERS",
]
