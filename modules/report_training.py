"""Training report adapters backed by the persisted learning tables.

The adapter owns the semantic contract for ``/report/training/test``.  It
keeps the source enums in SQLite, but exposes the observed Vietnamese report
columns and accepts the filter names emitted by the reference form.  Empty
source data stays empty; no report row is invented here.
"""
from __future__ import annotations

import sqlite3
from typing import Any, Iterable, Mapping


STATUS_LABELS = {
    "DRAFT": "Bản nháp",
    "OPEN": "Đang mở",
    "CLOSED": "Đã đóng",
}

# Observed attendance legend. Stored enum values remain internal; report
# consumers can render this note without exposing English status tokens.
ATTENDANCE_LEGEND_NOTE = "M: Đi học · CP: Vắng có phép · KP: Vắng không phép · -: Chưa có dữ liệu"


# The coordinator's module autoloader uses these declarations to keep the
# report-provider seam explicit.  The list is intentionally limited to W4's
# training and teacher routes; unrelated report providers remain untouched.
TRAINING_REPORT_ENTITIES = (
    "report_training_attendance",
    "report_training_test",
    "report_training_daily_evaluation_index",
    "report_training_class_v2",
    "report_training_tuition_class_index",
    "report_training_allocation_student_index",
    "report_training_change_class_index",
    "report_training_reserve_training_index",
    "report_training_homework_ratio_index",
    "report_training_attendance_center_index",
    "report_training_using_course_index",
    "report_training_enroll_index",
    "report_training_allocation_hours_index",
    "report_training_schedule_index",
    "report_training_diligence_index",
    "report_training_register_learning",
    "report_training_student_pause",
    "report_training_student_training_v2",
    "report_training_due_date_student",
    "report_training_absent_classes",
    "report_training_top_notebook",
    "report_training_student_drop_index",
    "report_training_new_enrollment_index",
    "report_training_require_support_index",
    "report_training_instead_teacher",
    "report_training_examination_month_index",
)

TEACHER_REPORT_ENTITIES = (
    "report_teacher_sth_index",
    "report_teacher_rest_learning",
)

RESULT_LABELS = {
    "scored": "Đã chấm",
    "pending": "Chưa chấm",
}

# Inventory evidence marks these routes as chart/shell views or as having no
# observed local source. Keep their metadata explicit so adapters do not add
# fabricated columns or placeholder rows.
REPORT_NO_DATA_POLICY = {
    "report_training_daily_evaluation_index": "EMPTY_ROWS_ALLOWED",
    "report_training_top_notebook": "EMPTY_COLUMNS_OBSERVED",
    "report_training_change_class_index": "NO_LOCAL_SOURCE",
    "report_training_require_support_index": "NO_LOCAL_SOURCE",
}


def no_data_message(entity: str) -> str:
    """Vietnamese bounded message for callers rendering an empty report."""
    policy = REPORT_NO_DATA_POLICY.get(str(entity or "").lower())
    if policy == "NO_LOCAL_SOURCE":
        return "Chưa có dữ liệu local cho báo cáo này"
    return "Chưa có dữ liệu phù hợp"


def _first_filter(filters: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = filters.get(key)
        if value not in (None, ""):
            return value
    return None


def _optional_int(value: Any, key: str) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} phải là số") from exc


def _ignore_choice(value: Any) -> bool:
    """Return true for observed placeholder choices, never for real values."""
    return str(value or "").strip().casefold() in {
        "",
        "tất cả",
        "chọn lớp học",
        "chọn bài kiểm tra",
        "trung tâm centeronline - demo",
    }


def install_report_adapter(service: Any) -> bool:
    """Attach W4's persistent adapter at the report-provider seam.

    The coordinator-owned service autoload calls ``register`` after creating
    its report engine.  Wrapping only ``query_report`` keeps authentication,
    filters, projection, and CSV export in the shared engine while routing W4
    entities to the real SQLite joins here.  A marker makes repeated module
    registration idempotent.
    """
    engine = getattr(service, "report_engine_v2", None)
    provider = getattr(engine, "provider", None)
    original = getattr(provider, "query_report", None)
    if provider is None or not callable(original):
        return False
    if getattr(provider, "_w4_report_adapter_installed", False):
        return True

    def query_report(*, entity: str, filters: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
        normalized = str(entity or "").lower()
        if normalized.startswith("report_training_") or normalized.startswith("report_teacher_"):
            return training_report_rows(getattr(service, "db"), normalized, filters)
        return original(entity=entity, filters=filters)

    provider.query_report = query_report
    provider._w4_report_adapter_installed = True
    provider._w4_report_adapter_original = original
    return True


def register(app_or_router: Any = None, service: Any = None) -> dict[str, Any]:
    """Register W4 training report entities with the coordinator autoloader."""
    target = service if service is not None else app_or_router
    installed = install_report_adapter(target)
    return {
        "routes": list(TRAINING_REPORT_ENTITIES),
        "source": "persistent-sqlite",
        "status": "ADAPTER_READY" if installed else "PENDING_PROVIDER",
    }


def test_report_rows(db: Any, filters: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    """Return student test result rows for the Vietnamese report contract.

    Filters: ``class_id``, ``test_id``, ``teacher_id``, ``student_query``,
    ``status``.  Empty result sets stay empty; callers decide NO_DATA policy.
    """
    filters = dict(filters or {})
    # The reference form has unnamed selects.  The HTTP layer preserves them
    # as filter_2/filter_3; direct callers may use the semantic names.
    class_choice = _first_filter(filters, "class_id", "class_code", "class", "filter_2")
    test_choice = _first_filter(filters, "test_id", "test_name", "test", "filter_3")
    student_query = _first_filter(
        filters,
        "student_query",
        "nhap_ten_hoc_vien",
        "tim_trong_bang",
        "q",
        "query",
    )
    sql = (
        "SELECT s.student_code,s.full_name,t.name AS criterion,t.max_score,"
        "t.status AS test_status,t.test_date,r.score,r.note AS feedback,"
        "c.code AS class_code,u.full_name AS teacher_name "
        "FROM tests t JOIN classes c ON c.id=t.class_id "
        "JOIN enrollments e ON e.class_id=c.id AND e.status='ENROLLED' "
        "JOIN students s ON s.id=e.student_id "
        "LEFT JOIN test_results r ON r.test_id=t.id AND r.student_id=s.id "
        "LEFT JOIN users u ON u.id=c.teacher_id"
    )
    where: list[str] = []
    params: list[Any] = []
    class_id = _optional_int(class_choice, "class_id") if class_choice and not _ignore_choice(class_choice) and str(class_choice).strip().isdigit() else None
    if class_id is not None:
        where.append("c.id=?")
        params.append(class_id)
    elif class_choice and not _ignore_choice(class_choice):
        where.append("c.code=?")
        params.append(str(class_choice).strip())

    test_id = _optional_int(test_choice, "test_id") if test_choice and not _ignore_choice(test_choice) and str(test_choice).strip().isdigit() else None
    if test_id is not None:
        where.append("t.id=?")
        params.append(test_id)
    elif test_choice and not _ignore_choice(test_choice):
        where.append("t.name=?")
        params.append(str(test_choice).strip())

    teacher_id = _optional_int(filters.get("teacher_id"), "teacher_id")
    if teacher_id is not None:
        where.append("c.teacher_id=?")
        params.append(teacher_id)

    status = filters.get("status")
    if status and not _ignore_choice(status):
        normalized_status = str(status).strip().upper()
        if normalized_status not in STATUS_LABELS:
            raise ValueError("trạng thái bài kiểm tra không hợp lệ")
        where.append("t.status=?")
        params.append(normalized_status)

    if student_query and not _ignore_choice(student_query):
        where.append("(s.full_name LIKE ? OR s.student_code LIKE ?)")
        needle = f"%{str(student_query).strip()}%"
        params.extend([needle, needle])
    date_from = _first_filter(filters, "date_from", "from_date")
    date_to = _first_filter(filters, "date_to", "to_date")
    if date_from:
        where.append("t.test_date>=?")
        params.append(str(date_from).strip())
    if date_to:
        where.append("t.test_date<=?")
        params.append(str(date_to).strip())
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY s.full_name,s.id,t.test_date DESC,t.id DESC"
    try:
        source_rows = db.execute(sql, params).fetchall()
    except sqlite3.OperationalError as exc:
        # A partially initialized local DB may not have training tables yet.
        # Keep this adapter read-only and return a bounded empty result.
        if any(f"no such table: {table}" in str(exc).lower() for table in ("tests", "test_results", "students", "enrollments", "classes", "users")):
            return []
        raise
    rows = []
    for index, row in enumerate(source_rows, start=1):
        item = dict(row) if isinstance(row, Mapping) else {key: row[pos] for pos, key in enumerate(("student_code", "full_name", "criterion", "max_score", "test_status", "test_date", "score", "feedback", "class_code", "teacher_name"))}
        status = str(item.pop("test_status") or "").strip().upper()
        score = item.pop("score")
        max_score = item.pop("max_score")
        feedback = item.pop("feedback") or ""
        if feedback:
            comment = str(feedback)
        elif score is not None:
            comment = RESULT_LABELS["scored"]
        else:
            comment = RESULT_LABELS["pending"]
        rows.append({
            "stt": index,
            "student_code": item.pop("student_code"),
            "ho_ten": item.pop("full_name"),
            "tieu_chi": item.pop("criterion"),
            "nhan_xet": comment,
            "score": score,
            "max_score": max_score,
            "test_date": item.pop("test_date"),
            "class_code": item.pop("class_code"),
            "teacher_name": item.pop("teacher_name"),
            "trang_thai": STATUS_LABELS.get(status, ""),
        })
    return rows


def _rows(db: Any, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    try:
        source = db.execute(sql, list(params)).fetchall()
    except sqlite3.OperationalError as exc:
        if any(f"no such table: {table}" in str(exc).lower() for table in (
            "users", "students", "classes", "courses", "enrollments", "attendance",
            "timetable_sessions", "evaluations", "homework", "tests", "test_results",
            "finance_contracts", "finance_reserves", "parents",
        )):
            return []
        raise
    return [dict(row) if isinstance(row, Mapping) else dict(row) for row in source]


def _has_table(db: Any, table: str) -> bool:
    try:
        return db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone() is not None
    except sqlite3.Error:
        return False


def _gender_vi(value: Any) -> str:
    return {"M": "Nam", "F": "Nữ", "MALE": "Nam", "FEMALE": "Nữ"}.get(
        str(value or "").strip().upper(), ""
    )


def _vi_status(value: Any) -> str:
    text = str(value or "").strip()
    known_vi = {
        "Đang hoạt động", "Đang học", "Chưa học", "Đã học xong", "Đã hủy",
        "Nghỉ học", "Bảo lưu", "Ngừng hoạt động", "Có mặt", "Đi muộn",
        "Vắng không phép", "Vắng có phép", "Bản nháp", "Đã công bố",
        "Đã lên lịch", "Đã xác nhận", "Mới", "Đã đặt lịch", "Đã chấm",
        "Từ chối", "Đã duyệt", "Đang chờ", "Chờ xử lý", "Đã cộng vào ví",
        "Đang hiệu lực", "Đã thanh toán", "Còn nợ", "Quá hạn",
    }
    if text in known_vi:
        return text
    return {
        "ACTIVE": "Đang hoạt động", "OPEN": "Đang học", "IN_PROGRESS": "Đang học",
        "PLANNED": "Chưa học", "COMPLETED": "Đã học xong", "CANCELLED": "Đã hủy",
        "ENROLLED": "Đang học", "DROPPED": "Nghỉ học", "PAUSED": "Bảo lưu",
        "GRADUATED": "Đã học xong", "INACTIVE": "Ngừng hoạt động",
        "PRESENT": "Có mặt", "LATE": "Đi muộn", "ABSENT": "Vắng không phép",
        "EXCUSED": "Vắng có phép", "DRAFT": "Bản nháp", "PUBLISHED": "Đã công bố",
        "SCHEDULED": "Đã lên lịch", "CONFIRMED": "Đã xác nhận", "NEW": "Mới",
        "BOOKED": "Đã đặt lịch", "SCORED": "Đã chấm", "CANCELLED": "Đã hủy",
        "REJECTED": "Từ chối", "APPROVED": "Đã duyệt", "WAITING": "Đang chờ",
        "PAID": "Đã thanh toán", "PARTIAL": "Còn nợ", "PENDING": "Chờ xử lý",
        "OVERDUE": "Quá hạn", "ACTIVE_CONTRACT": "Đang hiệu lực",
    }.get(text.upper(), "")


def _query(filters: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = filters.get(key)
        if value not in (None, ""):
            text = str(value).strip()
            # Select placeholders are transport values, not predicates.  A
            # previous implementation treated ``Tất cả`` as a student name
            # and returned an empty report for an otherwise valid query.
            if text.casefold() in {"tất cả", "all", "chọn", "chọn lớp học", "chọn trạng thái", "tất cả các lớp", "tất cả khóa học"}:
                continue
            return text
    return ""


def _date_clause(filters: Mapping[str, Any], column: str = "a.session_date") -> tuple[str, list[Any]]:
    clauses: list[str] = []
    args: list[Any] = []
    start = _query(filters, "date_from", "from_date", "start_date", "tu_ngay", "from_date_absent", "from_date_enroll")
    end = _query(filters, "date_to", "to_date", "end_date", "en_ngay", "to_date_absent", "to_date_enroll")
    if start:
        clauses.append(f"{column}>=?"); args.append(start)
    if end:
        clauses.append(f"{column}<=?"); args.append(end)
    return (" AND ".join(clauses), args)


def _student_filter(filters: Mapping[str, Any], alias: str = "s") -> tuple[str, list[Any]]:
    query = _query(filters, "q", "query", "student_query", "nhap_ten_hoc_vien", "tim_trong_bang", "tim_kiem")
    if not query:
        return "", []
    needle = f"%{query}%"
    return f"({alias}.full_name LIKE ? OR {alias}.student_code LIKE ?)", [needle, needle]


def _with_index(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for index, row in enumerate(rows, 1):
        row.setdefault("no", index)
        row.setdefault("stt", index)
    return rows


def _attendance_rows(db: Any, filters: Mapping[str, Any]) -> list[dict[str, Any]]:
    # Reference form names are from_date/to_date; absent bounds intentionally
    # mean all persisted attendance. A caller may supply today explicitly.
    date_sql, date_args = _date_clause(filters)
    query_sql, query_args = _student_filter(filters)
    where = ["e.status='ENROLLED'"]
    args: list[Any] = []
    if date_sql:
        where.append(date_sql); args.extend(date_args)
    if query_sql:
        where.append(query_sql); args.extend(query_args)
    class_id = _query(filters, "class_id", "filter_2", "tim_lop_hoc")
    if class_id:
        if class_id.isdigit():
            where.append("c.id=?"); args.append(int(class_id))
        elif class_id.casefold() not in {"tất cả", "chọn lớp học"}:
            where.append("c.code=?"); args.append(class_id)
    sql = """
        SELECT s.student_code,s.full_name,c.code AS class_code,
          COALESCE(SUM(CASE WHEN a.status IN ('PRESENT','LATE') THEN 1 ELSE 0 END),0) AS present,
          COALESCE(SUM(CASE WHEN a.status='EXCUSED' THEN 1 ELSE 0 END),0) AS excused,
          COALESCE(SUM(CASE WHEN a.status='ABSENT' THEN 1 ELSE 0 END),0) AS unexcused
        FROM students s JOIN enrollments e ON e.student_id=s.id
        JOIN classes c ON c.id=e.class_id
        LEFT JOIN attendance a ON a.class_id=e.class_id AND a.student_id=s.id
    """
    # Date predicates belong to the LEFT JOIN to preserve zero-count rows.
    if date_sql:
        sql = sql.replace("LEFT JOIN attendance a ON a.class_id=e.class_id AND a.student_id=s.id", "LEFT JOIN attendance a ON a.class_id=e.class_id AND a.student_id=s.id AND " + date_sql)
        args = query_args + ([int(class_id)] if class_id and class_id.isdigit() else ([class_id] if class_id and class_id.casefold() not in {"tất cả", "chọn lớp học"} else []))
        where = ["e.status='ENROLLED'"]
        if query_sql: where.append(query_sql)
    sql += " WHERE " + " AND ".join(where) + " GROUP BY s.id,c.id ORDER BY s.full_name,s.id"
    result = []
    for row in _rows(db, sql, date_args + args if date_sql else args):
        result.append({"ma_hoc_sinh": row["student_code"], "ten_hoc_sinh": row["full_name"], "so_buoi_i_hoc": row["present"], "vang_co_phep": row["excused"], "vang_khong_phep": row["unexcused"], "lop_hoc": row["class_code"]})
    return _with_index(result)


def _enrollment_rows(db: Any, filters: Mapping[str, Any], *, paused: bool = False) -> list[dict[str, Any]]:
    query_sql, query_args = _student_filter(filters)
    where = ["1=1"]; args: list[Any] = []
    if paused: where.append("s.status='PAUSED'")
    status = _query(filters, "status", "filter_3", "filter_6")
    if status and status not in {"Tất cả", "Chọn trạng thái"}:
        status_map = {"Đang học": "ENROLLED", "Bảo lưu": "PAUSED", "Đã học xong": "COMPLETED", "Nghỉ học": "DROPPED"}
        mapped = status_map.get(status, status.upper())
        if mapped == "PAUSED":
            where.append("s.status='PAUSED'")
        elif mapped in {"ENROLLED", "COMPLETED", "DROPPED"}:
            where.append("e.status=?"); args.append(mapped)
    if query_sql: where.append(query_sql); args.extend(query_args)
    date_sql, date_args = _date_clause(filters, "e.enrolled_at")
    if date_sql: where.append(date_sql); args.extend(date_args)
    contract_columns = """
        (SELECT fc.contract_code FROM finance_contracts fc WHERE fc.student_id=s.id AND fc.class_id=c.id ORDER BY fc.id DESC LIMIT 1) AS contract_code,
        (SELECT fc.total_amount FROM finance_contracts fc WHERE fc.student_id=s.id AND fc.class_id=c.id ORDER BY fc.id DESC LIMIT 1) AS contract_total,
        (SELECT fc.direct_discount FROM finance_contracts fc WHERE fc.student_id=s.id AND fc.class_id=c.id ORDER BY fc.id DESC LIMIT 1) AS contract_discount,
        (SELECT fc.paid_amount FROM finance_contracts fc WHERE fc.student_id=s.id AND fc.class_id=c.id ORDER BY fc.id DESC LIMIT 1) AS contract_paid,
        (SELECT fc.payment_status FROM finance_contracts fc WHERE fc.student_id=s.id AND fc.class_id=c.id ORDER BY fc.id DESC LIMIT 1) AS contract_status,
        (SELECT fc.note FROM finance_contracts fc WHERE fc.student_id=s.id AND fc.class_id=c.id ORDER BY fc.id DESC LIMIT 1) AS contract_note,
        (SELECT u.full_name FROM users u JOIN finance_contracts fc ON fc.created_by=u.id WHERE fc.student_id=s.id AND fc.class_id=c.id ORDER BY fc.id DESC LIMIT 1) AS contract_creator,
        (SELECT fb.invoice_code FROM finance_bills fb WHERE fb.contract_code=(SELECT fc.contract_code FROM finance_contracts fc WHERE fc.student_id=s.id AND fc.class_id=c.id ORDER BY fc.id DESC LIMIT 1) ORDER BY fb.id DESC LIMIT 1) AS invoice_code,
        (SELECT fb.payment_amount FROM finance_bills fb WHERE fb.contract_code=(SELECT fc.contract_code FROM finance_contracts fc WHERE fc.student_id=s.id AND fc.class_id=c.id ORDER BY fc.id DESC LIMIT 1) ORDER BY fb.id DESC LIMIT 1) AS invoice_amount,
        (SELECT fb.invoice_date FROM finance_bills fb WHERE fb.contract_code=(SELECT fc.contract_code FROM finance_contracts fc WHERE fc.student_id=s.id AND fc.class_id=c.id ORDER BY fc.id DESC LIMIT 1) ORDER BY fb.id DESC LIMIT 1) AS invoice_date
    """ if _has_table(db, "finance_contracts") and _has_table(db, "finance_bills") else "NULL AS contract_code,NULL AS contract_total,NULL AS contract_discount,NULL AS contract_paid,NULL AS contract_status,NULL AS contract_note,NULL AS contract_creator,NULL AS invoice_code,NULL AS invoice_amount,NULL AS invoice_date"
    rows = _rows(db, """
      SELECT s.id AS student_id,s.full_name,s.student_code,s.school,s.date_of_birth,s.gender,
             s.parent1_name,s.parent1_code,s.parent1_phone,s.parent2_name,s.parent2_code,s.parent2_phone,
             c.code AS class_code,c.code AS class_name,co.name AS course_name,c.start_date,c.end_date,
             c.hours AS class_hours,c.sessions_count AS class_sessions,c.teacher_id,e.enrolled_at,e.status,e.class_id,s.status AS student_status,
             u.full_name AS teacher_name,
             """ + contract_columns + """
      FROM enrollments e JOIN students s ON s.id=e.student_id JOIN classes c ON c.id=e.class_id
      JOIN courses co ON co.id=c.course_id LEFT JOIN users u ON u.id=c.teacher_id WHERE """ + " AND ".join(where) + " ORDER BY e.enrolled_at DESC,e.id DESC", args)
    out=[]
    for row in rows:
        status_vi = _vi_status(row["status"])
        attended = _rows(db, "SELECT COUNT(*) AS n FROM attendance WHERE class_id=? AND student_id=? AND status IN ('PRESENT','LATE')", (row["class_id"], row["student_id"]))
        attended_count = attended[0]["n"] if attended else 0
        session_count = _rows(db, "SELECT COUNT(*) AS n FROM timetable_sessions WHERE class_id=? AND session_date>=? AND session_date<=?", (row["class_id"], row["start_date"], row["end_date"]))
        registered_count = session_count[0]["n"] if session_count else 0
        attendance = _rows(db, "SELECT session_date,status FROM attendance WHERE class_id=? AND student_id=?", (row["class_id"], row["student_id"]))
        present = {str(x["session_date"]): str(x["status"]).upper() for x in attendance}
        absent_count = sum(1 for x in present.values() if x in {"ABSENT", "EXCUSED"})
        excused_count = sum(1 for x in present.values() if x == "EXCUSED")
        unexcused_count = sum(1 for x in present.values() if x == "ABSENT")
        month_present = {month: sum(1 for day, state in present.items() if len(day) >= 7 and int(day[5:7]) == month and state in {"PRESENT", "LATE"}) for month in range(1, 13)}
        contract_total = row["contract_total"]
        per_session = round(float(contract_total) / registered_count, 2) if contract_total is not None and registered_count else None
        base = {"ten_hoc_vien": row["full_name"], "ma_hoc_vien": row["student_code"], "truong_hoc": row["school"], "ngay_sinh": row["date_of_birth"], "gioi_tinh": _gender_vi(row["gender"]), "ngay_ang_ky_hoc": row["enrolled_at"], "ngay_bat_au": row["start_date"], "ngay_ket_thuc": row["end_date"], "lop_ang_ky": row["class_name"], "ma_lop": row["class_code"], "lop_hoc": row["class_name"], "khoa_hoc_ang_ky": row["course_name"], "khoa_hoc": row["course_name"], "trang_thai": status_vi, "trang_thai_hoc_vien": _vi_status(row["student_status"]), "phu_huynh_1": row["parent1_name"], "ma_phu_huynh_1": row["parent1_code"], "sdt_phu_huynh_1": row["parent1_phone"], "phu_huynh_2": row["parent2_name"], "ma_phu_huynh_2": row["parent2_code"], "sdt_phu_huynh_2": row["parent2_phone"], "giao_vien": row["teacher_name"], "tro_giang": None, "ma_ghi_danh": None, "hop_ong": row["contract_code"], "hoa_on": row["invoice_code"], "chi_nhanh": "Trung tâm CenterOnline - Demo", "ten_chi_nhanh": "Trung tâm CenterOnline - Demo", "ma_hop_ong": row["contract_code"], "ma_hoa_on": row["invoice_code"], "tong_tien_hop_ong": contract_total, "so_tien_giam_gia_h": row["contract_discount"], "so_tien_thuc_thu_h": row["contract_paid"], "trang_thai_hop_ong": _vi_status(row["contract_status"]), "ghi_chu_hop_ong": row["contract_note"], "nhan_vien_tao_hop_ong": row["contract_creator"], "so_tien_hoa_on": row["invoice_amount"], "thoi_gian_hoa_on": row["invoice_date"], "thoi_gian_hop_ong": row["enrolled_at"], "so_buoi_hoc_theo_ghi_danh": registered_count, "so_gio_hoc_theo_ghi_danh": row["class_hours"], "so_gio_ghi_danh": row["class_hours"], "so_tien_buoi": per_session, "a_hoc_so_buoi_ghi_danh": f"{attended_count} / {registered_count}", "so_buoi_ang_ky": registered_count, "so_buoi_ghi_danh": registered_count, "so_buoi_hoc": registered_count, "so_buoi_i_hoc": attended_count, "ti_le_i_hoc": round(attended_count * 100 / registered_count, 2) if registered_count else None, "so_buoi_nghi": absent_count, "so_buoi_nghi_co_phep": excused_count, "so_buoi_nghi_khong_phep": unexcused_count, "so_buoi_nghi_co_phep_2": excused_count, "so_buoi_nghi_khong_phep_2": unexcused_count, "so_tien_dung": None, "so_tien_dung_2": None, "so_tien_dung_3": None, "so_tien_dung_4": None, "so_tien_dung_5": None, "so_tien_dung_6": None, "so_tien_dung_7": None, "so_tien_dung_8": None, "so_tien_dung_9": None, "so_tien_dung_10": None, "so_tien_dung_11": None, "so_tien_dung_12": None, "ngay_bat_au_ngay_ket_thuc": f"{row['start_date'] or ''} - {row['end_date'] or ''}", "so_buoi_chua_hoc_theo_ghi_danh": max(0, registered_count - attended_count), "so_buoi_chua_hoc_theo_hop_ong": None, "so_buoi_a_hoc": attended_count, "so_buoi_a_hoc_bu": None, "trang_thai_gia_han": None, "ghi_chu": row["contract_note"], "cong_cu_ghi_danh_them": ""}
        for month, count in month_present.items():
            base[f"thang_{month}"] = count
            base[f"so_buoi_hoc_{month}"] = count
            base[f"so_buoi_i_hoc_{month}"] = count
            base[f"ti_le_i_hoc_{month}"] = round(count * 100 / registered_count, 2) if registered_count else None
            base[f"so_buoi_nghi_co_phep_{month}"] = sum(1 for day, state in present.items() if len(day) >= 7 and int(day[5:7]) == month and state == "EXCUSED")
            base[f"so_buoi_nghi_khong_phep_{month}"] = sum(1 for day, state in present.items() if len(day) >= 7 and int(day[5:7]) == month and state == "ABSENT")
            base[f"so_gio_hoc_{month if month > 1 else ''}".rstrip("_")] = None
        out.append(base)
    return _with_index(out)


def training_report_rows(db: Any, entity: str, filters: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    """Dispatch all owned training report entities to real local joins."""
    filters = dict(filters or {}); kind = str(entity or "").lower()
    if kind == "report_teacher_sth_index":
        from .report_teacher import teacher_hours_rows
        return teacher_hours_rows(db, filters)
    if kind == "report_training_test":
        return test_report_rows(db, filters)
    if kind == "report_teacher_rest_learning":
        from .report_teacher import teacher_rest_learning_rows
        return teacher_rest_learning_rows(db, filters)
    if kind == "report_training_attendance":
        return _attendance_rows(db, filters)
    if kind.endswith("class_v2"):
        rows = _rows(db, """SELECT co.name AS course_name,COUNT(c.id) AS class_count,
          SUM(CASE WHEN substr(c.created_at,1,7)=strftime('%Y-%m','now') THEN 1 ELSE 0 END) AS created_this_month,
          SUM(CASE WHEN c.status IN ('OPEN','IN_PROGRESS') THEN 1 ELSE 0 END) AS in_progress,
          SUM(CASE WHEN c.status='PLANNED' THEN 1 ELSE 0 END) AS planned,
          SUM(CASE WHEN c.status='COMPLETED' THEN 1 ELSE 0 END) AS completed,
          SUM(CASE WHEN c.status='CANCELLED' THEN 1 ELSE 0 END) AS cancelled,
          SUM(CASE WHEN c.end_date >= date('now') AND c.end_date <= date('now','+30 day') THEN 1 ELSE 0 END) AS ending,
          SUM(CASE WHEN NOT EXISTS(SELECT 1 FROM timetable_sessions t WHERE t.class_id=c.id) THEN 1 ELSE 0 END) AS without_schedule
          FROM classes c JOIN courses co ON co.id=c.course_id GROUP BY co.id ORDER BY co.name""")
        return _with_index([{"trung_tam": "Trung tâm CenterOnline - Demo", "khoa_hoc": r["course_name"], "tong_so_lop": r["class_count"], "tao_moi_trong_thang": r["created_this_month"], "lop_ang_hoc": r["in_progress"], "lop_chua_hoc": r["planned"], "a_hoc_ket_thuc": r["completed"], "huy_lop": r["cancelled"], "lop_sap_ket_thuc": r["ending"], "lop_chua_co_lich": r["without_schedule"], "chi_tiet": "Xem chi tiết"} for r in rows])
    if kind.endswith("tuition_class_index"):
        rows = _rows(db, """SELECT c.code AS class_code,co.subject AS subject,
          SUM(CASE WHEN f.payment_status='PAID' THEN 1 ELSE 0 END) AS paid,
          SUM(CASE WHEN COALESCE(f.payment_status,'')<>'PAID' THEN 1 ELSE 0 END) AS unpaid,
          COUNT(f.id) AS total FROM classes c JOIN courses co ON co.id=c.course_id
          LEFT JOIN finance_contracts f ON f.class_id=c.id GROUP BY c.id ORDER BY c.code""")
        return _with_index([{"lop_hoc": r["class_code"], "mon_hoc": r["subject"] or "", "a_ong": r["paid"], "chua_ong_tien": r["unpaid"], "tong": r["total"], "chi_tiet": ""} for r in rows])
    if kind.endswith("daily_evaluation_index"):
        where, args = [], []
        start = _query(filters, "start_date", "from_date")
        end = _query(filters, "end_date", "to_date")
        if start: where.append("e.session_date>=?"); args.append(start)
        if end: where.append("e.session_date<=?"); args.append(end)
        class_choice = _query(filters, "filter_3", "class_code", "class_id")
        if class_choice and class_choice.casefold() not in {"chọn lớp học", "tất cả"}:
            if class_choice.isdigit(): where.append("c.id=?")
            else: where.append("c.code=?")
            args.append(int(class_choice) if class_choice.isdigit() else class_choice)
        rows = _rows(db, """SELECT e.session_date,e.status,e.score,e.note,c.code AS class_code,s.full_name
          FROM evaluations e JOIN classes c ON c.id=e.class_id JOIN students s ON s.id=e.student_id
          """ + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY e.session_date DESC,e.id DESC", args)
        return _with_index([{"ngay":r["session_date"],"lop_hoc":r["class_code"],"ho_ten":r["full_name"],"trang_thai":_vi_status(r["status"]),"diem":r["score"],"ghi_chu":r["note"]} for r in rows])
    if kind.endswith("homework_ratio_index"):
        rows = _rows(db, """SELECT c.code AS class_code,s.full_name,s.date_of_birth,s.gender,c.start_date,c.end_date,
          COUNT(DISTINCT h.id) AS homework_count,
          COUNT(DISTINCT CASE WHEN h.status='CLOSED' THEN h.id END) AS submitted
          FROM enrollments e JOIN students s ON s.id=e.student_id JOIN classes c ON c.id=e.class_id
          LEFT JOIN homework h ON h.class_id=c.id GROUP BY s.id,c.id ORDER BY s.full_name""")
        # The local schema has homework assignment state, not a per-student
        # submission ledger.  Report assignment counts only; submission ratio
        # stays empty until that durable source exists.
        return _with_index([{"lop":r["class_code"],"ho_va_ten":r["full_name"],"ngay_sinh":r["date_of_birth"],"gioi_tinh":_gender_vi(r["gender"]),"so_buoi_hoc_co_bai_tap":r["homework_count"],"so_buoi_hoc_a_tra_bai":None,"ti_le_lam_bai_tap":None,"ngay_bat_au_hoc":r["start_date"],"ngay_ket_thuc":r["end_date"]} for r in rows])
    if kind.endswith("change_class_index"):
        # The local schema has no transfer ledger. Enrollment history alone
        # cannot prove a class change, so fail closed instead of projecting a
        # generic enrollment row as a transfer event.
        return []
    if kind.endswith("attendance_center_index"):
        rows = _attendance_rows(db, filters)
        details = _rows(db, "SELECT s.student_code,s.date_of_birth,s.gender,c.code AS class_code FROM students s JOIN enrollments e ON e.student_id=s.id JOIN classes c ON c.id=e.class_id WHERE e.status='ENROLLED'")
        by_code = {(r["student_code"], r["class_code"]): r for r in details}
        return [{"no":r["no"],"lop_hoc":r.get("lop_hoc"),"ho_ten":r["ten_hoc_sinh"],"ngay_sinh":by_code.get((r["ma_hoc_sinh"],r.get("lop_hoc")),{}).get("date_of_birth"),"gioi_tinh":_gender_vi(by_code.get((r["ma_hoc_sinh"],r.get("lop_hoc")),{}).get("gender")),"so_buoi_thuc_hoc":r["so_buoi_i_hoc"],"so_buoi_hien_tai":r["so_buoi_i_hoc"],"tong_so_buoi_hoc":sum(r.get(k,0) or 0 for k in ("so_buoi_i_hoc","vang_co_phep","vang_khong_phep")),"ti_le_chuyen_can":round((r["so_buoi_i_hoc"] or 0)*100/max(1,sum(r.get(k,0) or 0 for k in ("so_buoi_i_hoc","vang_co_phep","vang_khong_phep"))),2)} for r in rows]
    if kind.endswith("using_course_index"):
        schools = _rows(db, "SELECT c.course_id, GROUP_CONCAT(DISTINCT NULLIF(s.school,'')) AS schools FROM classes c JOIN enrollments e ON e.class_id=c.id AND e.status='ENROLLED' JOIN students s ON s.id=e.student_id GROUP BY c.course_id")
        school_by_course = {r["course_id"]: r["schools"] or "" for r in schools}
        rows = _rows(db, """SELECT co.id AS course_id,co.name AS course_name,COUNT(DISTINCT c.id) AS class_count,
          COUNT(DISTINCT e.student_id) AS student_count,MIN(c.start_date) AS start_date,MAX(c.end_date) AS end_date
          FROM courses co LEFT JOIN classes c ON c.course_id=co.id
          LEFT JOIN enrollments e ON e.class_id=c.id AND e.status='ENROLLED' GROUP BY co.id ORDER BY co.name""")
        return _with_index([{"ten_chuong_trinh":r["course_name"],"truong_hoc":school_by_course.get(r["course_id"],""),"so_lop":r["class_count"],"so_hoc_vien":r["student_count"],"thoi_gian_bat_au":r["start_date"],"thoi_gian_ket_thuc":r["end_date"]} for r in rows])
    if kind.endswith("reserve_training_index"):
        query = _query(filters, "nhap_ten_hoc_vien", "q", "query")
        where = ["1=1"]; args: list[Any] = []
        if query:
            where.append("(student_name LIKE ? OR contract_code LIKE ? OR course_name LIKE ?)"); args.extend((f"%{query}%",)*3)
        start = _query(filters, "from_date", "date_absent")
        end = _query(filters, "to_date", "date_absent_2", "date_absent_3")
        if start: where.append("reserve_date>=?"); args.append(start)
        if end: where.append("reserve_date<=?"); args.append(end)
        rows = _rows(db, "SELECT student_name,reserve_date,amount_or_days,course_name,status,note FROM finance_reserves WHERE " + " AND ".join(where) + " ORDER BY reserve_date DESC,id DESC", args)
        return _with_index([{"ten_hoc_vien":r["student_name"],"ngay_bao_luu":r["reserve_date"],"ly_do":None,"lop_hoc_khoa_hoc":r["course_name"],"so_tien_so_buoi_bao_luu":r["amount_or_days"],"so_buoi_a_hoc":None,"so_buoi_ang_ky":None,"ngay_het_han":None,"ghi_chu_sau_bao_luu":r["note"],"trang_thai":_vi_status(r["status"]),"cong_cu":""} for r in rows])
    if kind.endswith("diligence_index"):
        date_sql, date_args = _date_clause(filters, "a.session_date")
        where = (" WHERE " + date_sql) if date_sql else ""
        rows = _rows(db, """SELECT c.code AS class_code,co.name AS course_name,
          COUNT(a.id) AS total,SUM(CASE WHEN a.status='PRESENT' THEN 1 ELSE 0 END) AS present,
          SUM(CASE WHEN a.status='LATE' THEN 1 ELSE 0 END) AS late,SUM(CASE WHEN a.status='EXCUSED' THEN 1 ELSE 0 END) AS excused,
          SUM(CASE WHEN a.status='ABSENT' THEN 1 ELSE 0 END) AS absent FROM classes c JOIN courses co ON co.id=c.course_id
          LEFT JOIN attendance a ON a.class_id=c.id""" + where + " GROUP BY c.id ORDER BY c.code", date_args)
        def pct(v,t): return round((v or 0)*100/max(1,t or 0),2)
        return _with_index([{"lop":r["class_code"],"khoa_hoc":r["course_name"],"ty_le_tham_gia_ung_gio":pct(r["present"],r["total"]),"ti_le_muon":pct(r["late"],r["total"]),"ti_le_vang_co_phep":pct(r["excused"],r["total"]),"ti_le_vang_khong_phep":pct(r["absent"],r["total"])} for r in rows])
    if kind.endswith("schedule_index"):
        rows = _rows(db, """SELECT t.session_date,t.start_time,t.end_time,t.room,c.code AS class_code,co.name AS course_name,
          u.full_name AS teacher,c.start_date,c.end_date,COUNT(e.id) AS enrolled FROM timetable_sessions t
          JOIN classes c ON c.id=t.class_id JOIN courses co ON co.id=c.course_id LEFT JOIN users u ON u.id=t.teacher_id
          LEFT JOIN enrollments e ON e.class_id=c.id AND e.status='ENROLLED' GROUP BY t.id ORDER BY t.session_date,t.start_time""")
        date_keys = (("26_10_2026", "2026-10-26"), ("27_10_2026", "2026-10-27"), ("28_10_2026", "2026-10-28"), ("29_10_2026", "2026-10-29"), ("30_10_2026", "2026-10-30"), ("31_10_2026", "2026-10-31"), ("01_11_2026", "2026-11-01"))
        weekdays = (("thu_2", 0), ("thu_3", 1), ("thu_4", 2), ("thu_5", 3), ("thu_6", 4), ("thu_7", 5), ("chu_nhat", 6))
        out = []
        for r in rows:
            item = {"thoi_gian": f"{r['session_date']} {r['start_time']}-{r['end_time']}", "ten_khoa_hoc": r["course_name"], "ten_lop": r["class_code"], "cm_chinh": r["teacher"], "cm_phu": "-", "hoc_vien_trong_lop": r["enrolled"], "ngay_bat_au": r["start_date"], "ngay_ket_thuc": r["end_date"], "phong_hoc": r["room"]}
            for key, value in date_keys:
                item[key] = "Có lịch" if r["session_date"] == value else "-"
            for key, weekday in weekdays:
                item[key] = "Có lịch" if r["session_date"] and __import__("datetime").date.fromisoformat(r["session_date"]).weekday() == weekday else "-"
            out.append(item)
        return _with_index(out)
    if kind == "training_timetable" or kind.endswith("/training_timetable"):
        rows = _rows(db, """SELECT t.session_date,t.room,t.start_time,t.end_time,c.code AS class_code,
          co.name AS course_name,u.full_name AS teacher FROM timetable_sessions t
          JOIN classes c ON c.id=t.class_id JOIN courses co ON co.id=c.course_id
          LEFT JOIN users u ON u.id=t.teacher_id ORDER BY t.session_date,t.start_time,t.id""")
        return _with_index([{"ngay":r["session_date"],"phong_hoc_ca_hoc":r["room"],
          "ca_hoc":f"{r['start_time']}-{r['end_time']}","lop_hoc":r["class_code"],
          "khoa_hoc":r["course_name"],"giao_vien":r["teacher"]} for r in rows])
    if kind == "training_pending_enrollment_index":
        rows = _rows(db, """SELECT p.customer_name,p.preferred_day,p.preferred_session,p.status,p.notes,
          p.created_at,co.name AS course_name FROM pending_enrollments p LEFT JOIN courses co ON co.id=p.course_id
          ORDER BY p.created_at DESC,p.id DESC""")
        return _with_index([{"khach_hang":r["customer_name"],"trung_tam":"Trung tâm CenterOnline - Demo",
          "ca_hoc":r["preferred_day"] + (f" {r['preferred_session']}" if r["preferred_session"] else ""),
          "khoa_hoc":r["course_name"],"ngay_bat_au":r["created_at"],"ghi_chu":r["notes"],
          "trang_thai":_vi_status(r["status"]),"tao_boi":None,"hanh_ong":None} for r in rows])
    if kind == "training_confirm":
        rows = _rows(db, """SELECT s.full_name,c.code AS class_code,c.schedule,c.sessions_count,
          e.created_at,e.contract_code,e.status,u.full_name AS confirmed_by FROM enrollment_confirmations e
          JOIN students s ON s.id=e.student_id JOIN classes c ON c.id=e.class_id
          LEFT JOIN users u ON u.id=e.confirmed_by ORDER BY e.created_at DESC,e.id DESC""")
        return _with_index([{"ho_ten":r["full_name"],"lop_ang_ky":r["class_code"],"so_buoi":r["sessions_count"],
          "lich":r["schedule"],"ngay_ghi_danh_vao_lop":r["created_at"],"ma_hop_ong":r["contract_code"],
          "trang_thai":_vi_status(r["status"]),"nguoi_thuc_hien":r["confirmed_by"],"cong_cu":None} for r in rows])
    if kind.endswith("register_learning"):
        return _enrollment_rows(db, filters)
    if kind.endswith("student_pause"):
        return _enrollment_rows(db, filters, paused=True)
    if kind.endswith("student_training_v2"):
        rows = _rows(db, "SELECT student_code,full_name,date_of_birth,school,gender,status FROM students ORDER BY full_name")
        return _with_index([{"ma_hoc_vien":r["student_code"],"ho_ten":r["full_name"],"ngay_sinh":r["date_of_birth"],"truong_hoc":r["school"],"gioi_tinh":_gender_vi(r["gender"]),"trang_thai":_vi_status(r["status"])} for r in rows])
    if kind.endswith("enroll_index") or kind.endswith("allocation_student_index") or kind.endswith("allocation_hours_index") or kind.endswith("due_date_student"):
        return _enrollment_rows(db, filters)
    if kind.endswith("absent_classes"):
        rows = _rows(db, """SELECT c.code AS class_code,c.code AS class_name,c.status,
          COUNT(DISTINCT CASE WHEN e.status='ENROLLED' THEN e.student_id END) AS enrolled,
          COUNT(CASE WHEN a.status IN ('ABSENT','EXCUSED') THEN 1 END) AS absent,
          COUNT(CASE WHEN a.status='EXCUSED' THEN 1 END) AS excused,
          COUNT(CASE WHEN a.status='ABSENT' THEN 1 END) AS unexcused,
          c.schedule,(SELECT MIN(t.start_time || '-' || t.end_time) FROM timetable_sessions t WHERE t.class_id=c.id) AS session_time FROM classes c LEFT JOIN enrollments e ON e.class_id=c.id LEFT JOIN attendance a ON a.class_id=c.id GROUP BY c.id ORDER BY c.code""")
        return _with_index([{"ma_lop":r["class_code"],"lop_hoc":r["class_name"],"trang_thai":_vi_status(r["status"]),"hoc_vien_ang_hoc":r["enrolled"],"ngay_hoc_trong_tuan":r["schedule"],"ca_hoc":r["session_time"] or "-","so_luong_vang":r["absent"],"so_luong_co_phep":r["excused"],"so_luong_khong_phep":r["unexcused"]} for r in rows])
    if kind.endswith("top_notebook"):
        date_sql, date_args = _date_clause(filters, "e.session_date")
        where_clauses: list[str] = []
        params: list[Any] = []
        if date_sql:
            where_clauses.append(date_sql)
            params.extend(date_args)
        query_sql, query_args = _student_filter(filters)
        if query_sql:
            where_clauses.append(query_sql)
            params.extend(query_args)
        rows = _rows(db, """SELECT e.session_date,e.score,e.note,e.status,c.code AS class_code,s.full_name
          FROM evaluations e JOIN classes c ON c.id=e.class_id JOIN students s ON s.id=e.student_id"""
          + (" WHERE " + " AND ".join(where_clauses) if where_clauses else "")
          + " ORDER BY e.session_date DESC,e.id DESC", params)
        return _with_index([{"ngay":r["session_date"],"lop":r["class_code"],"ho_va_ten":r["full_name"],"diem":r["score"],"ghi_chu":r["note"],"trang_thai":_vi_status(r["status"])} for r in rows])
    if kind.endswith("student_drop_index") or kind.endswith("new_enrollment_index"):
        # Local students.status has no DROPPED enum. INACTIVE is the persisted
        # terminal state used by this rebuild for dropped learners.
        wanted = "INACTIVE" if kind.endswith("student_drop_index") else "ACTIVE"
        rows = _rows(db, "SELECT s.student_code,s.full_name,s.english_name,s.date_of_birth,s.gender,s.parent1_name,s.parent1_phone,s.status,s.note,s.created_at,c.code AS class_code,c.start_date,u.full_name AS teacher FROM students s LEFT JOIN enrollments e ON e.student_id=s.id LEFT JOIN classes c ON c.id=e.class_id LEFT JOIN users u ON u.id=c.teacher_id WHERE s.status=? ORDER BY s.created_at DESC", (wanted,))
        if kind.endswith("new_enrollment_index"):
            return _with_index([{
                "trung_tam": "Trung tâm CenterOnline - Demo",
                "ma_hoc_vien": r["student_code"], "ho_ten": r["full_name"],
                "ten_tieng_anh": r["english_name"] or "-", "ngay_sinh": r["date_of_birth"] or "-",
                "gioi_tinh": _gender_vi(r["gender"]), "phu_huynh": r["parent1_name"] or "-",
                "sdt_phu_huynh": r["parent1_phone"] or "-", "ngay_tao": r["created_at"],
                "ngay_bat_au": r["start_date"], "trang_thai": _vi_status(r["status"]),
                "lop_ang_hoc": r["class_code"] or "-",
            } for r in rows])
        return _with_index([{"ma_hoc_vien":r["student_code"],"ho_ten":r["full_name"],"ten_tieng_anh":r["english_name"] or "-","ngay_sinh":r["date_of_birth"] or "-","phu_huynh":r["parent1_name"] or "-","sdt_phu_huynh":r["parent1_phone"] or "-","trang_thai":_vi_status(r["status"]),"ghi_chu":r["note"] or "-","ngay_drop":r["created_at"],"lop_cuoi_cung_a_hoc":r["class_code"] or "-","ten_on_vi":"Trung tâm CenterOnline - Demo","giao_vien":r["teacher"] or "-"} for r in rows])
    if kind.endswith("examination_month_index"):
        rows = _rows(db, """SELECT co.name AS course_name,c.code AS class_code,t.name,t.test_date,u.full_name AS teacher
          FROM tests t JOIN classes c ON c.id=t.class_id JOIN courses co ON co.id=c.course_id LEFT JOIN users u ON u.id=c.teacher_id
          ORDER BY t.test_date DESC,t.id DESC""")
        return _with_index([{"khoa_hoc":r["course_name"],"lop_hoc":r["class_code"],"ten_bai_kiem_tra":r["name"],"thoi_gian_dien_ra":r["test_date"],"giao_vien":r["teacher"]} for r in rows])
    if kind.endswith("instead_teacher"):
        rows = _rows(db, """SELECT t.session_date,t.start_time,t.end_time,t.room,c.code AS class_code,
          u.full_name AS teacher FROM timetable_sessions t JOIN classes c ON c.id=t.class_id
          LEFT JOIN users u ON u.id=c.teacher_id WHERE t.status='CANCELLED'
          ORDER BY t.session_date DESC,t.id DESC""")
        return _with_index([{"chi_nhanh":"Trung tâm CenterOnline - Demo", "giao_vien_day_chinh":r["teacher"],
          "ngay_nghi":r["session_date"], "lop_nghi_day":r["class_code"], "so_gio_nghi":None,
          "ca_day":f"{r['start_time']}-{r['end_time']}", "thu":None, "ly_do_nghi":None,
          "giao_vien_day_thay":None, "replacement_shift":None, "so_gio_day_thay":None} for r in rows])
    # No persisted local source has been defined for support requests, class
    # changes, replacement teachers, or reserve-specific training metadata.
    # Return no rows so the shared engine can expose NO_DATA truthfully.
    return []


__all__ = [
    "STATUS_LABELS", "TRAINING_REPORT_ENTITIES", "TEACHER_REPORT_ENTITIES",
    "ATTENDANCE_LEGEND_NOTE",
    "REPORT_NO_DATA_POLICY", "no_data_message", "test_report_rows", "training_report_rows",
    "install_report_adapter", "register",
]
