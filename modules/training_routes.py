"""Persistent contracts for the home and training route lane.

The reference capture exposes the Vietnamese screen shape, while the private
HTTP API is unavailable.  This module keeps a small, explicit local contract
that a controller can mount without guessing field names or enum labels.  It
uses SQLite JSON records for routes whose source tables are not yet wired and
provides the same CRUD, filtering, export, and role checks for every route.

Course data uses the same field vocabulary as the existing ``courses`` table
(``code``, ``name``, ``sessions_count`` and so on), so the coordinator can
mount the course contract directly on the existing persistent course API.
The optional natural seed is explicit and idempotent; it never copies rows
from the reference system.
"""
from __future__ import annotations

import csv
import io
import json
import re
import sqlite3
from datetime import datetime
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


READ_ROLES = frozenset(("ADMIN", "STAFF", "TEACHER", "STUDENT"))
MANAGE_ROLES = frozenset(("ADMIN", "STAFF"))
TEACHING_ROLES = frozenset(("ADMIN", "STAFF", "TEACHER"))


def _field(
    name: str,
    label: str,
    *,
    required: bool = False,
    kind: str = "text",
    options: Sequence[str] = (),
) -> Dict[str, Any]:
    return {
        "name": name,
        "label": label,
        "required": required,
        "kind": kind,
        "options": list(options),
    }


def _columns(*labels: str) -> List[Dict[str, str]]:
    """Give the observed table labels stable JSON keys."""
    output: List[Dict[str, str]] = []
    used: Dict[str, int] = {}
    for label in labels:
        if label in ("No.", "STT"):
            key = "no"
        else:
            # Keys are deliberately hand-readable and stable.  They are
            # presentation metadata, not a claim about the private API.
            key = {
                "Tên khóa học": "name",
                "Tên lớp": "class_name",
                "Chi nhánh": "branch",
                "Buổi học": "session_name",
                "Giáo viên": "teacher_name",
                "Điểm danh": "attendance",
                "Đánh giá": "evaluation",
                "Kiểm tra": "test_count",
                "Nội dung bài học": "lesson_content",
                "BTVN": "homework",
                "Số buổi / Số giờ": "sessions_hours",
                "Học phí": "fee_display",
                "Bài đánh giá hàng ngày": "daily_evaluation",
                "Bài kiểm tra": "test_count",
                "Môn học": "subject",
                "Trạng thái": "status",
                "Hành động": "actions",
                "Khóa học": "course_name",
                "Lớp học": "class_name",
                "Học viên": "student_name",
                "Họ tên": "full_name",
                "Họ và tên": "full_name",
                "Khách hàng": "customer_name",
                "Phụ huynh": "parent_name",
                "Nhân viên sale": "sale_owner",
                "Sales rep": "sale_owner",
                "Ngày hẹn test": "test_date",
                "Ghi chú": "note",
                "Nội dung": "content",
                "Người tạo": "created_by",
                "Ngày tạo": "created_at_value",
                "Mã hợp đồng": "contract_code",
                "Người thực hiện": "performed_by",
                "Công cụ": "actions",
                "Hành động": "actions",
                "Trung tâm": "center_name",
                "Ca học": "session_name",
                "Số buổi": "sessions_count",
                "Ngày bắt đầu": "start_date",
                "Khóa học đăng ký": "course_name",
                "Khóa học đăng kí": "course_name",
                "Tạo bởi": "created_by",
            }.get(label, label.lower().replace(" ", "_"))
        count = used.get(key, 0) + 1
        used[key] = count
        if count > 1:
            key = "%s_%s" % (key, count)
        output.append({"key": key, "label": label})
    return output


STATUS_COURSE = ("Hoạt động", "Ngừng hoạt động")
STATUS_ABSENT = ("Chưa phê duyệt", "Đồng ý", "Từ chối", "Hủy", "Nhận thông tin")
STATUS_SENT = ("Mới tạo", "Đã gửi")
STATUS_POST = ("Chờ phê duyệt", "Đã phê duyệt")
STATUS_CLASS = ("Chưa học", "Đang học", "Sắp kết thúc", "Đã xong", "Bị hủy", "Chưa có lịch học")
STATUS_ATTENDANCE = ("Có mặt", "Vắng", "Đi muộn", "Có phép")
STATUS_TEST = ("Chưa bắt đầu", "Đang học", "Đã học xong")
STATUS_PENDING = ("Đang chờ", "Đã vào lớp", "Hủy")

# The authenticated capture exposed a three-step class wizard at
# ``/training/class/create`` in addition to the class list.  The host keeps
# the durable transaction in ``/api/classes/workflow`` (app.py owns that
# domain table), so this lane owns only the observed field/step contract and
# the wire normalizer used by the local renderer.  The editable ``fullname``
# input is transported as the explicit coordinator key ``name``.  The host
# must add/read that field on ``classes`` before a successful response can be
# claimed; this lane never aliases it to ``code`` or ``notes``.
CLASS_CREATE_ROUTE = "/training/class/create"
CLASS_NAME_MAX_LENGTH = 160
CLASS_CREATE_STEPS: Tuple[Dict[str, str], ...] = (
    {"key": "class", "label": "Lớp học"},
    {"key": "schedule", "label": "Lịch học"},
    {"key": "students", "label": "Học viên"},
)
CLASS_CREATE_FIELDS: Tuple[Dict[str, Any], ...] = (
    _field("fullname", "Tên lớp", kind="text"),
    _field("code", "Mã lớp", required=True),
    _field("course_id", "Khóa học", required=True, kind="number"),
    _field("number_of_session", "Số buổi", kind="number"),
    _field("number_of_session_vietnam_teacher", "Số buổi giáo viên Việt", kind="number"),
    _field("number_of_session_foreign_teacher", "Số buổi giáo viên nước ngoài", kind="number"),
    _field("number_of_hours", "Số giờ", kind="number"),
    _field("open_at", "Ngày bắt đầu", kind="date"),
    _field("close_at", "Ngày kết thúc", kind="date"),
    _field("type_cost", "Hình thức học phí", options=("0", "1", "2", "Theo khóa", "Theo buổi", "Theo tháng")),
    _field("max_student", "Số học viên tối đa", kind="number"),
    _field("max_student_per_session", "Số học viên tối đa mỗi buổi", kind="number"),
    _field("cm_ids[]", "CM chính", kind="select-multiple"),
    _field("cm_second_ids[]", "CM phụ", kind="select-multiple"),
    _field("daily_evaluation_id", "Bài đánh giá hàng ngày"),
    _field("note", "Ghi chú"),
    _field("room", "Phòng học"),
    _field("teacher_id", "Giáo viên", kind="number"),
    _field("status", "Trạng thái", options=("PLANNED", "OPEN", "IN_PROGRESS", "COMPLETED", "CANCELLED")),
    _field("sessions", "Các buổi học", kind="array"),
    _field("student_ids", "Học viên đã chọn", kind="array"),
)
CLASS_CREATE_CONTRACT: Dict[str, Any] = {
    "route": CLASS_CREATE_ROUTE,
    "title": "Tạo lớp học",
    "resource": "class_create_workflow",
    "columns": [],
    "filters": [],
    "actions": ["Lưu & tiếp tục"],
    "read_roles": READ_ROLES,
    "write_roles": MANAGE_ROLES,
    "domain_endpoint": "/api/classes/workflow",
    "steps": list(CLASS_CREATE_STEPS),
    "fields": list(CLASS_CREATE_FIELDS),
    "submit": "/api/classes/workflow",
    "source": "observed DOM + local workflow adapter",
    "persistence": "coordinator-owned classes.name + classes/timetable_sessions/enrollments transaction",
    "name_transport": {
        "input": "fullname",
        "payload": "name",
        "max_length": CLASS_NAME_MAX_LENGTH,
        "provenance": "observed DOM field; coordinator integration key",
        "readback": "data.class.name must equal the submitted trimmed value",
    },
    "unknowns": ["cm_ids[]", "cm_second_ids[]", "daily_evaluation_id"],
}


def class_workflow_payload(data: Mapping[str, Any]) -> Dict[str, Any]:
    """Normalize observed wizard fields to the host's atomic workflow wire.

    The private reference form names are retained in ``CLASS_CREATE_FIELDS``.
    ``fullname`` has a deliberate local wire mapping to ``name`` so user input
    cannot be silently discarded.  CM selectors and daily evaluation remain
    unknown reference fields and are not put on the host workflow wire.
    """
    if not isinstance(data, Mapping):
        raise ValueError("Dữ liệu tạo lớp phải là một đối tượng")
    try:
        course_id = int(data.get("course_id"))
    except (TypeError, ValueError) as exc:
        raise ValueError("Khóa học là bắt buộc") from exc
    if course_id < 1:
        raise ValueError("Khóa học không hợp lệ")
    code = str(data.get("code") or "").strip().upper()
    if not code:
        raise ValueError("Mã lớp là bắt buộc")
    if len(code) > 32:
        raise ValueError("Mã lớp không được dài quá 32 ký tự")

    has_fullname = "fullname" in data
    raw_fullname = data.get("fullname", "")
    if raw_fullname is None:
        raw_fullname = ""
    if not isinstance(raw_fullname, str):
        raise ValueError("Tên lớp phải là văn bản")
    fullname = raw_fullname.strip()
    if has_fullname and not fullname:
        raise ValueError("Tên lớp là bắt buộc")
    if len(fullname) > CLASS_NAME_MAX_LENGTH:
        raise ValueError("Tên lớp không được dài quá %s ký tự" % CLASS_NAME_MAX_LENGTH)

    payload: Dict[str, Any] = {"course_id": course_id, "code": code}
    if fullname:
        payload["name"] = fullname
    number_map = (
        ("number_of_session", "sessions_count"),
        ("number_of_session_vietnam_teacher", "vn_teacher_sessions"),
        ("number_of_session_foreign_teacher", "foreign_teacher_sessions"),
        ("number_of_hours", "hours"),
        ("max_student", "max_students"),
        ("max_student_per_session", "max_students_per_session"),
    )
    for source, target in number_map:
        value = data.get(source)
        if value in (None, ""):
            continue
        payload[target] = _number(value, source, required=False)
    date_map = (("open_at", "start_date"), ("close_at", "end_date"))
    for source, target in date_map:
        value = data.get(source)
        if value not in (None, ""):
            payload[target] = _date(value, source, required=False)
    if payload.get("start_date") and payload.get("end_date") and payload["end_date"] < payload["start_date"]:
        raise ValueError("Ngày kết thúc phải sau ngày bắt đầu")
    payment = data.get("type_cost")
    if payment not in (None, ""):
        payment_labels = {"0": "Theo khóa", "1": "Theo buổi", "2": "Theo tháng"}
        payload["payment_method"] = payment_labels.get(str(payment), str(payment).strip())
    for source, target in (
        ("note", "notes"),
        ("room", "room"),
        ("status", "status"),
    ):
        value = data.get(source)
        if value not in (None, ""):
            payload[target] = str(value).strip()
    teacher_id = data.get("teacher_id")
    if teacher_id not in (None, ""):
        try:
            payload["teacher_id"] = int(teacher_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("teacher_id phải là số") from exc
    sessions = data.get("sessions", [])
    if not isinstance(sessions, list):
        raise ValueError("Các buổi học phải là danh sách")
    normalized_sessions: List[Dict[str, Any]] = []
    for index, item in enumerate(sessions, start=1):
        if not isinstance(item, Mapping):
            raise ValueError("Buổi học %s không hợp lệ" % index)
        session_date = _date(item.get("session_date"), "sessions[%s].session_date" % index, required=True)
        start_time = str(item.get("start_time") or "").strip()
        end_time = str(item.get("end_time") or "").strip()
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", start_time) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", end_time):
            raise ValueError("Buổi học %s phải có giờ hợp lệ" % index)
        if end_time <= start_time:
            raise ValueError("Buổi học %s phải kết thúc sau giờ bắt đầu" % index)
        row = {"session_date": session_date, "start_time": start_time, "end_time": end_time}
        if item.get("room") not in (None, ""):
            row["room"] = str(item["room"]).strip()
        normalized_sessions.append(row)
    payload["sessions"] = normalized_sessions
    student_ids = data.get("student_ids", [])
    if not isinstance(student_ids, list):
        raise ValueError("Học viên đã chọn phải là danh sách")
    normalized_students: List[int] = []
    for value in student_ids:
        try:
            student_id = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Mã học viên phải là số") from exc
        if student_id < 1 or student_id in normalized_students:
            raise ValueError("Danh sách học viên không hợp lệ hoặc bị trùng")
        normalized_students.append(student_id)
    payload["student_ids"] = normalized_students
    return payload


ROUTE_CONTRACTS: Dict[str, Dict[str, Any]] = {
    "/": {
        "title": "Trang chủ", "resource": "training_dashboard",
        "columns": _columns("Tên lớp", "Chi nhánh", "Buổi học", "Giáo viên", "Điểm danh", "Đánh giá", "Kiểm tra", "Nội dung bài học", "BTVN"),
        "filters": [_field("date", "Chọn ngày", kind="date"), _field("query", "Tìm kiếm")],
        "actions": [], "fields": [_field("class_name", "Tên lớp", required=True), _field("branch", "Chi nhánh"), _field("session_name", "Buổi học"), _field("teacher_name", "Giáo viên"), _field("attendance", "Điểm danh"), _field("evaluation", "Đánh giá"), _field("test_count", "Kiểm tra"), _field("lesson_content", "Nội dung bài học"), _field("homework", "BTVN")], "read_roles": READ_ROLES, "write_roles": frozenset(),
    },
    "/dashboard/training": {
        "title": "Trang chủ quản lý đào tạo", "resource": "training_dashboard",
        "columns": _columns("Tên lớp", "Chi nhánh", "Buổi học", "Giáo viên", "Điểm danh", "Đánh giá", "Kiểm tra", "Nội dung bài học", "BTVN"),
        "filters": [_field("branch", "Chi nhánh"), _field("date", "Chọn ngày", kind="date"), _field("query", "Tìm kiếm")],
        "actions": [], "fields": [_field("class_name", "Tên lớp", required=True), _field("branch", "Chi nhánh"), _field("session_name", "Buổi học"), _field("teacher_name", "Giáo viên"), _field("attendance", "Điểm danh"), _field("evaluation", "Đánh giá"), _field("test_count", "Kiểm tra"), _field("lesson_content", "Nội dung bài học"), _field("homework", "BTVN")], "read_roles": READ_ROLES, "write_roles": frozenset(),
    },
    "/training/announcement": {
        "title": "Thông báo", "resource": "announcements",
        "columns": _columns("No.", "Thông báo", "Đã xem/Đã gửi", "Trạng thái", "Tạo bởi", "Cấu hình bình luận", "Chi nhánh", "Hành động"),
        "filters": [_field("status", "Trạng thái", options=("Tất cả",) + STATUS_SENT), _field("query", "Tìm kiếm")],
        "actions": ["Tạo thông báo"],
        "fields": [_field("title", "Tiêu đề", required=True), _field("status", "Trạng thái", options=STATUS_SENT), _field("created_by", "Tạo bởi"), _field("comment_config", "Cấu hình bình luận"), _field("branch", "Chi nhánh"), _field("note", "Ghi chú")],
        "read_roles": READ_ROLES, "write_roles": MANAGE_ROLES,
    },
    "/training/absent-v2": {
        "title": "Xin nghỉ", "resource": "absence_requests",
        "columns": _columns("No.", "Học viên", "Buổi nghỉ", "Lý do", "Trạng thái", "Bình luận"),
        "filters": [_field("status", "Trạng thái", options=("Tất cả",) + STATUS_ABSENT), _field("class_name", "Lớp học"), _field("from_date", "Từ ngày", kind="date"), _field("to_date", "Đến ngày", kind="date"), _field("query", "Tìm kiếm")],
        "actions": ["Thêm mới", "Đồng ý", "Từ chối"],
        "fields": [_field("student_name", "Học viên", required=True), _field("class_name", "Lớp học", required=True), _field("from_date", "Từ ngày", required=True, kind="date"), _field("to_date", "Đến ngày", required=True, kind="date"), _field("reason", "Lý do"), _field("status", "Trạng thái", options=STATUS_ABSENT), _field("comment", "Bình luận")],
        "read_roles": READ_ROLES, "write_roles": TEACHING_ROLES,
    },
    "/training/event": {
        "title": "Sự kiện đào tạo", "resource": "training_events",
        "columns": _columns("No.", "Lượt xem", "Nội dung", "Đã xem/Đã gửi", "Trạng thái", "Bình luận", "Công cụ"),
        "filters": [_field("status", "Trạng thái", options=("Tất cả",) + STATUS_SENT), _field("query", "Tìm kiếm")],
        "actions": ["Tạo sự kiện đào tạo"],
        "fields": [_field("title", "Tiêu đề", required=True), _field("description", "Mô tả"), _field("max_register", "Số người tối đa", kind="number"), _field("start_date", "Ngày bắt đầu", kind="date"), _field("end_date", "Ngày kết thúc", kind="date"), _field("status", "Trạng thái", options=STATUS_SENT), _field("range", "Phạm vi")],
        "read_roles": READ_ROLES, "write_roles": MANAGE_ROLES,
    },
    "/training/post": {
        "title": "Bài viết", "resource": "training_posts",
        "columns": _columns("No.", "Lớp học", "Nội dung", "Người tạo", "Ngày tạo", "Cấu hình bình luận", "Trạng thái", "Chi nhánh", "Hành động"),
        "filters": [_field("class_name", "Lớp học"), _field("status", "Trạng thái", options=("Tất cả",) + STATUS_POST), _field("from_date", "Từ ngày", kind="date"), _field("to_date", "Đến ngày", kind="date"), _field("query", "Tìm kiếm")],
        "actions": ["Tạo bài viết"],
        "fields": [_field("class_name", "Lớp học"), _field("content", "Nội dung", required=True), _field("created_by", "Người tạo"), _field("created_at_value", "Ngày tạo", kind="date"), _field("comment_config", "Cấu hình bình luận"), _field("status", "Trạng thái", options=STATUS_POST), _field("branch", "Chi nhánh")],
        "read_roles": READ_ROLES, "write_roles": MANAGE_ROLES,
    },
    "/training/course": {
        "title": "Khóa học", "resource": "courses",
        "columns": _columns("No.", "Tên khóa học", "Số buổi / Số giờ", "Học phí", "Bài đánh giá hàng ngày", "Bài kiểm tra", "Môn học", "Trạng thái", "Hành động"),
        "filters": [_field("query", "Tìm...")], "actions": ["Thêm mới", "Nhân bản", "Excel"],
        "fields": [_field("code", "Mã khóa", required=True), _field("name", "Tên khóa học", required=True), _field("sessions_count", "Số buổi", kind="number"), _field("hours", "Số giờ", kind="number"), _field("fee_method", "Phương thức thu tiền", options=("Theo khóa", "Theo buổi", "Theo tháng")), _field("fee", "Học phí", kind="number"), _field("daily_evaluation", "Bài đánh giá hàng ngày"), _field("subject", "Môn học"), _field("status", "Trạng thái", options=STATUS_COURSE), _field("description", "Mô tả")],
        "read_roles": READ_ROLES, "write_roles": MANAGE_ROLES, "source_table": "courses",
    },
    "/training/class": {
        "title": "Lớp học", "resource": "classes",
        "columns": _columns("No.", "Lớp học", "Khóa học", "Học viên (Đang học)", "Thời gian", "Lịch học", "CM", "Giáo viên", "Đã học/Số buổi", "Hành động"),
        "filters": [_field("status", "Trạng thái", options=("Tất cả",) + STATUS_CLASS), _field("course_name", "Khóa học"), _field("query", "Tìm kiếm"), _field("teacher_name", "Giáo viên"), _field("start_from", "Ngày bắt đầu: từ ngày", kind="date"), _field("start_to", "Ngày bắt đầu: đến ngày", kind="date")],
        "actions": ["Upload", "Excel", "Thêm mới"],
        "fields": [_field("code", "Lớp học", required=True), _field("course_name", "Khóa học", required=True), _field("student_count", "Học viên", kind="number"), _field("start_date", "Ngày bắt đầu", kind="date"), _field("end_date", "Ngày kết thúc", kind="date"), _field("schedule", "Lịch học"), _field("manager", "CM"), _field("teacher_name", "Giáo viên"), _field("status", "Trạng thái", options=STATUS_CLASS), _field("notes", "Ghi chú")],
        "read_roles": READ_ROLES, "write_roles": MANAGE_ROLES,
    },
    "/training/timetable": {
        "title": "Thời khóa biểu", "resource": "timetable_sessions",
        "columns": _columns("Ngày", "Phòng học Ca học", "A01", "A02", "c5", "Phòng 01", "Phòng 1", "phòng học Sky, giáo viên Hà Anh", "phòng học Sky, giáo viên Hà Anh"),
        "filters": [_field("week", "Tuần"), _field("teacher_name", "Giáo viên"), _field("course_name", "Khóa học"), _field("class_name", "Lớp học"), _field("room", "Phòng học")],
        "actions": ["Tìm kiếm", "Excel"],
        "fields": [_field("session_date", "Ngày", required=True, kind="date"), _field("start_time", "Giờ bắt đầu"), _field("end_time", "Giờ kết thúc"), _field("room", "Phòng học"), _field("session_name", "Ca học"), _field("class_name", "Lớp học", required=True), _field("course_name", "Khóa học"), _field("teacher_name", "Giáo viên"), _field("status", "Trạng thái", options=("Đã lên lịch", "Đã hoàn thành", "Đã hủy"))],
        "read_roles": READ_ROLES, "write_roles": MANAGE_ROLES,
    },
    "/training/attendance": {
        "title": "Điểm danh", "resource": "attendance", "columns": [],
        "filters": [_field("status", "Trạng thái", options=("Đang học", "Đã học", "Tất cả")), _field("class_name", "Lớp học"), _field("session_name", "Buổi học")], "actions": [],
        "fields": [_field("student_name", "Học viên", required=True), _field("class_name", "Lớp học", required=True), _field("session_date", "Ngày", required=True, kind="date"), _field("status", "Trạng thái", options=STATUS_ATTENDANCE), _field("note", "Ghi chú")],
        "read_roles": READ_ROLES, "write_roles": TEACHING_ROLES,
    },
    "/training/daily-evaluation-v2": {
        "title": "Đánh giá hàng ngày", "resource": "daily_evaluations", "columns": [],
        "filters": [_field("class_name", "Lớp học"), _field("session_date", "Ngày", kind="date")], "actions": [],
        "fields": [_field("student_name", "Học viên", required=True), _field("class_name", "Lớp học", required=True), _field("session_date", "Ngày", required=True, kind="date"), _field("score", "Điểm", kind="number"), _field("note", "Nhận xét")],
        "read_roles": READ_ROLES, "write_roles": TEACHING_ROLES,
    },
    "/training/test": {
        "title": "Kiểm tra", "resource": "training_tests", "columns": [],
        "filters": [_field("status", "Trạng thái", options=("Đang học", "Đã học", "Tất cả")), _field("class_name", "Lớp học"), _field("test_name", "Bài kiểm tra"), _field("query", "Tìm...")], "actions": [],
        "fields": [_field("name", "Tên bài kiểm tra", required=True), _field("class_name", "Lớp học", required=True), _field("test_date", "Ngày", required=True, kind="date"), _field("max_score", "Điểm tối đa", kind="number"), _field("status", "Trạng thái", options=STATUS_TEST), _field("note", "Ghi chú")],
        "read_roles": READ_ROLES, "write_roles": TEACHING_ROLES,
    },
    "/training/homework": {
        "title": "Bài tập về nhà", "resource": "homework", "columns": [],
        "filters": [_field("status", "Trạng thái", options=("Đang học", "Đã học", "Tất cả")), _field("class_name", "Lớp học"), _field("session_date", "Buổi học", kind="date"), _field("returned", "Trạng thái trả bài", options=("Đã trả bài", "Chưa trả bài"))], "actions": [],
        "fields": [_field("title", "Tiêu đề", required=True), _field("class_name", "Lớp học", required=True), _field("due_date", "Hạn nộp", required=True, kind="date"), _field("status", "Trạng thái", options=("Bản nháp", "Đang mở", "Đã đóng")), _field("returned", "Trạng thái trả bài", options=("Đã trả bài", "Chưa trả bài")), _field("description", "Mô tả")],
        "read_roles": READ_ROLES, "write_roles": TEACHING_ROLES,
    },
    "/training/elearn/topic": {
        "title": "Bộ đề", "resource": "elearn_topics", "columns": [], "filters": [], "actions": ["Đồng bộ", "Bỏ qua"],
        "fields": [_field("name", "Tên bộ đề", required=True), _field("subject", "Môn học"), _field("status", "Trạng thái", options=("Đang dùng", "Tạm dừng"))],
        "read_roles": READ_ROLES, "write_roles": MANAGE_ROLES,
    },
    "/training/elearn/exam_first_test": {
        "title": "Danh sách bài test đầu vào", "resource": "elearn_entry_tests", "columns": [], "filters": [], "actions": [],
        "fields": [_field("name", "Tên bài test", required=True), _field("subject", "Môn học"), _field("status", "Trạng thái", options=("Đang dùng", "Tạm dừng"))],
        "read_roles": READ_ROLES, "write_roles": MANAGE_ROLES,
    },
    "/training/class_enroll_trail_wait": {
        "title": "Danh sách khách hàng đăng ký học thử", "resource": "trial_registrations",
        "columns": _columns("No.", "Khách hàng", "Phụ huynh", "Sales rep", "Lớp học", "Thời gian", "Trạng thái", "Hành động", "Ghi chú"),
        "filters": [_field("class_name", "Lớp học"), _field("status", "Trạng thái", options=("Tất cả", "Chưa phê duyệt", "Đã phê duyệt", "Hủy học thử")), _field("from_date", "Từ ngày", kind="date"), _field("to_date", "Đến ngày", kind="date"), _field("query", "Tìm...")], "actions": ["Excel"],
        "fields": [_field("customer_name", "Khách hàng", required=True), _field("parent_name", "Phụ huynh"), _field("sale_owner", "Sales rep"), _field("class_name", "Lớp học"), _field("schedule", "Thời gian"), _field("status", "Trạng thái", options=("Chưa phê duyệt", "Đã phê duyệt", "Hủy học thử")), _field("note", "Ghi chú")],
        "read_roles": READ_ROLES, "write_roles": MANAGE_ROLES,
    },
    "/training/confirm": {
        "title": "Xác nhận ghi danh", "resource": "enrollment_confirmations",
        "columns": _columns("No.", "Họ tên", "Lớp đăng ký", "Số buổi", "Lịch", "Ngày ghi danh vào lớp", "Mã hợp đồng", "Trạng thái", "Người thực hiện", "Công cụ"),
        "filters": [_field("query", "Tìm trong bảng..."), _field("class_name", "Lớp học"), _field("performed_by", "Người thực hiện")], "actions": ["Excel"],
        "fields": [_field("full_name", "Họ tên", required=True), _field("class_name", "Lớp đăng ký", required=True), _field("sessions_count", "Số buổi", kind="number"), _field("schedule", "Lịch"), _field("enrolled_at", "Ngày ghi danh", kind="date"), _field("contract_code", "Mã hợp đồng", required=True), _field("status", "Trạng thái", options=("Chờ duyệt", "Đã duyệt", "Từ chối")), _field("performed_by", "Người thực hiện")],
        "read_roles": READ_ROLES, "write_roles": MANAGE_ROLES,
    },
    "/training/customer_test": {
        "title": "Danh sách test / hẹn test", "resource": "customer_tests",
        "columns": _columns("STT", "Khách hàng", "Phụ huynh", "Ngày hẹn test", "Điểm test", "Nhân viên sale", "Ghi chú"),
        "filters": [_field("query", "Tìm trong bảng..."), _field("from_date", "Từ ngày", kind="date"), _field("to_date", "Đến ngày", kind="date"), _field("sale_owner", "Nhân viên sale")], "actions": ["Excel"],
        "fields": [_field("customer_name", "Khách hàng", required=True), _field("parent_name", "Phụ huynh"), _field("test_date", "Ngày hẹn test", required=True, kind="date"), _field("score", "Điểm test", kind="number"), _field("sale_owner", "Nhân viên sale"), _field("note", "Ghi chú")],
        "read_roles": READ_ROLES, "write_roles": MANAGE_ROLES,
    },
    "/training/pending_enrollment/index": {
        "title": "Đăng ký chờ lớp", "resource": "pending_enrollments",
        "columns": _columns("No.", "Khách hàng", "Trung tâm", "Ca học", "Số buổi", "Ngày bắt đầu", "Khóa học", "Ghi chú", "Trạng thái", "Tạo bởi", "Hành động"),
        "filters": [_field("status", "Trạng thái", options=STATUS_PENDING), _field("session_name", "Ca học"), _field("course_name", "Khóa học"), _field("query", "Tìm kiếm ...")], "actions": ["Tạo mới", "Excel"],
        "fields": [_field("customer_name", "Khách hàng", required=True), _field("center_name", "Trung tâm", required=True), _field("session_name", "Ca học"), _field("sessions_count", "Số buổi", kind="number"), _field("start_date", "Ngày bắt đầu", kind="date"), _field("course_name", "Khóa học"), _field("note", "Ghi chú"), _field("status", "Trạng thái", options=STATUS_PENDING), _field("created_by", "Tạo bởi", required=True)],
        "read_roles": READ_ROLES, "write_roles": MANAGE_ROLES,
    },
}


SCHEMA = """
CREATE TABLE IF NOT EXISTS training_route_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  route TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_by TEXT NOT NULL,
  deleted_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_training_route_records_route
  ON training_route_records(route, id);
"""


def _date(value: Any, label: str, required: bool = False) -> Optional[str]:
    text = str(value or "").strip()
    if not text:
        if required:
            raise ValueError("%s là bắt buộc" % label)
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError("%s phải là ngày hợp lệ" % label)


def _number(value: Any, label: str, required: bool = False) -> Optional[float]:
    if value in (None, ""):
        if required:
            raise ValueError("%s là bắt buộc" % label)
        return None
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("%s phải là số" % label) from exc
    if number < 0:
        raise ValueError("%s không được âm" % label)
    return int(number) if number.is_integer() else number


def _role(role: str, allowed: Iterable[str]) -> None:
    if str(role or "").upper() not in set(allowed):
        raise PermissionError("Bạn không có quyền truy cập màn hình đào tạo")


class TrainingRoutesStore:
    """SQLite-backed CRUD/query/export boundary for the training lane."""

    def __init__(self, connection: sqlite3.Connection):
        self.db = connection
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.db.commit()

    @staticmethod
    def contract(route: str) -> Dict[str, Any]:
        try:
            return ROUTE_CONTRACTS[route]
        except KeyError as exc:
            raise ValueError("Route đào tạo chưa có hợp đồng: %s" % route) from exc

    def list(
        self,
        route: str,
        *,
        role: str,
        query: str = "",
        filters: Optional[Mapping[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        contract = self.contract(route)
        _role(role, contract.get("read_roles", READ_ROLES))
        filters = dict(filters or {})
        rows = self.db.execute(
            "SELECT * FROM training_route_records WHERE route=? AND deleted_at IS NULL ORDER BY id DESC",
            (route,),
        ).fetchall()
        needle = str(query or filters.get("query") or "").strip().casefold()
        output: List[Dict[str, Any]] = []
        for row in rows:
            data = self._decode(row["payload_json"])
            haystack = json.dumps(data, ensure_ascii=False).casefold()
            if needle and needle not in haystack:
                continue
            if not self._matches_filters(data, filters):
                continue
            output.append(self._record(route, row))
        start = max(0, int(offset))
        return output[start : start + max(1, min(int(limit), 500))]

    def get(self, route: str, record_id: int, *, role: str) -> Optional[Dict[str, Any]]:
        contract = self.contract(route)
        _role(role, contract.get("read_roles", READ_ROLES))
        row = self.db.execute(
            "SELECT * FROM training_route_records WHERE route=? AND id=? AND deleted_at IS NULL",
            (route, int(record_id)),
        ).fetchone()
        if row is None:
            return None
        return self._record(route, row)

    def create(self, route: str, *, role: str, created_by: str, data: Mapping[str, Any]) -> Dict[str, Any]:
        contract = self.contract(route)
        _role(role, contract.get("write_roles", frozenset()))
        normalized = self._validate(contract, data)
        if not normalized:
            raise ValueError("Ít nhất một trường dữ liệu là bắt buộc")
        cur = self.db.execute(
            "INSERT INTO training_route_records(route,payload_json,created_by) VALUES(?,?,?)",
            (route, json.dumps(normalized, ensure_ascii=False, sort_keys=True), str(created_by).strip() or "Quản trị viên trung tâm"),
        )
        self.db.commit()
        return self.get(route, int(cur.lastrowid), role=role) or {}

    def update(self, route: str, record_id: int, *, role: str, data: Mapping[str, Any]) -> Dict[str, Any]:
        contract = self.contract(route)
        _role(role, contract.get("write_roles", frozenset()))
        current = self.get(route, int(record_id), role=role)
        if current is None:
            raise KeyError("Không tìm thấy bản ghi")
        field_names = {str(item["name"]) for item in contract.get("fields", []) if item.get("name")}
        merged = {key: current[key] for key in field_names if key in current}
        merged.update(dict(data))
        normalized = self._validate(contract, merged)
        self.db.execute(
            "UPDATE training_route_records SET payload_json=?,updated_at=CURRENT_TIMESTAMP WHERE route=? AND id=? AND deleted_at IS NULL",
            (json.dumps(normalized, ensure_ascii=False, sort_keys=True), route, int(record_id)),
        )
        self.db.commit()
        return self.get(route, int(record_id), role=role) or {}

    def duplicate(self, route: str, record_id: int, *, role: str, data: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        """Duplicate a course contract while preserving a unique local code."""
        contract = self.contract(route)
        _role(role, contract.get("write_roles", frozenset()))
        source = self.get(route, int(record_id), role=role)
        if source is None:
            raise KeyError("Không tìm thấy bản ghi")
        field_names = {str(item["name"]) for item in contract.get("fields", []) if item.get("name")}
        payload = {key: source[key] for key in field_names if key in source}
        overrides = dict(data or {})
        if route == "/training/course":
            source_code = str(payload.get("code") or "KHOA-HOC")
            payload.update(overrides)
            requested = str(overrides.get("code") or "").strip().upper()
            base_code = requested or source_code
            code = (base_code[:26] + "-SAO") if not requested else base_code
            suffix = 2
            while self.db.execute(
                "SELECT 1 FROM training_route_records WHERE route=? AND deleted_at IS NULL AND json_extract(payload_json,'$.code')=?",
                (route, code),
            ).fetchone():
                tail = "-%s" % suffix
                code = base_code[: max(1, 32 - len(tail))] + tail
                suffix += 1
            payload["code"] = code
            if not overrides.get("name"):
                payload["name"] = str(payload.get("name") or "Khóa học") + " (bản sao)"
        else:
            payload.update(overrides)
        return self.create(route, role=role, created_by=self._creator(route, int(record_id)), data=payload)

    def delete(self, route: str, record_id: int, *, role: str) -> None:
        contract = self.contract(route)
        _role(role, contract.get("write_roles", frozenset()))
        cur = self.db.execute(
            "UPDATE training_route_records SET deleted_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP WHERE route=? AND id=? AND deleted_at IS NULL",
            (route, int(record_id)),
        )
        if cur.rowcount != 1:
            raise KeyError("Không tìm thấy bản ghi")
        self.db.commit()

    def export_csv(self, route: str, *, role: str, query: str = "", filters: Optional[Mapping[str, Any]] = None) -> str:
        contract = self.contract(route)
        rows = self.list(route, role=role, query=query, filters=filters, limit=10000)
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        columns = contract.get("columns", [])
        writer.writerow([column["label"] for column in columns])
        for index, row in enumerate(rows, 1):
            writer.writerow([index if column["key"] == "no" else self._display_value(column["key"], row) for column in columns])
        return "\ufeff" + output.getvalue()

    def seed_natural(self, route: Optional[str] = None) -> int:
        """Insert local Vietnamese seed rows only into an empty route.

        This is intentionally opt-in.  It gives an isolated demo database
        useful rows without altering a user's database or copying reference
        records.  The values are ordinary local examples, not reference data.
        """
        routes = [route] if route else [
            item_route for item_route, item_contract in ROUTE_CONTRACTS.items()
            if item_contract.get("fields")
        ]
        seeded = 0
        samples = {
            "/training/announcement": [
                {"title": "Lịch học tháng 11", "status": "Đã gửi", "created_by": "Nguyễn Thu Hà", "comment_config": "Cho phép bình luận", "branch": "Trung tâm CenterOnline - Demo", "note": "Thông báo lịch học và lịch nghỉ."},
            ],
            "/training/absent-v2": [
                {"student_name": "Nguyễn Minh Anh", "class_name": "TA-NEN-TANG-01", "from_date": "2026-11-10", "to_date": "2026-11-10", "reason": "Học viên có việc gia đình", "status": "Chưa phê duyệt", "comment": ""},
            ],
            "/training/event": [
                {"title": "Ngày hội giao tiếp tiếng Anh", "description": "Hoạt động thực hành theo nhóm cho học viên.", "max_register": 40, "start_date": "2026-11-21", "end_date": "2026-11-21", "status": "Mới tạo", "range": "Toàn trung tâm"},
            ],
            "/training/post": [
                {"class_name": "TA-NEN-TANG-01", "content": "Tài liệu ôn tập buổi 3 đã được cập nhật.", "created_by": "Trần Minh Anh", "created_at_value": "2026-11-03", "comment_config": "Cho phép bình luận", "status": "Đã phê duyệt", "branch": "Trung tâm CenterOnline - Demo"},
            ],
            "/": [
                {"class_name": "TA-NEN-TANG-01", "branch": "Trung tâm CenterOnline - Demo", "session_name": "03/11/2026 · 18:30 - 20:00", "teacher_name": "Trần Minh Anh", "attendance": "12/12", "evaluation": "Đã đánh giá", "test_count": "1", "lesson_content": "Thì hiện tại đơn", "homework": "1"},
                {"class_name": "IELTS-MUC-TIEU-02", "branch": "Trung tâm CenterOnline - Demo", "session_name": "07/11/2026 · 09:00 - 11:00", "teacher_name": "Lê Quốc Bảo", "attendance": "9/9", "evaluation": "Đã đánh giá", "test_count": "0", "lesson_content": "Reading: Matching headings", "homework": "1"},
            ],
            "/dashboard/training": [
                {"class_name": "TA-NEN-TANG-01", "branch": "Trung tâm CenterOnline - Demo", "session_name": "03/11/2026 · 18:30 - 20:00", "teacher_name": "Trần Minh Anh", "attendance": "12/12", "evaluation": "Đã đánh giá", "test_count": "1", "lesson_content": "Thì hiện tại đơn", "homework": "1"},
                {"class_name": "IELTS-MUC-TIEU-02", "branch": "Trung tâm CenterOnline - Demo", "session_name": "07/11/2026 · 09:00 - 11:00", "teacher_name": "Lê Quốc Bảo", "attendance": "9/9", "evaluation": "Đã đánh giá", "test_count": "0", "lesson_content": "Reading: Matching headings", "homework": "1"},
            ],
            "/training/course": [
                {"code": "TA-NEN-TANG", "name": "Tiếng Anh nền tảng", "sessions_count": 40, "hours": 80, "fee_method": "Theo khóa", "fee": 7000000, "daily_evaluation": "Đánh giá hàng ngày", "subject": "Tiếng Anh", "status": "Hoạt động", "description": "Lộ trình giao tiếp và ngữ pháp nền tảng."},
                {"code": "IELTS-MUC-TIEU", "name": "IELTS mục tiêu 6.5", "sessions_count": 48, "hours": 96, "fee_method": "Theo khóa", "fee": 9800000, "daily_evaluation": "Đánh giá hàng ngày", "subject": "IELTS", "status": "Hoạt động", "description": "Luyện bốn kỹ năng theo mục tiêu đầu ra."},
                {"code": "TA-THIEU-NHI", "name": "Tiếng Anh thiếu nhi", "sessions_count": 36, "hours": 54, "fee_method": "Theo tháng", "fee": 3200000, "daily_evaluation": "Đánh giá hàng ngày", "subject": "Tiếng Anh trẻ em", "status": "Hoạt động", "description": "Học qua trò chơi, truyện ngắn và hoạt động nhóm."},
            ],
            "/training/class": [
                {"code": "TA-NEN-TANG-01", "course_name": "Tiếng Anh nền tảng", "student_count": 12, "start_date": "2026-11-03", "end_date": "2027-02-28", "schedule": "Thứ 3, Thứ 5 · 18:30 - 20:00", "manager": "Nguyễn Thu Hà", "teacher_name": "Trần Minh Anh", "status": "Đang học", "notes": "Lớp tối tại cơ sở Cầu Giấy."},
                {"code": "IELTS-MUC-TIEU-02", "course_name": "IELTS mục tiêu 6.5", "student_count": 9, "start_date": "2026-11-07", "end_date": "2027-03-20", "schedule": "Thứ 7 · 09:00 - 11:00", "manager": "Phạm Ngọc Linh", "teacher_name": "Lê Quốc Bảo", "status": "Chưa học", "notes": "Đã đủ giáo viên và phòng học."},
            ],
            "/training/timetable": [
                {"session_date": "2026-11-03", "start_time": "18:30", "end_time": "20:00", "room": "Phòng Cầu Giấy 01", "session_name": "Ca tối", "class_name": "TA-NEN-TANG-01", "course_name": "Tiếng Anh nền tảng", "teacher_name": "Trần Minh Anh", "status": "Đã lên lịch"},
            ],
            "/training/attendance": [
                {"student_name": "Nguyễn Minh Anh", "class_name": "TA-NEN-TANG-01", "session_date": "2026-11-03", "status": "Có mặt", "note": "Tham gia đầy đủ"},
            ],
            "/training/daily-evaluation-v2": [
                {"student_name": "Nguyễn Minh Anh", "class_name": "TA-NEN-TANG-01", "session_date": "2026-11-03", "score": 9, "note": "Chủ động phát biểu"},
            ],
            "/training/test": [
                {"name": "Bài kiểm tra đầu khóa", "class_name": "TA-NEN-TANG-01", "test_date": "2026-11-05", "max_score": 10, "status": "Đang học", "note": "Kiểm tra từ vựng và nghe hiểu."},
            ],
            "/training/homework": [
                {"title": "Ôn tập thì hiện tại đơn", "class_name": "TA-NEN-TANG-01", "due_date": "2026-11-06", "status": "Đang mở", "returned": "Chưa trả bài", "description": "Hoàn thành phiếu bài tập sau buổi học."},
            ],
            "/training/elearn/topic": [
                {"name": "Bộ đề nền tảng A1", "subject": "Tiếng Anh", "status": "Đang dùng"},
            ],
            "/training/elearn/exam_first_test": [
                {"name": "Bài test đầu vào A1", "subject": "Tiếng Anh", "status": "Đang dùng"},
            ],
            "/training/customer_test": [
                {"customer_name": "Nguyễn Minh Anh", "parent_name": "Trần Thu Hà", "test_date": "2026-11-08", "score": 7.5, "sale_owner": "Phạm Ngọc Linh", "note": "Đã gửi kết quả và tư vấn lộ trình."},
                {"customer_name": "Lê Hoàng Nam", "parent_name": "Lê Thị Hương", "test_date": "2026-11-10", "score": None, "sale_owner": "Nguyễn Hải Yến", "note": "Chờ lịch kiểm tra đầu vào."},
            ],
            "/training/class_enroll_trail_wait": [
                {"customer_name": "Võ Ngọc Mai", "parent_name": "Nguyễn Thị Lan", "sale_owner": "Phạm Ngọc Linh", "class_name": "TA-NEN-TANG-01", "schedule": "Buổi 1 · 03/11/2026 (18:30 - 20:00)", "status": "Chưa phê duyệt", "note": "Đang chờ xác nhận lịch học."},
            ],
            "/training/confirm": [
                {"full_name": "Nguyễn Minh Anh", "class_name": "TA-NEN-TANG-01", "sessions_count": 40, "schedule": "Thứ 3, Thứ 5 · 18:30 - 20:00", "enrolled_at": "2026-11-03", "contract_code": "HD-TA-0001", "status": "Đã duyệt", "performed_by": "Nguyễn Thu Hà"},
            ],
            "/training/pending_enrollment/index": [
                {"customer_name": "Phạm Gia Huy", "center_name": "Trung tâm CenterOnline - Demo", "session_name": "Thứ 2 · 18:30 - 20:00", "sessions_count": 40, "start_date": "2026-11-16", "course_name": "Tiếng Anh nền tảng", "note": "Ưu tiên lớp buổi tối.", "status": "Đang chờ", "created_by": "Nguyễn Thu Hà"},
            ],
        }
        for item_route in routes:
            contract = self.contract(item_route)
            if not contract.get("fields"):
                continue
            exists = self.db.execute("SELECT 1 FROM training_route_records WHERE route=? AND deleted_at IS NULL LIMIT 1", (item_route,)).fetchone()
            if exists:
                continue
            for row in samples.get(item_route, []):
                normalized = self._validate(contract, row)
                self.db.execute("INSERT INTO training_route_records(route,payload_json,created_by) VALUES(?,?,?)", (item_route, json.dumps(normalized, ensure_ascii=False, sort_keys=True), "Dữ liệu khởi tạo cục bộ"))
                seeded += 1
        self.db.commit()
        return seeded

    @staticmethod
    def _decode(payload: Any) -> Dict[str, Any]:
        try:
            value = json.loads(payload)
        except (TypeError, ValueError, json.JSONDecodeError):
            value = {}
        return value if isinstance(value, dict) else {}

    @classmethod
    def _record(cls, route: str, row: sqlite3.Row) -> Dict[str, Any]:
        """Return payload fields without clobbering a route field named created_by."""
        record = {"id": row["id"], "route": route, **cls._decode(row["payload_json"])}
        record.setdefault("created_by", row["created_by"])
        record["created_at"] = row["created_at"]
        record["updated_at"] = row["updated_at"]
        return record

    def _creator(self, route: str, record_id: int) -> str:
        row = self.db.execute(
            "SELECT created_by FROM training_route_records WHERE route=? AND id=?",
            (route, int(record_id)),
        ).fetchone()
        return str(row["created_by"] if row else "Quản trị viên trung tâm")

    @staticmethod
    def _filter_date(data: Mapping[str, Any], key: str) -> str:
        """Find the route's primary date for generic from/to filters."""
        if key in {"start_from", "start_to"}:
            candidates = ("start_date",)
        elif key in {"end_from", "end_to"}:
            candidates = ("end_date",)
        elif key in {"to_date", "date_to"}:
            candidates = ("to_date", "end_date", "test_date", "session_date", "start_date", "from_date")
        elif key in {"from_date", "date_from"}:
            candidates = ("from_date", "start_date", "session_date", "test_date", "created_at_value", "enrolled_at", "due_date", "end_date")
        else:
            candidates = (
                "date", "session_date", "test_date", "start_date", "from_date",
                "created_at_value", "enrolled_at", "due_date", "end_date",
            )
        for candidate in candidates:
            value = str(data.get(candidate) or "").strip()
            if value:
                return value[:10]
        return ""

    @staticmethod
    def _matches_filters(data: Mapping[str, Any], filters: Mapping[str, Any]) -> bool:
        for key, value in filters.items():
            if value in (None, "", "Tất cả", "Chọn trạng thái") or key in {"query", "page_size"}:
                continue
            actual = str(data.get(key, ""))
            if key.endswith("_from") or key in {"from_date", "date_from"}:
                target = TrainingRoutesStore._filter_date(data, key)
                boundary = _date(value, key, True) or ""
                if target and target < boundary:
                    return False
            elif key.endswith("_to") or key in {"to_date", "date_to"}:
                target = TrainingRoutesStore._filter_date(data, key)
                boundary = _date(value, key, True) or ""
                if target and target > boundary:
                    return False
            elif actual.casefold() != str(value).strip().casefold():
                return False
        return True

    @staticmethod
    def _display_value(key: str, row: Mapping[str, Any]) -> Any:
        if key == "sessions_hours":
            return "%s / %s" % (row.get("sessions_count", ""), row.get("hours", ""))
        if key == "fee_display":
            fee = row.get("fee")
            return "" if fee in (None, "") else "%s %s" % (row.get("fee_method", ""), "{:,.0f} VND".format(float(fee)))
        if key == "test_count":
            return row.get("test_count", "0 bài")
        return row.get(key, "")

    @classmethod
    def _validate(cls, contract: Mapping[str, Any], data: Mapping[str, Any]) -> Dict[str, Any]:
        fields = {str(item["name"]): item for item in contract.get("fields", []) if item.get("name")}
        unknown = sorted(set(data) - set(fields))
        if unknown:
            raise ValueError("Trường không được hỗ trợ: " + ", ".join(unknown))
        normalized: Dict[str, Any] = {}
        for name, spec in fields.items():
            value = data.get(name, "")
            if spec.get("required") and str(value).strip() == "":
                raise ValueError("%s là bắt buộc" % spec.get("label", name))
            if spec.get("kind") == "date":
                value = _date(value, str(spec.get("label", name)), bool(spec.get("required")))
            elif spec.get("kind") == "number":
                value = _number(value, str(spec.get("label", name)), bool(spec.get("required")))
            else:
                value = str(value or "").strip()
            options = spec.get("options") or []
            if options and value not in options and value != "":
                raise ValueError("%s không hợp lệ" % spec.get("label", name))
            if isinstance(value, str) and value.casefold() in {"unknown", "chưa cập nhật"}:
                raise ValueError("%s không được để ở trạng thái không xác định" % spec.get("label", name))
            if value not in (None, ""):
                normalized[name] = value
        return normalized


def route_manifest() -> List[Dict[str, Any]]:
    return [
        {"route": route, **{key: contract[key] for key in ("title", "resource", "columns", "filters", "actions")}}
        for route, contract in ROUTE_CONTRACTS.items()
    ]


def register(app_or_router: Any = None, service: Any = None) -> Dict[str, Any]:
    """Attach the lane store to the host's optional module registry.

    The host owns HTTP dispatch, authentication and CSRF.  Registration only
    ensures the persistent route table exists and exposes the store/manifest
    for the coordinator's adapter.  Natural rows remain opt-in; startup never
    mutates a user's database with demo data.
    """
    target = service if service is not None else app_or_router
    connection = getattr(target, "db", None)
    if connection is None:
        raise RuntimeError("training route module requires the host SQLite connection")
    store = getattr(target, "training_routes_store", None)
    if not isinstance(store, TrainingRoutesStore) or getattr(store, "db", None) is not connection:
        store = TrainingRoutesStore(connection)
        setattr(target, "training_routes_store", store)
    setattr(target, "training_route_manifest", route_manifest())
    setattr(target, "training_route_contracts", ROUTE_CONTRACTS)
    metadata: Dict[str, Any] = {
        "routes": list(ROUTE_CONTRACTS),
        "source": "modules.training_routes",
        "status": "PERSISTENT_SQLITE_CONTRACT",
        "schema": "training_route_records",
        "seed": "opt-in",
    }
    registrar = getattr(target, "register_module", None)
    if callable(registrar):
        return registrar("training_routes", metadata=metadata)
    return {"name": "training_routes", "registered": True, **metadata}


__all__ = [
    "READ_ROLES", "MANAGE_ROLES", "TEACHING_ROLES", "ROUTE_CONTRACTS", "SCHEMA",
    "CLASS_CREATE_ROUTE", "CLASS_CREATE_STEPS", "CLASS_CREATE_FIELDS", "CLASS_CREATE_CONTRACT",
    "class_workflow_payload", "TrainingRoutesStore", "route_manifest", "register",
]
