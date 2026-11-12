"""Teacher report adapters for the observed Vietnamese report contracts.

The first bounded route is ``/report/teacher/sth/index`` (thống kê giờ dạy).
Rows are calculated from the persisted teacher, class, timetable, enrollment,
and attendance tables.  The module does not seed data or perform controller
wiring; a coordinator can attach :func:`teacher_hours_rows` to the shared
report provider without changing this semantic mapping.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from typing import Any, Mapping


# The reference capture includes one date column in the teacher-hours grid.
# Keep that observed key stable while calculating its value from the durable
# timetable rows.  The date is a report column, not a generated sample row.
REFERENCE_HOURS_DATE = "2026-11-01"
REFERENCE_HOURS_KEY = "01_11_2026"
REFERENCE_HOURS_DATES = tuple((f"2026-11-{day:02d}", f"{day:02d}_11_2026", f"{day:02d}/11/2026") for day in range(1, 11))

def _parse_report_date(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"{field} không hợp lệ")


def normalize_teacher_hours_filters(filters: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Normalize the report date filters and cap the visible span at 62 days."""
    normalized = dict(filters or {})
    start = _parse_report_date(_date_filter(normalized, "from_date", "date_from"), "Từ ngày")
    end = _parse_report_date(_date_filter(normalized, "to_date", "date_to"), "Đến ngày")
    if not start and not end:
        start, end = "2026-11-01", "2026-11-10"
    elif start and not end:
        end = start
    elif end and not start:
        start = end
    first = datetime.strptime(start, "%Y-%m-%d").date()
    last = datetime.strptime(end, "%Y-%m-%d").date()
    if last < first:
        raise ValueError("Đến ngày phải bằng hoặc sau Từ ngày")
    if (last - first).days > 61:
        raise ValueError("Khoảng ngày tối đa là 62 ngày")
    normalized["from_date"], normalized["to_date"] = first.isoformat(), last.isoformat()
    return normalized


def _report_dates(filters: Mapping[str, Any] | None = None) -> tuple[tuple[str, str, str], ...]:
    normalized = normalize_teacher_hours_filters(filters)
    start = datetime.strptime(normalized["from_date"], "%Y-%m-%d").date()
    end = datetime.strptime(normalized["to_date"], "%Y-%m-%d").date()
    return tuple(
        (day.isoformat(), day.strftime("%d_%m_%Y"), day.strftime("%d/%m/%Y"))
        for offset in range((end - start).days + 1)
        for day in (start + timedelta(days=offset),)
    )


def teacher_hours_columns(filters: Mapping[str, Any] | None = None) -> tuple[tuple[str, str], ...]:
    date_columns = _report_dates(filters)
    return TEACHER_HOURS_COLUMNS[:9] + tuple((key, label) for _date, key, label in date_columns)


TEACHER_HOURS_COLUMNS = (
    ("no", "No."),
    ("giao_vien", "Giáo viên"),
    ("tong_so_gio_day", "Tổng số giờ dạy"),
    ("day_chinh", "Dạy chính"),
    ("tro_giang", "Trợ giảng"),
    ("day_bu", "Dạy bù"),
    ("tong_so_ca_day", "Tổng số Ca dạy"),
    ("tong_so_ngay_day", "Tổng số ngày dạy"),
    (
        "tong_so_gio_day_hoc_vien_ang_hoc_a_iem_danh",
        "Tổng số giờ dạy (Học viên đang học/Đã điểm danh)",
    ),
    *tuple((key, label) for _date, key, label in REFERENCE_HOURS_DATES),
)

TEACHER_HOURS_FILTERS = (
    {"name": "from_date", "label": "Từ ngày", "placeholder": "Từ ngày", "type": "text"},
    {"name": "to_date", "label": "Đến ngày", "placeholder": "Đến ngày", "type": "text"},
    {
        "name": "nhap_ten_giao_vien",
        "label": "Nhập tên giáo viên",
        "placeholder": "Nhập tên giáo viên",
        "type": "text",
    },
)

TEACHER_REPORT_ENTITIES = (
    "report_teacher_sth_index",
    "report_teacher_rest_learning",
)


def register(app_or_router: Any = None, service: Any = None) -> dict[str, Any]:
    """Register teacher report entities with the coordinator autoloader."""
    from .report_training import install_report_adapter

    target = service if service is not None else app_or_router
    installed = install_report_adapter(target)
    return {
        "routes": list(TEACHER_REPORT_ENTITIES),
        "source": "persistent-sqlite",
        "status": "ADAPTER_READY" if installed else "PENDING_PROVIDER",
    }


def _date_filter(filters: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = filters.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return ""


def _hours(start: Any, end: Any) -> float:
    """Return a non-negative duration in hours for HH:MM values."""
    first = last = None
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            first = datetime.strptime(str(start), fmt)
            last = datetime.strptime(str(end), fmt)
            break
        except (TypeError, ValueError):
            continue
    if first is None or last is None:
        return 0.0
    seconds = max(0, (last - first).total_seconds())
    return round(seconds / 3600, 2)


def _round(value: float) -> int | float:
    rounded = round(float(value), 2)
    return int(rounded) if rounded.is_integer() else rounded


def teacher_hours_rows(
    db: Any,
    filters: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Aggregate teacher teaching hours from durable class timetable rows.

    Supported filters are the observed ``from_date``, ``to_date`` and
    ``nhap_ten_giao_vien`` fields, plus ``teacher_id`` for role-scoped callers.
    A teacher with no scheduled sessions is retained with zero aggregates;
    this mirrors the reference table's teacher roster without fabricating a
    teaching event.
    """
    filters = dict(filters or {})
    filters = normalize_teacher_hours_filters(filters)
    date_specs = _report_dates(filters)
    from_date = filters["from_date"]
    to_date = filters["to_date"]
    name_query = _date_filter(filters, "nhap_ten_giao_vien", "teacher_query", "teacher", "q")

    sql = """
        SELECT u.id AS teacher_id,
               u.full_name AS teacher_name,
               t.id AS session_id,
               t.session_date,
               t.start_time,
               t.end_time,
               t.status AS session_status,
               c.id AS class_id,
               c.teacher_id AS primary_teacher_id,
               COUNT(DISTINCT CASE WHEN e.status='ENROLLED' AND a.status IN ('PRESENT','LATE') THEN e.student_id END) AS attended_students
        FROM users u
        LEFT JOIN timetable_sessions t ON t.teacher_id=u.id
        LEFT JOIN classes c ON c.id=t.class_id
        LEFT JOIN enrollments e ON e.class_id=c.id
        LEFT JOIN attendance a ON a.class_id=e.class_id
          AND a.student_id=e.student_id
          AND a.session_date=t.session_date
        WHERE u.role='TEACHER' AND u.active=1
    """
    params: list[Any] = []
    if from_date:
        sql += " AND (t.session_date IS NULL OR t.session_date>=?)"
        params.append(from_date)
    if to_date:
        sql += " AND (t.session_date IS NULL OR t.session_date<=?)"
        params.append(to_date)
    if name_query:
        sql += " AND (u.full_name LIKE ? OR u.username LIKE ?)"
        needle = f"%{name_query}%"
        params.extend((needle, needle))
    teacher_id = filters.get("teacher_id")
    if teacher_id not in (None, ""):
        try:
            teacher_id = int(teacher_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("teacher_id phải là số") from exc
        sql += " AND u.id=?"
        params.append(teacher_id)
    sql += " GROUP BY u.id,t.id ORDER BY u.full_name,t.session_date,t.start_time"

    try:
        source_rows = db.execute(sql, params).fetchall()
    except sqlite3.OperationalError as exc:
        if any(f"no such table: {table}" in str(exc).lower() for table in ("users", "timetable_sessions", "classes", "enrollments", "attendance")):
            return []
        raise

    grouped: dict[int, dict[str, Any]] = {}
    for row in source_rows:
        item = dict(row) if isinstance(row, Mapping) else dict(zip(
            ("teacher_id", "teacher_name", "session_id", "session_date", "start_time", "end_time", "session_status", "class_id", "primary_teacher_id", "attended_students"),
            row,
        ))
        teacher_key = int(item["teacher_id"])
        bucket = grouped.setdefault(teacher_key, {
            "giao_vien": item["teacher_name"],
            "tong_so_gio_day": 0.0,
            "day_chinh": 0.0,
            "tro_giang": 0.0,
            "day_bu": 0.0,
            "tong_so_ca_day": 0,
            "tong_so_ngay_day": set(),
            "tong_so_gio_day_hoc_vien_ang_hoc_a_iem_danh": 0.0,
            **{key: 0.0 for _date, key, _label in date_specs},
        })
        if item["session_id"] is None:
            continue
        if str(item.get("session_status") or "").upper() == "CANCELLED":
            continue
        duration = _hours(item["start_time"], item["end_time"])
        bucket["tong_so_gio_day"] += duration
        # Current schema has one primary teacher relation.  Assistant and
        # replacement shifts remain explicit zero until their source tables
        # exist; no English/UNKNOWN enum is exposed to the report.
        if item["primary_teacher_id"] == teacher_key:
            bucket["day_chinh"] += duration
        if item["attended_students"]:
            bucket["tong_so_gio_day_hoc_vien_ang_hoc_a_iem_danh"] += duration
        for report_date, report_key, _label in date_specs:
            if item["session_date"] == report_date:
                bucket[report_key] += duration
        bucket["tong_so_ca_day"] += 1
        if item["session_date"]:
            bucket["tong_so_ngay_day"].add(item["session_date"])

    rows = []
    for index, bucket in enumerate(grouped.values(), start=1):
        bucket["no"] = index
        bucket["tong_so_ngay_day"] = len(bucket["tong_so_ngay_day"])
        for key in ("tong_so_gio_day", "day_chinh", "tro_giang", "day_bu", "tong_so_gio_day_hoc_vien_ang_hoc_a_iem_danh", *(key for _date, key, _label in date_specs)):
            bucket[key] = _round(bucket[key])
        rows.append(bucket)
    return rows


def teacher_hours_definition() -> dict[str, Any]:
    """Return a serializable local definition for coordinator wiring/tests."""
    return {
        "route": "/report/teacher/sth/index",
        "title": "Thống kê giờ dạy giáo viên",
        "entity": "report_teacher_sth_index",
        "columns": [{"key": key, "label": label} for key, label in TEACHER_HOURS_COLUMNS],
        "filters": list(TEACHER_HOURS_FILTERS),
        "buttons": ["Excel"],
    }


def teacher_rest_learning_rows(
    db: Any,
    filters: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return absent enrolled learners with Vietnamese report semantics."""
    filters = dict(filters or {})
    where = ["a.status IN ('ABSENT','EXCUSED')", "e.status='ENROLLED'"]
    args: list[Any] = []
    query = next((str(filters[k]).strip() for k in ("nhap_ten_hoc_vien", "student_query", "q") if filters.get(k)), "")
    if query:
        where.append("(s.full_name LIKE ? OR s.student_code LIKE ?)")
        args.extend((f"%{query}%", f"%{query}%"))
    start = next((str(filters[k]).strip() for k in ("from_date_absent", "from_date", "date_from") if filters.get(k)), "")
    end = next((str(filters[k]).strip() for k in ("to_date_absent", "to_date", "date_to") if filters.get(k)), "")
    if start:
        where.append("a.session_date>=?"); args.append(start)
    if end:
        where.append("a.session_date<=?"); args.append(end)
    status = str(filters.get("filter_1") or "").strip()
    if status in {"Vắng có phép", "EXCUSED"}:
        where = [x for x in where if x != "a.status IN ('ABSENT','EXCUSED')"] + ["a.status='EXCUSED'"]
    elif status in {"Vắng không phép", "ABSENT"}:
        where = [x for x in where if x != "a.status IN ('ABSENT','EXCUSED')"] + ["a.status='ABSENT'"]
    student_status = str(filters.get("filter_2") or "").strip()
    student_status_map = {
        "Đang học": "ACTIVE", "Bảo lưu": "PAUSED", "Đã xong": "GRADUATED",
        "Nghỉ học": "INACTIVE", "ACTIVE": "ACTIVE", "PAUSED": "PAUSED",
        "GRADUATED": "GRADUATED", "INACTIVE": "INACTIVE",
    }
    if student_status in student_status_map:
        where.append("s.status=?")
        args.append(student_status_map[student_status])
    # The reference form exposes a class selector and a class-end-date range
    # in addition to the absence-date range.  Keep placeholder choices inert,
    # but apply real class/date values to the durable joins.
    class_choice = str(filters.get("filter_6") or filters.get("class_code") or "").strip()
    if class_choice and class_choice.casefold() not in {"tất cả", "danh sách lớp học", "chọn lớp học"}:
        if class_choice.isdigit():
            where.append("c.id=?")
            args.append(int(class_choice))
        else:
            where.append("c.code=?")
            args.append(class_choice)
    class_end_from = next((str(filters[k]).strip() for k in ("from_date_enroll", "class_end_from") if filters.get(k)), "")
    class_end_to = next((str(filters[k]).strip() for k in ("to_date_enroll", "class_end_to") if filters.get(k)), "")
    if class_end_from:
        where.append("c.end_date>=?")
        args.append(class_end_from)
    if class_end_to:
        where.append("c.end_date<=?")
        args.append(class_end_to)
    sql = """
        SELECT s.full_name AS student_name,COALESCE(NULLIF(s.parent1_name,''),p.full_name,'') AS parent_name,c.code AS class_code,
               c.end_date,a.session_date,a.status,a.note,t.start_time,t.end_time,
               COUNT(*) OVER (PARTITION BY s.id,c.id) AS absence_total,
               SUM(CASE WHEN a.status='EXCUSED' THEN 1 ELSE 0 END) OVER (PARTITION BY s.id,c.id) AS excused_total,
               SUM(CASE WHEN a.status='ABSENT' THEN 1 ELSE 0 END) OVER (PARTITION BY s.id,c.id) AS unexcused_total,
               s.status AS student_status
        FROM attendance a JOIN students s ON s.id=a.student_id
        JOIN enrollments e ON e.student_id=s.id AND e.class_id=a.class_id
        JOIN classes c ON c.id=a.class_id
        LEFT JOIN parents p ON p.student_id=s.id AND p.status='ACTIVE'
        LEFT JOIN timetable_sessions t ON t.class_id=a.class_id AND t.session_date=a.session_date
        WHERE """ + " AND ".join(where) + " ORDER BY a.session_date DESC,s.full_name"
    try:
        source = db.execute(sql, args).fetchall()
    except sqlite3.OperationalError as exc:
        if any(f"no such table: {table}" in str(exc).lower() for table in ("attendance", "students", "enrollments", "classes", "timetable_sessions")):
            return []
        raise
    rows=[]
    for index, row in enumerate(source, 1):
        r = dict(row) if isinstance(row, Mapping) else dict(zip(("student_name","parent_name","class_code","end_date","session_date","status","note","start_time","end_time","absence_total","excused_total","unexcused_total","student_status"), row))
        rows.append({
            "no": index, "hoc_vien": r["student_name"], "phu_huynh": r["parent_name"], "lop": r["class_code"],
            "ngay_ket_thuc": r["end_date"], "ngay_ket_thuc_trong_lop": r["end_date"],
            "tong_so_buoi_nghi": r["absence_total"], "co_phep": r["excused_total"], "khong_phep": r["unexcused_total"],
            "trang_thai_hoc_vien": {"ACTIVE":"Đang học","PAUSED":"Bảo lưu","GRADUATED":"Đã xong","INACTIVE":"Nghỉ học"}.get(r["student_status"], ""),
            # No makeup ledger exists in the local schema.  The absence count
            # is durable; money/makeup fields stay blank until a source exists.
            "so_buoi_khong_hoc_bu": None, "so_tien_khong_hoc_bu": None,
            "ngay": r["session_date"], "ca_hoc": f"{r['start_time'] or ''}-{r['end_time'] or ''}", "bai_hoc": "",
            "ghi_chu": r["note"], "trang_thai_nghi": "Vắng có phép" if r["status"] == "EXCUSED" else "Vắng không phép",
            "ghi_chu_hoc_bu": "", "thong_tin_hoc_bu": "", "trang_thai_buoi_hoc_bu": "",
            "iem_danh": "Có phép" if r["status"] == "EXCUSED" else "Vắng không phép", "cong_cu": "",
        })
    return rows


__all__ = [
    "REFERENCE_HOURS_DATE", "REFERENCE_HOURS_KEY", "REFERENCE_HOURS_DATES", "TEACHER_HOURS_COLUMNS", "teacher_hours_columns", "normalize_teacher_hours_filters", "TEACHER_HOURS_FILTERS", "teacher_hours_definition",
    "TEACHER_REPORT_ENTITIES", "teacher_hours_rows", "teacher_rest_learning_rows", "register",
]
