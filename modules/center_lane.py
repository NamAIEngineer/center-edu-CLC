"""W6 persistent contracts for Center, Setup, CSO, Callcenter and Tenant.

The shared HTTP shell currently renders unregistered reference routes through
its generic local screen store.  This module is the owned domain layer the
coordinator can wire into that shell without changing ``app.py``.  It keeps
the observed Vietnamese table/form vocabulary, durable SQLite records,
filters, soft-delete, CSV export and role checks together.
"""

from __future__ import annotations

import csv
import io
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable, Mapping

RBAC = {
    "ADMIN": frozenset({"read", "create", "update", "archive", "export"}),
    "STAFF": frozenset({"read", "create", "update", "export"}),
    "TEACHER": frozenset({"read"}),
    "STUDENT": frozenset(),
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS w6_route_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route TEXT NOT NULL,
    data_json TEXT NOT NULL DEFAULT '{}',
    created_by INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    version INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_w6_route_records_route ON w6_route_records(route, id);
"""


@dataclass(frozen=True)
class RouteContract:
    route: str
    title: str
    entity: str
    columns: tuple[tuple[str, str], ...]
    fields: tuple[Mapping[str, Any], ...] = ()
    filters: tuple[Mapping[str, Any], ...] = ()
    actions: tuple[str, ...] = ("read", "create", "update", "export")

    @property
    def column_keys(self) -> tuple[str, ...]:
        return tuple(key for key, _label in self.columns if key != "no")

    @property
    def labels(self) -> tuple[str, ...]:
        return tuple(label for _key, label in self.columns)


def _f(name: str, label: str, kind: str = "text", *, required: bool = False, options: tuple[str, ...] = ()) -> dict[str, Any]:
    value: dict[str, Any] = {"name": name, "label": label, "type": kind, "required": required}
    if options:
        value["options"] = options
    return value


_STATUS = ("Đang hoạt động", "Đang xử lý", "Đã hoàn thành", "Đã đóng")
_ROLES = ("Quản trị viên", "Nhân viên", "Giáo viên", "Nhân viên chăm sóc khách hàng")
_STAFF = ("Nguyễn Ngọc Mai", "Lê Hoàng Anh", "Trần Minh Tú")
_CLASSES = ("Lớp Tiếng Anh giao tiếp A1", "Lớp IELTS Foundation", "Lớp Thiếu nhi Starters")


CONTRACTS: dict[str, RouteContract] = {
    "/report/center/birth_day/config": RouteContract(
        "/report/center/birth_day/config", "Cấu hình lời chúc sinh nhật", "birthday_wish_config", (),
        (_f("days_before", "Gửi trước ngày sinh nhật", required=True, options=tuple(str(day) for day in range(31))),
         _f("time_sent", "Thời gian gửi", required=True, options=tuple(str(hour) for hour in range(24))),
         _f("content", "Nội dung lời chúc", "textarea")),
    ),
    "/center/student/index": RouteContract(
        "/center/student/index", "Danh sách học viên", "center_students",
        (("no", "No."), ("hoc_vien", "Học viên"), ("tai_khoan", "Tài khoản"), ("phu_huynh", "Phụ huynh"), ("sales_rep", "Sales rep"), ("lop_hoc", "Lớp học"), ("nguon_gioi_thieu", "Nguồn giới thiệu"), ("ghi_chu", "Ghi chú")),
        (_f("fullname", "Họ và tên", required=True), _f("student_name", "Học viên"), _f("parent_name", "Phụ huynh"), _f("class_name", "Lớp học"), _f("dob", "Ngày sinh", "date"), _f("nickname", "Tên tiếng Anh"), _f("gender", "Giới tính", options=("Nam", "Nữ")), _f("phone", "Số điện thoại"), _f("email", "Email"), _f("code", "Mã tài khoản", required=True), _f("username", "Tên đăng nhập", required=True), _f("identity_code", "Mã định danh"), _f("sale_name", "Nhân viên sale", options=_STAFF), _f("support_name", "Nhân viên hỗ trợ", options=_STAFF), _f("status", "Trạng thái", options=("Đang học", "Bảo lưu", "Đã xong", "Nghỉ học")), _f("note", "Ghi chú", "textarea"), _f("school", "Trường học")),
        ({"name": "q", "label": "Tìm kiếm..."}, {"name": "parent", "label": "Tìm phụ huynh"}, {"name": "status", "label": "Chọn trạng thái"}, {"name": "class_code", "label": "Chọn lớp học"}, {"name": "source", "label": "Nguồn giới thiệu"}, {"name": "school", "label": "Chọn trường học"}),
    ),
    "/center/teacher": RouteContract(
        "/center/teacher", "Danh sách giáo viên", "center_teachers",
        (("no", "No."), ("giao_vien", "Giáo viên"), ("tai_khoan", "Tài khoản"), ("lien_he", "Liên hệ"), ("quoc_tich", "Quốc tịch"), ("phan_quyen", "Phân quyền"), ("trang_thai", "Trạng thái")),
        (_f("fullname", "Họ và tên", required=True), _f("username", "Tên đăng nhập", required=True), _f("phone", "Số điện thoại"), _f("email", "Email"), _f("nationality", "Quốc tịch", options=("Việt Nam", "Hoa Kỳ", "Anh", "Úc")), _f("role", "Phân quyền", options=("Giáo viên", "Giáo viên chủ nhiệm")), _f("status", "Trạng thái", options=("Kích hoạt", "Đang khóa"))),
        ({"name": "q", "label": "Tìm kiếm"}, {"name": "nationality", "label": "Chọn quốc tịch"}, {"name": "status", "label": "Chọn trạng thái"}),
    ),
    "/center/parent/index": RouteContract(
        "/center/parent/index", "Danh sách phụ huynh", "center_parents",
        (("no", "No."), ("phu_huynh", "Phụ huynh"), ("tai_khoan", "Tài khoản"), ("hoc_vien", "Học viên"), ("lien_he", "Liên hệ"), ("trung_tam", "Trung tâm"), ("nguon_gioi_thieu", "Nguồn giới thiệu"), ("trang_thai", "Trạng thái"), ("hanh_ong", "Hành động")),
        (_f("fullname", "Họ và tên", required=True), _f("username", "Tên đăng nhập"), _f("phone", "Số điện thoại"), _f("email", "Email"), _f("student_name", "Học viên"), _f("relationship", "Quan hệ", options=("Phụ huynh", "Người giám hộ")), _f("source", "Nguồn giới thiệu"), _f("center", "Trung tâm"), _f("status", "Trạng thái", options=("Hoạt động", "Đang khóa")), _f("address", "Địa chỉ", "textarea")),
        ({"name": "q", "label": "Tìm kiếm..."}, {"name": "status", "label": "Chọn trạng thái"}, {"name": "source", "label": "Nguồn giới thiệu"}),
    ),
    "/center/staff": RouteContract(
        "/center/staff", "Danh sách nhân viên", "center_staff",
        (("no", "No."), ("nhan_vien", "Nhân viên"), ("tai_khoan", "Tài khoản"), ("lien_he", "Liên hệ"), ("phan_quyen", "Phân quyền"), ("trang_thai", "Trạng thái"), ("hanh_ong", "Hành động")),
        (_f("fullname", "Họ và tên", required=True), _f("username", "Tên đăng nhập", required=True), _f("phone", "Số điện thoại"), _f("email", "Email"), _f("roles", "Phân quyền", "select-multiple", options=_ROLES), _f("department", "Phòng ban", options=("Quản lý trung tâm", "Phòng chăm sóc khách hàng", "Tài chính")), _f("status", "Trạng thái", options=("Hoạt động", "Đang khóa"))),
        ({"name": "q", "label": "Tìm kiếm..."}, {"name": "status", "label": "Chọn trạng thái"}),
    ),
    "/setup/classroom": RouteContract(
        "/setup/classroom", "Phòng học", "setup_classrooms",
        (("no", "No."), ("ma_phong_hoc", "Mã phòng học"), ("ten_phong_hoc", "Tên phòng học"), ("so_ghe", "Số ghế"), ("mo_ta", "Mô tả"), ("trang_thai", "Trạng thái"), ("hanh_ong", "Hành động")),
        (_f("code", "Mã phòng học", required=True), _f("name", "Tên phòng học", required=True), _f("capacity", "Số ghế", "number"), _f("description", "Mô tả", "textarea"), _f("status", "Trạng thái", options=("Hoạt động", "Đã khóa"))),
        ({"name": "q", "label": "Tìm..."}, {"name": "status", "label": "Trạng thái"}),
    ),
    "/center/holiday/index": RouteContract(
        "/center/holiday/index", "Lịch nghỉ", "center_holidays",
        (("no", "No."), ("ten_lich_nghi", "Tên lịch nghỉ"), ("tu_ngay", "Từ ngày"), ("den_ngay", "Đến hết ngày"), ("mo_ta", "Mô tả"), ("thong_bao", "Thông báo"), ("trang_thai", "Trạng thái"), ("hanh_ong", "Hành động")),
        (_f("name", "Tên lịch nghỉ", required=True), _f("start_date", "Từ ngày", "date"), _f("end_date", "Đến hết ngày", "date"), _f("description", "Mô tả", "textarea"), _f("status", "Trạng thái", "radio", options=("Kích hoạt", "Đã khóa")), _f("select_class_ignore", "Lớp không áp dụng", "select-multiple", options=("Starters 1", "AA1", "Bimbon", "Lớp Kind1", "Lớp E1 9h-9h30", "TA trẻ em 2026", "milele test", "Lớp Test MS Team", "Test MS Team")), _f("is_send_noti", "Gửi thông báo", "checkbox"), _f("send_at", "Thời gian gửi", "datetime-local"), _f("content", "Nội dung", "textarea"), _f("notice", "Thông báo")),
        ({"name": "q", "label": "Tìm..."},),
    ),
    "/setup/daily-evaluation": RouteContract(
        "/setup/daily-evaluation", "Thiết lập đánh giá hàng ngày", "setup_daily_evaluations", (),
        (_f("name", "Tên bài đánh giá", required=True), _f("description", "Mô tả", "textarea"),
         _f("status", "Trạng thái", options=("Hoạt động", "Đã khóa")),
         _f("course_ids", "Khóa học", "select-multiple"),
         _f("criteria", "Tiêu chí", "json")),
    ),
    "/setup/criteria": RouteContract(
        "/setup/criteria", "Thiết lập tiêu chí test", "setup_criteria",
        (("stt", "STT"), ("ky_nang", "Kỹ năng"), ("hinh_thuc_anh_gia", "Hình thức đánh giá"), ("gia_tri", "Giá trị"), ("hanh_ong", "Hành động")),
        (_f("name", "Tên tiêu chí", required=True), _f("skill", "Kỹ năng", options=("Nghe", "Nói", "Đọc", "Viết")), _f("assessment_type", "Hình thức đánh giá", "radio", options=("Bằng số", "Bằng phần trăm", "Bằng ký tự", "Bằng văn bản")), _f("max_value", "Giá trị tối đa", "number"), _f("value", "Giá trị"), _f("character_values", "Thang ký tự (JSON)"), _f("note", "Ghi chú", "textarea"), _f("center", "Trung tâm", required=True), _f("status", "Trạng thái", options=("Hoạt động", "Đã khóa")), _f("show_in_total", "Hiển thị ở tổng", options=("Có", "Không"))),
    ),
    # Used as the durable source for the Bài test panel on /setup/criteria.
    # It intentionally has no navigation entry of its own.
    "/setup/test": RouteContract(
        "/setup/test", "Bài test", "setup_tests", (),
        (_f("name", "Tên bài test", required=True), _f("skills", "Kỹ năng", "select-multiple", required=True, options=("Nghe", "Nói", "Đọc", "Viết")), _f("course_ids", "Mã khóa học"), _f("center", "Trung tâm", required=True)),
    ),
    "/center/manager/index": RouteContract(
        "/center/manager/index", "Quản lý trung tâm", "center_managers", (),
        (_f("fullname", "Họ và tên", required=True), _f("center", "Trung tâm", required=True), _f("phone", "Số điện thoại"), _f("email", "Email"), _f("status", "Trạng thái", options=("Đang hoạt động", "Đang nghỉ"))),
    ),
    "/center/options": RouteContract(
        "/center/options", "Tùy chọn trung tâm", "center_options",
        (("no", "No."), ("ten_gia_tri", "Tên giá trị"), ("trung_tam_ap_dung", "Trung tâm áp dụng"), ("thoi_gian", "Thời gian"), ("cong_cu", "Công cụ")),
        (_f("name", "Nhập tên giá trị", required=True), _f("center", "Trung tâm áp dụng", required=True), _f("effective_date", "Thời gian", "date")),
        ({"name": "center", "label": "Trung tâm"},),
    ),
    "/center/tool/center/index": RouteContract(
        "/center/tool/center/index", "Công cụ trung tâm", "center_tools", (),
        (_f("class_url", "Nhập đường link của lớp", required=True), _f("cancelled_session_date", "Ngày buổi hủy", "date"), _f("new_start_date", "Ngày bắt đầu mới", "date"), _f("action", "Thao tác", options=("Khôi phục buổi hủy", "Đổi ngày bắt đầu"))),
        ({"name": "class_url", "label": "Nhập đường link của lớp"},),
    ),
    "/center/document-permission": RouteContract(
        "/center/document-permission", "Phân quyền tài liệu", "center_document_permissions", (),
        (_f("course", "Khóa học", required=True), _f("document", "Tài liệu", required=True), _f("role", "Vai trò", options=_ROLES), _f("enabled", "Được phép", options=("Có", "Không"))),
        ({"name": "course", "label": "Chọn khóa học"}, {"name": "q", "label": "Tìm kiếm ..."}),
    ),
    "/center/upload_address": RouteContract(
        "/center/upload_address", "Cập nhật địa chỉ học viên", "center_addresses",
        (("no", "No."), ("chi_nhanh", "Chi nhánh"), ("ma_hoc_vien", "Mã học viên"), ("hoc_vien", "Học viên"), ("ma_dinh_danh", "Mã định danh"), ("ten_tieng_anh", "Tên tiếng Anh"), ("gioi_tinh", "Giới tính"), ("ngay_sinh", "Ngày sinh"), ("tai_khoan", "Tài khoản"), ("so_dien_thoai", "Số điện thoại"), ("email", "Email"), ("tinh_cu", "Tỉnh cũ"), ("huyen_cu", "Huyện cũ"), ("xa_phuong", "Xã phường"), ("tinh_moi", "Tỉnh mới"), ("phuong_xa_moi", "Phường xã mới")),
        (_f("branch", "Chi nhánh", required=True), _f("student_code", "Mã học viên", required=True), _f("student_name", "Học viên", required=True), _f("identity_code", "Mã định danh"), _f("english_name", "Tên tiếng Anh"), _f("gender", "Giới tính", options=("Nam", "Nữ")), _f("dob", "Ngày sinh", "date"), _f("username", "Tài khoản"), _f("phone", "Số điện thoại"), _f("email", "Email"), _f("old_province", "Tỉnh cũ"), _f("old_district", "Huyện cũ"), _f("old_ward", "Xã phường"), _f("new_province", "Tỉnh mới"), _f("new_ward", "Phường xã mới")),
        ({"name": "page_size", "label": "Hiển thị 5 10 25 50 bản ghi"},),
    ),
    "/center/upload_address/index_customer": RouteContract(
        "/center/upload_address/index_customer", "Cập nhật địa chỉ khách hàng tiềm năng", "center_customer_addresses",
        (("no", "No."), ("branch", "Chi nhánh"), ("customer_name", "Họ tên khách hàng"),
         ("customer_dob", "Ngày sinh khách hàng"), ("customer_gender", "Giới tính khách hàng"),
         ("customer_code", "Mã khách hàng"), ("identity_code", "Mã định danh"), ("phone", "SĐT"),
         ("email", "Email"), ("old_province", "Tỉnh cũ"), ("old_district", "Huyện cũ"),
         ("old_ward", "Xã phường"), ("new_province", "Tỉnh mới"), ("new_ward", "Phường xã mới")),
        (_f("branch", "Chi nhánh", required=True), _f("customer_name", "Họ tên khách hàng", required=True),
         _f("customer_dob", "Ngày sinh khách hàng", "date"), _f("customer_gender", "Giới tính khách hàng", options=("Nam", "Nữ")),
         _f("customer_code", "Mã khách hàng", required=True), _f("identity_code", "Mã định danh"),
         _f("phone", "Số điện thoại"), _f("email", "Email"), _f("old_province", "Tỉnh cũ"),
         _f("old_district", "Huyện cũ"), _f("old_ward", "Xã phường"), _f("new_province", "Tỉnh mới"), _f("new_ward", "Phường xã mới")),
        ({"name": "page_size", "label": "Hiển thị 5 10 25 50 bản ghi"},),
    ),
    "/cso/support": RouteContract(
        "/cso/support", "Hỗ trợ", "cso_support",
        (("no", "No."), ("thoi_gian", "Thời gian"), ("loai", "Loại"), ("noi_dung", "Nội dung"), ("nguoi_gui", "Người gửi"), ("lop_cua_hoc_vien", "Lớp của học viên"), ("nhan_vien", "Nhân viên"), ("trang_thai", "Trạng thái")),
        (_f("sender", "Học viên / Phụ huynh"), _f("student_name", "Học viên"), _f("content", "Nội dung", "textarea", required=True), _f("staff_name", "Nhân viên", options=_STAFF), _f("type", "Loại", options=("Phản hồi/Hỗ trợ", "Khiếu nại")), _f("deadline", "Hạn xử lý", "date"), _f("status", "Trạng thái", options=("Mới tiếp nhận", "Đang xử lý", "Đã xử lý", "Đã đóng")), _f("note", "Ghi chú", "textarea")),
        ({"name": "status", "label": "Tất cả trạng thái"}, {"name": "type", "label": "Tất cả loại"}, {"name": "date_from", "label": "Từ ngày"}, {"name": "date_to", "label": "Đến ngày"}, {"name": "q", "label": "Tìm..."}),
    ),
    "/cso/customer-care": RouteContract(
        "/cso/customer-care", "Chăm sóc khách hàng", "cso_customer_care",
        # The reference table has seven data columns plus six trailing action
        # cells.  Keep those cells explicit so the renderer does not collapse
        # the row menu/edit/delete affordances into one generic column.
        (("no", "No."), ("hoc_vien", "Học viên"), ("lop", "Lớp"), ("nhan_vien", "Nhân viên"), ("lan_cham_soc", "Lần chăm sóc"), ("noi_dung", "Nội dung"), ("trang_thai", "Trạng thái"), ("action_1", ""), ("action_2", ""), ("action_3", ""), ("action_4", ""), ("action_5", ""), ("action_6", "")),
        (_f("student_name", "Học viên", required=True), _f("class_name", "Lớp", options=_CLASSES), _f("staff_name", "Nhân viên", options=_STAFF), _f("care_round", "Lần chăm sóc", options=("Lần 01", "Lần 02", "Lần 03", "Lần 04")), _f("content", "Nội dung", "textarea"), _f("action", "Hành động", options=("Gọi điện", "Nhắn tin", "Khảo sát")), _f("purpose", "Mục đích", options=("Khảo sát", "Bán thêm", "Xử lý góp ý/khiếu nại")), _f("result", "Kết quả", options=("Đồng ý", "Từ chối")), _f("care_date", "Ngày chăm sóc", "date"), _f("status", "Trạng thái", options=("Chưa xử lý", "Đang xử lý", "Đã xong", "Quá hạn")), _f("note", "Ghi chú", "textarea")),
        ({"name": "status", "label": "Tất cả", "options": ("Tất cả", "Chưa xử lý", "Đang xử lý", "Đã xong", "Quá hạn")}, {"name": "date_from", "label": "Từ ngày"}, {"name": "date_to", "label": "Đến ngày"}, {"name": "q", "label": "Tìm..."}, {"name": "class_name", "label": "Chọn lớp học", "options": _CLASSES}, {"name": "staff_name", "label": "Chọn nhân viên", "options": _STAFF}, {"name": "care_round", "label": "Chọn số lần chăm sóc", "options": tuple(f"Lần {i:02d}" for i in range(1, 11))}, {"name": "action", "label": "Chọn hành động", "type": "select-multiple", "multiple": True, "compact_input": True, "options": ("Gọi điện", "Nhắn tin", "Khảo sát")}, {"name": "result", "label": "Chọn kết quả", "type": "select-multiple", "multiple": True, "compact_input": True, "options": ("Đồng ý", "Từ chối")}, {"name": "purpose", "label": "Chọn mục đích", "type": "select-multiple", "multiple": True, "compact_input": True, "options": ("Khảo sát", "Bán thêm", "Xử lý góp ý/khiếu nại")}, {"name": "page_size", "label": "Hiển thị 5 10 25 50 bản ghi", "options": ("5", "10", "25", "50")}),
    ),
    "/callcenter/extension": RouteContract("/callcenter/extension", "Tổng đài", "callcenter_extensions", (), (_f("extension", "Số máy nhánh", required=True), _f("staff_name", "Nhân viên", options=_STAFF), _f("status", "Trạng thái", options=("Đang hoạt động", "Đã khóa")))),
    "/callcenter/staff": RouteContract(
        "/callcenter/staff", "Danh sách nhân viên trực", "callcenter_staff",
        (("staff_name", "Nhân viên"), ("total_calls", "Tổng cuộc gọi"), ("processed_calls", "Đã xử lý"), ("successful_calls", "Thành công"), ("failed_calls", "Thất bại")),
        (_f("staff_name", "Nhân viên", required=True, options=_STAFF), _f("extension", "Số máy nhánh", required=True), _f("active", "Đang trực", "checkbox"), _f("note", "Ghi chú", "textarea")),
        ({"name": "q", "label": "Tìm kiếm"},),
    ),
    "/callcenter/get-statistic": RouteContract(
        "/callcenter/get-statistic", "Thống kê cuộc gọi vào", "callcenter_statistics",
        (("no", "No."), ("staff_name", "Nhân viên nghe"), ("sale_group", "Nhóm sale"),
         ("center", "Trung tâm"), ("total_calls", "Tổng cuộc gọi"),
         ("answered_calls", "Cuộc gọi thành công"), ("missed_calls", "Cuộc gọi nhỡ"),
         ("failed_calls", "Thất bại")),
        (_f("from_date", "Từ ngày", "date", required=True), _f("to_date", "Đến ngày", "date", required=True), _f("total_calls", "Tổng số cuộc gọi", "number"), _f("answered_calls", "Cuộc gọi đã nghe", "number"), _f("missed_calls", "Cuộc gọi nhỡ", "number")),
        ({"name": "from_date", "label": "Từ ngày"}, {"name": "to_date", "label": "Đến ngày"}),
    ),
    "/callcenter/history": RouteContract(
        "/callcenter/history", "Lịch sử cuộc gọi", "callcenter_history",
        (("no", "No."), ("thoi_gian", "Thời gian"), ("nguoi_goi", "Người gọi"), ("doi_tuong", "Đối tượng"), ("nhan_vien", "Nhân viên"), ("ket_qua", "Kết quả")),
        (_f("called_at", "Thời gian", "date", required=True), _f("caller", "Người gọi", required=True), _f("party", "Đối tượng", options=("Học viên", "Phụ huynh", "Giáo viên", "Nhân viên", "Tiềm năng")), _f("staff_name", "Nhân viên", options=_STAFF), _f("result", "Kết quả", options=("Thất bại", "Gọi nhỡ", "Thành công")), _f("duration", "Thời lượng", "number"), _f("note", "Ghi chú", "textarea")),
        ({"name": "q", "label": "Tìm kiếm"}, {"name": "party", "label": "Đối tượng"}, {"name": "staff_name", "label": "Nhân viên"}, {"name": "result", "label": "Kết quả"}, {"name": "date_from", "label": "Từ ngày"}, {"name": "date_to", "label": "Đến ngày"}),
    ),
    "/tenant/config_excel": RouteContract(
        "/tenant/config_excel", "Cấu hình xuất Excel", "tenant_excel_config",
        (("no", "No."), ("bao_cao", "Báo cáo"), ("bat_excel", "Bật xuất Excel báo cáo"), ("tat_ca", "Tất cả")),
        (_f("report_name", "Tên báo cáo", required=True), _f("enabled", "Bật xuất Excel", "checkbox"), _f("center", "Trung tâm", options=("Trung tâm CenterOnline - Demo",))),
        ({"name": "enabled", "label": "Bật xuất Excel"},),
    ),
}


SEEDS: dict[str, dict[str, Any]] = {
    "/center/student/index": {"fullname": "Nguyễn Minh Anh", "code": "HV-1001", "username": "minhanh", "phone": "0903123456", "email": "minhanh@center.edu.vn", "student_name": "Nguyễn Minh Anh", "parent_name": "Nguyễn Thị Lan", "class_name": _CLASSES[0], "status": "Đang học", "school": "THCS Nguyễn Du", "note": "Theo dõi tiến độ phát âm."},
    "/center/teacher": {"fullname": "Lê Hoàng Anh", "username": "hoanganh", "phone": "0903987654", "email": "hoanganh@center.edu.vn", "nationality": "Việt Nam", "role": "Giáo viên chủ nhiệm", "status": "Kích hoạt"},
    "/center/parent/index": {"fullname": "Nguyễn Thị Lan", "username": "lan.nguyen", "phone": "0903555666", "email": "lan.nguyen@example.vn", "student_name": "Nguyễn Minh Anh", "relationship": "Phụ huynh", "source": "Giới thiệu", "status": "Hoạt động", "center": "Trung tâm CenterOnline - Demo"},
    "/center/staff": {"fullname": "Trần Minh Tú", "username": "minhtu", "phone": "0903777888", "email": "minhtu@center.edu.vn", "roles": ["Nhân viên", "Nhân viên chăm sóc khách hàng"], "department": "Phòng chăm sóc khách hàng", "status": "Hoạt động"},
    "/setup/classroom": {"code": "P-A201", "name": "Phòng học A201", "capacity": 24, "description": "Phòng có máy chiếu và bảng tương tác.", "status": "Hoạt động"},
    "/center/holiday/index": {"name": "Nghỉ lễ Quốc khánh", "start_date": "2026-09-01", "end_date": "2026-09-02", "description": "Nghỉ theo lịch trung tâm.", "notice": "Đã thông báo phụ huynh.", "status": "Kích hoạt"},
    "/setup/daily-evaluation": {
        "name": "Mức độ tham gia lớp học",
        "description": "Đánh giá thái độ và mức độ hoàn thành bài tập.",
        "status": "Hoạt động",
        "course_ids": [],
        "criteria": '[{"name":"Mức độ tham gia","assessment_type":"Nhập điểm","max_value":10,"status":"Hoạt động"}]',
    },
    # Natural fixture satisfies the required-field contract used by create/update.
    "/setup/criteria": {"name": "Đánh giá kỹ năng nghe", "skill": "Nghe", "assessment_type": "Bằng số", "max_value": 10, "value": "0 đến 10", "center": "Trung tâm CenterOnline - Demo", "note": "Chấm theo thang điểm 10.", "status": "Hoạt động"},
    "/center/manager/index": {"fullname": "Nguyễn Ngọc Mai", "center": "Trung tâm CenterOnline - Demo", "phone": "0903111222", "email": "mai.nguyen@center.edu.vn", "status": "Đang hoạt động"},
    "/center/options": {"name": "Số buổi học tiêu chuẩn", "center": "Trung tâm CenterOnline - Demo", "effective_date": "2026-11-01"},
    "/center/tool/center/index": {"class_url": "/training/class/ENG-FND-01", "cancelled_session_date": "2026-11-05", "new_start_date": "2026-11-12", "action": "Khôi phục buổi hủy"},
    "/center/document-permission": {"course": "IELTS Foundation", "document": "Tài liệu phát âm tuần 1", "role": "Giáo viên", "enabled": "Có"},
    "/center/upload_address": {"branch": "Cơ sở Cầu Giấy", "student_code": "HV-1001", "student_name": "Nguyễn Minh Anh", "identity_code": "ID-1001", "english_name": "Mia Nguyen", "gender": "Nữ", "dob": "2012-04-18", "username": "minhanh", "phone": "0903123456", "email": "minhanh@center.edu.vn", "old_province": "Hà Nội", "old_district": "Đống Đa", "old_ward": "Láng Hạ", "new_province": "Hà Nội", "new_ward": "Láng"},
    "/cso/support": {"sender": "Nguyễn Minh Anh", "student_name": "Nguyễn Minh Anh", "content": "Xin hỗ trợ đổi lịch học tuần này.", "staff_name": "Nguyễn Ngọc Mai", "type": "Phản hồi/Hỗ trợ", "deadline": "2026-11-05", "status": "Mới tiếp nhận", "note": "Đã ghi nhận yêu cầu."},
    "/cso/customer-care": {"student_name": "Nguyễn Minh Anh", "student_code": "HV-1001", "care_time": "16:13 06/04/2026", "class_name": _CLASSES[0], "staff_name": "Lê Hoàng Anh", "care_round": "Lần 01", "content": "Gọi hỏi thăm tiến độ học tập.", "action": "Gọi điện", "purpose": "Khảo sát", "result": "Đồng ý", "care_date": "2026-11-03", "status": "Đã xong", "note": "Phụ huynh phản hồi tích cực."},
    "/callcenter/extension": {"extension": "101", "staff_name": "Trần Minh Tú", "status": "Đang hoạt động"},
    "/callcenter/staff": {"staff_name": "Trần Minh Tú", "extension": "101", "active": "Có", "note": "Trực ca chiều."},
    "/callcenter/get-statistic": {"from_date": "2026-11-01", "to_date": "2026-11-07", "total_calls": 18, "answered_calls": 15, "missed_calls": 3},
    "/callcenter/history": {"called_at": "2026-11-03", "caller": "Nguyễn Thị Lan", "party": "Phụ huynh", "staff_name": "Trần Minh Tú", "result": "Thành công", "duration": 240, "note": "Đã xác nhận lịch học bù."},
    "/tenant/config_excel": {"report_name": "Báo cáo điểm danh theo lớp", "enabled": "Có", "center": "Trung tâm CenterOnline - Demo"},
}

# Presentation columns for CSO screens use the Vietnamese labels/keys exposed
# by the reference table, while the durable local contract keeps domain names
# (deadline/content/staff_name, etc.).  Keep this mapping explicit so export
# never silently emits blank cells for populated records.
EXPORT_KEY_ALIASES: dict[str, dict[str, str]] = {
    "/center/holiday/index": {
        "ten_lich_nghi": "name",
        "tu_ngay": "start_date",
        "den_ngay": "end_date",
        "mo_ta": "description",
        "thong_bao": "notice",
        "trang_thai": "status",
    },
    "/cso/support": {
        "thoi_gian": "deadline",
        "loai": "type",
        "noi_dung": "content",
        "nguoi_gui": "sender",
        "lop_cua_hoc_vien": "student_name",
        "nhan_vien": "staff_name",
        "trang_thai": "status",
    },
    "/cso/customer-care": {
        "hoc_vien": "student_name",
        "lop": "class_name",
        "nhan_vien": "staff_name",
        "lan_cham_soc": "care_round",
        "noi_dung": "content",
        "trang_thai": "status",
    },
}

# Route-only view metadata powers the observed dual tabs. These values are
# persisted with local demo records, never exposed as editable form fields.
VIEW_FIELDS: dict[str, tuple[str, frozenset[str]]] = {
    # Discriminator first, followed by projection-only values shown in each
    # tab's table. These are persisted route data, not editable form fields.
    "/callcenter/get-statistic": ("direction", frozenset({"staff_name", "sale_group", "center", "failed_calls"})),
    "/cso/support": ("scope", frozenset()),
    "/cso/customer-care": ("", frozenset({"student_code", "care_time", "deadline"})),
}

SEED_ROWS: dict[str, tuple[dict[str, Any], ...]] = {
    "/callcenter/get-statistic": (
        {**SEEDS["/callcenter/get-statistic"], "direction": "inbound", "staff_name": "Trần Minh Tú", "sale_group": "Nhóm sale 01", "center": "Trung tâm Cầu Giấy", "total_calls": 12, "answered_calls": 10, "missed_calls": 2, "failed_calls": 0},
        {**SEEDS["/callcenter/get-statistic"], "direction": "outbound", "staff_name": "Nguyễn Ngọc Mai", "sale_group": "Nhóm sale 01", "center": "Trung tâm Cầu Giấy", "total_calls": 8, "answered_calls": 7, "missed_calls": 1, "failed_calls": 0},
    ),
    "/cso/support": (
        {**SEEDS["/cso/support"], "scope": "external", "sender": "Nguyễn Minh Anh", "content": "Xin hỗ trợ đổi lịch học tuần này.", "status": "Mới tiếp nhận"},
        {**SEEDS["/cso/support"], "scope": "internal", "sender": "Trần Thu Hà", "content": "Đề nghị phối hợp cập nhật lịch lớp.", "status": "Đang xử lý"},
    ),
    "/center/parent/index": tuple({**SEEDS["/center/parent/index"], "fullname": name, "username": user, "student_name": student, "phone": phone} for name, user, student, phone in (
        ("Nguyễn Thị Lan", "lan.nguyen", "Nguyễn Minh Anh", "0903555666"), ("Trần Thu Hà", "ha.tran", "Trần Hoàng Nam", "0903555667"), ("Lê Thị Hương", "huong.le", "Lê Khánh Linh", "0903555668"), ("Phạm Văn Minh", "minh.pham", "Phạm Gia Huy", "0903555669"), ("Võ Ngọc Mai", "mai.vo", "Võ Ngọc Mai", "0903555670"), ("Đặng Thu Trang", "trang.dang", "Đặng Nhật Minh", "0903555671"), ("Bùi Thanh Tâm", "tam.bui", "Bùi Thu Hà", "0903555672"), ("Phan Đức Long", "long.phan", "Phan Đức Anh", "0903555673"), ("Hoàng Yến Nhi", "nhi.hoang", "Hoàng Yến Nhi", "0903555674"), ("Đỗ Quang Huy", "huy.do", "Đỗ Quang Huy", "0903555675"),
    )),
    "/center/staff": tuple({**SEEDS["/center/staff"], "fullname": name, "username": user} for name, user in (
        ("Trần Minh Tú", "minhtu"), ("Nguyễn Ngọc Mai", "mai.nguyen"), ("Lê Hoàng Anh", "hoanganh"), ("Phạm Quốc Bảo", "bao.pham"), ("Vũ Thanh Hà", "ha.vu"), ("Đặng Minh Quân", "quan.dang"), ("Bùi Khánh Linh", "linh.bui"), ("Phan Anh Dũng", "dung.phan"), ("Hoàng Thu Uyên", "uyen.hoang"),
    )),
    "/center/holiday/index": tuple({**SEEDS["/center/holiday/index"], "name": name, "start_date": start, "end_date": end} for name, start, end in (
        ("Nghỉ lễ Quốc khánh", "2026-09-01", "2026-09-02"), ("Nghỉ Tết Dương lịch", "2027-01-01", "2027-01-01"), ("Nghỉ Tết Nguyên đán", "2027-02-06", "2027-02-12"), ("Nghỉ Giỗ Tổ Hùng Vương", "2027-04-16", "2027-04-16"), ("Nghỉ lễ 30 tháng 4", "2027-04-30", "2027-05-01"),
    )),
}


def can(role: str, action: str) -> bool:
    return action in RBAC.get(str(role or "").upper(), frozenset())


def require(role: str, action: str) -> None:
    if not can(role, action):
        raise PermissionError(f"role {role or 'unknown'} cannot {action} route records")


def route_contract(route: str) -> RouteContract:
    try:
        return CONTRACTS[route]
    except KeyError as exc:
        raise KeyError(f"W6 route contract not found: {route}") from exc


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(w6_route_records)").fetchall()}
    if "version" not in columns:
        conn.execute("ALTER TABLE w6_route_records ADD COLUMN version INTEGER NOT NULL DEFAULT 1")
    conn.commit()


def _normalize_value(key: str, value: Any, *, date_field: bool = False, number_field: bool = False) -> Any:
    if value is None:
        return ""
    if isinstance(value, list):
        return [_normalize_value(key, item, date_field=date_field, number_field=number_field) for item in value]
    if number_field and value != "":
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{key} phải là số") from exc
        return int(number) if number.is_integer() else number
    text = str(value).strip() if not isinstance(value, (int, float, bool)) else value
    if isinstance(text, str) and (date_field or "date" in key or key.endswith("_at")):
        if "T" in text:
            try:
                datetime.fromisoformat(text)
                return text
            except ValueError as exc:
                raise ValueError(f"{key} phải theo định dạng ngày giờ hợp lệ") from exc
        if len(text) == 10 and text[2] == "/" and text[5] == "/":
            try:
                return date(int(text[6:]), int(text[3:5]), int(text[:2])).isoformat()
            except ValueError as exc:
                raise ValueError(f"{key} phải theo định dạng dd/mm/yyyy") from exc
        if text:
            try:
                date.fromisoformat(text)
            except ValueError as exc:
                raise ValueError(f"{key} phải theo định dạng dd/mm/yyyy") from exc
    return text


def validate_data(contract: RouteContract, data: Mapping[str, Any], *, current: Mapping[str, Any] | None = None) -> dict[str, Any]:
    current = current or {}
    merged = dict(current)
    merged.update(data)
    view_fields = VIEW_FIELDS.get(contract.route, ("", frozenset()))
    allowed = {str(field["name"]) for field in contract.fields} | set(view_fields[1]) | ({view_fields[0]} if view_fields[0] else set())
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ValueError("Trường không hợp lệ: " + ", ".join(unknown))
    for field in contract.fields:
        key = str(field["name"])
        field_type = str(field.get("type", "")).lower()
        raw_value = merged.get(key, "")
        if field_type == "json":
            if raw_value in (None, ""):
                value = ""
            else:
                try:
                    parsed = json.loads(raw_value) if isinstance(raw_value, str) else raw_value
                except (TypeError, ValueError, json.JSONDecodeError) as exc:
                    raise ValueError(f"{field['label']} phải là JSON hợp lệ") from exc
                if not isinstance(parsed, list):
                    raise ValueError(f"{field['label']} phải là danh sách")
                for item in parsed:
                    if not isinstance(item, dict) or not str(item.get("name", "")).strip():
                        raise ValueError(f"{field['label']} chứa tiêu chí không hợp lệ")
                value = json.dumps(parsed, ensure_ascii=False, sort_keys=True)
        else:
            value = _normalize_value(
                key,
                raw_value,
                date_field=field_type in {"date", "datetime", "date-text"},
                number_field=field_type in {"number", "integer"},
            )
        merged[key] = value
        if field.get("required") and (value is None or str(value).strip() == ""):
            raise ValueError(f"{field['label']} là bắt buộc")
        options = field.get("options") or ()
        if options and value not in (None, ""):
            if isinstance(value, list):
                invalid = [item for item in value if item not in options]
                if invalid:
                    raise ValueError(f"{field['label']} chứa lựa chọn không hợp lệ")
            elif value not in options:
                raise ValueError(f"{field['label']} chứa lựa chọn không hợp lệ")
    present = set(data) | set(current)
    # New holiday controls are optional. Preserve legacy rows/payloads without
    # manufacturing empty notification fields, while retaining supplied values.
    if contract.route == "/center/holiday/index":
        return {key: merged[key] for key in allowed if key in merged and key in present}
    return {key: merged[key] for key in allowed if key in merged}


def _record(row: sqlite3.Row) -> dict[str, Any]:
    try:
        data = json.loads(row["data_json"] or "{}")
    except (TypeError, ValueError, json.JSONDecodeError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    if row["route"] == "/setup/daily-evaluation":
        # Keep the human-facing fields first in the mapping.  Stored JSON is
        # sorted for deterministic persistence, which otherwise puts the
        # criteria blob before the title and makes the generic text filter
        # search an escaped JSON fragment instead of the visible name.
        ordered = {key: data[key] for key in ("name", "description", "status", "course_ids", "criteria") if key in data}
        ordered.update({key: value for key, value in data.items() if key not in ordered})
        data = ordered
        criteria = data.get("criteria", "")
        if isinstance(criteria, str):
            try:
                criteria = json.loads(criteria)
            except (TypeError, ValueError, json.JSONDecodeError):
                criteria = []
        if not isinstance(criteria, list):
            criteria = []
        data["criteria_count"] = len(criteria)
        courses = data.get("course_ids", [])
        if isinstance(courses, str):
            try:
                courses = json.loads(courses)
            except (TypeError, ValueError, json.JSONDecodeError):
                courses = [item for item in courses.split(",") if item.strip()]
        data["course_count"] = len(courses) if isinstance(courses, list) else 0
    return {"id": row["id"], "route": row["route"], "data": data, "created_at": row["created_at"], "updated_at": row["updated_at"], "version": row["version"] if "version" in row.keys() else 1}


def _date_fields(contract: RouteContract) -> tuple[str, ...]:
    """Return observed date fields in declaration order for range filtering."""
    return tuple(
        str(field["name"])
        for field in contract.fields
        if str(field.get("type", "")).lower() in {"date", "datetime", "date-text"}
        or "date" in str(field.get("name", ""))
        or str(field.get("name", "")).endswith("_at")
    )


def _seed_view_rows(conn: sqlite3.Connection, route: str, contract: RouteContract, *, created_by: int) -> int:
    """Add only missing route-view demo fixtures; never rewrite local records."""
    view_fields = VIEW_FIELDS.get(route)
    discriminator = view_fields[0] if view_fields else None
    if not discriminator:
        return 0
    rows = SEED_ROWS.get(route, ())
    existing = conn.execute("SELECT data_json FROM w6_route_records WHERE route=? AND deleted_at IS NULL", (route,)).fetchall()
    present = set()
    for row in existing:
        try:
            present.add(str(json.loads(row["data_json"] or "{}").get(discriminator, "")))
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
    added = 0
    for item in rows:
        key = str(item.get(discriminator, ""))
        if not key or key in present:
            continue
        clean = validate_data(contract, item)
        conn.execute("INSERT INTO w6_route_records(route,data_json,created_by) VALUES(?,?,?)", (route, json.dumps(clean, ensure_ascii=False, sort_keys=True), created_by))
        present.add(key)
        added += 1
    if added:
        conn.commit()
    return added


def seed(conn: sqlite3.Connection, route: str, *, created_by: int = 1) -> int:
    contract = route_contract(route)
    rich_demo = os.environ.get("CENTER_EDU_RICH_DEMO", "").strip().lower() in {"1", "true", "yes", "on"}
    if conn.execute("SELECT 1 FROM w6_route_records WHERE route=? AND deleted_at IS NULL LIMIT 1", (route,)).fetchone():
        if rich_demo and route in VIEW_FIELDS:
            return int(_seed_view_rows(conn, route, contract, created_by=created_by) > 0)
        return 0
    data = dict(SEEDS.get(route, {}))
    rows = () if route in VIEW_FIELDS and not rich_demo else SEED_ROWS.get(route, ())
    if rows:
        for item in rows:
            clean = validate_data(contract, item)
            conn.execute("INSERT INTO w6_route_records(route,data_json,created_by) VALUES(?,?,?)", (route, json.dumps(clean, ensure_ascii=False, sort_keys=True), created_by))
        conn.commit()
        # ``seed`` reports a successful route seed, not the number of fixture
        # rows.  Rich-demo routes may intentionally contain several natural
        # rows while the contract/test API remains a stable 0/1 idempotency
        # signal (1 = inserted, 0 = already present).
        return 1
    if not data:
        # A missing natural fixture must never become a fabricated customer row.
        # Keep route setup fail-closed so callers add an explicit Vietnamese seed
        # before exposing the route in a local runtime.
        raise ValueError(f"Chưa có dữ liệu khởi tạo tự nhiên cho tuyến {contract.route}")
    data = validate_data(contract, data)
    conn.execute("INSERT INTO w6_route_records(route,data_json,created_by) VALUES(?,?,?)", (route, json.dumps(data, ensure_ascii=False, sort_keys=True), created_by))
    conn.commit()
    return 1


def _staff_call_counts(conn: sqlite3.Connection) -> dict[str, dict[str, int]] | None:
    """Project the call ledger's explicit staff-name relation, not fixture totals."""
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='call_history'").fetchone():
        return None
    counts: dict[str, dict[str, int]] = {}
    for name, total, successful, failed in conn.execute("""
        SELECT staff_name, COUNT(*),
               SUM(CASE WHEN status IN ('CONNECTED', 'Thành công') THEN 1 ELSE 0 END),
               SUM(CASE WHEN status IN ('FAILED', 'Thất bại') THEN 1 ELSE 0 END)
        FROM call_history GROUP BY staff_name
    """).fetchall():
        counts[str(name)] = {"total_calls": total, "processed_calls": successful + failed,
                             "successful_calls": successful, "failed_calls": failed}
    return counts


def list_records(conn: sqlite3.Connection, route: str, filters: Mapping[str, Any] | None = None, *, role: str = "ADMIN") -> list[dict[str, Any]]:
    require(role, "read")
    contract = route_contract(route)
    filters = filters or {}
    rows = conn.execute("SELECT * FROM w6_route_records WHERE route=? AND deleted_at IS NULL ORDER BY id", (route,)).fetchall()
    query = str(filters.get("q", "")).strip().casefold()
    date_key = _date_fields(contract)[0] if _date_fields(contract) else ""
    date_from = _normalize_value(date_key, filters["date_from"]) if date_key and str(filters.get("date_from", "")).strip() else ""
    date_to = _normalize_value(date_key, filters["date_to"]) if date_key and str(filters.get("date_to", "")).strip() else ""
    if date_from and date_to and date_from > date_to:
        raise ValueError("Khoảng ngày lọc không hợp lệ")
    staff_counts = _staff_call_counts(conn) if route == "/callcenter/staff" else None
    output: list[dict[str, Any]] = []
    for row in rows:
        item = _record(row)
        if route == "/callcenter/staff" and staff_counts is not None:
            item["data"].update(staff_counts.get(str(item["data"].get("staff_name", "")), {
                "total_calls": 0, "processed_calls": 0, "successful_calls": 0, "failed_calls": 0,
            }))
        if date_key and (date_from or date_to):
            record_date = str(item["data"].get(date_key, ""))
            if date_from and (not record_date or record_date < date_from):
                continue
            if date_to and (not record_date or record_date > date_to):
                continue
        encoded = json.dumps(item["data"], ensure_ascii=False).casefold()
        if query and query not in encoded:
            continue
        for key, value in filters.items():
            if key in {"q", "page_size", "date_from", "date_to"} or not str(value).strip():
                continue
            raw_values = value if isinstance(value, (list, tuple, set)) else [value]
            expected_values = [str(item).strip().casefold() for item in raw_values if str(item).strip()]
            # UI sentinel options are presentation controls, not predicates.
            expected_values = [item for item in expected_values if item not in {"tất cả", "chọn lớp học", "chọn nhân viên", "chọn số lần chăm sóc", "chọn hành động", "chọn kết quả", "chọn mục đích", "all"}]
            if not expected_values:
                continue
            search_key = key[:-6] if key.endswith("_search") else key
            actual = item["data"].get(search_key if key.endswith("_search") else key)
            if isinstance(actual, list):
                matches = any(
                    (any(str(entry).casefold() == expected for expected in expected_values)
                     if not key.endswith("_search")
                     else any(expected in str(entry).casefold() for expected in expected_values))
                    for entry in actual
                )
            elif actual is not None:
                actual_text = str(actual).casefold()
                matches = any(
                    (expected in actual_text if key.endswith("_search") else actual_text == expected)
                    for expected in expected_values
                )
            else:
                matches = any(expected in encoded for expected in expected_values)
            if not matches:
                break
        else:
            output.append(item)
    page_size = filters.get("page_size")
    if page_size:
        try:
            output = output[: max(1, min(int(page_size), 100))]
        except (TypeError, ValueError):
            raise ValueError("Số bản ghi phải là số nguyên")
    return output


def create_record(conn: sqlite3.Connection, route: str, data: Mapping[str, Any], *, created_by: int = 1, role: str = "ADMIN") -> dict[str, Any]:
    require(role, "create")
    contract = route_contract(route)
    clean = validate_data(contract, data)
    cur = conn.execute("INSERT INTO w6_route_records(route,data_json,created_by) VALUES(?,?,?)", (route, json.dumps(clean, ensure_ascii=False, sort_keys=True), created_by))
    conn.commit()
    return _record(conn.execute("SELECT * FROM w6_route_records WHERE id=?", (cur.lastrowid,)).fetchone())


def update_record(
    conn: sqlite3.Connection,
    route: str,
    record_id: int,
    data: Mapping[str, Any],
    *,
    role: str = "ADMIN",
    expected_version: Any = None,
    expected_updated_at: Any = None,
    full_body: bool = False,
) -> dict[str, Any]:
    require(role, "update")
    contract = route_contract(route)
    row = conn.execute("SELECT * FROM w6_route_records WHERE id=? AND route=? AND deleted_at IS NULL", (int(record_id), route)).fetchone()
    if row is None:
        raise KeyError("Không tìm thấy bản ghi")
    version = row["version"] if "version" in row.keys() else 1
    if expected_version is None and expected_updated_at is None and full_body:
        raise ValueError("Bản ghi đầy đủ phải gửi version hoặc updated_at")
    if expected_version is not None and str(expected_version) != str(version):
        raise RuntimeError("CONFLICT")
    if expected_updated_at is not None and str(expected_updated_at) != str(row["updated_at"]):
        raise RuntimeError("CONFLICT")
    current = _record(row)["data"]
    clean = validate_data(contract, data, current=current)
    params: list[Any] = [json.dumps(clean, ensure_ascii=False, sort_keys=True), int(record_id)]
    predicate = "id=?"
    if expected_version is not None:
        predicate += " AND version=?"; params.append(expected_version)
    elif expected_updated_at is not None:
        predicate += " AND updated_at=?"; params.append(expected_updated_at)
    cursor = conn.execute("UPDATE w6_route_records SET data_json=?,version=version+1,updated_at=CURRENT_TIMESTAMP WHERE " + predicate, params)
    if (expected_version is not None or expected_updated_at is not None) and cursor.rowcount != 1:
        raise RuntimeError("CONFLICT")
    conn.commit()
    return _record(conn.execute("SELECT * FROM w6_route_records WHERE id=?", (int(record_id),)).fetchone())


def archive_record(
    conn: sqlite3.Connection,
    route: str,
    record_id: int,
    *,
    role: str = "ADMIN",
    expected_version: Any = None,
    expected_updated_at: Any = None,
) -> dict[str, Any]:
    require(role, "archive")
    route_contract(route)
    row = conn.execute("SELECT * FROM w6_route_records WHERE id=? AND route=? AND deleted_at IS NULL", (int(record_id), route)).fetchone()
    if row is None:
        raise KeyError("Không tìm thấy bản ghi")
    if expected_version is None and expected_updated_at is None:
        raise RuntimeError("CONCURRENCY_TOKEN_REQUIRED")
    if expected_version is not None and str(expected_version) != str(row["version"]):
        raise RuntimeError("CONFLICT")
    if expected_updated_at is not None and str(expected_updated_at) != str(row["updated_at"]):
        raise RuntimeError("CONFLICT")
    params: list[Any] = [int(record_id), route]
    predicate = "id=? AND route=? AND deleted_at IS NULL"
    if expected_version is not None:
        predicate += " AND version=?"; params.append(expected_version)
    elif expected_updated_at is not None:
        predicate += " AND updated_at=?"; params.append(expected_updated_at)
    cursor = conn.execute("UPDATE w6_route_records SET deleted_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP WHERE " + predicate, params)
    if cursor.rowcount != 1:
        conn.rollback()
        raise KeyError("Không tìm thấy bản ghi")
    conn.commit()
    return {"id": int(record_id), "route": route, "deleted": True}


def export_csv(conn: sqlite3.Connection, route: str, filters: Mapping[str, Any] | None = None, *, role: str = "ADMIN") -> str:
    require(role, "export")
    contract = route_contract(route)
    rows = list_records(conn, route, filters, role=role)
    output = io.StringIO(newline="")
    labels = list(contract.labels)
    if not labels:
        labels = [str(field["label"]) for field in contract.fields]
    writer = csv.writer(output)
    writer.writerow(labels)
    aliases = EXPORT_KEY_ALIASES.get(contract.route, {})
    for index, row in enumerate(rows, 1):
        data = row["data"]
        if contract.columns:
            writer.writerow([index if key == "no" else data.get(aliases.get(key, key), "") for key, _label in contract.columns])
        else:
            writer.writerow([data.get(str(field["name"]), "") for field in contract.fields])
    return "\ufeff" + output.getvalue()


def manifest() -> list[dict[str, Any]]:
    return [
        {"route": contract.route, "title": contract.title, "entity": contract.entity, "columns": contract.columns, "filters": contract.filters, "fields": contract.fields, "actions": contract.actions}
        for contract in CONTRACTS.values()
    ]


def register(app_or_router: Any = None, service: Any = None) -> dict[str, Any]:
    """Register the W6 Center/Setup/CSO/Callcenter/Tenant contract.

    The application autoloader passes the service as both arguments.  Keep
    this hook deliberately small and idempotent: schema setup is additive and
    route dispatch remains owned by the existing generated-screen transport.
    Returning metadata lets the host expose an observable registry entry
    without coupling this module to ``app.py`` internals.
    """
    target = service or app_or_router
    conn = getattr(target, "db", None)
    if conn is not None:
        ensure_schema(conn)
    return {
        "routes": tuple(CONTRACTS),
        "source": "modules.center_lane",
        "status": "PERSISTENT_LOCAL_CONTRACT",
        "schema": "w6_route_records",
        "seed": "explicit Vietnamese seeds only",
    }


__all__ = ["RBAC", "SCHEMA", "RouteContract", "CONTRACTS", "SEEDS", "can", "require", "route_contract", "ensure_schema", "validate_data", "seed", "list_records", "create_record", "update_record", "archive_record", "export_csv", "manifest", "register"]
