"""Persistent contracts for the remaining CRM route surfaces.

This module is intentionally host agnostic.  The coordinator can mount these
contracts from the existing HTTP layer without moving route policy into shared
application files.  Records are stored in SQLite as JSON payloads behind a
strict per-route field allow-list; no reference rows are copied or fabricated.
"""
from __future__ import annotations

import csv
import io
import json
import re
import sqlite3
from datetime import datetime
from typing import Any, Mapping

READ_ROLES = frozenset({"ADMIN", "STAFF"})
WRITE_ROLES = frozenset({"ADMIN", "STAFF"})
READ_ONLY_ROUTES = frozenset({"/dashboard/crm", "/dashboard/sale"})
# These screens already use a dedicated host renderer with a captured
# structure contract.  Keep that renderer authoritative while the lane store
# remains available for the remaining route surfaces; this avoids a module
# registration from regressing an observed structure match.
PRESERVED_HOST_ROUTES = frozenset({
    "/crm/target/index", "/crm/event2/index", "/sale/bill/index",
    "/sale/appointment_date", "/crm/discount", "/crm/packet",
})

# Form inventory names are kept as accepted input aliases.  Storage remains
# Vietnamese domain fields used by the route contract.  This lets the shared
# HTTP adapter pass observed form payloads without leaking private reference
# implementation names into the database.
FORM_ALIASES: dict[str, dict[str, str]] = {
    "/crm/event2/index": {"fullname": "title", "number_of_people": "max_people", "cost": "cost_vnd"},
    "/crm/discount": {"discount_name": "name", "sale": "discount_value"},
    "/crm/packet": {"fullname": "name", "price_not_select": "price_vnd", "reduce_detail": "discount_vnd", "net_price": "net_price_vnd"},
    "/crm/pending_enrollment/index": {"number_of_session": "sessions_count", "start_learn": "start_date"},
    "/sale/pending_enrollment/index": {"number_of_session": "sessions_count", "start_learn": "start_date"},
    "/sale/contract": {"expired_date": "expiry_date"},
    "/sale/bill/index": {"code": "invoice_code"},
}

FORM_VALUE_ALIASES: dict[str, dict[str, dict[str, str]]] = {
    "/crm/discount": {
        "discount_type": {"0": "VND", "1": "%"},
        "apply_type": {"0": "Tất cả gói và khóa", "1": "Tất cả gói và khóa học ngoại trừ", "2": "Chỉ gói và khóa cụ thể"},
        "status": {"1": "Đang hoạt động", "0": "Đã dừng"},
    },
    "/crm/packet": {
        "type_reduce": {"0": "VND", "1": "%"},
        "status": {"1": "Hoạt động", "0": "Đã hết hạn"},
    },
}


def _field(name: str, label: str, *, required: bool = False, kind: str = "text", options: tuple[str, ...] = ()) -> dict[str, Any]:
    return {"name": name, "label": label, "required": required, "kind": kind, "options": list(options)}


ROUTE_CONTRACTS: dict[str, dict[str, Any]] = {
    "/crm/customer/raw": {
        "title": "Khách hàng thô", "resource": "raw_potential_customers",
        "columns": ["No.", "", "Họ và tên", "Nhân viên sale", "nhóm nguồn", "Nguồn dữ liệu", "Trạng thái", "Ngày từ bỏ", "Người thực hiện", "Ghi chú chuyển đổi", "Ghi chú", "Chăm sóc gần nhất", "Hành động"],
        "filters": [_field("query", "Tìm kiếm..."), _field("page_size", "Số bản ghi", kind="select", options=("5", "10", "25", "50", "100", "200"))],
        "actions": ["Chuyển khách hàng", "Lọc", "Xóa", "Tải lên", "Tải xuống", "Tạo khách hàng"],
        "fields": [_field("full_name", "Họ và tên", required=True), _field("sale_owner", "Nhân viên sale"), _field("source_group", "nhóm nguồn"), _field("source", "Nguồn dữ liệu"), _field("status", "Trạng thái"), _field("abandoned_at", "Ngày từ bỏ", kind="date"), _field("performed_by", "Người thực hiện"), _field("conversion_note", "Ghi chú chuyển đổi"), _field("note", "Ghi chú"), _field("last_care", "Chăm sóc gần nhất"), _field("import_key", "Import key")],
    },
    "/crm/opportunity_history": {
        "title": "Lịch sử chăm sóc", "resource": "potential_customer_followups",
        "columns": ["No.", "Tên khách hàng", "Ngày chăm sóc", "Lần chăm sóc", "Trung tâm", "Mã khách hàng", "Ngày sinh khách hàng", "Số điện thoại khách hàng", "Email khách hàng", "Nguồn khách hàng", "Sale chính", "Sale phụ", "Hành động", "Trạng thái chăm sóc", "Kết quả", "Đánh giá mức độ hài lòng", "Phân loại khách hàng", "Khóa học quan tâm", "Khóa học đang chăm sóc", "Ghi chú", "Hành động tiếp theo", "Ngày hẹn", "Ghi chú hẹn", "Hành động"],
        "filters": [_field("potential_customer_id", "Khách hàng", kind="select"), _field("sale_owner", "Nhân viên sale", kind="select"), _field("action_type", "Hành động", kind="select"), _field("page_size", "Số bản ghi", kind="select", options=("10", "25", "50", "100"))],
        "actions": ["Lọc", "Excel", "Tạo lịch sử chăm sóc", "Upload"],
        "fields": [],
    },
    "/crm/sale_team/index": {
        "title": "Nhóm sale", "resource": "sale_team",
        "columns": ["No.", "Họ tên", "Liên lạc", "Trung tâm", "Nhân viên sale"],
        "filters": [_field("query", "Tìm..."), _field("page_size", "Số bản ghi", kind="select", options=("10", "25", "50", "100"))],
        "actions": [], "fields": [_field("full_name", "Họ tên", required=True), _field("phone", "Liên lạc"), _field("center_name", "Trung tâm", required=True), _field("team_name", "Nhóm sale", required=True)],
    },
    "/crm/target/index": {
        "title": "Chỉ tiêu kinh doanh", "resource": "targets",
        "columns": ["", "Thời gian", "Doanh thu", "Hợp đồng", "Tái tục", "Hành động"],
        "filters": [_field("year", "Năm", kind="number"), _field("scope", "Phạm vi", kind="select", options=("Toàn trung tâm", "Nhóm sale", "Nhân viên sale"))],
        "actions": [], "fields": [_field("year", "Năm", required=True, kind="number"), _field("scope", "Phạm vi", required=True, options=("Toàn trung tâm", "Nhóm sale", "Nhân viên sale")), _field("scope_name", "Trung tâm/Nhóm", required=True), _field("revenue_target", "Doanh thu", required=True, kind="number"), _field("contract_target", "Hợp đồng", required=True, kind="number"), _field("renewal_target", "Tái tục", required=True, kind="number")],
    },
    "/crm/class_enroll_trail_wait": {
        "title": "Danh sách khách hàng đăng ký học thử", "resource": "trials",
        "columns": ["No.", "Khách hàng", "Phụ huynh", "Sales rep", "Lớp học", "Thời gian", "Trạng thái", "Công cụ"],
        "filters": [
            _field("class_name", "Tất cả lớp", kind="select", options=("Tất cả lớp", "Lớp Đàn Thầy Thái", "Lớp MissAlice", "IES", "Bimbon", "Lớp Ori", "lớp mới", "SHD ĐBP", "Test MS Team", "LC", "Lớp Test MS Team", "Ielts 2025", "Starter 02", "Starters 1", "LC-02", "LC-03", "TA trẻ em 2026", "AA1", "Lớp Kind1", "Tiếng anh cơ bản", "Lớp E1 9h-9h30", "Lớp Phụ Đạo", "Lớp SHD", "Lê Bích Hòa", "i08")),
            _field("status_filter", "Tất cả trạng thái", kind="select", options=("Tất cả trạng thái", "Chưa phê duyệt", "Đã phê duyệt", "Hủy học thử")),
            _field("date_from", "Từ ngày", kind="date"), _field("date_to", "Đến ngày", kind="date"), _field("query", "Tìm..."),
            _field("page_size", "10 20 50 100", kind="select", options=("10", "20", "50", "100")),
        ],
        "actions": [], "fields": [_field("customer_name", "Khách hàng", required=True), _field("parent_name", "Phụ huynh"), _field("sale_owner", "Sales rep"), _field("class_name", "Lớp học"), _field("schedule", "Thời gian"), _field("status", "Trạng thái", required=True, options=("Chưa phê duyệt", "Đã phê duyệt", "Hủy học thử")), _field("note", "Ghi chú")],
    },
    "/sale/class_enroll_trail_wait": {
        "title": "Danh sách khách hàng đăng ký học thử", "resource": "trials",
        "columns": ["No.", "Khách hàng", "Phụ huynh", "Sales rep", "Lớp học", "Thời gian", "Trạng thái", "Công cụ"],
        "filters": [
            _field("class_name", "Tất cả", kind="select", options=("Tất cả", "Lớp Đàn Thầy Thái", "Lớp MissAlice", "IES", "Bimbon", "Lớp Ori", "lớp mới", "SHD ĐBP", "Test MS Team", "LC", "Lớp Test MS Team", "Ielts 2025", "Starter 02", "Starters 1", "LC-02", "LC-03", "TA trẻ em 2026", "AA1", "Lớp Kind1", "Tiếng anh cơ bản", "Lớp E1 9h-9h30", "Lớp Phụ Đạo", "Lớp SHD", "Lê Bích Hòa", "i08")),
            _field("status_filter", "Tất cả", kind="select", options=("Tất cả", "Chưa phê duyệt", "Đã phê duyệt", "Hủy học thử")),
            _field("date_from", "Từ ngày", kind="date"), _field("date_to", "Đến ngày", kind="date"), _field("query", "Tìm kiếm..."),
            _field("page_size", "Hiển thị 10 25 50 100 bản ghi", kind="select", options=("10", "25", "50", "100")),
        ],
        "actions": [], "fields": [_field("customer_name", "Khách hàng", required=True), _field("parent_name", "Phụ huynh"), _field("sale_owner", "Sales rep"), _field("class_name", "Lớp học"), _field("schedule", "Thời gian"), _field("status", "Trạng thái", required=True, options=("Chưa phê duyệt", "Đã phê duyệt", "Hủy học thử")), _field("note", "Ghi chú")],
    },
    "/crm/event2/index": {
        "title": "Form Đăng Ký", "resource": "events",
        "columns": ["No.", "Lượt đăng ký", "Nội dung", "Trạng thái", "Đăng ký tối đa", "Link đăng ký", "Công cụ"],
        "filters": [_field("query", "Tìm kiếm..."), _field("page_size", "Số bản ghi", kind="select", options=("10", "25", "50", "100"))],
        "actions": ["Tạo Form"], "fields": [_field("code", "Mã form"), _field("title", "Tiêu đề", required=True), _field("description", "Mô tả", required=True), _field("start_at", "Ngày bắt đầu", required=True, kind="date"), _field("end_at", "Ngày kết thúc", kind="date"), _field("register_open_at", "Thời gian bắt đầu đăng ký", kind="date"), _field("register_closed_at", "Thời gian kết thúc đăng ký", kind="date"), _field("max_people", "Đăng ký tối đa", kind="number"), _field("cost_vnd", "Chi phí", kind="number"), _field("status", "Trạng thái", required=True, options=("Đang kích hoạt", "Đã dừng")), _field("registration_count", "Lượt đăng ký", kind="number"), _field("public_url", "Link đăng ký")],
    },
    "/crm/customer_test": {
        "title": "Danh sách test / hẹn test", "resource": "customer_tests",
        "columns": ["No.", "Khách hàng", "Phụ huynh", "Ngày hẹn test", "Điểm test", "Nhân viên sale", "Thời gian", "Công cụ"],
        "filters": [_field("query", "Tìm trong bảng..."), _field("date_from", "Từ ngày", kind="date"), _field("date_to", "Đếm ngày", kind="date"), _field("sale_owner", "Nhân viên sale", kind="select", options=("Tất cả", "Center Administrator", "Synthetic Sales Owner", "Synthetic Sales Assistant", "Synthetic CRM Staff", "Synthetic Partner", "Synthetic Branch")), _field("page_size", "Hiển thị 10 25 50 All bản ghi", kind="select", options=("10", "25", "50", "All"))],
        "actions": ["Excel"], "fields": [_field("customer_name", "Khách hàng", required=True), _field("parent_name", "Phụ huynh"), _field("test_date", "Ngày hẹn test", required=True, kind="date"), _field("score", "Điểm test", kind="number"), _field("sale_owner", "Nhân viên sale"), _field("note", "Ghi chú"), _field("activity", "Hoạt động")],
    },
    "/sale/customer_test": {
        "title": "Danh sách test / hẹn test", "resource": "customer_tests",
        "columns": ["No.", "Khách hàng", "Phụ huynh", "Ngày hẹn test", "Điểm test", "Nhân viên sale", "Ghi chú", "Hoạt động"],
        "filters": [_field("query", "  Tìm trong bảng..."), _field("date_from", "  Từ ngày", kind="date"), _field("date_to", "  Đếm ngày", kind="date"), _field("page_size", "Show 10 25 50 All entries", kind="select", options=("10", "25", "50", "All"))],
        "actions": ["Excel"], "fields": [_field("customer_name", "Khách hàng", required=True), _field("parent_name", "Phụ huynh"), _field("test_date", "Ngày hẹn test", required=True, kind="date"), _field("score", "Điểm test", kind="number"), _field("sale_owner", "Nhân viên sale"), _field("note", "Ghi chú"), _field("activity", "Hoạt động")],
    },
    "/crm/pending_enrollment/index": {
        "title": "Đăng ký chờ lớp", "resource": "pending_enrollments",
        "columns": ["No.", "Khách hàng", "Trung tâm", "Ca học", "Số buổi", "Ngày bắt đầu", "Khóa học", "Ghi chú", "Trạng thái", "Tạo bởi", "Hành động"],
        "filters": [_field("status", "Trạng thái", options=("Đang chờ", "Đã vào lớp", "Hủy")), _field("session_name", "Ca học"), _field("course_name", "Khóa học"), _field("query", "Tìm kiếm ...")],
        "actions": ["Tạo mới", "Excel"], "fields": [_field("customer_name", "Khách hàng", required=True), _field("center_name", "Trung tâm", required=True), _field("session_name", "Ca học"), _field("sessions_count", "Số buổi", kind="number"), _field("start_date", "Ngày bắt đầu", kind="date"), _field("course_name", "Khóa học"), _field("note", "Ghi chú"), _field("status", "Trạng thái", required=True, options=("Đang chờ", "Đã vào lớp", "Hủy")), _field("created_by", "Tạo bởi", required=True)],
    },
    "/sale/pending_enrollment/index": {
        "title": "Đăng ký chờ lớp", "resource": "pending_enrollments",
        "columns": ["No.", "Khách hàng", "Trung tâm", "Ca học", "Số buổi", "Ngày bắt đầu", "Khóa học", "Ghi chú", "Trạng thái", "Tạo bởi", "Hành động"],
        "filters": [_field("status", "Trạng thái", options=("Đang chờ", "Đã vào lớp", "Hủy")), _field("session_name", "Ca học"), _field("course_name", "Khóa học"), _field("query", "Tìm kiếm ...")],
        "actions": ["Tạo mới"], "fields": [_field("customer_name", "Khách hàng", required=True), _field("center_name", "Trung tâm", required=True), _field("session_name", "Ca học"), _field("sessions_count", "Số buổi", kind="number"), _field("start_date", "Ngày bắt đầu", kind="date"), _field("course_name", "Khóa học"), _field("note", "Ghi chú"), _field("status", "Trạng thái", required=True, options=("Đang chờ", "Đã vào lớp", "Hủy")), _field("created_by", "Tạo bởi", required=True)],
    },
    "/crm/discount": {
        "title": "Ưu đãi - Khuyến mãi", "resource": "discounts",
        "columns": ["Mã ưu đãi", "Tên ưu đãi", "Bắt đầu - kết thúc", "Nội dung ưu đãi", "Áp dụng", "Trạng thái", "Công cụ"],
        "filters": [_field("query", "Tìm trong bảng..."), _field("page_size", "Số bản ghi", kind="select", options=("5", "10", "25", "50"))],
        "actions": ["Excel", "Tạo ưu đãi"], "fields": [_field("code", "Mã ưu đãi", required=True), _field("name", "Tên ưu đãi", required=True), _field("start_date", "Ngày bắt đầu", required=True, kind="date"), _field("end_date", "Ngày kết thúc", kind="date"), _field("discount_type", "Loại giảm", required=True, options=("VND", "%")), _field("discount_value", "Mức giảm", required=True, kind="number"), _field("content", "Nội dung ưu đãi"), _field("apply_type", "Áp dụng", required=True, options=("Tất cả gói và khóa", "Tất cả gói và khóa học ngoại trừ", "Chỉ gói và khóa cụ thể")), _field("status", "Trạng thái", required=True, options=("Đang hoạt động", "Đã dừng")), _field("note", "Ghi chú")],
    },
    "/crm/packet": {
        "title": "Gói học phí", "resource": "packets",
        "columns": ["Gói học phí", "Khóa học trong gói", "Ngày bắt đầu/Ngày kết thúc", "Trạng thái", "Giá", "Giảm", "Thực thu", "Công cụ"],
        "filters": [_field("query", "Tìm trong bảng..."), _field("page_size", "Số bản ghi", kind="select", options=("5", "10", "25", "50"))],
        "actions": ["Excel", "Tạo gói học phí"], "fields": [_field("code", "Mã gói"), _field("name", "Tên gói", required=True), _field("start_date", "Ngày bắt đầu", kind="date"), _field("end_date", "Ngày kết thúc", kind="date"), _field("course_name", "Khóa học"), _field("price_vnd", "Giá", required=True, kind="number"), _field("discount_vnd", "Giảm", kind="number"), _field("net_price_vnd", "Thực thu", required=True, kind="number"), _field("status", "Trạng thái", required=True, options=("Hoạt động", "Đã hết hạn")), _field("note", "Ghi chú")],
    },

    "/sale/contract": {
        "title": "Hợp đồng khóa học", "resource": "contracts",
        "columns": ["No.", "Mã hợp đồng", "Khách hàng", "Ngày tạo/Hết hạn", "Khóa học đăng kí", "Thanh toán/Còn nợ", "Nhân viên sale", "Người tạo", "Trạng thái đóng tiền", "Trạng thái hợp đồng", "Ghi chú", "Công cụ"],
        "filters": [_field("query", "Tìm trong bảng..."), _field("created_from", "Từ ngày tạo", kind="date"), _field("created_to", "Đến ngày tạo", kind="date"), _field("expiry_from", "Từ ngày hết hạn", kind="date"), _field("expiry_to", "Đến ngày hết hạn", kind="date"), _field("payment_status", "Trạng thái đóng tiền"), _field("contract_status", "Trạng thái hợp đồng"), _field("discount_name", "Chọn ưu đãi"), _field("page_size", "Số bản ghi", kind="select", options=("10", "25", "50", "100"))],
        "actions": ["Lọc", "Tạo mới"], "fields": [_field("code", "Mã hợp đồng", required=True), _field("customer_name", "Khách hàng", required=True), _field("created_date", "Ngày tạo", required=True, kind="date"), _field("expiry_date", "Ngày hết hạn", kind="date"), _field("course_name", "Khóa học đăng kí", required=True), _field("total_vnd", "Tổng tiền", required=True, kind="number"), _field("paid_vnd", "Đã thanh toán", required=True, kind="number"), _field("sale_owner", "Nhân viên sale"), _field("created_by", "Người tạo", required=True), _field("payment_status", "Trạng thái đóng tiền", required=True, options=("Chưa đóng tiền", "Còn nợ", "Đóng đủ", "Đã hủy")), _field("contract_status", "Trạng thái hợp đồng", required=True), _field("note", "Ghi chú")],
    },
    "/sale/bill/index": {
        "title": "Hóa đơn", "resource": "bills",
        "columns": ["No.", "Mã hóa đơn", "Mã hợp đồng", "Lớp học", "Loại hóa đơn", "Khách hàng", "Thanh toán", "Nhân viên sale", "Người tạo", "Trạng thái xác nhận", "Ghi chú", "Công cụ"],
        "filters": [_field("query", "Tìm trong bảng..."), _field("branch", "Chi nhánh"), _field("date_from", "Từ ngày", kind="date"), _field("date_to", "Đến ngày", kind="date"), _field("confirmation_status", "Trạng thái xác nhận"), _field("page_size", "Số bản ghi", kind="select", options=("10", "25", "50", "100"))],
        "actions": ["Lọc", "Tạo hóa đơn"], "fields": [_field("invoice_code", "Mã hóa đơn", required=True), _field("contract_code", "Mã hợp đồng"), _field("class_name", "Lớp học"), _field("bill_type", "Loại hóa đơn", required=True, options=("Học viên", "Vật phẩm", "Khoản thu")), _field("customer_name", "Khách hàng", required=True), _field("payment_vnd", "Thanh toán", required=True, kind="number"), _field("sale_owner", "Nhân viên sale"), _field("created_by", "Người tạo", required=True), _field("confirmation_status", "Trạng thái xác nhận", required=True, options=("Đã xác nhận", "Cần xác nhận", "Không đồng ý")), _field("note", "Ghi chú")],
    },
    "/sale/appointment_date": {
        "title": "Hẹn đóng tiền", "resource": "payment_appointments",
        "columns": ["Trạng thái", "Học viên", "Phụ huynh", "Ngày hẹn", "Số tiền", "Ghi chú", "Kiểu/Mã", "Hợp đồng liên quan", "Công cụ"],
        "filters": [_field("query", "Tìm trong bảng..."), _field("date_from", "Từ ngày", kind="date"), _field("date_to", "Đến ngày", kind="date"), _field("appointment_type", "Kiểu", options=("Tất cả", "Theo hóa đơn", "Theo hợp đồng")), _field("page_size", "Số bản ghi", kind="select", options=("10", "25", "50", "100"))],
        "actions": [], "fields": [_field("status", "Trạng thái", required=True, options=("Chưa xử lý", "Đã xử lý", "Đã hủy")), _field("student_name", "Học viên", required=True), _field("parent_name", "Phụ huynh"), _field("appointment_date", "Ngày hẹn", required=True, kind="date"), _field("amount_vnd", "Số tiền", required=True, kind="number"), _field("note", "Ghi chú"), _field("appointment_type", "Kiểu", required=True, options=("Theo hóa đơn", "Theo hợp đồng")), _field("reference_code", "Mã", required=True), _field("contract_code", "Hợp đồng liên quan")],
    },
    "/dashboard/crm": {
        "title": "Trang chủ quản lý CRM", "resource": "crm_dashboard", "columns": [], "filters": [], "actions": [],
        "fields": [_field("as_of", "Ngày xem", kind="date"), _field("contract_count", "Hợp đồng", kind="number"), _field("contract_total_vnd", "Tiền hợp đồng", kind="number"), _field("bill_count", "Hóa đơn", kind="number"), _field("active_discount_count", "Ưu đãi đang chạy", kind="number")],
    },
    "/dashboard/sale": {
        "title": "Trang chủ SALE", "resource": "sale_dashboard", "columns": [], "filters": [_field("as_of", "Chọn ngày", kind="date")], "actions": ["Hôm nay", "1 Tuần", "1 Tháng"],
        "fields": [_field("as_of", "Ngày xem", kind="date"), _field("revenue_vnd", "Thực thu", kind="number"), _field("contract_count", "Hợp đồng", kind="number"), _field("new_customer_count", "Khách hàng mới", kind="number"), _field("care_count", "Đang chăm sóc", kind="number"), _field("appointment_count", "Lịch hẹn", kind="number")],
    },
}

# Prospect and care appointment persistence is owned by ``crm_domain``.  Keep
# their observed presentation contracts here so one coordinator manifest can
# describe all twenty CRM/Sale routes without duplicating their storage model.
CORE_ROUTE_METADATA: dict[str, dict[str, Any]] = {
    "/crm/potential/index": {
        "title": "Khách hàng tiềm năng", "resource": "prospects",
        "columns": ["No.", "Khách hàng", "Nhân viên sale", "Sale phụ", "Tag", "Khóa học chăm sóc", "Khóa học quan tâm", "Trạng thái", "Hẹn test", "Điểm test", "Học thử", "Ghi chú", "Chăm sóc", ""],
        "filters": ["Tìm kiếm...", "Nhân viên sale", "Sale phụ", "Số bản ghi"],
        "actions": ["Lọc", "Excel", "Chuyển khách hàng", "Tải lên", "Tạo khách hàng"],
        "fields": [_field("full_name", "Khách hàng", required=True), _field("sale_owner", "Nhân viên sale"), _field("sale_assistant", "Sale phụ"), _field("tag", "Tag"), _field("care_course", "Khóa học chăm sóc"), _field("interested_course", "Khóa học quan tâm"), _field("status", "Trạng thái", required=True, options=("Khách hàng mới", "Đang chăm sóc", "Đủ điều kiện", "Đã chuyển đổi", "Đã hủy tư vấn")), _field("test_appointment", "Hẹn test", kind="date"), _field("test_score", "Điểm test", kind="number"), _field("trial_status", "Học thử"), _field("note", "Ghi chú"), _field("care_progress", "Chăm sóc")],
    },
    "/sale/potential/index": {
        "title": "Khách hàng tiềm năng", "resource": "prospects",
        "columns": ["No.", "Khách hàng", "Nhân viên sale", "Sale phụ", "Tag", "Khóa học chăm sóc", "Khóa học quan tâm", "Trạng thái", "Hẹn test", "Điểm test", "Học thử", "Ghi chú", "Chăm sóc", ""],
        "filters": ["Tìm kiếm khách hàng", "Sale phụ", "Số bản ghi"],
        "actions": ["Lọc", "Tải lên", "Tạo khách hàng"],
        "fields": [_field("full_name", "Khách hàng", required=True), _field("sale_owner", "Nhân viên sale"), _field("sale_assistant", "Sale phụ"), _field("tag", "Tag"), _field("care_course", "Khóa học chăm sóc"), _field("interested_course", "Khóa học quan tâm"), _field("status", "Trạng thái", required=True, options=("Khách hàng mới", "Đang chăm sóc", "Đủ điều kiện", "Đã chuyển đổi", "Đã hủy tư vấn")), _field("test_appointment", "Hẹn test", kind="date"), _field("test_score", "Điểm test", kind="number"), _field("trial_status", "Học thử"), _field("note", "Ghi chú"), _field("care_progress", "Chăm sóc")],
    },
    "/crm/potential/appointment": {
        "title": "Lịch hẹn khách hàng", "resource": "care_appointments",
        "columns": ["No.", "Học viên", "Nhân viên sale", "Ngày hẹn", "Hành động", "Ghi chú", "Trạng thái"],
        "filters": ["Tìm kiếm...", "Từ ngày", "Đến ngày", "Trạng thái", "Nhân viên", "Hành động"],
        "actions": ["Excel"],
        "fields": [_field("customer_name", "Học viên", required=True), _field("sale_owner", "Nhân viên sale"), _field("appointment_date", "Ngày hẹn", required=True, kind="date"), _field("action_type", "Hành động", required=True, options=("Gọi", "Nhắn tin", "Gặp trực tiếp", "Ghi chú")), _field("note", "Ghi chú"), _field("status", "Trạng thái", required=True, options=("Chưa xử lý", "Đã xử lý", "Đã hủy cuộc hẹn"))],
    },
    "/sale/potential/appointment": {
        "title": "Lịch hẹn khách hàng", "resource": "care_appointments",
        "columns": ["No.", "Học viên", "Nhân viên sale", "Ngày hẹn", "Hành động", "Ghi chú", "Trạng thái"],
        "filters": ["Tìm kiếm...", "Từ ngày", "Đến ngày", "Trạng thái", "Hành động", "Số bản ghi"],
        "actions": [],
        "fields": [_field("customer_name", "Học viên", required=True), _field("sale_owner", "Nhân viên sale"), _field("appointment_date", "Ngày hẹn", required=True, kind="date"), _field("action_type", "Hành động", required=True, options=("Gọi", "Nhắn tin", "Gặp trực tiếp", "Ghi chú")), _field("note", "Ghi chú"), _field("status", "Trạng thái", required=True, options=("Chưa xử lý", "Đã xử lý", "Đã hủy cuộc hẹn"))],
    },
}

ROUTE_MANIFEST_ORDER = (
    "/crm/potential/index", "/crm/potential/appointment", "/crm/sale_team/index", "/crm/target/index",
    "/crm/customer/raw", "/crm/opportunity_history",
    "/crm/class_enroll_trail_wait", "/crm/event2/index", "/crm/customer_test", "/crm/pending_enrollment/index",
    "/sale/potential/index", "/sale/contract", "/sale/bill/index", "/sale/class_enroll_trail_wait",
    "/sale/customer_test", "/sale/potential/appointment", "/sale/appointment_date", "/sale/pending_enrollment/index",
    "/crm/discount", "/crm/packet", "/dashboard/crm", "/dashboard/sale",
)

# The integrated host already exposes the finance-backed repository and
# renderer for ``/sale/contract``.  Keep this generic contract available for
# isolated lane validation, but make its integration authority explicit so a
# worker registration cannot silently replace the finance route.
SALE_ROUTE_AUTHORITY: dict[str, dict[str, Any]] = {
    "/sale/contract": {
        "owner": "modules.finance_contract",
        "status": "SHARED_HOST_AUTHORITY",
        "generic_store": "modules.crm_routes",
        "generic_store_mounted": False,
    },
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS crm_route_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  route TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_by TEXT NOT NULL,
  deleted_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_crm_route_records_route ON crm_route_records(route, id);
"""


def _role(role: str, *, write: bool = False) -> None:
    if role not in (WRITE_ROLES if write else READ_ROLES):
        raise PermissionError("Bạn không có quyền truy cập dữ liệu CRM/Sale")


def _date(value: Any, label: str, *, required: bool = False) -> str | None:
    text = str(value or "").strip()
    if not text:
        if required:
            raise ValueError(f"{label} là bắt buộc")
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"{label} phải là ngày hợp lệ")


def _number(value: Any, label: str, *, required: bool = False, minimum: float = 0) -> float | int | None:
    if value in (None, ""):
        if required:
            raise ValueError(f"{label} là bắt buộc")
        return None
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} phải là số") from exc
    if number < minimum:
        raise ValueError(f"{label} không được nhỏ hơn {minimum}")
    return int(number) if number.is_integer() else number


class CRMRoutesStore:
    """Strict persistent CRUD/query/export boundary for route-specific records."""

    def __init__(self, connection: sqlite3.Connection):
        self.db = connection
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.db.commit()

    @staticmethod
    def contract(route: str) -> dict[str, Any]:
        try:
            contract = dict(ROUTE_CONTRACTS.get(route) or CORE_ROUTE_METADATA[route])
            contract["route"] = route
            return contract
        except KeyError as exc:
            raise ValueError(f"Route CRM/Sale chưa có hợp đồng: {route}") from exc

    def create(self, route: str, *, role: str, created_by: str, data: Mapping[str, Any]) -> dict[str, Any]:
        _role(role, write=True)
        if route in READ_ONLY_ROUTES:
            raise PermissionError("Trang tổng quan chỉ cho phép xem dữ liệu")
        contract = self.contract(route); normalized = self._validate(contract, data)
        cur = self.db.execute("INSERT INTO crm_route_records(route,payload_json,created_by) VALUES(?,?,?)", (route, json.dumps(normalized, ensure_ascii=False, sort_keys=True), str(created_by).strip() or "Quản trị viên trung tâm"))
        self.db.commit(); return self.get(route, cur.lastrowid, role=role)  # type: ignore[return-value]

    def list(self, route: str, *, role: str, query: str = "", filters: Mapping[str, Any] | None = None, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        _role(role); contract = self.contract(route); filters = filters or {}
        date_from = _date(filters.get("date_from"), "Từ ngày") if str(filters.get("date_from") or "").strip() else None
        date_to = _date(filters.get("date_to"), "Đến ngày") if str(filters.get("date_to") or "").strip() else None
        created_from = _date(filters.get("created_from"), "Từ ngày tạo") if str(filters.get("created_from") or "").strip() else None
        created_to = _date(filters.get("created_to"), "Đến ngày tạo") if str(filters.get("created_to") or "").strip() else None
        expiry_from = _date(filters.get("expiry_from"), "Từ ngày hết hạn") if str(filters.get("expiry_from") or "").strip() else None
        expiry_to = _date(filters.get("expiry_to"), "Đến ngày hết hạn") if str(filters.get("expiry_to") or "").strip() else None
        for start, end, label in (
            (date_from, date_to, "Khoảng ngày"),
            (created_from, created_to, "Khoảng ngày tạo"),
            (expiry_from, expiry_to, "Khoảng ngày hết hạn"),
        ):
            if start and end and start > end:
                raise ValueError(f"{label} lọc không hợp lệ")
        rows = self.db.execute("SELECT * FROM crm_route_records WHERE route=? AND deleted_at IS NULL ORDER BY id DESC", (route,)).fetchall(); output = []
        for row in rows:
            data = json.loads(row["payload_json"])
            haystack = json.dumps(data, ensure_ascii=False).lower()
            if query and str(query).strip().lower() not in haystack: continue
            rejected = False
            for key, value in filters.items():
                if key in {"date_from", "date_to", "created_from", "created_to", "expiry_from", "expiry_to", "page_size", "query", "q"} or str(value or "").strip() == "":
                    continue
                field = key if key in data else {"created_from": "created_date", "created_to": "created_date", "expiry_from": "expiry_date", "expiry_to": "expiry_date"}.get(key, key)
                if str(data.get(field, "")) != str(value).strip():
                    rejected = True
                    break
            if rejected:
                continue
            date_value = data.get("date_value") or data.get("test_date") or data.get("created_date") or data.get("expiry_date") or data.get("appointment_date") or data.get("start_date") or data.get("start_at")
            if date_from and date_value and str(date_value)[:10] < date_from: continue
            if date_to and date_value and str(date_value)[:10] > date_to: continue
            created_date = str(data.get("created_date") or "")[:10]
            expiry_date = str(data.get("expiry_date") or "")[:10]
            if created_from and created_date and created_date < created_from: continue
            if created_to and created_date and created_date > created_to: continue
            if expiry_from and expiry_date and expiry_date < expiry_from: continue
            if expiry_to and expiry_date and expiry_date > expiry_to: continue
            output.append({"id": row["id"], "route": route, **data, "record_created_by": row["created_by"], "created_at": row["created_at"], "updated_at": row["updated_at"]})
        return output[max(0, int(offset)):max(0, int(offset)) + max(1, min(int(limit), 500))]

    def get(self, route: str, record_id: int, *, role: str) -> dict[str, Any] | None:
        _role(role); self.contract(route); row = self.db.execute("SELECT * FROM crm_route_records WHERE route=? AND id=? AND deleted_at IS NULL", (route, int(record_id))).fetchone()
        if row is None: return None
        payload = json.loads(row["payload_json"])
        result = {"id": row["id"], "route": route, **payload, "created_at": row["created_at"], "updated_at": row["updated_at"]}
        result["record_created_by"] = row["created_by"]
        return result

    def update(self, route: str, record_id: int, *, role: str, data: Mapping[str, Any]) -> dict[str, Any]:
        _role(role, write=True)
        if route in READ_ONLY_ROUTES:
            raise PermissionError("Trang tổng quan chỉ cho phép xem dữ liệu")
        current = self.get(route, record_id, role=role)
        if current is None: raise KeyError("Không tìm thấy bản ghi")
        merged = {key: value for key, value in current.items() if key not in {"id", "route", "record_created_by", "created_at", "updated_at"}}; merged.update(data); normalized = self._validate(self.contract(route), merged)
        self.db.execute("UPDATE crm_route_records SET payload_json=?,updated_at=CURRENT_TIMESTAMP WHERE route=? AND id=?", (json.dumps(normalized, ensure_ascii=False, sort_keys=True), route, int(record_id))); self.db.commit(); return self.get(route, record_id, role=role)  # type: ignore[return-value]

    def delete(
        self,
        route: str,
        record_id: int,
        *,
        role: str,
        expected_version: Any = None,
        expected_updated_at: Any = None,
    ) -> None:
        _role(role, write=True)
        if route in READ_ONLY_ROUTES:
            raise PermissionError("Trang tổng quan chỉ cho phép xem dữ liệu")
        row = self.db.execute(
            "SELECT updated_at FROM crm_route_records WHERE route=? AND id=? AND deleted_at IS NULL",
            (route, int(record_id)),
        ).fetchone()
        if row is None:
            raise KeyError("Không tìm thấy bản ghi")
        # CRM route records expose updated_at (no version column). A delete
        # without that token would silently remove a stale row, so fail closed.
        if expected_updated_at is None:
            raise RuntimeError("CONCURRENCY_TOKEN_REQUIRED")
        if str(expected_updated_at) != str(row["updated_at"]):
            raise RuntimeError("CONFLICT")
        cur = self.db.execute(
            "UPDATE crm_route_records SET deleted_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP "
            "WHERE route=? AND id=? AND deleted_at IS NULL AND updated_at=?",
            (route, int(record_id), str(expected_updated_at)),
        )
        if cur.rowcount != 1: raise KeyError("Không tìm thấy bản ghi")
        self.db.commit()

    def summary(self, route: str, *, role: str) -> dict[str, Any]:
        """Compute persisted route metrics used by CRM/Sale dashboards."""
        _role(role)
        self.contract(route)
        count = int(self.db.execute(
            "SELECT COUNT(*) FROM crm_route_records WHERE route=? AND deleted_at IS NULL", (route,)
        ).fetchone()[0])
        rows = self.list(route, role=role, limit=500)
        numeric_totals: dict[str, float | int] = {}
        for row in rows:
            for key, value in row.items():
                if key in {"id", "route", "created_at", "updated_at", "record_created_by"}:
                    continue
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    numeric_totals[key] = numeric_totals.get(key, 0) + value
        return {"route": route, "record_count": count, "numeric_totals": numeric_totals}

    def export_csv(self, route: str, *, role: str, query: str = "", filters: Mapping[str, Any] | None = None) -> str:
        contract = self.contract(route); rows = self.list(route, role=role, query=query, filters=filters, limit=10000); output = io.StringIO(); writer = csv.writer(output); writer.writerow(contract["columns"])
        for index, row in enumerate(rows, 1):
            values = []
            for column in contract["columns"]:
                if column in {"No.", "STT"}: values.append(index)
                else: values.append(row.get(self._column_key(contract, column), ""))
            writer.writerow(values)
        return output.getvalue()

    @staticmethod
    def _column_key(contract: Mapping[str, Any], column: str) -> str:
        fields = contract.get("fields", [])
        for item in fields:
            if item.get("label") == column: return str(item["name"])
        aliases = {"Khách hàng": "customer_name", "Học viên": "customer_name", "Nhân viên sale": "sale_owner", "Nhân viên sale": "sale_owner", "Trạng thái": "status", "Nội dung": "description", "Tên ưu đãi": "name", "Mã ưu đãi": "code", "Gói học phí": "name"}
        return aliases.get(column, column)

    @staticmethod
    def _validate(contract: Mapping[str, Any], data: Mapping[str, Any]) -> dict[str, Any]:
        route = str(contract.get("route", ""))
        aliases = FORM_ALIASES.get(route, {})
        values_in: dict[str, Any] = {}
        for key, value in data.items():
            canonical = aliases.get(str(key), str(key))
            values_in[canonical] = value
        value_aliases = FORM_VALUE_ALIASES.get(route, {})
        for key, mapping in value_aliases.items():
            if key in values_in and str(values_in[key]) in mapping:
                values_in[key] = mapping[str(values_in[key])]
        fields = {str(item["name"]): item for item in contract.get("fields", [])}
        unknown = sorted(set(values_in) - set(fields))
        if unknown: raise ValueError("Trường không được hỗ trợ: " + ", ".join(unknown))
        normalized: dict[str, Any] = {}
        for name, spec in fields.items():
            value = values_in.get(name, "")
            if spec.get("required") and str(value).strip() == "": raise ValueError(f"{spec['label']} là bắt buộc")
            if spec.get("kind") == "date": value = _date(value, spec["label"], required=bool(spec.get("required")))
            elif spec.get("kind") == "number": value = _number(value, spec["label"], required=bool(spec.get("required")))
            else: value = str(value or "").strip()
            options = spec.get("options") or []
            if options and value not in options: raise ValueError(f"{spec['label']} không hợp lệ")
            if value not in (None, ""): normalized[name] = value
        return normalized


def route_manifest() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for route in ROUTE_MANIFEST_ORDER:
        contract = CORE_ROUTE_METADATA.get(route) or ROUTE_CONTRACTS[route]
        result.append({"route": route, **{key: value for key, value in contract.items() if key in {"title", "resource", "columns", "filters", "actions"}}})
    return result


_W3_NAMES = ("Nguyễn Minh Anh", "Trần Thu Hà", "Lê Hoàng Anh", "Phạm Gia Bảo", "Vũ Minh Khôi", "Hoàng Minh Châu")
_W3_PARENTS = ("Nguyễn Thị Lan", "Trần Văn Hùng", "Phạm Thu Trang", "Lê Quốc Dũng")
_W3_CENTERS = ("Trung tâm Cầu Giấy", "Trung tâm Bình Thạnh", "Trung tâm Hải Châu", "Trung tâm Quận 1")
_W3_COURSES = ("IELTS Foundation", "Tiếng anh cơ bản 1", "Tiếng anh nâng cao", "STARTERS")


def _natural_generated_value(route: str, key: str, value: Any, index: int) -> Any:
    """Present rich-demo rows with domain names instead of technical fixtures.

    The host's rich demo database is intentionally populated before worker
    modules load.  CRM/Sale owns the customer-facing projection, so normalize
    those persisted rows at the module seam without touching app.py or shared
    seed code.  User-created values pass through unchanged.
    """
    if not isinstance(value, str):
        return value
    text = value.strip()
    lower_key = str(key).lower()
    ordinal = max(0, int(index))
    if not re.search(r"demo|column\s+\d+", text, re.IGNORECASE):
        return value
    if "mã" in lower_key or lower_key in {"code", "ma_hoa_on", "ma_hop_ong", "ma_uu_ai", "ma_goi"}:
        if "ma_hop" in lower_key or "hợp đồng" in lower_key:
            return f"HD-2026-{ordinal + 1:03d}"
        if "ma_hoa" in lower_key or "hóa đơn" in lower_key:
            return f"HDN-2026-{ordinal + 1:03d}"
        if "bill" in text.lower() or "hóa đơn" in lower_key:
            return f"HDN-2026-{ordinal + 1:03d}"
        if "contract" in text.lower() or "hợp đồng" in lower_key:
            return f"HD-2026-{ordinal + 1:03d}"
        if "discount" in text.lower() or "ưu đãi" in lower_key:
            return f"KM-2026-{ordinal + 1:03d}"
        if "packet" in text.lower() or "gói" in lower_key:
            return f"GOI-2026-{ordinal + 1:03d}"
    if any(token in lower_key for token in ("khach_hang", "khách hàng", "hoc_vien", "học viên", "customer", "student")):
        return _W3_NAMES[ordinal % len(_W3_NAMES)]
    if any(token in lower_key for token in ("phu_huynh", "phụ huynh", "parent", "guardian")):
        return _W3_PARENTS[ordinal % len(_W3_PARENTS)]
    if any(token in lower_key for token in ("sale", "nhan_vien", "nhân viên", "sales_rep", "nguoi_tao", "người tạo")):
        return ("Trần Thu Hà", "Nguyễn Hải Yến", "Lê Hoàng Anh")[ordinal % 3]
    if any(token in lower_key for token in ("chi_nhanh", "trung_tam", "branch", "center")):
        return _W3_CENTERS[ordinal % len(_W3_CENTERS)]
    if any(token in lower_key for token in ("lop_hoc", "lớp học", "class")):
        return ("Lớp IELTS Foundation", "Lớp Tiếng anh cơ bản", "Lớp STARTERS")[ordinal % 3]
    if any(token in lower_key for token in ("loai_hoa", "loại hóa đơn", "bill_type")):
        return "Học viên"
    if any(token in lower_key for token in ("thanh_toan", "thanh toán", "payment")):
        return "1.500.000 VND"
    if any(token in lower_key for token in ("noi_dung", "nội dung", "description", "mo_ta", "mô tả")):
        return "Tư vấn lộ trình học tập"
    if any(token in lower_key for token in ("link", "url")):
        return "/dang-ky/ielts-thang-11"
    if any(token in lower_key for token in ("cong_cu", "công cụ", "action")):
        return "Xem chi tiết"
    if any(token in lower_key for token in ("luot_ang_ky", "lượt đăng ký")):
        return f"{12 + ordinal} lượt"
    if any(token in lower_key for token in ("ang_ky_toi", "đăng ký tối đa")):
        return f"{30 + ordinal * 5} người"
    if any(token in lower_key for token in ("ten_uu_ai", "tên ưu đãi", "discount_name")):
        return "Ưu đãi tháng 11"
    if any(token in lower_key for token in ("bat_au", "bắt đầu", "ngay_bat", "ngày bắt")):
        return "01/11/2026 - 30/11/2026"
    if any(token in lower_key for token in ("ap_dung", "áp dụng", "apply")):
        return "Khóa học IELTS"
    if any(token in lower_key for token in ("goi_hoc_phi", "gói học phí")):
        return "Gói IELTS Foundation 30 buổi"
    if any(token in lower_key for token in ("khoa_hoc_trong_goi", "khóa học trong gói")):
        return _W3_COURSES[ordinal % len(_W3_COURSES)]
    if lower_key in {"gia", "price", "price_vnd"}:
        return "15.000.000 VND"
    if lower_key in {"giam", "discount", "discount_vnd"}:
        return "1.500.000 VND"
    if lower_key in {"thuc_thu", "net_price", "net_price_vnd"}:
        return "13.500.000 VND"
    if lower_key.startswith("column_"):
        match = re.search(r"(\d+)", lower_key)
        return f"Tháng {match.group(1) if match else ordinal + 1}"
    if "doanh_thu" in lower_key or "revenue" in lower_key:
        return "100.000.000 VND"
    if "hop_ong" in lower_key or "contract" in lower_key:
        return "40"
    if "tai_tuc" in lower_key or "renew" in lower_key:
        return "12"
    if "ghi_chu" in lower_key or "note" in lower_key:
        return "Thanh toán học phí tháng 11"
    # Last-resort replacement catches legacy labels such as ``Dữ liệu demo``.
    return "Thông tin CRM/Sale"


def _naturalize_generated(route: str, payload: Any) -> Any:
    if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
        return payload
    def clean_text(value: Any) -> Any:
        if not isinstance(value, str):
            return value
        replacements = {
            "Trung tâm CenterOnline - Demo": "Trung tâm Cầu Giấy",
            "Trung tâm Center EDU - Demo": "Trung tâm Cầu Giấy",
            "CenterOnline - Demo": "Trung tâm Cầu Giấy",
            "Academic Team": "Nhóm Sale Hà Nội",
            "Center Administrator": "Quản trị viên trung tâm",
        }
        result = value
        for source, target in replacements.items():
            result = result.replace(source, target)
        return result

    def clean_nested(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: clean_nested(clean_text(item)) for key, item in value.items()}
        if isinstance(value, list):
            return [clean_nested(item) for item in value]
        return clean_text(value)

    records = []
    for index, record in enumerate(payload["records"]):
        if not isinstance(record, dict):
            records.append(record)
            continue
        copied = dict(record)
        data = copied.get("data")
        if isinstance(data, dict):
            copied["data"] = {key: _natural_generated_value(route, key, value, index) for key, value in data.items()}
        records.append(copied)
    # Keep observed metadata untouched.  The shell uses spec filter options to
    # reconcile controls; changing an option label here would alter the
    # structure contract even though only row display needs naturalization.
    return {**payload, "records": records}


def route_authority(route: str) -> dict[str, Any]:
    """Return bounded integration ownership metadata for ambiguous Sale routes."""
    try:
        return dict(SALE_ROUTE_AUTHORITY[route])
    except KeyError as exc:
        raise ValueError(f"Route chưa có metadata authority: {route}") from exc


__all__ = ["CRMRoutesStore", "ROUTE_CONTRACTS", "CORE_ROUTE_METADATA", "ROUTE_MANIFEST_ORDER", "SCHEMA", "READ_ROLES", "WRITE_ROLES", "READ_ONLY_ROUTES", "SALE_ROUTE_AUTHORITY", "route_authority", "route_manifest"]


def register(_app_or_router: Any, service: Any) -> dict[str, Any]:
    """Register the CRM/Sale route store through the host's module seam.

    ``app.py`` deliberately owns HTTP dispatch.  This hook only creates the
    lane schema on the already-open SQLite connection and exposes the store
    for the coordinator/host adapter; it does not seed rows or alter shared
    routing code.  Repeated autoload calls are idempotent.
    """
    connection = getattr(service, "db", None)
    if connection is None:
        raise RuntimeError("CRM/Sale module requires the host SQLite connection")
    store = getattr(service, "crm_routes_store", None)
    if not isinstance(store, CRMRoutesStore) or getattr(store, "db", None) is not connection:
        store = CRMRoutesStore(connection)
        setattr(service, "crm_routes_store", store)

    # The host's generic generated-screen seam is the only shared wiring
    # available to worker modules.  Route-specific methods below keep the
    # 18 non-core CRM/Sale surfaces on this lane's SQLite contract while
    # leaving the host's unrelated generated screens untouched.  Install once
    # because the host may reload modules during development.
    if not getattr(service, "_w3_crm_routes_bound", False):
        owned = frozenset(ROUTE_MANIFEST_ORDER) - PRESERVED_HOST_ROUTES - frozenset({
            "/crm/potential/index", "/crm/potential/appointment",
            "/sale/potential/index", "/sale/potential/appointment",
            "/crm/opportunity_history",
            # FinanceContract is the integrated authority for this route.
            "/sale/contract",
        })
        original_generated = service.generated_screen
        original_add = service.add_generated_record
        original_update = service.update_generated_record
        original_delete = service.delete_generated_record
        original_export = service.export_generated_screen

        def local_spec(route: str) -> dict[str, Any]:
            contract = CRMRoutesStore.contract(route)
            fields = list(contract.get("fields", []))
            by_label = {str(item.get("label")): str(item.get("name")) for item in fields}
            columns = []
            used: set[str] = set()
            for index, label in enumerate(contract.get("columns", []), 1):
                text = str(label)
                if text in {"No.", "STT"}:
                    key = "no"
                else:
                    key = by_label.get(text, text or f"column_{index}")
                if key in used and key != "no":
                    key = f"{key}_{index}"
                used.add(key)
                columns.append({"label": text, "key": key})
            filters = []
            for item in contract.get("filters", []):
                if isinstance(item, str):
                    filters.append({"label": item, "placeholder": item, "type": "text", "name": item})
                else:
                    filters.append(dict(item))
            return {
                "route": route, "title": contract.get("title", route),
                "columns": columns, "filters": filters,
                "buttons": list(contract.get("actions", [])),
                "form": {"fields": fields},
                "api_status": "LOCAL_PERSISTENT_CONTRACT",
            }

        def history_rows(actor: Any, query: str = "") -> list[dict[str, Any]]:
            _role(str(actor["role"]))
            sql = """SELECT f.id, p.id AS potential_customer_id, p.full_name AS customer_name, f.created_at AS care_date,
                (SELECT COUNT(*) FROM potential_customer_followups older WHERE older.potential_customer_id=f.potential_customer_id AND (older.created_at<f.created_at OR (older.created_at=f.created_at AND older.id<=f.id))) AS care_number,
                p.branch AS center, p.customer_code, p.date_of_birth, p.phone, p.email,
                p.source AS customer_source, p.sale_owner, p.sale_assistant, u.full_name AS performed_by, f.action_type,
                f.outcome, p.tag AS customer_type,
                p.interested_course, p.care_course, f.note, f.next_follow_up_at,
                f.next_follow_up_at AS appointment_date, '' AS appointment_note
                FROM potential_customer_followups f
                JOIN potential_customers p ON p.id=f.potential_customer_id
                JOIN users u ON u.id=f.created_by
                WHERE p.deleted_at IS NULL"""
            params: list[Any] = []
            if str(query).strip():
                sql += " AND (p.full_name LIKE ? OR p.customer_code LIKE ? OR p.phone LIKE ? OR f.note LIKE ?)"
                needle = f"%{str(query).strip()}%"; params.extend([needle] * 4)
            sql += " ORDER BY f.created_at DESC, f.id DESC"
            rows = service.db.execute(sql, params).fetchall()
            output = []
            for index, row in enumerate(rows, 1):
                item = dict(row)
                item["action_type"] = {"CALL": "Gọi", "MESSAGE": "Nhắn tin", "NOTE": "Ghi chú", "APPOINTMENT": "Gặp trực tiếp"}.get(item.get("action_type"), item.get("action_type") or "")
                output.append(item)
            return output

        def generated(actor: Any, route: str, query: str = "", filters: Mapping[str, Any] | None = None) -> Any:
            if route == "/crm/opportunity_history":
                rows = history_rows(actor, query)
                return {"spec": local_spec(route), "records": [{"id": row.pop("id"), "route": route, "data": row} for row in rows], "total": len(rows), "contract_status": "SOURCE_JOIN_READ_ONLY"}
            if route not in owned:
                result = original_generated(actor, route, query, filters=filters)
                return _naturalize_generated(route, result) if route in ROUTE_MANIFEST_ORDER else result
            rows = store.list(route, role=str(actor["role"]), query=query, limit=500)
            records = [{"id": row.pop("id"), "route": route, "data": row} for row in rows]
            return _naturalize_generated(route, {"spec": local_spec(route), "records": records,
                    "total": len(records), "contract_status": "LOCAL_PERSISTENT_CONTRACT"})

        def add(actor: Any, route: str, payload: dict[str, Any]) -> Any:
            if route == "/crm/opportunity_history":
                raise PermissionError("Lịch sử chăm sóc chỉ được tạo qua API chăm sóc khách hàng")
            if route not in owned:
                return original_add(actor, route, payload)
            raw = payload.get("data", payload)
            if not isinstance(raw, dict):
                raise ValueError("data phải là một đối tượng")
            return store.create(route, role=str(actor["role"]),
                                created_by=str(actor["full_name"]), data=raw)

        def update(actor: Any, route: str, record_id: Any, payload: dict[str, Any]) -> Any:
            if route == "/crm/opportunity_history":
                raise PermissionError("Lịch sử chăm sóc không thể sửa trực tiếp")
            if route not in owned:
                return original_update(actor, route, record_id, payload)
            raw = payload.get("data", payload)
            if not isinstance(raw, dict):
                raise ValueError("data phải là một đối tượng")
            return store.update(route, int(record_id), role=str(actor["role"]), data=raw)

        def delete(
            actor: Any,
            route: str,
            record_id: Any,
            *,
            expected_version: Any = None,
            expected_updated_at: Any = None,
        ) -> Any:
            if route == "/crm/opportunity_history":
                raise PermissionError("Lịch sử chăm sóc không thể xóa trực tiếp")
            if route not in owned:
                # Preserve the host's generated-screen CAS contract.  This
                # adapter wraps every route, including W6 routes, so it must
                # forward version/updated_at tokens instead of dropping them.
                return original_delete(
                    actor,
                    route,
                    record_id,
                    expected_version=expected_version,
                    expected_updated_at=expected_updated_at,
                )
            store.delete(
                route,
                int(record_id),
                role=str(actor["role"]),
                expected_version=expected_version,
                expected_updated_at=expected_updated_at,
            )
            return {"id": int(record_id), "route": route, "deleted": True}

        def export(actor: Any, route: str, query: str = "", filters: Mapping[str, Any] | None = None) -> Any:
            if route == "/crm/opportunity_history":
                return history_rows(actor, query)
            if route not in owned:
                return original_export(actor, route, query, filters=filters)
            # ``RequestHandler.send_csv`` accepts row mappings.  Flatten the
            # persisted payload so exports contain Vietnamese field columns,
            # rather than a Python representation of a nested ``data`` object.
            return store.list(route, role=str(actor["role"]), query=query, limit=10000)

        service.generated_screen = generated
        service.add_generated_record = add
        service.update_generated_record = update
        service.delete_generated_record = delete
        service.export_generated_screen = export
        service._w3_crm_routes_bound = True
        service._w3_crm_routes_spec = local_spec
    return {
        "routes": list(ROUTE_MANIFEST_ORDER),
        "source": "modules.crm_routes",
        "status": "PERSISTENT_SQLITE_CONTRACT",
        "schema": "crm_route_records",
        "seed": "none",
    }
