"""Read-only finance report source adapters.

Each owned route maps to its persistent local finance domain. Missing source
tables return an empty result; generic report fallback is never used here.
"""
from __future__ import annotations

import sqlite3
import unicodedata
from dataclasses import replace
from typing import Any, Iterable, Mapping

FINANCE_ENTITIES = frozenset({
    "finance_revenues", "finance_bills", "contracts",
    "report_finance_revenue_center_by_month_center_index",
    "report_finance_class_revenue_tracking_index",
    "report_finance_class_revenue_tracking_new_index",
    "report_finance_revenue_center",
    "report_finance_revenue_center_by_month_sale_team_index",
    "report_finance_revenue_center_by_month_sale_index",
    "report_finance_revenue_source_index", "report_finance_debt",
    "report_finance_student_finance", "report_finance_revenue_item_index",
    "report_finance_revenue_item_export", "report_finance_inventory_item_index",
    "report_finance_payment_index", "report_crm_contract_index",
    "report_crm_bill_index", "report_finance_reserve",
})

# The reference inventory contains both the canonical report paths and these
# legacy ``.../index`` deep links.  Keep the aliases at the adapter boundary so
# the shared report specification remains the source of truth and both links
# execute against the same persistent finance entity.
FINANCE_ROUTE_ALIASES = {
    "/report/finance/revenue/index": "/report/finance/revenue_center",
    "/report/finance/student_finance/index": "/report/finance/student_finance",
}

PAYMENT_METHOD_KEYS = {
    "vi_co": ("vi co", "ví co", "wallet", "co wallet"),
    "tien_mat": ("cash", "tien mat", "tiền mặt"),
    "chuyen_khoan": ("bank transfer", "bank_transfer", "transfer", "chuyen khoan", "chuyển khoản"),
    "quet_the": ("card", "credit card", "debit card", "quet the", "quẹt thẻ"),
    "vimass": ("vimass",), "vnpay": ("vnpay",), "9pay": ("9pay", "9 pay"),
    "tra_gop": ("installment", "tra gop", "trả góp"), "napas": ("napas",),
}

# Stored enum values remain English in the local schema.  Report rows expose
# the Vietnamese labels used by the observed report tables.
STATUS_VI = {
    "OPEN": "Đang mở", "ACTIVE": "Hoạt động", "IN_PROGRESS": "Đang xử lý",
    "PLANNED": "Dự kiến", "COMPLETED": "Đã hoàn thành", "DONE": "Đã hoàn thành",
    "CANCELLED": "Đã hủy", "CANCELED": "Đã hủy", "PAID": "Đã thanh toán",
    "UNPAID": "Chưa thanh toán", "PARTIAL": "Còn nợ", "PENDING": "Chờ xử lý",
    "NEW": "Mới", "CONTACTED": "Đã liên hệ", "QUALIFIED": "Đủ điều kiện",
    "CONVERTED": "Đã chuyển đổi", "LOST": "Mất cơ hội", "GRADUATED": "Đã xong",
    "RENEWED": "Đã tái tục", "RENEWAL": "Đã tái tục",
}

# Incoming report filters use the observed Vietnamese labels, while SQLite
# keeps stable transport enums.  Keep this translation at the adapter edge;
# never write presentation labels back to a source table.
CONFIRMATION_STATUS_ALIASES = {
    "pending": "PENDING", "can xac nhan": "PENDING",
    "confirmed": "CONFIRMED", "da xac nhan": "CONFIRMED",
    "rejected": "REJECTED", "khong dong y": "REJECTED",
}
PAYMENT_STATUS_ALIASES = {
    "pending": "PENDING", "chua dong tien": "PENDING", "cho xu ly": "PENDING",
    "partial": "PARTIAL", "con no": "PARTIAL",
    "paid": "PAID", "dong du": "PAID", "da thanh toan": "PAID",
    "overdue": "OVERDUE", "qua han": "OVERDUE",
}
CONTRACT_STATUS_ALIASES = {
    "active": "ACTIVE", "dang thuc hien": "ACTIVE", "dang hoc": "ACTIVE", "cho lop": "ACTIVE",
    "expired": "EXPIRED", "hop dong het han": "EXPIRED",
    "cancelled": "CANCELLED", "canceled": "CANCELLED", "huy": "CANCELLED", "da huy": "CANCELLED",
    "completed": "COMPLETED", "hoan thanh": "COMPLETED", "da xong": "COMPLETED",
}


def _fold(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).casefold()
    # LATIN SMALL LETTER D WITH STROKE does not decompose under NFKD, but
    # observed Vietnamese labels use it in words such as ``Đã`` and ``Đóng``.
    text = text.replace("đ", "d")
    return "".join(c for c in text if not unicodedata.combining(c)).strip()


def _bucket(value: Any) -> str | None:
    folded = _fold(value)
    for key, aliases in PAYMENT_METHOD_KEYS.items():
        if folded in {_fold(alias) for alias in aliases}:
            return key
    return None


def _first(filters: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = filters.get(key)
        if value not in (None, ""):
            return value
    return ""


def _num(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _status(value: Any) -> Any:
    if isinstance(value, str):
        return STATUS_VI.get(value.upper(), value)
    return value


def _canonical_status(value: Any, aliases: Mapping[str, str]) -> str:
    """Normalize a stored enum or observed display label for filtering."""
    text = str(value or "").strip()
    if not text:
        return ""
    return aliases.get(_fold(text), text.upper())


def _vi_status_row(row: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(row)
    for key in ("status", "confirmation_status", "payment_status", "contract_status"):
        if key in out:
            out[key] = _status(out[key])
    return out


class FinanceReportProvider:
    """SQLite provider for the finance and finance-backed CRM reports."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self.db.row_factory = sqlite3.Row

    def _exists(self, table: str) -> bool:
        return bool(self.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone())

    def _has_column(self, table: str, column: str) -> bool:
        if not self._exists(table):
            return False
        return bool(self.db.execute(f"PRAGMA table_info({table})").fetchall() and self.db.execute(
            f"SELECT 1 FROM pragma_table_info(?) WHERE name=?", (table, column)
        ).fetchone())

    def _dates(self, filters: Mapping[str, Any], column: str) -> tuple[list[str], list[Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        start = _first(filters, "from_date", "date_from", "from_date_2", "from_date_bill", "tu_ngay")
        end = _first(filters, "to_date", "date_to", "to_date_2", "to_date_bill", "den_ngay")
        if start:
            clauses.append(f"{column} >= ?"); params.append(start)
        if end:
            clauses.append(f"{column} <= ?"); params.append(end)
        return clauses, params

    def query_report(self, *, entity: str, filters: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
        f = dict(filters or {})
        if entity == "report_finance_payment_index":
            f.setdefault("from_date", f.get("filter_0") or f.get("q", ""))
            f.setdefault("to_date", f.get("filter_1", ""))
            f.pop("q", None)
            f.pop("filter_0", None)
            f.pop("filter_1", None)
            return self._payment(f)
        if entity in {"finance_bills", "report_crm_bill_index"}:
            return self._bills(f)
        if entity in {"contracts", "report_crm_contract_index"}:
            return self._contracts(f)
        if entity == "report_finance_revenue_center":
            return self._revenue_center(f)
        if entity == "report_finance_revenue_center_by_month_center_index":
            return self._monthly(f, "center")
        if entity == "report_finance_revenue_center_by_month_sale_team_index":
            return self._monthly(f, "sales_team")
        if entity == "report_finance_revenue_center_by_month_sale_index":
            return self._monthly(f, "sales_owner")
        if entity in {"report_finance_class_revenue_tracking_index", "report_finance_class_revenue_tracking_new_index"}:
            return self._class_revenue(f, entity.endswith("_new_index"))
        if entity == "report_finance_revenue_source_index":
            return self._revenue_source(f)
        if entity in {"report_finance_debt", "report_finance_student_finance"}:
            return self._student_finance(f)
        if entity in {"report_finance_revenue_item_index", "report_finance_revenue_item_export", "report_finance_inventory_item_index"}:
            return self._items(entity, f)
        if entity == "report_finance_reserve":
            return self._reserves(f)
        if entity == "finance_revenues":
            return self._revenues(f)
        return []

    def _bills(self, f: Mapping[str, Any], *, presentation: bool = True) -> list[dict[str, Any]]:
        if not self._exists("finance_bills"):
            return []
        date_column = next((f"b.{name}" for name in ("invoice_date", "created_at") if self._has_column("finance_bills", name)), None)
        clauses, params = self._dates(f, date_column) if date_column else ([], [])
        if date_column is None and any(_first(f, key) for key in ("from_date", "date_from", "from_date_2", "from_date_bill", "tu_ngay", "to_date", "date_to", "to_date_2", "to_date_bill", "den_ngay")):
            return []
        center = _first(f, "center", "branch", "filter_1")
        if center and "centeronline" not in _fold(center) and self._has_column("finance_bills", "center"):
            clauses.append("b.center LIKE ?"); params.append(f"%{center}%")
        elif center and "centeronline" not in _fold(center):
            return []
        status = _first(f, "confirmation_status", "payment_status")
        if status and _fold(status) not in {"all", "tất cả", "tat ca", "chon trang thai", "chọn trạng thái"}:
            stored_status = _canonical_status(status, CONFIRMATION_STATUS_ALIASES)
            if stored_status not in {"PENDING", "CONFIRMED", "REJECTED"}:
                return []
            if not self._has_column("finance_bills", "confirmation_status"):
                return []
            clauses.append("b.confirmation_status=?"); params.append(stored_status)
        q = _first(f, "q", "query", "tim_trong_bang")
        if q:
            searchable = [name for name in ("invoice_code", "contract_code", "customer_name", "note") if self._has_column("finance_bills", name)]
            if searchable:
                clauses.append("(" + " OR ".join(f"b.{name} LIKE ?" for name in searchable) + ")")
                params.extend([f"%{q}%"] * len(searchable))
        has_contracts = (
            self._exists("finance_contracts")
            and self._has_column("finance_bills", "contract_code")
            and self._has_column("finance_contracts", "contract_code")
        )
        has_students = has_contracts and self._exists("students") and self._has_column("finance_contracts", "student_id") and self._has_column("students", "id")
        has_users = self._exists("users") and self._has_column("finance_bills", "created_by") and self._has_column("users", "id")
        joins = []
        contract_columns = "NULL AS package_name,NULL AS total_amount,NULL AS paid_amount,NULL AS debt_amount,NULL AS payment_status,NULL AS contract_status"
        student_columns = "NULL AS parent1_name,NULL AS parent1_phone"
        user_column = "NULL AS created_by_name"
        if has_contracts:
            joins.append("LEFT JOIN finance_contracts c ON c.contract_code=b.contract_code")
            def contract_col(name: str) -> str:
                return f"c.{name}" if self._has_column("finance_contracts", name) else f"NULL AS {name}"
            contract_columns = ",".join(contract_col(name) for name in ("package_name", "total_amount", "paid_amount", "debt_amount", "payment_status", "contract_status"))
            if has_students:
                joins.append("LEFT JOIN students s ON s.id=c.student_id")
                parent1 = "s.parent1_name" if self._has_column("students", "parent1_name") else "NULL"
                parent_phone = "s.parent1_phone" if self._has_column("students", "parent1_phone") else "NULL"
                student_columns = f"{parent1} AS parent1_name,{parent_phone} AS parent1_phone"
        if has_users:
            joins.append("LEFT JOIN users u ON u.id=b.created_by")
            user_column = "u.full_name AS created_by_name"
        def bill_col(name: str) -> str:
            return f"b.{name}" if self._has_column("finance_bills", name) else f"NULL AS {name}"
        source_column = next((name for name in ("source", "source_type", "referral_source", "customer_source") if self._has_column("finance_bills", name)), None)
        source_projection = f"b.{source_column} AS source" if source_column else "NULL AS source"
        has_team_membership = (
            self._exists("finance_report_team_memberships")
            and self._has_column("finance_report_team_memberships", "invoice_code")
            and self._has_column("finance_report_team_memberships", "team_name")
        )
        team_projection = "t.team_name AS sales_team" if has_team_membership else "NULL AS sales_team"
        team_join = "LEFT JOIN finance_report_team_memberships t ON t.invoice_code=b.invoice_code" if has_team_membership else ""
        query = f"""SELECT {bill_col('invoice_code')},{bill_col('contract_code')},{bill_col('class_code')},{bill_col('customer_name')},{bill_col('payment_amount')},
                    {bill_col('confirmation_status')},{bill_col('payment_method')},{bill_col('invoice_date')},{bill_col('center')},{bill_col('branch')},{bill_col('employee')},
                    {bill_col('sales_owner')},{bill_col('note')},{bill_col('created_at')},{source_projection},{team_projection},{contract_columns},{student_columns},{user_column}
                 FROM finance_bills b {' '.join(joins)} {team_join}"""
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        order_columns = [f"b.{name}" for name in ("invoice_date", "created_at") if self._has_column("finance_bills", name)]
        order_expr = f"COALESCE({','.join(order_columns)})" if len(order_columns) > 1 else (order_columns[0] if order_columns else "b.rowid")
        tie_breaker = "b.id" if self._has_column("finance_bills", "id") else "b.rowid"
        query += f" ORDER BY {order_expr} DESC,{tie_breaker} DESC LIMIT 500"
        rows = [dict(row) for row in self.db.execute(query, params).fetchall()]
        return [_vi_status_row(row) for row in rows] if presentation else rows

    def _payment(self, f: Mapping[str, Any]) -> list[dict[str, Any]]:
        totals: dict[str, dict[str, Any]] = {}
        for row in self._bills(f, presentation=False):
            center = str(row.get("center") or "")
            out = totals.setdefault(center, {"trung_tam": center, **{key: 0 for key in PAYMENT_METHOD_KEYS}, "tong_doanh_thu": 0})
            amount = _num(row.get("payment_amount")); out["tong_doanh_thu"] += amount
            key = _bucket(row.get("payment_method"))
            if key:
                out[key] += amount
        return list(totals.values())

    def _revenue_center(self, f: Mapping[str, Any]) -> list[dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = {}
        for row in self._bills(f, presentation=False):
            center = str(row.get("center") or "")
            out = grouped.setdefault(center, {"trung_tam": center, "doanh_thu_moi": 0, "doanh_thu_tai_tuc": 0, "doanh_thu_tam_tinh": 0, "thuc_thu": 0, "so_tien_no": 0})
            amount = _num(row.get("payment_amount")); out["doanh_thu_tam_tinh"] += amount; out["so_tien_no"] += _num(row.get("debt_amount"))
            if str(row.get("confirmation_status") or "").upper() == "CONFIRMED": out["thuc_thu"] += amount
            # The local contract schema has no renewal discriminator.  Use it
            # only when a persisted renewal value exists; COMPLETED is a
            # lifecycle state and must not be mistaken for a renewal.
            contract_status = str(row.get("contract_status") or "").upper()
            if contract_status in {"RENEWED", "RENEWAL", "RECURRING"}:
                out["doanh_thu_tai_tuc"] += amount
            else:
                out["doanh_thu_moi"] += amount
        return list(grouped.values())

    def _monthly(self, f: Mapping[str, Any], group_key: str) -> list[dict[str, Any]]:
        groups: dict[str, dict[str, Any]] = {}
        year = str(_first(f, "year")).replace("Năm", "").strip()
        if group_key == "sales_team" and not self._exists("finance_report_team_memberships"):
            return []
        for row in self._bills(f, presentation=False):
            date = str(row.get("invoice_date") or "")
            if year and year not in date[:4]: continue
            try: month = int(date[5:7])
            except (ValueError, IndexError): continue
            start_month = _first(f, "start_month", "from_month")
            end_month = _first(f, "end_month", "to_month")
            if start_month and month < int(str(start_month).replace("Tháng", "").strip()): continue
            if end_month and month > int(str(end_month).replace("Tháng", "").strip()): continue
            key = str(row.get(group_key) or "")
            # A sale-team report needs a persisted team membership dimension.
            # Missing memberships remain absent; sales_owner is a different
            # fact and must never be promoted to team identity.
            if group_key == "sales_team" and not key.strip(): continue
            def new_group() -> dict[str, Any]:
                value: dict[str, Any] = {
                    group_key: key, "trung_tam": key, "nhom_sale_thanh_vien": key,
                    "nhan_vien_sale": key, "doanh_thu_moi": 0,
                    "doanh_thu_tai_tuc": 0, "doanh_thu_tam_tinh": 0,
                    "thuc_thu": 0, "so_tien_no": 0,
                }
                # Keep the row contract stable across groups. The renderer
                # consumes repeated month metric keys; absent facts are real
                # zeroes, not missing columns or synthetic bill rows.
                for month_index in range(1, 13):
                    value[f"thang_{month_index}"] = 0
                    child_index = month_index + 1 if group_key == "sales_owner" else month_index
                    suffix = "" if child_index == 1 else f"_{child_index}"
                    for metric in (
                        "chi_tieu", "doanh_thu_moi", "doanh_thu_tai_tuc",
                        "doanh_thu_tam_tinh", "thuc_thu", "so_tien_no",
                        "no_xau", "hoan_tra", "thanh_toan_bang_vi_co",
                        "at_uoc_chi_tieu",
                    ):
                        value[f"{metric}{suffix}"] = 0
                return value

            out = groups.setdefault(key, new_group())
            amount = _num(row.get("payment_amount")); debt = _num(row.get("debt_amount")); paid = amount if str(row.get("confirmation_status") or "").upper() == "CONFIRMED" else 0
            out[f"thang_{month}"] = _num(out.get(f"thang_{month}")) + amount
            contract_status = str(row.get("contract_status") or "").upper()
            renewal = contract_status in {"RENEWED", "RENEWAL", "RECURRING"}
            if group_key == "sales_owner":
                if renewal: out["doanh_thu_tai_tuc"] += amount
                else: out["doanh_thu_moi"] += amount
                out["doanh_thu_tam_tinh"] = _num(out.get("doanh_thu_tam_tinh")) + amount
                out["so_tien_no"] += debt
                if paid: out["thuc_thu"] = _num(out.get("thuc_thu")) + paid
            # The reference report repeats the metric block for every month.
            # Emit those numbered keys from the same persisted bill facts so
            # the shared table projection does not render empty child cells.
            suffix_index = month
            out[f"chi_tieu{'' if suffix_index == 1 else f'_{suffix_index}'}"] = _num(out.get(f"chi_tieu{'' if suffix_index == 1 else f'_{suffix_index}'}"))
            # Sale view has a leading all-month metric block, so its repeated
            # child metrics are offset by one suffix after the month-one key.
            for metric, value in (("doanh_thu_moi", 0 if renewal else amount),
                                  ("doanh_thu_tai_tuc", amount if renewal else 0),
                                  ("doanh_thu_tam_tinh", amount), ("thuc_thu", paid),
                                  ("so_tien_no", debt)):
                child_index = month + 1 if group_key == "sales_owner" else month
                suffix = "" if child_index == 1 else f"_{child_index}"
                field = f"{metric}{suffix}"
                out[field] = _num(out.get(field)) + value
            overdue = _num(row.get("debt_amount")) if _canonical_status(row.get("payment_status"), PAYMENT_STATUS_ALIASES) == "OVERDUE" else 0
            wallet = amount if _bucket(row.get("payment_method")) == "vi_co" else 0
            for metric, value in (("no_xau", overdue), ("hoan_tra", 0), ("thanh_toan_bang_vi_co", wallet)):
                child_index = month + 1 if group_key == "sales_owner" else month
                suffix = "" if child_index == 1 else f"_{child_index}"
                field = f"{metric}{suffix}"
                out[field] = _num(out.get(field)) + value
            if group_key in {"center", "sales_team"}:
                field = f"at_uoc_chi_tieu{'' if month == 1 else f'_{month}'}"
                out[field] = _num(out.get(field))
            else:
                field = f"at_uoc_chi_tieu{'' if month == 1 else f'_{month}'}"
                out[field] = _num(out.get(field))
        return list(groups.values())

    def _class_revenue(self, f: Mapping[str, Any], new: bool) -> list[dict[str, Any]]:
        if not all(self._exists(table) for table in ("classes", "courses", "enrollments", "finance_contracts")):
            return []
        clauses, params = [], []
        q = _first(f, "q", "tim_trong_bang", "filter_7")
        if q and "chon" not in _fold(q): clauses.append("(c.code LIKE ? OR co.name LIKE ?)"); params.extend([f"%{q}%"] * 2)
        teacher_projection = "u.full_name AS teacher_name" if self._exists("users") else "NULL AS teacher_name"
        teacher_join = "LEFT JOIN users u ON u.id=c.teacher_id" if self._exists("users") else ""
        query = f"""SELECT c.code AS class_code,c.code AS class_name,co.name AS course_name,c.start_date,c.end_date,c.sessions_count,c.hours,c.max_students,{teacher_projection},
                    (SELECT COUNT(*) FROM enrollments e WHERE e.class_id=c.id AND e.status='ENROLLED') AS enrolled,
                    (SELECT COALESCE(SUM(f.total_amount),0) FROM finance_contracts f WHERE f.class_id=c.id) AS total_amount,
                    (SELECT COALESCE(SUM(f.paid_amount),0) FROM finance_contracts f WHERE f.class_id=c.id) AS paid_amount
                 FROM classes c JOIN courses co ON co.id=c.course_id {teacher_join}"""
        if clauses: query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY c.id DESC LIMIT 500"
        out = []
        for row in self.db.execute(query, params).fetchall():
            source = dict(row)
            total = _num(source["total_amount"]); paid = _num(source["paid_amount"])
            common = {
                "course_name": source["course_name"], "class_name": source["class_name"], "ten_lop": source["class_name"],
                "enrolled": source["enrolled"], "so_hoc_vien": source["enrolled"], "si_so": source["enrolled"],
                "doanh_thu_tong": total, "doanh_thu_tu_hoc_phi": total, "total_amount": total, "paid_amount": paid,
                "so_tien_luy_ke_a_ong_theo_hoa_on": paid, "gia_khoa_hoc": total, "teacher_name": source["teacher_name"],
                "start_date": source["start_date"], "end_date": source["end_date"], "sessions_count": source["sessions_count"],
                # Exact observed keys.  The shared projection layer cannot
                # infer these names from the local class schema.
                "hoc_phi_chua_vat": total, "gia_hoc_phi_goc_khoa_hoc": total,
                "so_gio_cua_khoa": source["hours"], "so_buoi_lop": source["sessions_count"],
                "gv_phu_trach": source["teacher_name"], "khai_giang": source["start_date"], "ket_thuc": source["end_date"],
                "phai_thu": total, "so_tien_luy_ke_a_ong_a_xuat_hoa_on_theo_bo_loc_thoi_gian_luy_ke_en_thoi_iem_gan_nhat": paid,
                "tong_hoc_phi_hoc_vien_moi": total, "so_tien_a_ong_luy_ke_theo_hoa_on": paid,
                "so_tien_a_ong_luy_ke_theo_hoa_on": paid, "doanh_thu_phan_bo_thang_theo_hop_ong": total,
                "dt_phan_bo_thang_theo_hoa_on": paid,
            }
            out.append(common)
        return out

    def _revenue_source(self, f: Mapping[str, Any]) -> list[dict[str, Any]]:
        # A bill ledger without a persisted source dimension cannot support a
        # source report.  Returning its totals under an empty source would
        # fabricate a grouping and make the report look populated.
        if not self._exists("finance_bills"):
            return []
        source_column = next((name for name in ("source", "source_type", "referral_source", "customer_source") if self._has_column("finance_bills", name)), None)
        if source_column is None:
            return []
        groups: dict[tuple[str, str], dict[str, Any]] = {}
        for row in self._bills(f, presentation=False):
            source = str(row.get("source") or "").strip()
            if not source:
                continue
            center = str(row.get("center") or "")
            out = groups.setdefault((source, center), {
                "nguon_khach_hang": source,
                "trung_tam_centeronline_demo": center,
                "doanh_thu_tam_tinh": 0,
                "thuc_thu": 0,
            })
            amount = _num(row.get("payment_amount"))
            out["doanh_thu_tam_tinh"] += amount
            if str(row.get("confirmation_status") or "").upper() == "CONFIRMED":
                out["thuc_thu"] += amount
        return list(groups.values())

    def _contracts(self, f: Mapping[str, Any], *, limit: int | None = 500, summary_source: bool = False) -> list[dict[str, Any]]:
        if not self._exists("finance_contracts"): return []
        clauses, params = [], []
        q = _first(f, "q", "ten_khach_hang", "ma_hop_dong")
        has_students = self._exists("students")
        has_classes = self._exists("classes")
        has_users = self._exists("users")
        if q and "chon" not in _fold(q):
            search = ["c.contract_code LIKE ?", "c.package_name LIKE ?"]
            if has_students:
                search.insert(1, "COALESCE(s.full_name,'') LIKE ?")
            clauses.append("(" + " OR ".join(search) + ")"); params.extend([f"%{q}%"] * len(search))
        start = _first(f, "from_date", "from_date_2", "from_date_bill")
        end = _first(f, "to_date", "to_date_2", "to_date_bill")
        if start: clauses.append("c.created_date >= ?"); params.append(start)
        if end: clauses.append("c.created_date <= ?"); params.append(end)
        expiry_start = _first(f, "from_date_expired_date", "expiry_from")
        expiry_end = _first(f, "to_date_expired_date", "expiry_to")
        if expiry_start: clauses.append("c.expiry_date >= ?"); params.append(expiry_start)
        if expiry_end: clauses.append("c.expiry_date <= ?"); params.append(expiry_end)
        status = _first(f, "payment_status", "filter_2")
        if status and _fold(status) not in {"all", "tất cả", "tat ca", "chon trang thai", "chọn trạng thái"}:
            stored_payment_status = _canonical_status(status, PAYMENT_STATUS_ALIASES)
            if stored_payment_status not in {"PENDING", "PARTIAL", "PAID", "OVERDUE"}:
                return []
            clauses.append("c.payment_status=?"); params.append(stored_payment_status)
        contract_status = _first(f, "contract_status", "filter_3")
        if contract_status and _fold(contract_status) not in {"all", "tất cả", "tat ca", "chon trang thai", "chọn trạng thái"}:
            stored_contract_status = _canonical_status(contract_status, CONTRACT_STATUS_ALIASES)
            if stored_contract_status not in {"ACTIVE", "EXPIRED", "CANCELLED", "COMPLETED"}:
                return []
            clauses.append("c.contract_status=?"); params.append(stored_contract_status)
        # The student-finance reports include invoice code.  It is a bill
        # property, not a contract property, so resolve the latest durable
        # bill by the contract's persisted join key.  Keep the source absent
        # when the bill ledger is not installed; never copy a contract code
        # into the invoice column.
        invoice_column = "NULL AS invoice_code"
        if self._exists("finance_bills") and self._has_column("finance_bills", "invoice_code") and self._has_column("finance_bills", "contract_code"):
            bill_order = "COALESCE(b.invoice_date,b.created_at)" if self._has_column("finance_bills", "invoice_date") and self._has_column("finance_bills", "created_at") else "b.rowid"
            invoice_column = f"(SELECT b.invoice_code FROM finance_bills b WHERE b.contract_code=c.contract_code ORDER BY {bill_order} DESC,b.rowid DESC LIMIT 1) AS invoice_code"
        student_projection = "COALESCE(s.full_name,'') AS student_name" if has_students else "'' AS student_name"
        student_id_projection = "c.student_id AS student_id" if self._has_column("finance_contracts", "student_id") else "NULL AS student_id"
        student_code_projection = "NULL AS student_code"
        if self._has_column("finance_contracts", "student_code"):
            student_code_projection = "c.student_code AS student_code"
        elif has_students and self._has_column("students", "student_code"):
            student_code_projection = "s.student_code AS student_code"
        private_projection = f",{student_id_projection},{student_code_projection}" if summary_source else ""
        amounts = ",".join(f"c.{name}" if self._has_column("finance_contracts", name) else f"NULL AS {name}" for name in ("total_amount", "paid_amount", "debt_amount"))
        class_projection = "COALESCE(cl.code,'') AS class_code" if has_classes else "'' AS class_code"
        creator_projection = "CASE WHEN u.full_name IS NOT NULL AND u.full_name != '' THEN u.full_name ELSE COALESCE(CAST(c.created_by AS TEXT), '') END AS created_by_name" if has_users else "CAST(c.created_by AS TEXT) AS created_by_name"
        joins = []
        if has_students: joins.append("LEFT JOIN students s ON s.id=c.student_id")
        if has_classes: joins.append("LEFT JOIN classes cl ON cl.id=c.class_id")
        if has_users: joins.append("LEFT JOIN users u ON u.id=c.created_by")
        query = f"""SELECT c.contract_code,c.customer_type,c.package_name,c.created_date,c.expiry_date,{amounts},c.sales_owner,c.payment_status,c.contract_status,c.note,{invoice_column},{student_projection}{private_projection},{class_projection},{creator_projection}
                 FROM finance_contracts c {' '.join(joins)}"""
        if clauses: query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY c.created_date DESC,c.id DESC"
        if limit is not None:
            query += f" LIMIT {int(limit)}"
        return [_vi_status_row(row) for row in self.db.execute(query, params).fetchall()]

    def _student_finance(self, f: Mapping[str, Any]) -> list[dict[str, Any]]:
        rows = self._contracts(f)
        for row in rows:
            row.update({"full_name": row.get("student_name"), "payment_amount": row.get("paid_amount"), "amount_due": row.get("total_amount"), "course_name": row.get("package_name")})
        return rows

    def query_report_summary(self, *, entity: str, filters: Mapping[str, Any]) -> Mapping[str, Any] | None:
        """Return explicit persisted contract aggregates for finance reports only."""
        if entity not in {"report_finance_debt", "report_finance_student_finance"}:
            return None
        if not self._exists("finance_contracts"):
            return {}
        rows = self._contracts(dict(filters or {}), limit=None, summary_source=True)
        summary: dict[str, Any] = {}
        for key in ("total_amount", "paid_amount", "debt_amount"):
            if self._has_column("finance_contracts", key) and all(isinstance(row.get(key), (int, float)) for row in rows):
                summary[key] = sum(row[key] for row in rows)
        # Count only a complete stable dimension, never names or mixed IDs/codes.
        for key in ("student_id", "student_code"):
            if rows and all(row.get(key) not in (None, "") for row in rows):
                summary["student_count"] = len({row[key] for row in rows})
                break
        return summary

    def _items(self, entity: str, f: Mapping[str, Any]) -> list[dict[str, Any]]:
        if not self._exists("finance_items"): return []
        # The current local schema stores the item catalogue only.  Export
        # movement rows require a persisted movement table; do not project
        # catalogue rows into an export report.
        if entity == "report_finance_revenue_item_export":
            movement_table = next((t for t in ("finance_item_exports", "finance_item_movements", "inventory_movements") if self._exists(t)), None)
            # Catalog rows are not sales movements. If no durable movement
            # ledger exists, truthfully return NO_DATA rather than projecting
            # inventory into an export report.
            if movement_table is None:
                return []
            return self._movement_rows(movement_table, f)
        q = _first(f, "q", "tim_kiem", "nhap_ten_san_pham"); clauses=[]; params=[]
        if q: clauses.append("(code LIKE ? OR fullname LIKE ? OR category LIKE ?)"); params.extend([f"%{q}%"] * 3)
        start = _first(f, "from_date", "date_from")
        end = _first(f, "to_date", "date_to")
        if start: clauses.append("start_date >= ?"); params.append(start)
        if end: clauses.append("start_date <= ?"); params.append(end)
        branch = _first(f, "branch", "filter_1")
        if branch and _fold(branch) not in {"all", "tat ca", "chon trung tam", "centeronline"}:
            clauses.append("branch LIKE ?"); params.append(f"%{branch}%")
        query = "SELECT code,category,fullname,description,branch,quantity,sale_price,price_adjustment,status,start_date AS created_date FROM finance_items"
        if clauses: query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY id DESC LIMIT 500"
        rows = [_vi_status_row(row) for row in self.db.execute(query, params).fetchall()]
        out = []
        for row in rows:
            # Item catalogue -> stock report.  Values are persisted catalogue
            # facts; movement-only fields stay absent instead of fabricated.
            out.append({**row, "ma_vat_pham": row.get("code"), "vat_pham": row.get("fullname"),
                        "danh_muc_vat_pham": row.get("category"), "mo_ta_vat_pham": row.get("description"),
                        "trung_tam": row.get("branch"), "ngay_nhap": row.get("created_date"),
                        "ton_kho": row.get("quantity"), "on_gia_nhap": row.get("sale_price"),
                        "on_gia": row.get("sale_price"), "ton_cuoi_thang": row.get("quantity")})
        return out

    def _movement_rows(self, table: str, f: Mapping[str, Any]) -> list[dict[str, Any]]:
        """Project an optional persisted movement ledger without assuming columns."""
        cols = {str(r[1]) for r in self.db.execute(f"PRAGMA table_info({table})").fetchall()}
        aliases = {
            "ma_vat_pham": ("item_code", "code", "product_code"),
            "vat_pham": ("item_name", "fullname", "name"),
            "ngay_xuat": ("movement_date", "export_date", "created_at"),
            "khach_hang": ("customer_name", "student_name"),
            "ly_do_xuat": ("reason", "note"),
            "so_luong_xuat": ("quantity", "export_quantity"),
            "on_gia_xuat": ("unit_price", "sale_price"),
            "tong_tien": ("total_amount", "amount"),
            "giam_gia": ("discount", "discount_amount"),
            "thanh_tien": ("net_amount", "paid_amount", "total_amount", "amount"),
        }
        select = []
        for label, candidates in aliases.items():
            source = next((c for c in candidates if c in cols), None)
            select.append(f"m.{source} AS {label}" if source else f"NULL AS {label}")
        q = _first(f, "q", "tim_kiem", "nhap_ten_san_pham"); args=[]; where=[]
        searchable = [c for c in ("item_code", "code", "item_name", "fullname", "customer_name") if c in cols]
        if q and searchable:
            where.append("(" + " OR ".join(f"m.{c} LIKE ?" for c in searchable) + ")"); args.extend([f"%{q}%"] * len(searchable))
        date_col = next((c for c in ("movement_date", "export_date", "created_at") if c in cols), None)
        if date_col:
            start = _first(f, "from_date", "date_from"); end = _first(f, "to_date", "date_to")
            if start: where.append(f"m.{date_col} >= ?"); args.append(start)
            if end: where.append(f"m.{date_col} <= ?"); args.append(end)
        sql = "SELECT " + ",".join(select) + f" FROM {table} m"
        if where: sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY m.rowid DESC LIMIT 500"
        return [dict(r) for r in self.db.execute(sql, args).fetchall()]

    def _reserves(self, f: Mapping[str, Any]) -> list[dict[str, Any]]:
        if not self._exists("finance_reserves"): return []
        q = _first(f, "q", "tim_trong_bang"); query = "SELECT student_name,reserve_date,amount_or_days,contract_code,course_name,status,created_by FROM finance_reserves"; params=[]
        clauses = []
        if q: clauses.extend(["reserve_code LIKE ?", "student_name LIKE ?", "course_name LIKE ?"]); params.extend([f"%{q}%"] * 3)
        start = _first(f, "from_date", "date_from")
        end = _first(f, "to_date", "date_to")
        if start: clauses.append("reserve_date >= ?"); params.append(start)
        if end: clauses.append("reserve_date <= ?"); params.append(end)
        if clauses: query += " WHERE " + " OR ".join(clauses)
        query += " ORDER BY reserve_date DESC,id DESC LIMIT 500"
        return [_vi_status_row(row) for row in self.db.execute(query, params).fetchall()]

    def _revenues(self, f: Mapping[str, Any]) -> list[dict[str, Any]]:
        if not self._exists("finance_revenues"): return []
        q = _first(f, "q", "query"); query = "SELECT code,name,status,price,discount_value,amount_due,center,created_at AS created_date,note FROM finance_revenues"; params=[]
        if q: query += " WHERE code LIKE ? OR name LIKE ? OR note LIKE ?"; params.extend([f"%{q}%"] * 3)
        query += " ORDER BY id DESC LIMIT 500"
        return [dict(row) for row in self.db.execute(query, params).fetchall()]


def _install_report_adapter(service: Any) -> bool:
    """Install the finance source at the coordinator provider seam.

    The shared provider historically fell through to its generic query when a
    finance adapter returned an empty list.  That turns a valid source gap
    (for example, item movement export without a movement table) into a row
    from another domain.  This owned wrapper preserves an empty result for all
    finance entities while delegating unrelated entities to the prior query.
    """
    engine = getattr(service, "report_engine_v2", None)
    provider = getattr(engine, "provider", None)
    original = getattr(provider, "query_report", None)
    if provider is None or not callable(original):
        return False
    if getattr(provider, "_w5_finance_report_adapter_installed", False):
        return True

    adapter = getattr(provider, "finance_adapter", None)
    if not isinstance(adapter, FinanceReportProvider):
        adapter = FinanceReportProvider(getattr(service, "db"))
        provider.finance_adapter = adapter

    def query_report(*, entity: str, filters: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
        if entity in FINANCE_ENTITIES:
            return list(adapter.query_report(entity=entity, filters=filters))
        return original(entity=entity, filters=filters)

    original_summary = getattr(provider, "query_report_summary", None)

    def query_report_summary(*, entity: str, filters: Mapping[str, Any]) -> Mapping[str, Any] | None:
        if entity in FINANCE_ENTITIES:
            return adapter.query_report_summary(entity=entity, filters=filters)
        return original_summary(entity=entity, filters=filters) if callable(original_summary) else None

    provider.query_report = query_report
    provider.query_report_summary = query_report_summary
    provider._w5_finance_report_adapter_installed = True
    provider._w5_finance_report_adapter_original = original
    return True


def _install_route_aliases(service: Any) -> bool:
    """Expose observed finance deep links without a generic fallback.

    Aliases are copied from an existing loaded definition.  If the canonical
    definition is absent, the alias is left absent (fail closed) rather than
    inventing a report contract.
    """
    engine = getattr(service, "report_engine_v2", None)
    definitions = getattr(engine, "definitions", None)
    if not isinstance(definitions, dict):
        return False
    changed = False
    for alias, canonical in FINANCE_ROUTE_ALIASES.items():
        if alias in definitions:
            continue
        definition = definitions.get(canonical)
        if definition is None:
            continue
        definitions[alias] = replace(definition, route=alias, slug=alias.strip("/").replace("/", "_"))
        changed = True
    return changed or all(alias in definitions for alias in FINANCE_ROUTE_ALIASES)


def register(app_or_router: Any = None, service: Any = None) -> dict[str, Any]:
    """Register finance report entities with the coordinator autoloader."""
    target = service if service is not None else app_or_router
    installed = _install_report_adapter(target)
    aliases_installed = _install_route_aliases(target)
    return {
        "routes": sorted(set(FINANCE_ENTITIES) | set(FINANCE_ROUTE_ALIASES)),
        "source": "persistent-sqlite",
        "status": "ADAPTER_READY" if installed else "PENDING_PROVIDER",
        "route_aliases": sorted(FINANCE_ROUTE_ALIASES),
        "route_aliases_installed": aliases_installed,
        "schema": "finance_bills,finance_contracts,finance_items,finance_reserves",
        "seed": "none",
    }


__all__ = ["FinanceReportProvider", "FINANCE_ENTITIES", "FINANCE_ROUTE_ALIASES", "register"]
