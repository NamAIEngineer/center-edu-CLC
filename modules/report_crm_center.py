"""Route-specific CRM and Center report source adapters.

Only persistent local domain tables are read.  A missing domain table yields an
empty result so the report engine can expose ``NO_DATA`` instead of a generic
row from another domain.
"""
from __future__ import annotations

import sqlite3
import unicodedata
from typing import Any, Iterable, Mapping, Protocol

ROUTE_PREFIXES = ("/report/crm/", "/report/center/", "/report/cso/", "/report/callcenter/")
READ_ROLES = frozenset({"ADMIN", "STAFF", "TEACHER", "STUDENT"})
UTILITY_ROUTE_CONTRACTS = {
    "/cso/support": {"title": "Hỗ trợ", "tabs": ["Tiếp nhận từ người dùng", "Hỗ trợ nội bộ"], "columns": ["No.", "Thời gian", "Loại", "Nội dung", "Người gửi", "Lớp của học viên", "Nhân viên", "Trạng thái", ""], "filters": ["status", "type", "from_date", "to_date", "query"], "actions": ["Excel", "Tạo"]},
    "/callcenter/get-statistic": {"title": "Thống kê cuộc gọi vào", "tabs": ["Thống kê cuộc gọi vào", "Thống kê cuộc gọi ra"], "columns": ["No.", "Nhân viên nghe", "Nhóm sale", "Trung tâm", "Tổng cuộc gọi", "Cuộc gọi thành công", "Cuộc gọi nhỡ", "Thất bại"], "filters": ["from_date", "to_date"], "actions": ["Xuất excel"]},
    "/center/upload_address": {"title": "Tool chinh sửa địa chỉ", "tabs": ["Công cụ chỉnh sửa địa chỉ học sinh", "Công cụ chỉnh sửa địa chỉ khách hàng tiềm năng"], "columns": ["No.", "Chi nhánh", "Mã học viên", "Học viên", "Mã định danh", "Tên tiếng anh", "Giới tính", "Ngày sinh", "Tài khoản", "SĐT", "Email", "Tỉnh cũ", "Huyện cũ", "Xã phường", "Tỉnh mới", "Phường xã mới"], "filters": ["file"], "page_sizes": [5, 10, 25, 50], "actions": ["Lưu"]},
    "/tenant/config_excel": {"title": "Cấu hình xuất excel báo cáo", "tabs": ["Cấu hình xuất excel báo cáo"], "columns": ["No.", "Báo cáo", "Tắt/bật excel báo cáo", "Tất cả", ""], "filters": ["check_all", "publish_export_excel[]"], "actions": []},
}

ROUTE_ENTITY_MAP = {
    "/report/crm/contract/index": "report_crm_contract_index",
    "/report/crm/bill/index": "report_crm_bill_index",
    "/report/crm/customer_care/index": "report_crm_customer_care_index",
    "/report/crm/customer_care_result_by_center": "report_crm_customer_care_result_by_center",
    "/report/crm/customer_care_result_by_district": "report_crm_customer_care_result_by_district",
    "/report/crm/customer_care_result_by_dob": "report_crm_customer_care_result_by_dob",
    "/report/crm/customer_care_result_by_source": "report_crm_customer_care_result_by_source",
    "/report/crm/customer_care_result_by_sale": "report_crm_customer_care_result_by_sale",
    "/report/crm/customer_care_result": "report_crm_customer_care_result",
    "/report/crm/customer_report/index": "report_crm_customer_report_index",
    "/report/crm/customer_statistic/index": "report_crm_customer_statistic_index",
    "/report/crm/customer_trailer": "report_crm_customer_trailer",
    "/report/center/student_statistical/index": "report_center_student_statistical_index",
    "/report/center/birth_day/index": "report_center_birth_day_index",
    "/report/center/access_history": "report_center_access_history",
    "/report/center/staff_teacher": "report_center_staff_teacher",
    "/report/center/class_post/index": "report_center_class_post_index",
}
CRM_CENTER_ENTITIES = frozenset(ROUTE_ENTITY_MAP.values())

STATUS_VI = {
    "OPEN": "Đang mở", "ACTIVE": "Hoạt động", "IN_PROGRESS": "Đang xử lý",
    "PLANNED": "Dự kiến", "COMPLETED": "Đã hoàn thành", "DONE": "Đã hoàn thành",
    "CANCELLED": "Đã hủy", "CANCELED": "Đã hủy", "PAID": "Đã thanh toán",
    "UNPAID": "Chưa thanh toán", "PARTIAL": "Còn nợ", "PENDING": "Chờ xử lý",
    "NEW": "Mới", "CONTACTED": "Đã liên hệ", "QUALIFIED": "Đủ điều kiện",
    "CONVERTED": "Đã chuyển đổi", "LOST": "Mất cơ hội", "GRADUATED": "Đã xong",
    "INACTIVE": "Ngừng hoạt động", "ENROLLED": "Đang học", "PAUSED": "Bảo lưu", "DROPPED": "Nghỉ học",
    "RESERVED": "Bảo lưu", "TRANSFERRED": "Đã chuyển lớp", "SUSPENDED": "Tạm dừng",
    "ABSENT": "Vắng không phép", "EXCUSED": "Vắng có phép", "PRESENT": "Có mặt",
    "LATE": "Đi muộn", "DRAFT": "Bản nháp", "PUBLISHED": "Đã công bố",
    "SCHEDULED": "Đã lên lịch", "CONFIRMED": "Đã xác nhận", "WAITING": "Đang chờ",
    "APPROVED": "Đã duyệt", "REJECTED": "Từ chối", "BOOKED": "Đã đặt lịch",
    "SCORED": "Đã chấm", "OVERDUE": "Quá hạn", "ACTIVE_CONTRACT": "Đang hiệu lực",
}

ROLE_VI = {
    "ADMIN": "Quản trị viên", "STAFF": "Nhân viên", "TEACHER": "Giáo viên", "STUDENT": "Học viên",
}

CUSTOMER_TYPE_VI = {
    "STUDENT": "Học viên đang học",
    "LEAD": "Khách hàng tiềm năng",
}

DEMO_IDENTITY_VI = {
    # The rich local fixture uses stable identifiers so joins remain
    # deterministic.  Reports expose customer-facing Vietnamese names/codes,
    # never fixture-internal English seed labels.
    "Academic Team": "Phòng học vụ",
    "Center Administrator": "Quản trị trung tâm",
}


class SourceProvider(Protocol):
    def query_report(self, *, entity: str, filters: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]: ...


def is_owned_route(route: str) -> bool:
    return route.startswith(ROUTE_PREFIXES) or route in UTILITY_ROUTE_CONTRACTS


def utility_contract(route: str) -> dict[str, Any]:
    """Return a copy of an observed utility screen contract; fail closed."""
    if route not in UTILITY_ROUTE_CONTRACTS:
        raise KeyError(f"unknown utility route: {route}")
    return dict(UTILITY_ROUTE_CONTRACTS[route])


def _fold(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).casefold()
    return "".join(c for c in text if not unicodedata.combining(c)).strip()


def _status(value: Any) -> Any:
    if isinstance(value, str):
        text = value.strip()
        if not text or text.casefold() in {"unknown", "chưa cập nhật"}:
            return ""
        mapped = STATUS_VI.get(text.upper())
        if mapped:
            return mapped
        if text.upper() == text and all(char.isalnum() or char in "_-" for char in text):
            return ""
        return text
    return value


def _role(value: Any) -> Any:
    if isinstance(value, str):
        text = value.strip()
        if not text or text.casefold() in {"unknown", "chưa cập nhật"}:
            return ""
        mapped = ROLE_VI.get(text.upper())
        if mapped:
            return mapped
        if text.upper() == text and all(char.isalnum() or char in "_-" for char in text):
            return ""
        return text
    return value


def _action(value: Any) -> Any:
    labels = {"CALL": "Gọi", "PHONE": "Gọi", "MESSAGE": "Nhắn tin", "SMS": "Nhắn tin",
              "CHAT": "Nhắn tin", "MEETING": "Gặp trực tiếp", "IN_PERSON": "Gặp trực tiếp",
              "NOTE": "Ghi chú", "APPOINTMENT": "Đặt lịch"}
    if isinstance(value, str):
        text = value.strip()
        if not text or text.casefold() in {"unknown", "chưa cập nhật"}:
            return ""
        mapped = labels.get(text.upper())
        if mapped:
            return mapped
        if text.upper() == text and all(char.isalnum() or char in "_-" for char in text):
            return ""
        return text
    return value


def _customer_type(value: Any) -> Any:
    if isinstance(value, str):
        text = value.strip()
        if not text or text.casefold() in {"unknown", "chưa cập nhật"}:
            return ""
        mapped = CUSTOMER_TYPE_VI.get(text.upper())
        if mapped:
            return mapped
        if text.upper() == text and all(char.isalnum() or char in "_-" for char in text):
            return ""
        return text
    return value


def _clean_report_value(value: Any) -> Any:
    """Keep internal evidence markers out of customer-facing row values."""
    if isinstance(value, str) and value.strip().casefold() in {"unknown", "chưa cập nhật"}:
        return ""
    return value


def _natural_identity(value: Any) -> Any:
    if isinstance(value, str):
        if value in DEMO_IDENTITY_VI:
            return DEMO_IDENTITY_VI[value]
        if value.startswith("DEMO-CONTRACT-"):
            return value.replace("DEMO-CONTRACT-", "HD-EDU-")
    return value


def normalize_row(row: Mapping[str, Any]) -> dict[str, Any]:
    source = dict(row); out = dict(source)
    aliases = {
        "full_name": ("student_name", "customer_name", "name"),
        "student_name": ("full_name", "customer_name", "name"),
        "customer_name": ("full_name", "student_name", "name"),
        "student_code": ("ma_hoc_vien", "ma_hoc_sinh"),
        "contract_code": ("ma_hop_dong",),
        "invoice_code": ("ma_hoa_don",),
        "status": ("contract_status", "payment_status", "student_status"),
        "center": ("branch", "center_name"),
        "branch": ("center", "center_name"),
        "sales_owner": ("sale_owner", "employee", "staff_name"),
        # Do not infer a contract creation date from a prospect creation date.
        # Routes that need a prospect ingest date expose it under its own
        # observed Vietnamese column.
    }
    for key, candidates in aliases.items():
        if out.get(key) not in (None, ""): continue
        for candidate in candidates:
            if source.get(candidate) not in (None, ""):
                out[key] = source[candidate]; break
    for key, value in list(out.items()):
        if key in {"status", "contract_status", "payment_status", "student_status", "trang_thai", "trang_thai_kh"}:
            out[key] = _status(value)
        if key in {"role", "phan_quyen"}:
            out[key] = _role(value)
        if key in {"action_type", "hanh_ong"}:
            out[key] = _action(value)
        if key in {"customer_type", "o_tuong_kh"}:
            out[key] = _customer_type(value)
        if key in {"created_by_name", "sales_owner", "sale_owner", "employee", "staff_name"}:
            out[key] = _natural_identity(value)
        if key in {"contract_code", "ma_hop_dong"}:
            out[key] = _natural_identity(value)
        out[key] = _clean_report_value(out[key])
    return out


def _resolve_finance_customer_names(rows: Iterable[Mapping[str, Any]], db: sqlite3.Connection | None) -> list[dict[str, Any]]:
    """Replace fixture-only bill customer labels with the persisted student name.

    Finance bills keep the contract code as their durable join key.  The
    rich-demo seed stores ``Demo Customer N`` in the bill table, while the
    contract table links the same code to a real student row.  Resolve that
    join at the CRM report boundary so customer-facing tables never expose a
    generic fixture identity or invent a name when the join is absent.
    """
    if db is None:
        return [normalize_row(row) for row in rows]
    try:
        has_contracts = CrmCenterReportAdapter._exists(db, "finance_contracts")
        has_students = CrmCenterReportAdapter._exists(db, "students")
    except (sqlite3.Error, AttributeError):
        has_contracts = has_students = False
    names: dict[str, str] = {}
    if has_contracts and has_students:
        try:
            names = {
                str(row["contract_code"]): str(row["full_name"])
                for row in db.execute(
                    """SELECT c.contract_code, s.full_name
                       FROM finance_contracts c JOIN students s ON s.id=c.student_id
                       WHERE COALESCE(s.full_name,'')<>''"""
                ).fetchall()
            }
        except sqlite3.Error:
            names = {}
    out: list[dict[str, Any]] = []
    for raw in rows:
        row = dict(raw)
        contract_code = str(row.get("contract_code") or row.get("ma_hop_ong") or "")
        current = str(row.get("customer_name") or row.get("khach_hang") or "")
        if contract_code in names and (not current or current.casefold().startswith("demo customer")):
            row["customer_name"] = names[contract_code]
            row["khach_hang"] = names[contract_code]
        out.append(normalize_row(row))
    return out


class CrmCenterReportAdapter:
    def __init__(self, provider: SourceProvider):
        self.provider = provider
        self.missing_entities: set[str] = set()

    def entity_for_route(self, route: str) -> str:
        if not is_owned_route(route):
            raise ValueError(f"route outside CRM/CENTER scope: {route}")
        return ROUTE_ENTITY_MAP.get(route, route.strip("/").replace("/", "_"))

    def _db(self) -> sqlite3.Connection | None:
        """Recover the host SQLite connection without changing shared wiring."""
        owner = getattr(self.provider, "provider", None) or self.provider
        service = getattr(owner, "service", None) or owner
        db = getattr(service, "db", None)
        return db if isinstance(db, sqlite3.Connection) else None

    @staticmethod
    def _exists(db: sqlite3.Connection, table: str) -> bool:
        return bool(db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone())

    @staticmethod
    def _date_where(filters: Mapping[str, Any], column: str) -> tuple[list[str], list[Any]]:
        clauses: list[str] = []; params: list[Any] = []
        start = next((filters.get(k) for k in ("from_date", "date_from", "tu_ngay") if filters.get(k)), "")
        end = next((filters.get(k) for k in ("to_date", "date_to", "den_ngay") if filters.get(k)), "")
        if start: clauses.append(f"{column} >= ?"); params.append(start)
        if end: clauses.append(f"{column} <= ?"); params.append(end)
        return clauses, params

    def _local_rows(self, entity: str, filters: Mapping[str, Any]) -> list[dict[str, Any]] | None:
        db = self._db()
        if db is None:
            return None
        q = str(filters.get("q") or filters.get("query") or filters.get("tim_trong_bang") or filters.get("nhap_ten_hoc_vien") or filters.get("tim_theo_ten") or "").strip()
        center = self._center_name(db)
        if entity == "report_center_staff_teacher" and self._exists(db, "users"):
            clauses = ["role IN ('TEACHER','STAFF')"]; params: list[Any] = []
            if q: clauses.append("(full_name LIKE ? OR username LIKE ?)"); params.extend([f"%{q}%"] * 2)
            if filters.get("filter_5") and _fold(filters["filter_5"]) not in {"tat ca", "chon chuc danh"}:
                clauses.append("role=?"); params.append(str(filters["filter_5"]).upper())
            if filters.get("from_date"):
                clauses.append("date(created_at) >= date(?)"); params.append(filters["from_date"])
            if filters.get("to_date"):
                clauses.append("date(created_at) <= date(?)"); params.append(filters["to_date"])
            return [dict(row, trang_thai=("Hoạt động" if row["active"] else "Ngừng hoạt động"),
                         trung_tam_chi_nhanh=center, chuc_danh=_role(row["role"]), phong_ban=_role(row["role"]), phan_quyen=_role(row["role"]))
                    for row in db.execute("SELECT full_name,username,date_of_birth,phone,email,active,role FROM users WHERE " + " AND ".join(clauses) + " ORDER BY full_name", params).fetchall()]
        if entity == "report_center_access_history" and self._exists(db, "users") and self._exists(db, "sessions"):
            # Access history is event-backed.  Users with no session event are
            # not history rows and must not be projected as zero activity.
            if not db.execute("SELECT 1 FROM sessions LIMIT 1").fetchone():
                return []
            return [dict(row, trung_tam=center, hoc_vien=row["full_name"], so_lan_ang_nhap=row["login_count"],
                         lan_ang_nhap_cuoi=row["last_login"], phan_quyen=_role(row["role"]),
                         trang_thai=("Hoạt động" if row["active"] else "Ngừng hoạt động"))
                    for row in db.execute("""SELECT u.full_name,u.username,u.role, u.active,
                COUNT(s.id) AS login_count,
                MAX(CASE WHEN typeof(s.last_seen_at)='integer' THEN datetime(s.last_seen_at,'unixepoch') ELSE s.last_seen_at END) AS last_login
                FROM users u JOIN sessions s ON s.user_id=u.id
                GROUP BY u.id ORDER BY last_login DESC,u.full_name""").fetchall()]
        if entity == "report_center_student_statistical_index" and self._exists(db, "students") and self._exists(db, "classes") and self._exists(db, "enrollments"):
            clauses, params = [], []
            if filters.get("from_date"):
                clauses.append("date(e.enrolled_at) >= date(?)"); params.append(filters["from_date"])
            if filters.get("to_date"):
                clauses.append("date(e.enrolled_at) <= date(?)"); params.append(filters["to_date"])
            where = " WHERE " + " AND ".join(clauses) if clauses else ""
            row = db.execute("""SELECT
                COUNT(DISTINCT CASE WHEN c.status IN ('OPEN','IN_PROGRESS','ACTIVE') THEN c.id END) AS active_classes,
                COUNT(DISTINCT CASE WHEN e.status='ENROLLED' THEN e.student_id END) AS ending_students,
                COUNT(DISTINCT CASE WHEN e.status='ENROLLED' AND s.status='ACTIVE' THEN e.student_id END) AS active_students,
                COUNT(DISTINCT CASE WHEN s.status='NEW' THEN s.id END) AS new_students,
                COUNT(DISTINCT CASE WHEN s.status IN ('PAUSED','INACTIVE') THEN s.id END) AS paused_students,
                COUNT(DISTINCT CASE WHEN s.status='RESERVED' THEN s.id END) AS reserved_students,
                COUNT(DISTINCT CASE WHEN s.status IN ('TRANSFERRED','MOVED') THEN s.id END) AS transferred_students,
                COUNT(DISTINCT CASE WHEN s.status IN ('GRADUATED','COMPLETED') THEN s.id END) AS completed_students
                FROM classes c LEFT JOIN enrollments e ON e.class_id=c.id LEFT JOIN students s ON s.id=e.student_id""" + where, params).fetchone()
            return [dict(row, trung_tam=center, so_lop_ang_hoc=row["active_classes"],
                         so_luong_hoc_vien_au_thang=row["ending_students"], hoc_vien_moi=row["new_students"],
                         nghi_hoc=row["paused_students"], bao_luu=row["reserved_students"],
                         bao_luu_i_hoc_lai=0, chuyen_lop=row["transferred_students"], a_xong=row["completed_students"],
                         so_luong_hoc_vien_cuoi_thang=row["active_students"])]
        if entity == "report_center_birth_day" or entity == "report_center_birth_day_index":
            if not self._exists(db, "students"):
                return []
            # A birthday report row requires a persisted birthday dimension.
            # A student roster without a date is not a birthday event.
            clauses, params = ["COALESCE(s.date_of_birth,'')<>''"], []
            if q: clauses.append("(s.full_name LIKE ? OR s.student_code LIKE ?)"); params.extend([f"%{q}%"] * 2)
            if filters.get("filter_4") and str(filters["filter_4"]).isdigit():
                clauses.append("CAST(substr(s.date_of_birth,6,2) AS INTEGER)=?"); params.append(int(filters["filter_4"]))
            where = " WHERE " + " AND ".join(clauses) if clauses else ""
            return [dict(row, ho_ten=row["full_name"], phu_huynh=row["parent1_name"], ngay_sinh=row["date_of_birth"],
                         lop=row["class_codes"], ca_hoc=row["schedule"],
                         # These fields are event-backed in the reference
                         # system.  Keep them absent when no durable gift or
                         # message event exists; the renderer shows an empty
                         # cell instead of inventing delivery state.
                         qua_tang=None, ngay_tang=None, trang_thai=_status(row["status"]),
                         trang_thai_loi_chuc=None, ngay_hen_gui=None, hanh_ong=None)
                    for row in db.execute("""SELECT s.full_name,s.parent1_name,s.date_of_birth,s.status,s.class_codes,
                        COALESCE((SELECT GROUP_CONCAT(c.schedule,'; ') FROM classes c WHERE instr('|'||s.class_codes||'|','|'||c.code||'|')>0),'') AS schedule
                        FROM students s""" + where + " ORDER BY substr(s.date_of_birth,6,5),s.full_name", params).fetchall()]
        if entity == "report_crm_customer_report_index" and self._exists(db, "potential_customers"):
            clauses, params = [], []
            if q: clauses.append("(full_name LIKE ? OR customer_code LIKE ?)"); params.extend([f"%{q}%"] * 2)
            if filters.get("filter_2") and _fold(filters["filter_2"]) not in {"tat ca", "chon nhan vien"}:
                clauses.append("sale_owner=?"); params.append(filters["filter_2"])
            date_clauses, date_params = self._date_where(filters, "created_at"); clauses.extend(date_clauses); params.extend(date_params)
            where = " WHERE " + " AND ".join(clauses) if clauses else ""
            return [dict(row,
                         ma_khach_hang=row["customer_code"], chi_nhanh_kh=row["branch"], trang_thai_kh=_status(row["status"]),
                         ket_qua_cham_soc=row["care_progress"], nhan_vien_sale=row["sale_owner"],
                         ngay_ua_khach_hang_len_he_thong=row["created_at"], ngay_sinh=row["date_of_birth"],
                         ghi_chu=row["note"], nguon_kh=row["source"], khoa_hoc_chinh=row["interested_course"])
                    for row in db.execute("SELECT full_name,customer_code,branch,status,care_progress,sale_owner,created_at,source,interested_course,date_of_birth,phone,email,note FROM potential_customers" + where + " ORDER BY id DESC", params).fetchall()]
        if entity == "report_crm_customer_care_index" and self._exists(db, "potential_customers"):
            clauses, params = self._date_where(filters, "p.created_at")
            if q: clauses.append("(p.full_name LIKE ? OR p.customer_code LIKE ?)"); params.extend([f"%{q}%"] * 2)
            where = " WHERE " + " AND ".join(clauses) if clauses else ""
            return [dict(row, ten_khach_hang_thong_tin_chung=row["customer_name"], nhap_len_he_thong=row["created_at"],
                sale_phu_trach_ngay_chuyen_cho_sale=row["sale_owner"], ngay_test=row["test_appointment"],
                trang_thai=_status(row["status"]), khoa_hoc_ang_ky=row["interested_course"])
                for row in db.execute("""SELECT p.full_name AS customer_name,p.source,p.sale_owner,p.status,p.created_at,
                p.care_course,p.interested_course,p.care_progress,p.test_appointment,p.test_score,
                COALESCE(SUM(CASE WHEN f.outcome='Chăm sóc thành công' THEN 1 ELSE 0 END),0) AS successful_care
                FROM potential_customers p LEFT JOIN potential_customer_followups f ON f.potential_customer_id=p.id""" + where + " GROUP BY p.id ORDER BY p.id DESC", params).fetchall()]
        if entity.startswith("report_crm_customer_care_result_by_") and self._exists(db, "potential_customers"):
            suffix = entity.rsplit("_by_", 1)[1]
            if suffix == "district":
                district_column = "ward" if self._has_column(db, "potential_customers", "ward") else ("district" if self._has_column(db, "potential_customers", "district") else None)
                if district_column is None:
                    # Branch is not a district. Do not substitute a generic
                    # dimension when the persisted schema has no district.
                    return []
                else:
                    dimension = district_column
            else:
                dimension = {"center": "branch", "dob": "substr(date_of_birth,1,4)", "source": "source", "sale": "sale_owner"}[suffix]
            label = {"center": "facility", "district": "district", "dob": "nam_sinh", "source": "nguon_du_lieu", "sale": "nhan_vien"}[suffix]
            date_clauses, date_params = self._date_where(filters, "created_at")
            where = " WHERE " + " AND ".join(date_clauses) if date_clauses else ""
            rows = [dict(row) for row in db.execute(f"SELECT COALESCE({dimension},'') AS dimension, COUNT(*) AS customer_count, SUM(CASE WHEN status='CONVERTED' THEN 1 ELSE 0 END) AS converted, SUM(CASE WHEN status='LOST' THEN 1 ELSE 0 END) AS lost, SUM(CASE WHEN status='NEW' THEN 1 ELSE 0 END) AS new_count FROM potential_customers{where} GROUP BY {dimension} ORDER BY customer_count DESC", date_params).fetchall()]
            out = []
            for row in rows:
                total = int(row.get("customer_count") or 0); converted = int(row.get("converted") or 0); lost = int(row.get("lost") or 0); new_count = int(row.get("new_count") or 0)
                out.append({label: row.get("dimension") or "", "so_luong_khach_hang": total, "kh_ong_y": converted, "kh_tu_choi": lost, "khach_hang_moi": new_count, "so_luong": total, "ti_le": round(converted * 100 / total, 2) if total else 0, "so_luong_2": converted, "ti_le_2": round(converted * 100 / total, 2) if total else 0, "so_luong_3": lost, "ti_le_3": round(lost * 100 / total, 2) if total else 0})
            return out
        if entity == "report_crm_customer_statistic_index" and self._exists(db, "potential_customers"):
            rows = [dict(row) for row in db.execute("SELECT COALESCE(source,'') AS source, COUNT(*) AS total, SUM(CASE WHEN status IN ('CONTACTED','QUALIFIED','CONVERTED') THEN 1 ELSE 0 END) AS cared, SUM(CASE WHEN trial_status<>'' THEN 1 ELSE 0 END) AS trial, SUM(CASE WHEN test_appointment<>'' THEN 1 ELSE 0 END) AS tested, SUM(CASE WHEN status='CONVERTED' THEN 1 ELSE 0 END) AS successful FROM potential_customers GROUP BY source ORDER BY total DESC").fetchall()]
            out = []
            for row in rows:
                total = int(row["total"] or 0); cared = int(row["cared"] or 0); trial = int(row["trial"] or 0); tested = int(row["tested"] or 0); successful = int(row["successful"] or 0)
                out.append(dict(row, nguon_du_lieu=row["source"], tong=total, khach_hang_cham_soc=cared,
                                khach_hang_hoc_thu=trial, khach_hang_test_hen_test=tested,
                                khach_hang_cham_soc_thanh_cong=successful, so_luong=cared, ti_le=round(cared*100/total,2) if total else 0,
                                so_luong_2=trial, ti_le_2=round(trial*100/total,2) if total else 0,
                                so_luong_3=tested, ti_le_3=round(tested*100/total,2) if total else 0,
                                so_luong_4=successful, ti_le_4=round(successful*100/total,2) if total else 0))
            return out
        if entity == "report_crm_customer_trailer" and self._exists(db, "potential_customers"):
            clauses, params = self._date_where(filters, "p.created_at")
            # This report is trial/test backed.  Exclude ordinary prospects
            # without a trial marker or test appointment.
            clauses.append("(COALESCE(p.trial_status,'')<>'' OR COALESCE(p.test_appointment,'')<>'')")
            if q: clauses.append("p.full_name LIKE ?"); params.append(f"%{q}%")
            where = " WHERE " + " AND ".join(clauses) if clauses else ""
            return [dict(row, ngay=row["test_date"], ho_ten=row["full_name"], trung_tam=row["branch"], trang_thai=_status(row["status"]),
                         ket_qua=row["trial_status"], nhan_vien_sale=row["sale_owner"])
                    for row in db.execute("SELECT p.test_appointment AS test_date,p.full_name,p.customer_code,p.branch,p.status,p.sale_owner,p.interested_course,p.trial_status FROM potential_customers p" + where + " ORDER BY p.test_appointment DESC,p.created_at DESC", params).fetchall()]
        if entity == "report_crm_customer_care_result" and self._exists(db, "potential_customer_followups") and self._exists(db, "potential_customers"):
            clauses, params = self._date_where(filters, "f.created_at")
            where = " WHERE " + " AND ".join(clauses) if clauses else ""
            rows = db.execute("""SELECT p.branch,f.action_type,f.outcome,f.created_at
                FROM potential_customer_followups f JOIN potential_customers p ON p.id=f.potential_customer_id""" + where + " ORDER BY f.created_at DESC,f.id DESC", params).fetchall()
            out = []
            for row in rows:
                action = _action(row["action_type"]); outcome = str(row["outcome"] or "")
                out.append({"trung_tam": row["branch"], "hanh_ong": action, "ket_qua": outcome,
                            "gap_truc_tiep": 1 if action == "Gặp trực tiếp" else 0,
                            "nhan_tin": 1 if action == "Nhắn tin" else 0,
                            "goi": 1 if action == "Gọi" else 0,
                            "kh_tu_choi": 1 if "từ chối" in _fold(outcome) or "lost" in _fold(outcome) else 0,
                            "kh_ong_y": 1 if "thành công" in _fold(outcome) or "đồng ý" in _fold(outcome) else 0,
                            "created_at": row["created_at"]})
            return out
        if entity == "report_center_class_post_index":
            # Class-post reporting is backed by the durable local event table.
            # A roster alone is never enough: when no event has been persisted
            # the report remains explicit NO_DATA.  Once events exist, classes
            # are grouped with their enrolled count and the published event
            # aggregate; this is a real report join, not a generic screen row.
            required = ("class_post_events", "classes", "enrollments", "users")
            if not all(self._exists(db, table) for table in required):
                self.missing_entities.add(entity)
                return []
            if not db.execute(
                "SELECT 1 FROM class_post_events WHERE status='PUBLISHED' LIMIT 1"
            ).fetchone():
                self.missing_entities.add(entity)
                return []
            clauses: list[str] = []
            params: list[Any] = []
            class_query = str(filters.get("chon_lop_hoc") or filters.get("nhap_ten_lop") or "").strip()
            if class_query:
                clauses.append("(c.code LIKE ? OR c.room LIKE ? OR co.name LIKE ?)")
                needle = f"%{class_query}%"
                params.extend([needle, needle, needle])
            status_filter = str(filters.get("filter_3") or filters.get("status") or "").strip()
            status_map = {
                "Chưa học": "PLANNED", "Đang học": "IN_PROGRESS", "Sắp kết thúc": "OPEN",
                "Đã xong": "COMPLETED", "Hủy lớp": "CANCELLED", "Chưa có lịch học": "PLANNED",
                "PLANNED": "PLANNED", "OPEN": "OPEN", "IN_PROGRESS": "IN_PROGRESS",
                "COMPLETED": "COMPLETED", "CANCELLED": "CANCELLED",
            }
            if status_filter and status_filter not in {"Tất cả", "Chọn trạng thái lớp"}:
                clauses.append("c.status=?")
                params.append(status_map.get(status_filter, status_filter))
            # Date controls in the observed report are day-based.  Make the
            # end date inclusive for timestamped events; comparing directly
            # with ``YYYY-MM-DD`` would silently discard posts later that day.
            date_clauses, date_params = self._date_where(filters, "p.posted_at")
            # ``_date_where`` returns all bound values in the same order as
            # its clauses (from-date, then to-date).  Only the final bound
            # value is the inclusive upper bound.
            for index, value in enumerate(date_params):
                if index != len(date_params) - 1:
                    continue
                if isinstance(value, str) and len(value) == 10:
                    date_params[index] = value + " 23:59:59"
            clauses.extend(date_clauses)
            params.extend(date_params)
            where = " WHERE " + " AND ".join(clauses) if clauses else ""
            rows = db.execute(
                """SELECT c.code AS ten_lop,
                          CASE c.status WHEN 'PLANNED' THEN 'Chưa học'
                                       WHEN 'OPEN' THEN 'Đang học'
                                       WHEN 'IN_PROGRESS' THEN 'Đang học'
                                       WHEN 'COMPLETED' THEN 'Đã xong'
                                       WHEN 'CANCELLED' THEN 'Hủy lớp'
                                       ELSE c.status END AS trang_thai,
                          COUNT(DISTINCT e.student_id) AS so_luong_hoc_vien,
                          COUNT(DISTINCT CASE WHEN p.status='PUBLISHED' THEN p.id END) AS so_luong_bai_ang,
                          MAX(CASE WHEN p.status='PUBLISHED' THEN p.posted_at END) AS thoi_iem_bai_ang_cuoi_cung,
                          (SELECT u.full_name FROM class_post_events lp
                             JOIN users u ON u.id=lp.author_id
                            WHERE lp.class_id=c.id AND lp.status='PUBLISHED'
                            ORDER BY lp.posted_at DESC,lp.id DESC LIMIT 1) AS nguoi_ang_bai
                     FROM classes c
                     JOIN courses co ON co.id=c.course_id
                     LEFT JOIN enrollments e ON e.class_id=c.id AND e.status='ENROLLED'
                     LEFT JOIN class_post_events p ON p.class_id=c.id AND p.status='PUBLISHED'""" + where +
                " GROUP BY c.id ORDER BY c.id DESC",
                params,
            ).fetchall()
            return [dict(row) for row in rows]
        return None

    @staticmethod
    def _has_column(db: sqlite3.Connection, table: str, column: str) -> bool:
        return bool(db.execute("SELECT 1 FROM pragma_table_info(?) WHERE name=?", (table, column)).fetchone())

    @staticmethod
    def _center_name(db: sqlite3.Connection) -> str:
        for table in ("finance_bills", "finance_revenues"):
            if not CrmCenterReportAdapter._exists(db, table):
                continue
            try:
                row = db.execute(f"SELECT center FROM {table} WHERE COALESCE(center,'')<>'' ORDER BY id LIMIT 1").fetchone()
            except sqlite3.OperationalError:
                row = None
            if row:
                return str(row[0])
        return ""

    def query_report(self, *, entity: str, filters: Mapping[str, Any], route: str | None = None) -> Iterable[Mapping[str, Any]]:
        if route is not None and not is_owned_route(route):
            raise ValueError(f"route outside CRM/CENTER scope: {route}")
        try:
            local_rows = self._local_rows(entity, filters)
            if local_rows is not None:
                return [normalize_row(row) for row in local_rows]
            # Once this adapter owns the entity, a missing local table is a
            # truthful source gap.  Never recurse through the wrapped provider
            # or project a generic row from another domain.
            if entity in CRM_CENTER_ENTITIES:
                self.missing_entities.add(entity)
                return []
            return [normalize_row(row) for row in self.provider.query_report(entity=entity, filters=filters)]
        except sqlite3.OperationalError as exc:
            if "no such table" not in str(exc).lower(): raise
            self.missing_entities.add(entity)
            return []

    def run_owned(self, engine: Any, route: str, *, filters: Mapping[str, Any] | None = None, group_by: str | None = None, limit: int = 100) -> dict[str, Any]:
        if not is_owned_route(route):
            raise ValueError(f"route outside CRM/CENTER scope: {route}")
        definition = engine.definition(route); entity = self.entity_for_route(route)
        rows = list(self.query_report(entity=entity, filters=filters or {}, route=route))
        projected = [engine._project(row, definition, index) for index, row in enumerate(rows[:max(1, min(int(limit), 10000))], 1)]
        return {"route": route, "title": definition.title, "columns": list(definition.columns), "filters": list(definition.filters), "rows": projected, "data_status": "OBSERVED" if projected else "NO_DATA", "source_entity": entity, "source_missing": entity in self.missing_entities}


def _install_report_adapter(service: Any) -> bool:
    """Install CRM/Center source routing at the coordinator provider seam."""
    engine = getattr(service, "report_engine_v2", None)
    provider = getattr(engine, "provider", None)
    original = getattr(provider, "query_report", None)
    if provider is None or not callable(original):
        return False
    if getattr(provider, "_w5_crm_center_report_adapter_installed", False):
        return True

    adapter = getattr(provider, "crm_adapter", None)
    if not isinstance(adapter, CrmCenterReportAdapter):
        adapter = CrmCenterReportAdapter(getattr(provider, "_adapter_source", provider))
        provider.crm_adapter = adapter

    def query_report(*, entity: str, filters: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
        # Finance owns the two finance-backed CRM grids.  Let the prior
        # wrapper serve their joins/filters, then apply this lane's customer
        # labels at the report boundary.  The shared engine projects raw
        # finance keys directly, so doing this here avoids English enum text
        # leaking into the customer-facing CRM report.
        if entity in {"report_crm_contract_index", "report_crm_bill_index"}:
            rows = original(entity=entity, filters=filters)
            db = adapter._db()
            return _resolve_finance_customer_names(rows, db)
        if entity in CRM_CENTER_ENTITIES:
            return list(adapter.query_report(entity=entity, filters=filters))
        return original(entity=entity, filters=filters)

    provider.query_report = query_report
    provider._w5_crm_center_report_adapter_installed = True
    provider._w5_crm_center_report_adapter_original = original
    return True


def register(app_or_router: Any = None, service: Any = None) -> dict[str, Any]:
    """Register CRM and Center report entities with coordinator autoload."""
    target = service if service is not None else app_or_router
    installed = _install_report_adapter(target)
    return {
        "routes": sorted(ROUTE_ENTITY_MAP),
        "source": "persistent-sqlite",
        "status": "ADAPTER_READY" if installed else "PENDING_PROVIDER",
        "schema": "users,sessions,students,classes,enrollments,potential_customers,potential_customer_followups",
        "seed": "none",
    }


__all__ = ["CrmCenterReportAdapter", "ROUTE_ENTITY_MAP", "CRM_CENTER_ENTITIES", "ROUTE_PREFIXES", "UTILITY_ROUTE_CONTRACTS", "utility_contract", "READ_ROLES", "normalize_row", "register"]
