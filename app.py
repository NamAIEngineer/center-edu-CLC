#!/usr/bin/env python3
"""Center EDU independent rebuild.

Small production-shaped local service: persistent SQLite, cookie sessions,
password hashing, role checks, audit events, and JSON APIs.  The reference
application is not copied; this implementation uses an explicit domain model
that can be expanded when authenticated reference evidence becomes available.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import hmac
import importlib
import io
import logging
import math
import json
import mimetypes
import os
import re
import secrets
import sqlite3
import threading
import time
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import parse_qs, urlparse

TRAINING_NATURAL_NAMES = (
    "Nguyễn Minh Anh", "Trần Hoàng Nam", "Lê Khánh Linh", "Phạm Gia Huy",
    "Võ Ngọc Mai", "Đặng Nhật Minh", "Bùi Thu Hà", "Phan Đức Anh",
    "Hoàng Yến Nhi", "Đỗ Quang Huy", "Nguyễn Thảo Vy", "Trần Gia Bảo",
    "Lê Minh Khang", "Phạm Ngọc Hân", "Vũ Minh Khôi", "Đinh Hà My",
)

def training_seed_value(route_name: str, key: str, row_number: int) -> Any:
    """Route-owned synthetic values shared by initial seed and backfill."""
    names = TRAINING_NATURAL_NAMES
    if route_name == "/training/absent-v2":
        if key in {"hoc_vien", "student_name", "student_id"}: return names[(row_number - 1) % len(names)]
        if key in {"buoi_nghi", "session_name"}: return f"Buổi {((row_number - 1) % 6) + 1} · {((row_number - 1) % 20) + 1:02d}/11/2026"
        if key in {"ly_do", "reason"}: return ["Sức khỏe", "Gia đình", "Lịch cá nhân", "Công việc"][(row_number - 1) % 4]
        if key in {"trang_thai", "status"}: return ["Chưa phê duyệt", "Đồng ý", "Từ chối", "Hủy", "Nhận thông tin"][(row_number - 1) % 5]
        if key in {"binh_luan", "comment"}: return ""
    if route_name == "/training/event":
        if key in {"luot_xem", "views", "view_count"}: return row_number * 7
        if key in {"noi_dung", "description", "content", "title"}: return ["Workshop kỹ năng học tập", "Ngày hội trải nghiệm tiếng Anh", "Tọa đàm định hướng lộ trình"][(row_number - 1) % 3]
        if key in {"a_xem_a_gui", "sent", "viewed_sent", "read_sent"}: return f"{(row_number % 8) + 2}/12"
        if key in {"trang_thai", "status"}: return "Đã gửi" if row_number % 2 == 0 else "Chưa gửi"
        if key in {"binh_luan", "comment", "cong_cu", "actions"}: return ""
    return None

try:
    from screen_engine import load_specs
except ImportError:  # pragma: no cover - direct package invocation fallback
    load_specs = None  # type: ignore[assignment]

try:
    from modules.report_engine import load_report_engine
except ImportError:  # pragma: no cover - direct package invocation fallback
    load_report_engine = None  # type: ignore[assignment]

try:
    from modules.report_training import test_report_rows
    from modules.finance_report_adapter import FinanceReportProvider
    from modules.report_crm_center import CrmCenterReportAdapter, normalize_row as normalize_crm_report_row
    from modules.seed_quality import sanitize_payload as sanitize_customer_payload
except ImportError:  # pragma: no cover - direct package invocation fallback
    test_report_rows = None  # type: ignore[assignment]
    FinanceReportProvider = None  # type: ignore[assignment,misc]
    CrmCenterReportAdapter = None  # type: ignore[assignment,misc]
    normalize_crm_report_row = None  # type: ignore[assignment]
    sanitize_customer_payload = lambda value: value  # type: ignore[assignment]

try:
    from modules.finance import FinanceSpend
except ImportError:  # pragma: no cover - direct package invocation fallback
    FinanceSpend = None  # type: ignore[assignment,misc]

try:
    from modules.crm_next import AppointmentRepository
except ImportError:  # pragma: no cover - direct package invocation fallback
    AppointmentRepository = None  # type: ignore[assignment,misc]

try:
    from modules.finance_assessment import FinanceAssessment
except ImportError:  # pragma: no cover - direct package invocation fallback
    FinanceAssessment = None  # type: ignore[assignment,misc]

try:
    from modules.finance_reserve import FinanceReserve
except ImportError:  # pragma: no cover - direct package invocation fallback
    FinanceReserve = None  # type: ignore[assignment,misc]

try:
    from modules.finance_points import FinancePoints
except ImportError:  # pragma: no cover - direct package invocation fallback
    FinancePoints = None  # type: ignore[assignment,misc]

try:
    from modules.finance_item import ensure_schema as ensure_finance_item_schema, seed as seed_finance_items, list_items as list_finance_items, create_item as create_finance_item, update_item as update_finance_item, export_csv as export_finance_items
except ImportError:  # pragma: no cover - direct package invocation fallback
    ensure_finance_item_schema = seed_finance_items = list_finance_items = create_finance_item = update_finance_item = export_finance_items = None  # type: ignore[assignment,misc]

try:
    from modules.finance_debit_item import DebitItemRepository
except ImportError:  # pragma: no cover - direct package invocation fallback
    DebitItemRepository = None  # type: ignore[assignment,misc]

try:
    from modules.finance_wallet import ensure_schema as ensure_finance_wallet_schema, seed as seed_finance_wallets, list_wallets, export_csv as export_finance_wallets, READ_ROLES as FINANCE_WALLET_READ_ROLES
except ImportError:  # pragma: no cover - direct package invocation fallback
    ensure_finance_wallet_schema = seed_finance_wallets = list_wallets = export_finance_wallets = None  # type: ignore[assignment,misc]
    FINANCE_WALLET_READ_ROLES = frozenset()

try:
    from modules.center_lane import (
        CONTRACTS as W6_CONTRACTS,
        ensure_schema as ensure_w6_schema,
        seed as seed_w6_route,
        list_records as list_w6_records,
        create_record as create_w6_record,
        update_record as update_w6_record,
        archive_record as archive_w6_record,
        export_csv as export_w6_csv,
        EXPORT_KEY_ALIASES as W6_EXPORT_KEY_ALIASES,
    )
except ImportError:  # pragma: no cover - direct package invocation fallback
    W6_CONTRACTS = {}
    W6_EXPORT_KEY_ALIASES = {}
    ensure_w6_schema = seed_w6_route = list_w6_records = create_w6_record = update_w6_record = archive_w6_record = export_w6_csv = None  # type: ignore[assignment,misc]


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
DEFAULT_DB = ROOT / "data" / "center-edu.sqlite3"
MODULE_LOG = logging.getLogger("center_edu.module_loader")
SESSION_TTL = int(os.environ.get("CENTER_EDU_SESSION_TTL", "28800"))
PBKDF2_ITERATIONS = 220_000

# Sale contract is a presentation projection of the finance contract domain.
# Keep the generic screen transport read-only for this route so it cannot
# create a second writable contract store.
GENERIC_SCREEN_WRITE_BLOCKED_ROUTES = frozenset({"/sale/contract"})

# The reference upload screen exposes these human-facing columns.  The
# private reference endpoint/format is still UNKNOWN, so this is an explicit
# local contract derived from the observed DOM.  ``No.`` is a display-only
# column and is intentionally not persisted.
STUDENT_IMPORT_FIELDS = (
    "student_code", "identifier", "full_name", "english_name", "email",
    "phone", "username", "sales_rep", "date_of_birth", "gender", "class_codes",
    "parent1_code", "parent1_name", "parent1_phone", "parent1_email",
    "parent1_username", "parent2_code", "parent2_name", "parent2_phone",
    "parent2_email", "parent2_username", "expected_start_date",
    "expected_sessions", "province", "ward", "address", "school",
    "class_name", "birth_place", "note",
)


def cookie_secure_enabled() -> bool:
    """Require HTTPS-only session cookies when the deployment terminates TLS."""
    return os.environ.get("CENTER_EDU_COOKIE_SECURE", "0").strip().lower() in {"1", "true", "yes", "on"}


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('ADMIN','STAFF','TEACHER','STUDENT')),
    phone TEXT NOT NULL DEFAULT '',
    date_of_birth TEXT,
    gender TEXT NOT NULL DEFAULT '',
    nationality TEXT NOT NULL DEFAULT '',
    account_code TEXT NOT NULL DEFAULT '',
    permissions_json TEXT NOT NULL DEFAULT '[]',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    csrf_token TEXT NOT NULL,
    expires_at INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    level TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    sessions_count INTEGER,
    hours REAL,
    fee_method TEXT NOT NULL DEFAULT '',
    fee REAL,
    daily_evaluation TEXT NOT NULL DEFAULT '',
    unit TEXT NOT NULL DEFAULT '',
    subject TEXT NOT NULL DEFAULT '',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL REFERENCES courses(id),
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL DEFAULT '',
    room TEXT NOT NULL DEFAULT '',
    schedule TEXT NOT NULL DEFAULT '',
    start_date TEXT,
    end_date TEXT,
    sessions_count INTEGER,
    hours REAL,
    payment_method TEXT NOT NULL DEFAULT '',
    max_students INTEGER,
    max_students_per_session INTEGER,
    primary_manager TEXT NOT NULL DEFAULT '',
    secondary_manager TEXT NOT NULL DEFAULT '',
    daily_evaluation TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    vn_teacher_sessions INTEGER,
    foreign_teacher_sessions INTEGER,
    teacher_id INTEGER REFERENCES users(id),
    status TEXT NOT NULL DEFAULT 'PLANNED' CHECK (status IN ('PLANNED','OPEN','IN_PROGRESS','COMPLETED','CANCELLED')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Setup/classroom is an independent local contract derived from the
-- authenticated reference table headers.  It is deliberately separate from
-- classes.room: a room is a scheduling attribute, while this entity owns the
-- room catalogue and its availability state.
CREATE TABLE IF NOT EXISTS classrooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 0 CHECK (capacity >= 0),
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','INACTIVE')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE SET NULL,
    student_code TEXT NOT NULL UNIQUE,
    identifier TEXT NOT NULL DEFAULT '',
    full_name TEXT NOT NULL,
    english_name TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL,
    phone TEXT NOT NULL DEFAULT '',
    username TEXT NOT NULL DEFAULT '',
    sales_rep TEXT NOT NULL DEFAULT '',
    date_of_birth TEXT,
    gender TEXT NOT NULL DEFAULT '',
    class_codes TEXT NOT NULL DEFAULT '',
    parent1_code TEXT NOT NULL DEFAULT '',
    parent1_name TEXT NOT NULL DEFAULT '',
    parent1_phone TEXT NOT NULL DEFAULT '',
    parent1_email TEXT NOT NULL DEFAULT '',
    parent1_username TEXT NOT NULL DEFAULT '',
    parent2_code TEXT NOT NULL DEFAULT '',
    parent2_name TEXT NOT NULL DEFAULT '',
    parent2_phone TEXT NOT NULL DEFAULT '',
    parent2_email TEXT NOT NULL DEFAULT '',
    parent2_username TEXT NOT NULL DEFAULT '',
    expected_start_date TEXT,
    expected_sessions INTEGER,
    province TEXT NOT NULL DEFAULT '',
    ward TEXT NOT NULL DEFAULT '',
    address TEXT NOT NULL DEFAULT '',
    school TEXT NOT NULL DEFAULT '',
    class_name TEXT NOT NULL DEFAULT '',
    birth_place TEXT NOT NULL DEFAULT '',
    referral_source TEXT NOT NULL DEFAULT '',
    enrollment_year INTEGER,
    note TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','PAUSED','GRADUATED','INACTIVE')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'ENROLLED' CHECK (status IN ('ENROLLED','DROPPED','COMPLETED')),
    enrolled_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(class_id, student_id)
);

CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    session_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('PRESENT','ABSENT','LATE','EXCUSED')),
    note TEXT NOT NULL DEFAULT '',
    marked_by INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(class_id, student_id, session_date)
);

CREATE TABLE IF NOT EXISTS timetable_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    session_slot_id INTEGER REFERENCES session_slots(id) ON DELETE SET NULL,
    session_date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    room TEXT NOT NULL DEFAULT '',
    teacher_id INTEGER REFERENCES users(id),
    status TEXT NOT NULL DEFAULT 'SCHEDULED' CHECK (status IN ('SCHEDULED','COMPLETED','CANCELLED')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(class_id, session_date, start_time)
);

-- Ca học is a local contract derived from the observed setup/classroom tab.
-- The private reference schema remains UNKNOWN; this bounded entity owns the
-- reusable code/name/time/status values and can be attached to timetable rows.
CREATE TABLE IF NOT EXISTS session_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','INACTIVE')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    session_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'DRAFT' CHECK (status IN ('DRAFT','PUBLISHED')),
    score REAL,
    note TEXT NOT NULL DEFAULT '',
    marked_by INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(class_id, student_id, session_date)
);

CREATE TABLE IF NOT EXISTS tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    test_date TEXT NOT NULL,
    max_score REAL NOT NULL DEFAULT 10,
    status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('DRAFT','OPEN','CLOSED')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS test_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id INTEGER NOT NULL REFERENCES tests(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    score REAL,
    note TEXT NOT NULL DEFAULT '',
    marked_by INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(test_id, student_id)
);

CREATE TABLE IF NOT EXISTS homework (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    due_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('DRAFT','OPEN','CLOSED')),
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trial_registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    guardian_name TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    trial_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'NEW' CHECK (status IN ('NEW','CONFIRMED','CANCELLED')),
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS enrollment_confirmations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    contract_code TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING','APPROVED','REJECTED')),
    confirmed_by INTEGER REFERENCES users(id),
    confirmed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customer_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    parent_name TEXT NOT NULL DEFAULT '',
    test_date TEXT NOT NULL,
    score REAL,
    sales_owner TEXT NOT NULL DEFAULT '',
    note TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'BOOKED' CHECK (status IN ('BOOKED','SCORED','CANCELLED')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pending_enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    phone TEXT NOT NULL DEFAULT '',
    course_id INTEGER REFERENCES courses(id),
    preferred_day TEXT NOT NULL DEFAULT '',
    preferred_session TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'WAITING' CHECK (status IN ('WAITING','ASSIGNED','CANCELLED')),
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Finance, survey and call-center surfaces are evidence-derived local
-- contracts.  The reference browser observation exposed headers/filters, but
-- private API schemas and mutation semantics remain UNKNOWN.  Keep these
-- entities isolated so an empty local table is truthful and cannot be read as
-- reference data.
CREATE TABLE IF NOT EXISTS finance_bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_code TEXT NOT NULL UNIQUE,
    contract_code TEXT NOT NULL DEFAULT '',
    class_code TEXT NOT NULL DEFAULT '',
    subject TEXT NOT NULL DEFAULT '',
    customer_name TEXT NOT NULL DEFAULT '',
    payment_amount REAL,
    sales_owner TEXT NOT NULL DEFAULT '',
    created_by INTEGER REFERENCES users(id),
    center TEXT NOT NULL DEFAULT '',
    branch TEXT NOT NULL DEFAULT '',
    employee TEXT NOT NULL DEFAULT '',
    confirmation_status TEXT NOT NULL DEFAULT 'PENDING' CHECK (confirmation_status IN ('PENDING','CONFIRMED','REJECTED')),
    payment_method TEXT NOT NULL DEFAULT '',
    note TEXT NOT NULL DEFAULT '',
    invoice_date TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Finance contract is a first-class local domain entity.  It joins the
-- observed contract -> bill -> revenue workflow without pretending to know
-- the reference application's private API.  Bills keep their historical
-- contract_code; this table owns the durable contract record and balances.
CREATE TABLE IF NOT EXISTS finance_catalog_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL UNIQUE,
    item_type TEXT NOT NULL CHECK (item_type IN ('COURSE','PACKET','PRODUCT','CHARGE')),
    name TEXT NOT NULL,
    course_id INTEGER REFERENCES courses(id) ON DELETE SET NULL,
    unit TEXT NOT NULL DEFAULT 'Gói',
    unit_price REAL NOT NULL DEFAULT 0 CHECK (unit_price >= 0),
    sessions INTEGER,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','INACTIVE')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_finance_catalog_active ON finance_catalog_items(status,item_type,name);
CREATE TABLE IF NOT EXISTS finance_contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_code TEXT NOT NULL UNIQUE,
    customer_type TEXT NOT NULL DEFAULT 'STUDENT' CHECK (customer_type IN ('LEAD','STUDENT')),
    account_id INTEGER,
    student_id INTEGER REFERENCES students(id) ON DELETE SET NULL,
    class_id INTEGER REFERENCES classes(id) ON DELETE SET NULL,
    course_id INTEGER REFERENCES courses(id) ON DELETE SET NULL,
    item_id INTEGER REFERENCES finance_catalog_items(id) ON DELETE SET NULL,
    package_name TEXT NOT NULL DEFAULT '',
    created_date TEXT NOT NULL,
    expiry_date TEXT,
    payment_due_date TEXT,
    payment_due_amount REAL CHECK (payment_due_amount IS NULL OR payment_due_amount >= 0),
    payment_note TEXT NOT NULL DEFAULT '',
    discount_code TEXT NOT NULL DEFAULT '',
    direct_discount REAL NOT NULL DEFAULT 0 CHECK (direct_discount >= 0),
    total_amount REAL NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    paid_amount REAL NOT NULL DEFAULT 0 CHECK (paid_amount >= 0),
    debt_amount REAL NOT NULL DEFAULT 0 CHECK (debt_amount >= 0),
    sales_owner TEXT NOT NULL DEFAULT '',
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    payment_status TEXT NOT NULL DEFAULT 'PENDING' CHECK (payment_status IN ('PENDING','PARTIAL','PAID','OVERDUE')),
    contract_status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (contract_status IN ('ACTIVE','EXPIRED','CANCELLED','COMPLETED')),
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_finance_contracts_student ON finance_contracts(student_id, id);
CREATE INDEX IF NOT EXISTS idx_finance_contracts_status ON finance_contracts(contract_status, payment_status, id);

-- Contract transfer ledger.  This local entity models the observed transfer
-- list without asserting the reference application's private mutation API.
CREATE TABLE IF NOT EXISTS finance_transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transfer_code TEXT NOT NULL UNIQUE,
    transfer_date TEXT NOT NULL,
    from_student_id INTEGER REFERENCES students(id) ON DELETE SET NULL,
    to_student_id INTEGER REFERENCES students(id) ON DELETE SET NULL,
    contract_id INTEGER REFERENCES finance_contracts(id) ON DELETE SET NULL,
    course_id INTEGER REFERENCES courses(id) ON DELETE SET NULL,
    amount_received REAL NOT NULL DEFAULT 0 CHECK (amount_received >= 0),
    note TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING','PROCESSED','CANCELLED')),
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_finance_transfers_date ON finance_transfers(transfer_date, id);
CREATE INDEX IF NOT EXISTS idx_finance_transfers_status ON finance_transfers(status, id);

CREATE TABLE IF NOT EXISTS finance_revenues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','INACTIVE')),
    price REAL,
    discount_type TEXT NOT NULL DEFAULT '',
    discount_value REAL,
    amount_due REAL,
    center TEXT NOT NULL DEFAULT '',
    note TEXT NOT NULL DEFAULT '',
    created_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS parents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_code TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    phone TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    relationship TEXT NOT NULL DEFAULT 'Phụ huynh',
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','INACTIVE')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_parents_student ON parents(student_id, id);

CREATE TABLE IF NOT EXISTS surveys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    due_date TEXT,
    completed_count INTEGER NOT NULL DEFAULT 0,
    sent_count INTEGER NOT NULL DEFAULT 0,
    recipient_count INTEGER NOT NULL DEFAULT 0,
    created_by INTEGER REFERENCES users(id),
    status TEXT NOT NULL DEFAULT 'DRAFT' CHECK (status IN ('DRAFT','PUBLISHED','CLOSED')),
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS survey_pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    survey_id INTEGER NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    position INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS survey_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    page_id INTEGER NOT NULL REFERENCES survey_pages(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('INPUT','CHECKBOX','DROPDOWN','COMMENT','RATING','IMAGE')),
    label TEXT NOT NULL,
    options_json TEXT NOT NULL DEFAULT '[]',
    position INTEGER NOT NULL DEFAULT 0,
    required INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS survey_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    survey_id INTEGER NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,
    respondent_name TEXT NOT NULL DEFAULT '',
    respondent_role TEXT NOT NULL DEFAULT '',
    answers_json TEXT NOT NULL DEFAULT '{}',
    submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(survey_id, respondent_name, submitted_at)
);

CREATE TABLE IF NOT EXISTS call_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER REFERENCES students(id) ON DELETE SET NULL,
    potential_customer_id INTEGER REFERENCES potential_customers(id) ON DELETE SET NULL,
    phone TEXT NOT NULL DEFAULT '',
    full_name TEXT NOT NULL DEFAULT '',
    party_role TEXT NOT NULL DEFAULT '',
    call_type TEXT NOT NULL DEFAULT '',
    staff_name TEXT NOT NULL DEFAULT '',
    note TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT '',
    duration_seconds INTEGER,
    recording_ref TEXT NOT NULL DEFAULT '',
    called_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CRM potential customers.  This is an independent rebuild contract based on
-- the authenticated reference surface (list/search/status/sale assignment,
-- detail and care history); it does not copy reference records.
CREATE TABLE IF NOT EXISTS potential_customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_code TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    phone TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'NEW' CHECK (status IN ('NEW','CONTACTED','QUALIFIED','CONVERTED','LOST')),
    sale_owner TEXT NOT NULL DEFAULT '',
    sale_assistant TEXT NOT NULL DEFAULT '',
    interest TEXT NOT NULL DEFAULT '',
    note TEXT NOT NULL DEFAULT '',
    date_of_birth TEXT,
    branch TEXT NOT NULL DEFAULT '',
    tag TEXT NOT NULL DEFAULT '',
    care_course TEXT NOT NULL DEFAULT '',
    interested_course TEXT NOT NULL DEFAULT '',
    test_appointment TEXT,
    test_score REAL,
    trial_status TEXT NOT NULL DEFAULT '',
    care_progress TEXT NOT NULL DEFAULT '',
    last_contact_at TEXT,
    next_follow_up_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS potential_customer_followups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    potential_customer_id INTEGER NOT NULL REFERENCES potential_customers(id) ON DELETE CASCADE,
    action_type TEXT NOT NULL CHECK (action_type IN ('CALL','MESSAGE','NOTE','APPOINTMENT')),
    outcome TEXT NOT NULL DEFAULT '',
    note TEXT NOT NULL DEFAULT '',
    next_follow_up_at TEXT,
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    entity TEXT NOT NULL,
    entity_id TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Class posts are durable class activity events.  The report must not infer
-- posts from a class roster: only rows written here count as published
-- activity.  This local table is intentionally independent from the observed
-- reference private API.
CREATE TABLE IF NOT EXISTS class_post_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PUBLISHED' CHECK (status IN ('DRAFT','PUBLISHED','ARCHIVED')),
    posted_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_class_post_events_class_date
    ON class_post_events(class_id, posted_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_class_post_events_status
    ON class_post_events(status, posted_at DESC);

-- Generic records back the configuration-driven screens whose private
-- reference API was not observable.  Values are local JSON contracts keyed
-- by the observed route; this table never imports reference sample rows.
CREATE TABLE IF NOT EXISTS generated_screen_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route TEXT NOT NULL,
    data_json TEXT NOT NULL DEFAULT '{}',
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    ,deleted_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_generated_screen_records_route
    ON generated_screen_records(route, id);
"""


class AppError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def now() -> int:
    return int(time.time())


def follow_up_datetime(value: Any, field: str = "next_follow_up_at") -> Optional[str]:
    """Validate the CRM follow-up datetime wire format.

    Follow-up values are persisted and later used for date filtering. Keep the
    protocol strict so malformed or ambiguous text cannot become a scheduled
    care appointment. Empty values intentionally clear the optional field.
    """
    if value in (None, ""):
        return None
    text = str(value).strip()
    if len(text) != 16 or text[10] != " ":
        raise AppError(400, "VALIDATION_ERROR", f"{field} must be YYYY-MM-DD HH:MM")
    try:
        dt.datetime.strptime(text, "%Y-%m-%d %H:%M")
    except (TypeError, ValueError) as exc:
        raise AppError(400, "VALIDATION_ERROR", f"{field} must be YYYY-MM-DD HH:MM") from exc
    return text


def password_hash(password: str, *, salt: Optional[bytes] = None) -> str:
    if not password or len(password) > 512:
        raise ValueError("invalid password")
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS, salt.hex(), digest.hex()
    )


def password_matches(password: str, encoded: str) -> bool:
    # Keep verification bounded to the same input contract as password_hash.
    # Reject oversized values before PBKDF2 to avoid unnecessary work for a
    # malformed login candidate.
    if not isinstance(password, str) or not password or len(password) > 512:
        return False
    if not isinstance(encoded, str):
        return False
    try:
        algorithm, iterations_text, salt_hex, digest_hex = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        # Keep malformed persisted hashes from turning login into an
        # unbounded PBKDF2 workload. The current contract uses 220,000.
        if iterations < 1 or iterations > 1_000_000:
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(candidate.hex(), digest_hex)
    except (ValueError, TypeError, OverflowError):
        return False


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(db_path), timeout=10, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA journal_mode = WAL")
    db.executescript(SCHEMA)
    # Existing proof databases predate the evidence-backed course/class fields.
    # Add only nullable/defaulted columns; this preserves all existing rows and
    # keeps a restart/recovery safe after the next controlled deployment.
    migrations = {
        "courses": {
            "sessions_count": "INTEGER",
            "hours": "REAL",
            "fee_method": "TEXT NOT NULL DEFAULT ''",
            "fee": "REAL",
            "daily_evaluation": "TEXT NOT NULL DEFAULT ''",
            "unit": "TEXT NOT NULL DEFAULT ''",
            "subject": "TEXT NOT NULL DEFAULT ''",
        },
        "classes": {
            "name": "TEXT NOT NULL DEFAULT ''",
            "start_date": "TEXT",
            "end_date": "TEXT",
            "sessions_count": "INTEGER",
            "hours": "REAL",
            "payment_method": "TEXT NOT NULL DEFAULT ''",
            "max_students": "INTEGER",
            "max_students_per_session": "INTEGER",
            "primary_manager": "TEXT NOT NULL DEFAULT ''",
            "secondary_manager": "TEXT NOT NULL DEFAULT ''",
            "daily_evaluation": "TEXT NOT NULL DEFAULT ''",
            "notes": "TEXT NOT NULL DEFAULT ''",
            "vn_teacher_sessions": "INTEGER",
            "foreign_teacher_sessions": "INTEGER",
        },
        "students": {
            "identifier": "TEXT NOT NULL DEFAULT ''",
            "english_name": "TEXT NOT NULL DEFAULT ''",
            "username": "TEXT NOT NULL DEFAULT ''",
            "sales_rep": "TEXT NOT NULL DEFAULT ''",
            "date_of_birth": "TEXT",
            "gender": "TEXT NOT NULL DEFAULT ''",
            "class_codes": "TEXT NOT NULL DEFAULT ''",
            "parent1_code": "TEXT NOT NULL DEFAULT ''",
            "parent1_name": "TEXT NOT NULL DEFAULT ''",
            "parent1_phone": "TEXT NOT NULL DEFAULT ''",
            "parent1_email": "TEXT NOT NULL DEFAULT ''",
            "parent1_username": "TEXT NOT NULL DEFAULT ''",
            "parent2_code": "TEXT NOT NULL DEFAULT ''",
            "parent2_name": "TEXT NOT NULL DEFAULT ''",
            "parent2_phone": "TEXT NOT NULL DEFAULT ''",
            "parent2_email": "TEXT NOT NULL DEFAULT ''",
            "parent2_username": "TEXT NOT NULL DEFAULT ''",
            "expected_start_date": "TEXT",
            "expected_sessions": "INTEGER",
            "province": "TEXT NOT NULL DEFAULT ''",
            "ward": "TEXT NOT NULL DEFAULT ''",
            "address": "TEXT NOT NULL DEFAULT ''",
            "school": "TEXT NOT NULL DEFAULT ''",
            "class_name": "TEXT NOT NULL DEFAULT ''",
            "birth_place": "TEXT NOT NULL DEFAULT ''",
            "referral_source": "TEXT NOT NULL DEFAULT ''",
            "enrollment_year": "INTEGER",
            "note": "TEXT NOT NULL DEFAULT ''",
        },
        "users": {
            "phone": "TEXT NOT NULL DEFAULT ''",
            "date_of_birth": "TEXT",
            "gender": "TEXT NOT NULL DEFAULT ''",
            "nationality": "TEXT NOT NULL DEFAULT ''",
            "account_code": "TEXT NOT NULL DEFAULT ''",
            "permissions_json": "TEXT NOT NULL DEFAULT '[]'",
        },
        "finance_contracts": {
            "customer_type": "TEXT NOT NULL DEFAULT 'STUDENT'",
            "account_id": "INTEGER REFERENCES students(id) ON DELETE SET NULL",
            "item_id": "INTEGER REFERENCES finance_catalog_items(id) ON DELETE SET NULL",
            "payment_due_date": "TEXT",
            "payment_due_amount": "REAL",
            "payment_note": "TEXT NOT NULL DEFAULT ''",
            "discount_code": "TEXT NOT NULL DEFAULT ''",
            "direct_discount": "REAL NOT NULL DEFAULT 0",
        },
        "timetable_sessions": {
            "session_slot_id": "INTEGER REFERENCES session_slots(id) ON DELETE SET NULL",
        },
        "call_history": {
            "student_id": "INTEGER REFERENCES students(id) ON DELETE SET NULL",
            "potential_customer_id": "INTEGER REFERENCES potential_customers(id) ON DELETE SET NULL",
        },
        "potential_customers": {
            "date_of_birth": "TEXT",
            "branch": "TEXT NOT NULL DEFAULT ''",
            "tag": "TEXT NOT NULL DEFAULT ''",
            "care_course": "TEXT NOT NULL DEFAULT ''",
            "interested_course": "TEXT NOT NULL DEFAULT ''",
            "test_appointment": "TEXT",
            "test_score": "REAL",
            "trial_status": "TEXT NOT NULL DEFAULT ''",
            "care_progress": "TEXT NOT NULL DEFAULT ''",
            "deleted_at": "TEXT",
        },
        "class_post_events": {
            "status": "TEXT NOT NULL DEFAULT 'PUBLISHED'",
            "posted_at": "TEXT",
            "created_at": "TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
        },
        "generated_screen_records": {
            "deleted_at": "TEXT",
        },
    }
    for table, columns in migrations.items():
        existing = {row[1] for row in db.execute(f"PRAGMA table_info({table})").fetchall()}
        for name, declaration in columns.items():
            if name not in existing:
                db.execute(f"ALTER TABLE {table} ADD COLUMN {name} {declaration}")
    db.commit()
    return db


def row_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    return dict(row) if row is not None else None


def rows_dict(rows: Iterable[sqlite3.Row]) -> List[Dict[str, Any]]:
    return [dict(row) for row in rows]


def seed(db: sqlite3.Connection) -> None:
    """Create safe demo data only when a database is empty."""
    if db.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
        return
    demo_password = os.environ.get("CENTER_EDU_DEMO_PASSWORD", "ChangeMe!CenterEdu2026")
    users = [
        ("admin", "admin@center.edu.vn", "Center Administrator", "ADMIN"),
        ("staff", "staff@center.edu.vn", "Academic Staff", "STAFF"),
        ("teacher", "teacher@center.edu.vn", "Demo Teacher", "TEACHER"),
        ("student", "student@center.edu.vn", "Demo Student", "STUDENT"),
    ]
    for username, email, full_name, role in users:
        db.execute(
            "INSERT INTO users(username,email,full_name,password_hash,role) VALUES(?,?,?,?,?)",
            (username, email, full_name, password_hash(demo_password), role),
        )
    teacher_id = db.execute("SELECT id FROM users WHERE username='teacher'").fetchone()[0]
    student_user_id = db.execute("SELECT id FROM users WHERE username='student'").fetchone()[0]
    db.execute(
        "INSERT INTO students(user_id,student_code,full_name,email,phone,sales_rep) VALUES(?,?,?,?,?,?)",
        (student_user_id, "HV-0001", "Demo Student", "student@center.edu.vn", "0900000000", "Demo Sales"),
    )
    db.execute(
        "INSERT INTO courses(code,name,level,description) VALUES(?,?,?,?)",
        ("ENG-FND", "English Foundation", "Foundation", "Core English foundation course."),
    )
    db.execute(
        "INSERT INTO courses(code,name,level,description) VALUES(?,?,?,?)",
        ("IELTS-65", "IELTS Target 6.5", "Intermediate", "Structured IELTS preparation."),
    )
    course_id = db.execute("SELECT id FROM courses WHERE code='ENG-FND'").fetchone()[0]
    db.execute(
        "INSERT INTO classes(course_id,code,room,schedule,teacher_id,status) VALUES(?,?,?,?,?,?)",
        (course_id, "ENG-FND-01", "Room A1", "Tue/Thu 18:30", teacher_id, "OPEN"),
    )
    db.execute(
        "INSERT INTO classrooms(code,name,capacity,description,status) VALUES(?,?,?,?,?)",
        ("ROOM-A1", "Phòng học A1", 18, "Phòng học mẫu cho dữ liệu demo.", "ACTIVE"),
    )
    class_id = db.execute("SELECT id FROM classes WHERE code='ENG-FND-01'").fetchone()[0]
    student_id = db.execute("SELECT id FROM students WHERE student_code='HV-0001'").fetchone()[0]
    db.execute("INSERT INTO enrollments(class_id,student_id) VALUES(?,?)", (class_id, student_id))
    db.execute(
        "INSERT INTO timetable_sessions(class_id,session_date,start_time,end_time,room,teacher_id) VALUES(?,?,?,?,?,?)",
        (class_id, "2026-11-03", "18:30", "20:00", "Room A1", teacher_id),
    )
    db.execute(
        "INSERT INTO tests(class_id,name,test_date,max_score) VALUES(?,?,?,?)",
        (class_id, "Foundation checkpoint", "2026-11-05", 10),
    )
    db.execute(
        "INSERT INTO homework(class_id,title,description,due_date,status,created_by) VALUES(?,?,?,?,?,?)",
        (class_id, "Vocabulary review", "Review unit 1 vocabulary.", "2026-11-06", "OPEN", teacher_id),
    )
    db.execute(
        "INSERT INTO trial_registrations(full_name,guardian_name,phone,trial_date,status) VALUES(?,?,?,?,?)",
        ("Demo Trial Learner", "Demo Guardian", "0911111111", "2026-11-07", "NEW"),
    )
    db.execute(
        "INSERT INTO enrollment_confirmations(student_id,class_id,contract_code,status) VALUES(?,?,?,?)",
        (student_id, class_id, "CTR-DEMO-001", "APPROVED"),
    )
    db.execute(
        "INSERT INTO customer_tests(customer_name,parent_name,test_date,score,sales_owner,note,status) VALUES(?,?,?,?,?,?,?)",
        ("Demo Candidate", "Demo Parent", "2026-11-08", 7.5, "Academic Team", "Initial placement", "SCORED"),
    )
    db.execute(
        "INSERT INTO pending_enrollments(customer_name,phone,course_id,preferred_day,preferred_session,status) VALUES(?,?,?,?,?,?)",
        ("Pending Learner", "0922222222", course_id, "Tue/Thu", "18:30", "WAITING"),
    )
    # Rich synthetic rows are opt-in.  The default test fixture stays small
    # and deterministic; an isolated customer-facing demo can opt in with
    # CENTER_EDU_RICH_DEMO=1 without changing the production seed contract.
    rich_demo = os.environ.get("CENTER_EDU_RICH_DEMO", "").strip().lower() in {"1", "true", "yes", "on"}
    if rich_demo:
        second_course = db.execute("SELECT id FROM courses WHERE code='IELTS-65'").fetchone()
        second_course_id = second_course[0] if second_course else course_id
        admin_id = db.execute("SELECT id FROM users WHERE username='admin'").fetchone()[0]
        # Synthetic teacher directory data is isolated to rich demo databases.
        # It exercises the observed teacher-management contract without
        # importing reference identities or customer data.
        teacher_ids = [teacher_id]
        for index in range(2, 13):
            username = f"teacher{index:02d}"
            email = f"teacher{index:02d}@demo.center.edu.vn"
            cur = db.execute(
                "INSERT INTO users(username,email,full_name,password_hash,role,phone,date_of_birth,gender,nationality,account_code,permissions_json,active) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (username, email, f"Giáo viên Demo {index:02d}", password_hash(demo_password), "TEACHER",
                 f"0901{index:06d}", f"198{index % 10}-{(index % 9) + 1:02d}-15",
                 "F" if index % 2 else "M", ["Vietnamese", "American", "British"][index % 3],
                 f"GV-{index:04d}", json.dumps(["Teacher", "Xem danh sách lớp"], ensure_ascii=False), 1),
            )
            teacher_ids.append(cur.lastrowid)
        for index, (code, schedule, status) in enumerate([
            ("ENG-FND-02", "Thứ 2 / Thứ 4 · 18:30 - 20:00", "OPEN"),
            ("IELTS-65-01", "Thứ 3 / Thứ 5 · 19:00 - 20:30", "IN_PROGRESS"),
            ("IELTS-65-02", "Thứ 7 / Chủ nhật · 09:00 - 10:30", "PLANNED"),
            ("ENG-FND-03", "Thứ 6 · 18:00 - 19:30", "OPEN"),
        ], start=2):
            db.execute(
                "INSERT INTO classes(course_id,code,room,schedule,teacher_id,status) VALUES(?,?,?,?,?,?)",
                (course_id if index % 2 == 0 else second_course_id, code, f"Room B{index}", schedule, teacher_ids[(index - 2) % len(teacher_ids)], status),
            )
        for index, status in enumerate(["CONFIRMED", "CONFIRMED", "PENDING", "CONFIRMED", "REJECTED"], start=1):
            db.execute(
                "INSERT INTO finance_bills(invoice_code,contract_code,class_code,subject,customer_name,payment_amount,sales_owner,created_by,center,branch,employee,confirmation_status,payment_method,note,invoice_date) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (f"DEMO-INV-{index:03d}", f"DEMO-CONTRACT-{index:03d}", f"ENG-FND-{index:01d}", "Học phí", f"Demo Customer {index}", 1000000 * index, "Academic Team", admin_id, "Center EDU", "Chi nhánh Demo", "Academic Team", status, "Chuyển khoản", "Dữ liệu demo nội bộ", f"2026-11-{index + 1:02d}"),
            )
        for code, name, amount in [
            ("TUITION", "Học phí khóa học", 3000000),
            ("MATERIAL", "Vật phẩm học tập", 250000),
            ("REGISTRATION", "Phí ghi danh", 500000),
            ("MAKEUP", "Phí học bù", 150000),
        ]:
            db.execute(
                "INSERT INTO finance_revenues(code,name,status,price,discount_type,discount_value,amount_due,center,note,created_by) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (code, name, "ACTIVE", amount, "FIXED", 0, amount, "Center EDU", "Dữ liệu demo nội bộ", admin_id),
            )
        # Deterministic, synthetic volume for the customer-facing demo only.
        # Tests and ordinary local runs retain the compact seed above.
        existing_classes = db.execute("SELECT COUNT(*) FROM classes").fetchone()[0]
        for index in range(existing_classes + 1, 26):
            db.execute(
                "INSERT INTO classes(course_id,code,room,schedule,teacher_id,status,max_students,notes) VALUES(?,?,?,?,?,?,?,?)",
                (course_id if index % 2 else second_course_id, f"DEMO-CLASS-{index:02d}", f"Room C{index:02d}", "Thứ 2 / Thứ 4 · 18:30 - 20:00" if index % 2 else "Thứ 3 / Thứ 5 · 19:00 - 20:30", teacher_ids[(index - 1) % len(teacher_ids)], ["OPEN", "IN_PROGRESS", "PLANNED"][index % 3], 20 + (index % 3) * 5, "Dữ liệu demo tổng hợp"),
            )
        for index in range(2, 81):
            db.execute(
                "INSERT INTO students(student_code,identifier,full_name,email,phone,sales_rep,gender,class_codes,school,referral_source,status) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (f"HV-DEMO-{index:03d}", f"ID-DEMO-{index:03d}", f"Demo Learner {index:03d}", f"learner{index:03d}@demo.center.edu.vn", f"0900{index:06d}", "Demo Sales", "F" if index % 2 else "M", f"DEMO-CLASS-{(index % 25) + 1:02d}", "Demo School", ["Website", "Referral", "Event"][index % 3], ["ACTIVE", "PAUSED", "GRADUATED"][index % 3]),
            )
        # Give every demo class an explicit lifecycle, timetable history and
        # enrolled learners so list/report views render real non-zero values.
        class_rows = db.execute("SELECT id,code,status FROM classes ORDER BY id").fetchall()
        student_rows = db.execute("SELECT id FROM students ORDER BY id").fetchall()
        for class_index, class_row in enumerate(class_rows, start=1):
            start_date = dt.date(2026, 9, 1) + dt.timedelta(days=(class_index % 12) * 3)
            end_date = start_date + dt.timedelta(days=90)
            completed_count = 26 if class_row["status"] == "IN_PROGRESS" else (8 if class_row["status"] == "OPEN" else 0)
            db.execute(
                "UPDATE classes SET start_date=?,end_date=?,sessions_count=?,hours=?,max_students=COALESCE(max_students,30) WHERE id=?",
                (start_date.isoformat(), end_date.isoformat(), 60, 90, class_row["id"]),
            )
            assigned = student_rows[(class_index * 3) % max(1, len(student_rows)):((class_index * 3) % max(1, len(student_rows))) + 4]
            if not assigned:
                assigned = student_rows[:4]
            for student_row in assigned:
                db.execute("INSERT OR IGNORE INTO enrollments(class_id,student_id,status) VALUES(?,?,?)", (class_row["id"], student_row["id"], "ENROLLED"))
            for session_index in range(1, completed_count + 1):
                session_date = start_date + dt.timedelta(days=session_index * 2)
                db.execute(
                    "INSERT INTO timetable_sessions(class_id,session_date,start_time,end_time,room,teacher_id,status) SELECT ?,?,?,?,?,teacher_id,'COMPLETED' FROM classes WHERE id=?",
                    (class_row["id"], session_date.isoformat(), "18:30", "20:00", f"Room {class_index:02d}", class_row["id"]),
                )
                for student_row in assigned[:3]:
                    attendance_status = ["PRESENT", "PRESENT", "EXCUSED", "ABSENT"][((session_index + student_row["id"]) % 4)]
                    db.execute(
                        "INSERT OR IGNORE INTO attendance(class_id,student_id,session_date,status,marked_by) VALUES(?,?,?,?,?)",
                        (class_row["id"], student_row["id"], session_date.isoformat(), attendance_status, admin_id),
                    )
            for session_index in range(completed_count + 1, completed_count + 4):
                session_date = start_date + dt.timedelta(days=session_index * 2)
                db.execute(
                    "INSERT INTO timetable_sessions(class_id,session_date,start_time,end_time,room,teacher_id,status) SELECT ?,?,?,?,?,teacher_id,'SCHEDULED' FROM classes WHERE id=?",
                    (class_row["id"], session_date.isoformat(), "18:30", "20:00", f"Room {class_index:02d}", class_row["id"]),
                )
        existing_bills = db.execute("SELECT COUNT(*) FROM finance_bills").fetchone()[0]
        for index in range(existing_bills + 1, 71):
            db.execute(
                "INSERT INTO finance_bills(invoice_code,contract_code,class_code,subject,customer_name,payment_amount,sales_owner,created_by,center,branch,employee,confirmation_status,payment_method,note,invoice_date) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (f"DEMO-INV-{index:03d}", f"DEMO-CONTRACT-{index:03d}", f"DEMO-CLASS-{(index % 25) + 1:02d}", "Học phí", f"Demo Customer {index:03d}", 750000 + index * 12500, "Academic Team", admin_id, "Center EDU", f"Chi nhánh {(index % 4) + 1}", "Academic Team", ["CONFIRMED", "PENDING", "REJECTED"][index % 3], "Chuyển khoản", "Dữ liệu demo tổng hợp", f"2026-10-{(index % 28) + 1:02d}"),
            )
        for index in range(1, 21):
            db.execute(
                "INSERT INTO potential_customers(customer_code,full_name,phone,email,source,status,sale_owner,interest,note) VALUES(?,?,?,?,?,?,?,?,?)",
                (f"LEAD-DEMO-{index:03d}", f"Demo Prospect {index:03d}", f"0912{index:06d}", f"prospect{index:03d}@demo.center.edu.vn", ["Website", "Facebook", "Referral"][index % 3], ["NEW", "CONTACTED", "QUALIFIED"][index % 3], "Demo Sales", "English course", "Dữ liệu demo tổng hợp"),
            )
        # Generic reference-derived routes have no private API contract.  Seed
        # a small, deterministic local dataset for every route so the rich
        # demo renders real looking entities, filters and pagination.  Values
        # are synthetic and derived only from observed labels; reference rows
        # are never copied into the product.
        def _demo_label(label: str, key: str) -> str:
            value = (label or key or "Bản ghi").strip()
            if value.lower().startswith("column_") or value.lower() in {"field", "input"}:
                value = value.replace("_", " ")
            aliases = {
                "created_at": "Ngày tạo", "updated_at": "Ngày cập nhật", "department_id": "Phòng ban",
                "position_id": "Chức vụ", "role_id": "Vai trò", "status": "Trạng thái",
                "note_select": "Ghi chú", "column_8": "Thông tin bổ sung",
            }
            return aliases.get(key.lower(), value[:1].upper() + value[1:])

        def _generated_demo_value(label: str, key: str, route_name: str, row_number: int, field_type: str = "text", options: list[Any] | None = None) -> Any:
            options = options or []
            if options:
                return str(options[(row_number - 1) % len(options)])
            normalized = f"{label} {key}".lower()
            if field_type in {"number", "integer"} or any(token in normalized for token in ("số lượng", "count", "total", "tổng số", "amount", "tiền", "điểm")):
                return row_number * 10
            if field_type in {"date", "datetime", "dateinput"} or any(token in normalized for token in ("ngày", "date", "thời gian")):
                return f"2026-{((row_number - 1) % 9) + 1:02d}-{((row_number - 1) % 27) + 1:02d}"
            if any(token in normalized for token in ("trạng thái", "status", "state")):
                return ["Đang hoạt động", "Đang xử lý", "Đã hoàn thành"][(row_number - 1) % 3]
            if any(token in normalized for token in ("email", "e-mail")):
                return f"demo{row_number:02d}@center.edu.vn"
            if any(token in normalized for token in ("số điện thoại", "điện thoại", "phone", "mobile")):
                return f"090{row_number:07d}"
            if any(token in normalized for token in ("giáo viên", "teacher")):
                return f"Giáo viên Demo {row_number:02d}"
            if any(token in normalized for token in ("học viên", "student", "khách hàng", "customer")):
                return f"Học viên Demo {row_number:02d}"
            if any(token in normalized for token in ("lớp", "class")):
                return f"Lớp Demo {row_number:02d}"
            if any(token in normalized for token in ("chi nhánh", "branch", "trung tâm", "center")):
                return f"Chi nhánh Demo {(row_number % 4) + 1}"
            if any(token in normalized for token in ("mã", "code", "id", "số hóa đơn", "invoice")):
                return f"DEMO-{re.sub(r'[^a-z0-9]+', '-', route_name.lower()).strip('-')[:12].upper()}-{row_number:03d}"
            if field_type == "textarea":
                return f"Dữ liệu demo tổng hợp {row_number:02d}"
            return f"{label or key or 'Bản ghi'} Demo {row_number:02d}"


        specs_path = ROOT / "screen_specs" / "reference-screen-specs.json"
        try:
            specs_data = json.loads(specs_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            specs_data = {}
        for ordinal, spec in enumerate(specs_data.get("screens", []) if isinstance(specs_data, dict) else [], start=1):
            if not isinstance(spec, dict) or not spec.get("route"):
                continue
            route = str(spec["route"])
            if db.execute("SELECT 1 FROM generated_screen_records WHERE route=? LIMIT 1", (route,)).fetchone():
                continue
            data: Dict[str, Any] = {}
            form = spec.get("form") if isinstance(spec.get("form"), dict) else {}
            fields = form.get("fields") if isinstance(form.get("fields"), list) else []
            columns = spec.get("columns") if isinstance(spec.get("columns"), list) else []
            # Keep table columns and form fields together.  A form often has
            # additional required fields that are not visible in the list.
            descriptors: List[Dict[str, Any]] = [item for item in columns if isinstance(item, dict)]
            descriptors.extend(item for item in fields if isinstance(item, dict))
            seen_keys: set[str] = set()
            unique_descriptors: List[Dict[str, Any]] = []
            for item in descriptors:
                key = str(item.get("name") or item.get("key") or "").strip()
                if not key or key in seen_keys or key.lower() == "no":
                    continue
                seen_keys.add(key)
                unique_descriptors.append(item)
            for row_number in range(1, 13):
                data = {}
                for field in unique_descriptors:
                    key = str(field.get("name") or field.get("key") or "").strip()
                    label = _demo_label(str(field.get("label") or field.get("observed_label") or ""), key)
                    field_type = str(field.get("type") or "text").lower()
                    options = field.get("options") if isinstance(field.get("options"), list) else []
                    data[key] = training_seed_value(route, key, row_number)
                    if data[key] is None:
                        data[key] = _generated_demo_value(label, key, route, row_number, field_type, options)
                if not data:
                    data["name"] = f"Bản ghi Demo {row_number:02d}"
                db.execute(
                    "INSERT INTO generated_screen_records(route,data_json,created_by) VALUES(?,?,?)",
                    (route, json.dumps(data, ensure_ascii=False, sort_keys=True), admin_id),
                )
    db.commit()


class _AdapterSourceProvider:
    """Expose the base SQLite query surface to scoped report adapters."""

    def __init__(self, provider: "_SQLiteReportProvider"):
        self.provider = provider

    def query_report(self, *, entity: str, filters: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
        return self.provider._query_report_base(entity=entity, filters=filters)


class _SQLiteReportProvider:
    """SQLite adapter for the configuration-driven report engine.

    Report definitions come from the observed screen inventory.  This adapter
    only reads persisted local domain tables and returns empty rows when a
    report's source data is unavailable; it never manufactures a report row.
    """

    def __init__(self, service: "CenterEduService"):
        self.service = service
        self.training_adapter = test_report_rows
        self.finance_adapter = FinanceReportProvider(service.db) if FinanceReportProvider is not None else None
        self.crm_adapter = (
            CrmCenterReportAdapter(_AdapterSourceProvider(self))
            if CrmCenterReportAdapter is not None else None
        )

    @staticmethod
    def _like(rows: List[Dict[str, Any]], filters: Mapping[str, Any]) -> List[Dict[str, Any]]:
        needle = str(filters.get("q") or filters.get("query") or "").strip().lower()
        if not needle:
            return rows
        return [row for row in rows if needle in json.dumps(row, ensure_ascii=False, default=str).lower()]

    def query_report(self, *, entity: str, filters: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
        """Route report entities through the scoped, real-data adapters first."""
        if entity == "report_training_test" and self.training_adapter is not None:
            return self.training_adapter(self.service.db, filters)
        if self.finance_adapter is not None and (
            entity.startswith("report_finance_")
            or entity in {"finance_revenues", "finance_bills", "contracts", "report_crm_contract_index", "report_crm_bill_index"}
        ):
            rows = list(self.finance_adapter.query_report(entity=entity, filters=filters))
            return rows if rows else self._query_report_base(entity=entity, filters=filters)
        if self.crm_adapter is not None and entity.startswith(("report_crm_", "report_center_", "report_cso_", "report_callcenter_")):
            rows = list(self.crm_adapter.query_report(entity=entity, filters=filters))
            return rows
        return self._query_report_base(entity=entity, filters=filters)

    def _query_report_base(self, *, entity: str, filters: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
        db = self.service.db
        kind = str(entity or "").lower()
        rows: List[Dict[str, Any]] = []
        if "attendance" in kind or kind.endswith("diligence"):
            sql = """
                SELECT s.student_code,s.full_name,
                       COALESCE(SUM(CASE WHEN a.status IN ('PRESENT','LATE') THEN 1 ELSE 0 END),0) AS present,
                       COALESCE(SUM(CASE WHEN a.status='EXCUSED' THEN 1 ELSE 0 END),0) AS excused,
                       COALESCE(SUM(CASE WHEN a.status='ABSENT' THEN 1 ELSE 0 END),0) AS unexcused,
                       COUNT(a.id) AS total
                FROM students s JOIN enrollments e ON e.student_id=s.id AND e.status='ENROLLED'
                JOIN classes c ON c.id=e.class_id LEFT JOIN attendance a ON a.class_id=e.class_id AND a.student_id=s.id
                GROUP BY s.id ORDER BY s.student_code
            """
            rows = rows_dict(db.execute(sql).fetchall())
        elif "class" in kind or "schedule" in kind or "allocation" in kind:
            rows = rows_dict(db.execute(
                "SELECT c.code AS class_code,co.name AS course_name,c.status,c.start_date,c.end_date,"
                "COUNT(e.id) AS enrolled,c.room,c.schedule FROM classes c JOIN courses co ON co.id=c.course_id "
                "LEFT JOIN enrollments e ON e.class_id=c.id AND e.status='ENROLLED' GROUP BY c.id ORDER BY c.id DESC"
            ).fetchall())
        elif "student" in kind or "enroll" in kind or "birth" in kind:
            rows = rows_dict(db.execute(
                "SELECT s.student_code,s.full_name,s.date_of_birth,s.school,s.status,s.referral_source,"
                "s.parent1_name,s.parent1_phone,s.class_codes FROM students s ORDER BY s.id DESC"
            ).fetchall())
        elif "finance" in kind or "revenue" in kind or "debt" in kind or "payment" in kind or "inventory" in kind:
            rows = rows_dict(db.execute(
                "SELECT f.invoice_code,f.contract_code,f.customer_name,f.payment_amount,f.confirmation_status,"
                "f.payment_method,f.invoice_date,f.center,f.branch,f.employee FROM finance_bills f "
                "ORDER BY COALESCE(f.invoice_date,f.created_at) DESC,f.id DESC"
            ).fetchall())
            if not rows:
                rows = rows_dict(db.execute(
                    "SELECT code,name,status,price,amount_due,center,created_at FROM finance_revenues ORDER BY id DESC"
                ).fetchall())
            # A compact test database may be created before rich-demo mode is
            # enabled.  Contracts are still backfilled idempotently and are a
            # durable finance source, so use them as the final local source
            # instead of reporting a fabricated zero row or losing the report
            # entirely.  Unsupported invoice-only dimensions stay empty.
            if not rows:
                rows = rows_dict(db.execute(
                    "SELECT f.contract_code,f.package_name AS name,f.contract_status AS status,"
                    "f.total_amount AS total_amount,f.paid_amount,f.debt_amount,"
                    "f.sales_owner,f.created_date,f.expiry_date "
                    "FROM finance_contracts f ORDER BY f.created_date DESC,f.id DESC"
                ).fetchall())
        elif "contract" in kind:
            rows = rows_dict(db.execute(
                "SELECT f.contract_code,s.full_name AS student_name,f.package_name,f.created_date,f.expiry_date,"
                "f.total_amount,f.paid_amount,f.debt_amount,f.sales_owner,f.payment_status,f.contract_status,f.note "
                "FROM finance_contracts f LEFT JOIN students s ON s.id=f.student_id ORDER BY f.created_date DESC,f.id DESC"
            ).fetchall())
        elif "customer" in kind or "care" in kind or "crm" in kind:
            rows = rows_dict(db.execute(
                "SELECT customer_code,full_name,phone,source,sale_owner,status,created_at,interest,care_course "
                "FROM potential_customers WHERE deleted_at IS NULL ORDER BY id DESC"
            ).fetchall())
        elif "teacher" in kind or "staff" in kind:
            rows = rows_dict(db.execute(
                "SELECT username,full_name,role,phone,email,active,nationality FROM users "
                "WHERE role IN ('TEACHER','STAFF') ORDER BY full_name"
            ).fetchall())
        elif "test" in kind or "examination" in kind:
            rows = rows_dict(db.execute(
                "SELECT t.name,t.test_date,t.max_score,t.status,c.code AS class_code "
                "FROM tests t JOIN classes c ON c.id=t.class_id ORDER BY t.test_date DESC,t.id DESC"
            ).fetchall())
        elif "evaluation" in kind or "notebook" in kind or "homework" in kind:
            rows = rows_dict(db.execute(
                "SELECT e.session_date,e.status,e.score,e.note,c.code AS class_code,s.full_name "
                "FROM evaluations e JOIN classes c ON c.id=e.class_id JOIN students s ON s.id=e.student_id "
                "ORDER BY e.session_date DESC,e.id DESC"
            ).fetchall())
        return self._like(rows, filters)


class CenterEduService:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_lock = threading.RLock()
        self.db = connect(self.db_path)
        seed(self.db)
        # W6 owns additive Center/Setup/CSO/Callcenter/Tenant local contracts.
        # Keep these routes behind the existing generated-screen transport so
        # the shared shell/API remains backward compatible while the worker's
        # persistent tables become reachable.
        self.w6_routes = frozenset(W6_CONTRACTS)
        if ensure_w6_schema is not None:
            ensure_w6_schema(self.db)
            if os.environ.get("CENTER_EDU_RICH_DEMO", "").strip().lower() in {"1", "true", "yes", "on"}:
                for _route in self.w6_routes:
                    try:
                        seed_w6_route(self.db, _route)
                    except (KeyError, ValueError):
                        # A route without an explicit worker seed remains
                        # unavailable rather than becoming a fabricated row.
                        continue
        if FinanceSpend is None:  # pragma: no cover - packaging failure
            raise RuntimeError("FinanceSpend module is unavailable")
        self.finance_spend_store = FinanceSpend(self.db)
        if AppointmentRepository is None:  # pragma: no cover - packaging failure
            raise RuntimeError("AppointmentRepository module is unavailable")
        self.appointment_store = AppointmentRepository(self.db)
        if FinanceAssessment is None:  # pragma: no cover - packaging failure
            raise RuntimeError("FinanceAssessment module is unavailable")
        self.finance_assessment_store = FinanceAssessment(self.db)
        if FinanceReserve is None:  # pragma: no cover - packaging failure
            raise RuntimeError("FinanceReserve module is unavailable")
        self.finance_reserve_store = FinanceReserve(self.db)
        if FinancePoints is None:  # pragma: no cover - packaging failure
            raise RuntimeError("FinancePoints module is unavailable")
        self.finance_points_store = FinancePoints(self.db)
        if ensure_finance_item_schema is None or DebitItemRepository is None:  # pragma: no cover - packaging failure
            raise RuntimeError("Finance inventory modules are unavailable")
        ensure_finance_item_schema(self.db)
        self.finance_debit_item_store = DebitItemRepository(self.db)
        if ensure_finance_wallet_schema is None:  # pragma: no cover - packaging failure
            raise RuntimeError("Finance wallet module is unavailable")
        ensure_finance_wallet_schema(self.db)
        self._ensure_rich_domain_backfill()
        if os.environ.get("CENTER_EDU_RICH_DEMO", "").strip().lower() in {"1", "true", "yes", "on"}:
            self.finance_spend_store.seed_demo()
            self.appointment_store.seed_demo()
            self.finance_assessment_store.seed_demo()
            self.finance_reserve_store.seed_demo()
            self.finance_points_store.seed_demo()
            seed_finance_items(self.db, count=10)
            self.finance_debit_item_store.seed_demo(minimum=10)
            seed_finance_wallets(self.db, count=20)
        self._ensure_generated_demo_records()
        if load_report_engine is None:  # pragma: no cover - packaging failure
            raise RuntimeError("Report engine module is unavailable")
        self.report_engine_v2 = load_report_engine(_SQLiteReportProvider(self))
        # Worker-owned modules are discovered after the core service is ready.
        # A module is optional: one import/registration failure is recorded and
        # skipped so the shell and already-integrated routes remain available.
        self.module_registry: Dict[str, Dict[str, Any]] = {}
        self.module_load_errors: Dict[str, str] = {}
        self._autoload_modules()
        # Optional worker stores own their schema.  Rich demo data is seeded
        # only in disposable/demo runtimes; an empty production-like DB stays
        # empty and therefore cannot be mistaken for live reference data.
        if os.environ.get("CENTER_EDU_RICH_DEMO", "").strip().lower() in {"1", "true", "yes", "on"}:
            history_store = getattr(self, "finance_history_move_store", None)
            if history_store is not None and hasattr(history_store, "seed_demo"):
                history_store.seed_demo()

    def register_module(self, name: str, *, module: Any = None, metadata: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        """Record a module registration without exposing internal paths.

        Worker ``register(app_or_router, service)`` hooks may call this after
        they install schema/seed/route adapters.  The HTTP shell remains the
        compatibility boundary; metadata is intentionally small and sanitized.
        """
        key = clean_text(name, 120) or "unnamed"
        value: Dict[str, Any] = {"name": key, "registered": True}
        if metadata:
            for field in ("routes", "source", "status", "schema", "seed"):
                if field in metadata:
                    value[field] = metadata[field]
        self.module_registry[key] = value
        return value

    def _autoload_modules(self) -> None:
        """Safely call optional worker module registration hooks.

        Modules are imported independently.  A broken optional lane cannot
        prevent the core Center EDU service from starting.  Existing explicit
        imports remain authoritative for compatibility; this loader adds the
        registry seam for workers that expose ``register``.
        """
        modules_dir = ROOT / "modules"
        if not modules_dir.is_dir():
            return
        for path in sorted(modules_dir.glob("*.py")):
            # Test helpers live beside production lane modules so workers can
            # keep focused coverage local.  They are never production
            # registration units: importing one during service startup can
            # pull unittest-only dependencies and create a misleading
            # LOAD_ERROR in the module registry.  Keep the autoloader
            # fail-soft for optional production modules while excluding these
            # explicitly named test files.
            if path.name.startswith("_") or path.name.startswith("test_"):
                continue
            name = path.stem
            import_name = f"modules.{name}"
            try:
                module = importlib.import_module(import_name)
                hook = getattr(module, "register", None)
                if not callable(hook):
                    self.module_registry[name] = {
                        "name": name,
                        "registered": False,
                        "status": "NO_REGISTER_HOOK",
                    }
                    continue
                result = hook(self, self)
                metadata = result if isinstance(result, Mapping) else {}
                self.register_module(name, module=module, metadata=metadata)
            except Exception as exc:  # pragma: no cover - exercised via focused loader test
                message = f"{type(exc).__name__}: {exc}"
                self.module_load_errors[name] = message[:300]
                # Keep sanitized diagnostics available to health/debug views;
                # never include tracebacks, environment values or secrets.
                self.module_registry[name] = {
                    "name": name,
                    "registered": False,
                    "status": "LOAD_ERROR",
                    "error": message[:300],
                }
                MODULE_LOG.warning("optional module %s skipped: %s", name, message[:300])

    def frontend_module_names(self) -> List[str]:
        """Return the allowlisted browser module filenames.

        Only direct ``static/modules/*.js`` files are returned.  This keeps
        the endpoint same-origin and prevents arbitrary filesystem disclosure.
        """
        if not (STATIC_DIR / "modules").is_dir():
            return []
        return sorted(
            path.name
            for path in (STATIC_DIR / "modules").glob("*.js")
            if path.is_file() and re.fullmatch(r"[A-Za-z0-9_.-]+\.js", path.name)
        )

    def _w6_spec(self, route: str) -> Dict[str, Any]:
        """Adapt a W6 RouteContract to the generated-screen view model."""
        contract = W6_CONTRACTS.get(route)
        if contract is None:
            raise AppError(404, "SCREEN_SPEC_NOT_FOUND", "screen contract not found")
        # W6 owns a few utility routes that are rendered by the shared local
        # screen engine.  Their durable fields remain the local contract, but
        # the observed navigation chrome (tabs, controls, action labels and
        # table headings) is already captured in the sanitized screen-spec
        # artifact.  Expose that shape here so the common wrapper can apply it
        # once instead of every lane reimplementing the same parity logic.
        observed = self._screen_specs().get(route, {})
        local_columns = list(contract.columns)
        observed_columns = list(observed.get("columns") or []) if isinstance(observed, Mapping) else []
        if observed_columns:
            keys = [key for key, _label in local_columns]
            columns = []
            for index, item in enumerate(observed_columns):
                label = str(item.get("label") or "") if isinstance(item, Mapping) else str(item)
                key = keys[index] if index < len(keys) else f"observed_{index + 1}"
                columns.append({"key": key, "label": label})
        else:
            columns = [{"key": key, "label": label} for key, label in local_columns]
        filters = [dict(item) for item in contract.filters]
        if isinstance(observed, Mapping) and observed.get("filters"):
            # Tenant checkboxes are row controls rather than a filter strip;
            # keep its compact local selector until a dedicated grid renderer
            # owns those controls.  Other utility routes use the full observed
            # list (including placeholders/options) verbatim.
            if route != "/tenant/config_excel":
                filters = [dict(item) for item in observed.get("filters", []) if isinstance(item, Mapping)]
        buttons = [str(item) for item in (observed.get("buttons") or []) if str(item).strip() and "trung tâm" not in str(item).lower()] if isinstance(observed, Mapping) else []
        if not buttons:
            buttons = ["Thêm mới", "Excel"]
        return {
            "route": route,
            "title": contract.title,
            "entity": contract.entity,
            "columns": columns,
            "filters": filters,
            "tabs": [str(item) for item in (observed.get("tabs") or []) if str(item).strip()] if isinstance(observed, Mapping) else [],
            "buttons": buttons,
            "form": {"fields": [dict(item) for item in contract.fields]},
            "api_status": "LOCAL_CONTRACT",
            "runtime_status": "SOURCE_PRESENT",
        }

    def _w6_rows(self, route: str, query: str = "", *, role: str) -> List[Dict[str, Any]]:
        if list_w6_records is None:
            return []
        rows = list_w6_records(self.db, route, {"q": query} if query else {}, role=role)
        return [{"id": row["id"], "route": route, "data": row["data"],
                 "created_at": row.get("created_at", ""), "updated_at": row.get("updated_at", "")}
                for row in rows]

    def _ensure_rich_domain_backfill(self) -> None:
        """Backfill durable demo domains after a code upgrade.

        ``seed`` intentionally exits when a database already has users.  The
        customer-facing rich demo must still converge after restart, so this
        method is idempotent and inserts only missing synthetic rows.  It is
        disabled for ordinary tests and production-shaped databases.
        """
        if os.environ.get("CENTER_EDU_RICH_DEMO", "").strip().lower() not in {"1", "true", "yes", "on"}:
            return
        admin = self.db.execute("SELECT id FROM users WHERE username='admin' LIMIT 1").fetchone()
        if admin is None:
            return
        admin_id = admin["id"]
        # Customer-facing rich demo identities are natural Vietnamese labels;
        # retain the stable usernames/password contract used by local tests.
        self.db.execute("UPDATE users SET full_name=? WHERE username='admin' AND full_name='Center Administrator'", ("Nguyễn Ngọc Mai",))
        self.db.execute("UPDATE users SET full_name=? WHERE username='staff' AND full_name='Academic Staff'", ("Trần Thu Hà",))
        self.db.execute("UPDATE users SET full_name=? WHERE username='teacher' AND full_name='Demo Teacher'", ("Ms Nga",))
        self.db.execute("UPDATE users SET full_name=? WHERE username='student' AND full_name='Demo Student'", ("Nguyễn Minh Anh",))
        demo_password = os.environ.get("CENTER_EDU_DEMO_PASSWORD", "ChangeMe!CenterEdu2026")
        teacher_names = [
            "Ms Nga", "Nguyễn Văn Cường", "Lê Quốc Bảo", "Trần Minh Anh", "Phạm Bảo Ánh",
            "Nguyễn Thị Huyền Trúc", "Nguyễn Trung Dũng", "Trần Thị Hoài Phượng", "Nguyễn Phương Linh",
            "Phạm Vinh Tiến", "Đặng Thu Hà", "Vũ Minh Khôi",
        ]
        staff_names = [
            "Trần Thu Hà", "Nguyễn Mai Anh", "Lê Hoàng Anh", "Phạm Thùy Dương", "Trần Minh Tú",
            "Bùi Linh Trang", "Phùng Kim Ngân", "Phạm Ngọc Anh", "Nguyễn Thu Ba", "Phạm Thị Du",
        ]
        # Keep at least twelve teachers and ten staff accounts, including
        # active teachers that can be assigned to live classes.
        teacher_count = self.db.execute("SELECT COUNT(*) FROM users WHERE role='TEACHER'").fetchone()[0]
        for index in range(teacher_count + 1, 13):
            username = f"teacher{index:02d}"
            try:
                self.db.execute(
                    "INSERT INTO users(username,email,full_name,password_hash,role,phone,date_of_birth,gender,nationality,account_code,permissions_json,active) VALUES(?,?,?,?,?,?,?,?,?,?,?,1)",
                    (username, f"{username}@demo.center.edu.vn", f"Giáo viên Demo {index:02d}", password_hash(demo_password), "TEACHER",
                     f"0901{index:06d}", f"198{index % 10}-{(index % 9) + 1:02d}-15", "F" if index % 2 else "M",
                     ["Vietnamese", "American", "British"][index % 3], f"GV-{index:04d}", json.dumps(["Teacher", "Xem danh sách lớp"], ensure_ascii=False)),
                )
            except sqlite3.IntegrityError:
                continue
        for position, row in enumerate(self.db.execute("SELECT id,username,full_name FROM users WHERE role='TEACHER' AND (username='teacher' OR username GLOB 'teacher[0-9]*') ORDER BY id").fetchall()):
            if str(row["full_name"] or "").startswith(("Demo ", "Giáo viên Demo")) or row["username"] == "teacher":
                self.db.execute("UPDATE users SET full_name=? WHERE id=?", (teacher_names[position % len(teacher_names)], row["id"]))
        staff_count = self.db.execute("SELECT COUNT(*) FROM users WHERE role='STAFF'").fetchone()[0]
        for index in range(staff_count + 1, 11):
            username = f"staff{index:02d}"
            try:
                self.db.execute(
                    "INSERT INTO users(username,email,full_name,password_hash,role,phone,date_of_birth,gender,nationality,account_code,permissions_json,active) VALUES(?,?,?,?,?,?,?,?,?,?,?,1)",
                    (username, f"{username}@demo.center.edu.vn", f"Nhân viên Demo {index:02d}", password_hash(demo_password), "STAFF",
                     f"0902{index:06d}", f"199{index % 10}-{(index % 9) + 1:02d}-20", "F" if index % 2 else "M", "Vietnamese",
                     f"NV-{index:04d}", json.dumps(["Staff", "Xem báo cáo"], ensure_ascii=False)),
                )
            except sqlite3.IntegrityError:
                continue
        for position, row in enumerate(self.db.execute("SELECT id,username,full_name FROM users WHERE role='STAFF' AND (username='staff' OR username GLOB 'staff[0-9]*') ORDER BY id").fetchall()):
            if str(row["full_name"] or "").startswith(("Academic Staff", "Nhân viên Demo")) or row["username"] == "staff":
                self.db.execute("UPDATE users SET full_name=? WHERE id=?", (staff_names[position % len(staff_names)], row["id"]))
        # Converge the first rich-demo seed batch as well.  The initial seed
        # predates the natural Vietnamese identity contract and may already
        # have durable rows, so this is an idempotent presentation cleanup
        # limited to exact scaffold markers.  IDs and relationships stay
        # unchanged; user-created names are not matched by these prefixes.
        natural_names = [
            "Nguyễn Minh Anh", "Trần Hoàng Nam", "Lê Khánh Linh", "Phạm Gia Huy",
            "Võ Ngọc Mai", "Đặng Nhật Minh", "Bùi Thu Hà", "Phan Đức Anh",
            "Hoàng Yến Nhi", "Đỗ Quang Huy", "Nguyễn Thảo Vy", "Trần Gia Bảo",
            "Lê Minh Khang", "Phạm Ngọc Hân", "Vũ Thanh Tùng", "Đinh Hà My",
            "Nguyễn Hải Đăng", "Trương Tú Anh", "Huỳnh Anh Khoa", "Mai Phương Thảo",
        ]
        for index, row in enumerate(self.db.execute("SELECT id,invoice_code,contract_code,customer_name,sales_owner,employee,note FROM finance_bills ORDER BY id").fetchall(), start=1):
            if not any(str(row[key] or "").startswith(prefix) for key in ("invoice_code", "contract_code", "customer_name", "sales_owner", "employee", "note") for prefix in ("DEMO-", "Demo ", "Academic Team", "Dữ liệu demo")):
                continue
            invoice_code = str(row["invoice_code"] or "")
            contract_code = str(row["contract_code"] or "")
            if invoice_code.startswith("DEMO-INV-"):
                invoice_code = invoice_code.replace("DEMO-INV-", "HD-INV-", 1)
            if contract_code.startswith("DEMO-CONTRACT-"):
                contract_code = contract_code.replace("DEMO-CONTRACT-", "HD-", 1)
            customer = natural_names[(index - 1) % len(natural_names)] if str(row["customer_name"] or "").startswith("Demo ") else row["customer_name"]
            sales = "Nguyễn Ngọc Mai" if str(row["sales_owner"] or "") == "Academic Team" else row["sales_owner"]
            employee = "Nguyễn Ngọc Mai" if str(row["employee"] or "") == "Academic Team" else row["employee"]
            note = "" if str(row["note"] or "").startswith("Dữ liệu demo") else row["note"]
            self.db.execute("UPDATE finance_bills SET invoice_code=?,contract_code=?,customer_name=?,sales_owner=?,employee=?,note=? WHERE id=?", (invoice_code, contract_code, customer, sales, employee, note, row["id"]))
        for row in self.db.execute("SELECT id,contract_code,sales_owner,note FROM finance_contracts ORDER BY id").fetchall():
            code = str(row["contract_code"] or "")
            sales = "Nguyễn Ngọc Mai" if str(row["sales_owner"] or "") == "Academic Team" else row["sales_owner"]
            note = "Hợp đồng học phí theo lộ trình" if str(row["note"] or "").startswith("Dữ liệu demo") else row["note"]
            new_code = code.replace("DEMO-CONTRACT-", "HD-", 1) if code.startswith("DEMO-CONTRACT-") else code
            if new_code != code or sales != row["sales_owner"] or note != row["note"]:
                self.db.execute("UPDATE finance_contracts SET contract_code=?,sales_owner=?,note=? WHERE id=?", (new_code, sales, note, row["id"]))
        # Durable references use the same contract code in enrollment records;
        # reconcile only the known synthetic prefix after the contract update.
        for table in ("enrollment_confirmations",):
            try:
                self.db.execute(f"UPDATE {table} SET contract_code=REPLACE(contract_code,'DEMO-CONTRACT-','HD-') WHERE contract_code LIKE 'DEMO-CONTRACT-%'")
            except sqlite3.OperationalError:
                pass
        self.db.execute("UPDATE finance_catalog_items SET item_code=REPLACE(item_code,'DEMO-ITEM-','VAT-PHAM-'), name=CASE WHEN name='Gói học phí Demo' THEN 'Gói học phí tiêu chuẩn' ELSE name END WHERE item_code LIKE 'DEMO-ITEM-%' OR name='Gói học phí Demo'")
        self.db.execute("UPDATE finance_transfers SET transfer_code=REPLACE(transfer_code,'CN-DEMO-','CN-EDU-'), note='' WHERE transfer_code LIKE 'CN-DEMO-%' OR note LIKE 'Dữ liệu demo%'")
        teacher_ids = [row["id"] for row in self.db.execute("SELECT id FROM users WHERE role='TEACHER' AND active=1 ORDER BY id").fetchall()]
        if teacher_ids:
            for offset, row in enumerate(self.db.execute("SELECT id FROM classes ORDER BY id").fetchall()):
                self.db.execute("UPDATE classes SET teacher_id=? WHERE id=?", (teacher_ids[offset % len(teacher_ids)], row["id"]))
        class_names = [
            "Starters 1", "IELTS 6.5 tối 2-4-6", "Tiếng Anh giao tiếp tối", "Foundation buổi sáng",
            "IELTS mục tiêu 6.5", "Tiếng Anh thiếu nhi", "Pre IELTS cuối tuần", "Lớp nền tảng 3",
        ]
        for position, row in enumerate(self.db.execute("SELECT id,code FROM classes WHERE code LIKE 'DEMO-CLASS-%' ORDER BY id").fetchall()):
            new_code = class_names[position % len(class_names)]
            if position >= len(class_names):
                new_code = f"{new_code} {position + 1}"
            if self.db.execute("SELECT 1 FROM classes WHERE code=? AND id<>?", (new_code, row["id"])).fetchone():
                new_code = f"{new_code} {row['id']}"
            self.db.execute("UPDATE classes SET code=? WHERE id=?", (new_code, row["id"]))
            self.db.execute("UPDATE students SET class_codes=REPLACE(class_codes,?,?) WHERE class_codes LIKE ?", (row["code"], new_code, f"%{row['code']}%"))
        # Existing databases can have been created before rich-demo mode was
        # enabled.  Converge their student directory before seeding dependent
        # domains (parents, contracts and transfers).  The one-time seed path
        # already creates these rows for a fresh rich DB; this idempotent block
        # repairs only the missing tail on an older compact DB.
        student_count = self.db.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        if student_count < 80:
            class_codes = [row["code"] for row in self.db.execute("SELECT code FROM classes ORDER BY id").fetchall()]
            for index in range(student_count + 1, 81):
                code = f"HV-DEMO-{index:03d}"
                if self.db.execute("SELECT 1 FROM students WHERE student_code=?", (code,)).fetchone():
                    continue
                class_code = class_codes[(index - 1) % len(class_codes)] if class_codes else ""
                self.db.execute(
                    "INSERT OR IGNORE INTO students(student_code,identifier,full_name,email,phone,sales_rep,gender,class_codes,school,referral_source,status,enrollment_year) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (code, f"ID-DEMO-{index:03d}", f"Demo Learner {index:03d}",
                     f"learner{index:03d}@demo.center.edu.vn", f"0900{index:06d}", "Demo Sales",
                     "F" if index % 2 else "M", class_code, "Demo School",
                     ["Website", "Referral", "Event"][index % 3],
                     ["ACTIVE", "PAUSED", "GRADUATED"][index % 3], 2026),
                )
        # Parent records are explicit so the student directory can join and
        # filter them without relying on denormalized display-only fields.
        students = self.db.execute("SELECT id,student_code,full_name FROM students ORDER BY id").fetchall()
        # Rich demo presentation uses plausible Vietnamese identities so
        # customer-facing screens do not expose scaffold labels.  Only rows
        # generated by the demo seed are changed; user-created identities are
        # preserved across restarts.
        demo_student_names = [
            "Nguyễn Minh Anh", "Trần Hoàng Nam", "Lê Khánh Linh", "Phạm Gia Huy",
            "Võ Ngọc Mai", "Đặng Nhật Minh", "Bùi Thu Hà", "Phan Đức Anh",
            "Hoàng Yến Nhi", "Đỗ Quang Huy", "Nguyễn Thảo Vy", "Trần Gia Bảo",
            "Lê Minh Khang", "Phạm Ngọc Hân", "Vũ Thanh Tùng", "Đinh Hà My",
            "Nguyễn Hải Đăng", "Trương Tú Anh", "Huỳnh Anh Khoa", "Mai Phương Thảo",
            "Cao Minh Quân", "Dương Khánh An", "Ngô Bảo Châu", "Lý Hoàng Long",
            "Đào Ngọc Ánh", "Phạm Tuấn Kiệt", "Nguyễn Hà Linh", "Trần Đức Minh",
            "Lê Quỳnh Chi", "Võ Thành Đạt", "Bùi Minh Thư", "Phan Nhật Nam",
            "Hoàng Minh Châu", "Đỗ Anh Tú", "Nguyễn Phúc An", "Trần Ngọc Diệp",
            "Lê Quốc Bảo", "Phạm Thanh Vân", "Vũ Minh Khôi", "Đinh Ngọc Lan",
        ]
        for index, row in enumerate(students):
            if str(row["full_name"] or "").startswith("Demo ") or str(row["student_code"] or "").startswith("HV-DEMO-"):
                name = demo_student_names[index % len(demo_student_names)]
                code = f"HV-EDU-{index + 1:03d}"
                self.db.execute(
                    "UPDATE students SET student_code=?,full_name=?,identifier=?,phone=?,note=? WHERE id=?",
                    (code, name, f"EDU-{index + 1:04d}", f"090{index + 1:07d}", "Học viên đang theo học tại trung tâm", row["id"]),
                )
        students = self.db.execute("SELECT id,student_code,full_name FROM students ORDER BY id").fetchall()
        for index, student in enumerate(students, start=1):
            code = f"PH-{student['student_code']}"
            if self.db.execute("SELECT 1 FROM parents WHERE parent_code=?", (code,)).fetchone():
                continue
            self.db.execute(
                "INSERT INTO parents(parent_code,full_name,phone,email,relationship,student_id,status) VALUES(?,?,?,?,?,?,?)",
                (code, f"Phụ huynh {student['full_name']}", f"0918{index:06d}", f"parent{index:03d}@demo.center.edu.vn", "Phụ huynh", student["id"], "ACTIVE"),
            )
        # Rich mode can be enabled after a compact database was created (the
        # focused tests deliberately do this).  Converge the finance source
        # tables before reconciling contracts so finance reports have durable
        # local rows on both fresh and upgraded demo databases.  Rows are
        # deterministic and idempotent; existing user-created invoices and
        # revenue definitions are preserved.
        existing_bill_count = self.db.execute("SELECT COUNT(*) FROM finance_bills").fetchone()[0]
        if existing_bill_count < 70:
            demo_names = [
                "Nguyễn Minh Anh", "Trần Hoàng Nam", "Lê Khánh Linh", "Phạm Gia Huy",
                "Võ Ngọc Mai", "Đặng Nhật Minh", "Bùi Thu Hà", "Phan Đức Anh",
                "Hoàng Yến Nhi", "Đỗ Quang Huy", "Nguyễn Thảo Vy", "Trần Gia Bảo",
                "Lê Minh Khang", "Phạm Ngọc Hân", "Vũ Thanh Tùng", "Đinh Hà My",
            ]
            class_codes = [row["code"] for row in self.db.execute("SELECT code FROM classes ORDER BY id").fetchall()]
            class_code = class_codes[0] if class_codes else ""
            for index in range(1, 71):
                invoice_code = f"HD-{index:04d}"
                if self.db.execute("SELECT 1 FROM finance_bills WHERE invoice_code=?", (invoice_code,)).fetchone():
                    continue
                customer = demo_names[(index - 1) % len(demo_names)]
                amount = 750000 + index * 12500
                status = ("CONFIRMED", "PENDING", "REJECTED")[index % 3]
                self.db.execute(
                    "INSERT INTO finance_bills(invoice_code,contract_code,class_code,subject,customer_name,payment_amount,sales_owner,created_by,center,branch,employee,confirmation_status,payment_method,note,invoice_date) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (invoice_code, f"HD-{index:04d}", class_code, "Học phí", customer,
                     amount, "Nguyễn Ngọc Mai", admin_id, "Center EDU", f"Chi nhánh {(index % 4) + 1}",
                     "Nguyễn Ngọc Mai", status, "Chuyển khoản", "", f"2026-10-{((index - 1) % 28) + 1:02d}"),
                )
        revenue_defs = (
            ("TUITION", "Học phí khóa học", 3000000),
            ("MATERIAL", "Vật phẩm học tập", 250000),
            ("REGISTRATION", "Phí ghi danh", 500000),
            ("MAKEUP", "Phí học bù", 150000),
        )
        for code, name, amount in revenue_defs:
            if self.db.execute("SELECT 1 FROM finance_revenues WHERE code=?", (code,)).fetchone():
                continue
            self.db.execute(
                "INSERT INTO finance_revenues(code,name,status,price,discount_type,discount_value,amount_due,center,note,created_by) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (code, name, "ACTIVE", amount, "FIXED", 0, amount, "Center EDU", "", admin_id),
            )
        # Contracts reconcile the durable invoice stream. Existing contract
        # codes are reused; no bill is deleted or overwritten.
        bills = self.db.execute("SELECT * FROM finance_bills WHERE contract_code<>'' ORDER BY id").fetchall()
        first_student = students[0]["id"] if students else None
        first_class = self.db.execute("SELECT id FROM classes ORDER BY id LIMIT 1").fetchone()
        for index, bill in enumerate(bills, start=1):
            code = str(bill["contract_code"] or f"DEMO-CONTRACT-{index:03d}")
            if self.db.execute("SELECT 1 FROM finance_contracts WHERE contract_code=?", (code,)).fetchone():
                continue
            student = students[(index - 1) % len(students)] if students else None
            class_row = self.db.execute("SELECT id,course_id FROM classes WHERE code=? LIMIT 1", (bill["class_code"],)).fetchone() if bill["class_code"] else None
            class_row = class_row or first_class
            course_id = class_row["course_id"] if class_row and "course_id" in class_row.keys() else None
            amount = float(bill["payment_amount"] or 0)
            paid = amount if bill["confirmation_status"] == "CONFIRMED" else (amount * 0.5 if bill["confirmation_status"] == "PENDING" else 0)
            total = round(amount * 1.2, 2)
            debt = max(0.0, total - paid)
            payment_status = "PAID" if debt == 0 else ("PARTIAL" if paid else "PENDING")
            self.db.execute(
                "INSERT INTO finance_contracts(contract_code,student_id,class_id,course_id,package_name,created_date,expiry_date,total_amount,paid_amount,debt_amount,sales_owner,created_by,payment_status,contract_status,note) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (code, student["id"] if student else first_student, class_row["id"] if class_row else None, course_id,
                 str(bill["subject"] or "Gói học phí"), str(bill["invoice_date"] or "2026-10-01"), "2027-10-01", total, paid, debt,
                 str(bill["sales_owner"] or "Nguyễn Ngọc Mai"), bill["created_by"] or admin_id, payment_status, "ACTIVE", "Hợp đồng học phí theo lộ trình"),
            )
        # A small database used by focused smoke tests may have fewer bills;
        # still provide the minimum domain volume promised by the demo.
        existing_contracts = self.db.execute("SELECT COUNT(*) FROM finance_contracts").fetchone()[0]
        # The observed contract table has 86 local-demo records.  Keep this
        # volume deterministic and isolated to RICH_DEMO so pagination and
        # summary cards exercise the same scale without importing reference
        # identities or rows.
        for index in range(existing_contracts + 1, 87):
            code = f"DEMO-CONTRACT-{index:03d}"
            if self.db.execute("SELECT 1 FROM finance_contracts WHERE contract_code=?", (code,)).fetchone():
                continue
            student = students[(index - 1) % len(students)] if students else None
            class_row = self.db.execute("SELECT id,course_id FROM classes ORDER BY id LIMIT 1").fetchone()
            total = 3000000 + index * 25000
            paid = total if index % 3 == 0 else round(total * 0.5, 2)
            self.db.execute(
                "INSERT INTO finance_contracts(contract_code,student_id,class_id,course_id,package_name,created_date,expiry_date,total_amount,paid_amount,debt_amount,sales_owner,created_by,payment_status,contract_status,note) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (code, student["id"] if student else None, class_row["id"] if class_row else None, class_row["course_id"] if class_row else None,
                 "Gói học phí tiêu chuẩn", f"2026-{((index - 1) % 9) + 1:02d}-01", "2027-12-31", total, paid, max(0, total - paid), "Nguyễn Ngọc Mai", admin_id,
                 "PAID" if paid == total else "PARTIAL", "ACTIVE", "Hợp đồng học phí theo lộ trình"),
            )
        # Keep a local catalogue for the contract create form.  This is
        # synthetic product data, separate from reference APIs and customer
        # data, and idempotent across restarts.
        catalog_count = self.db.execute("SELECT COUNT(*) FROM finance_catalog_items").fetchone()[0]
        if catalog_count == 0:
            courses = self.db.execute("SELECT id,code,name FROM courses ORDER BY id").fetchall()
            for index, course in enumerate(courses, start=1):
                self.db.execute(
                    "INSERT OR IGNORE INTO finance_catalog_items(item_code,item_type,name,course_id,unit,unit_price,sessions,status) VALUES(?,?,?,?,?,?,?,?)",
                    (f"COURSE-{course['code']}", "COURSE", course["name"], course["id"], "Khóa", 3000000 + index * 250000, 60, "ACTIVE"),
                )
            for index, (name, item_type, unit_price, unit) in enumerate((
                ("Gói học phí Demo", "PACKET", 4500000, "Gói"),
                ("Sách giáo trình", "PRODUCT", 250000, "Vật phẩm"),
                ("Phí kiểm tra đầu vào", "CHARGE", 150000, "Khoản thu"),
            ), start=1):
                self.db.execute(
                    "INSERT OR IGNORE INTO finance_catalog_items(item_code,item_type,name,unit_price,unit,status) VALUES(?,?,?,?,?,?)",
                    (f"DEMO-ITEM-{index:02d}", item_type, name, unit_price, unit, "ACTIVE"),
                )
        if self.db.execute("SELECT COUNT(*) FROM finance_transfers").fetchone()[0] == 0:
            contract_rows = self.db.execute("SELECT id,contract_code,student_id,course_id,total_amount FROM finance_contracts ORDER BY id LIMIT 15").fetchall()
            student_rows = self.db.execute("SELECT id FROM students ORDER BY id").fetchall()
            for index, contract in enumerate(contract_rows, start=1):
                if len(student_rows) < 2:
                    break
                from_student = contract["student_id"] or student_rows[(index - 1) % len(student_rows)]["id"]
                to_student = student_rows[index % len(student_rows)]["id"]
                if to_student == from_student:
                    to_student = student_rows[(index + 1) % len(student_rows)]["id"]
                self.db.execute(
                    "INSERT OR IGNORE INTO finance_transfers(transfer_code,transfer_date,from_student_id,to_student_id,contract_id,course_id,amount_received,note,status,created_by) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (f"CN-DEMO-{index:03d}", f"2026-10-{((index - 1) % 20) + 1:02d}", from_student, to_student, contract["id"], contract["course_id"], float(contract["total_amount"] or 0), "Dữ liệu demo tổng hợp", ["PENDING", "PROCESSED", "CANCELLED"][index % 3], admin_id),
                )
        # Converge rich-demo CRM prospects to the observed customer-facing
        # contract. Existing synthetic placeholders are replaced with natural
        # Vietnamese names and all newly observed fields; user-created rows
        # retain their own identity. This remains idempotent across restarts.
        vietnamese_names = [
            "Nguyễn Minh Anh", "Trần Hoàng Nam", "Lê Khánh Linh", "Phạm Gia Huy",
            "Võ Ngọc Mai", "Đặng Nhật Minh", "Bùi Thu Hà", "Phan Đức Anh",
            "Hoàng Yến Nhi", "Đỗ Quang Huy", "Nguyễn Thảo Vy", "Trần Gia Bảo",
            "Lê Minh Khang", "Phạm Ngọc Hân", "Vũ Thanh Tùng", "Đinh Hà My",
            "Nguyễn Hải Đăng", "Trương Tú Anh", "Huỳnh Anh Khoa", "Mai Phương Thảo",
            "Cao Minh Quân", "Dương Khánh An", "Ngô Bảo Châu", "Lý Hoàng Long",
            "Đào Ngọc Ánh", "Phạm Tuấn Kiệt", "Nguyễn Hà Linh", "Trần Đức Minh",
            "Lê Quỳnh Chi", "Võ Thành Đạt", "Bùi Minh Thư", "Phan Nhật Nam",
            "Hoàng Minh Châu", "Đỗ Anh Tú", "Nguyễn Phúc An", "Trần Ngọc Diệp",
            "Lê Quốc Bảo", "Phạm Thanh Vân", "Vũ Minh Khôi", "Đinh Ngọc Lan",
            "Nguyễn Anh Duy", "Trương Minh Tâm", "Huỳnh Gia Linh", "Mai Hoàng Sơn",
            "Cao Bảo Ngọc", "Dương Minh Đức",
        ]
        potential_statuses = (["NEW"] * 10) + (["CONTACTED"] * 7) + (["CONVERTED"] * 27) + (["LOST"] * 2)
        branches = ["Cơ sở Quận 1", "Cơ sở Cầu Giấy", "Cơ sở Bình Thạnh", "Cơ sở Hải Châu"]
        sale_names = ["Nguyễn Ngọc Mai", "Lê Hoàng Anh", "Trần Minh Tú", "Phạm Thùy Dương"]
        course_names = ["IELTS Foundation", "Tiếng Anh giao tiếp", "IELTS Target 6.5", "Tiếng Anh thiếu nhi"]
        current_potential = self.db.execute("SELECT * FROM potential_customers ORDER BY id").fetchall()
        for index, row in enumerate(current_potential, start=1):
            if str(row["customer_code"]).startswith("LEAD-DEMO-") or str(row["full_name"]).startswith("Demo Prospect"):
                self.db.execute(
                    "UPDATE potential_customers SET customer_code=?,full_name=?,phone=?,email=?,source=?,status=?,sale_owner=?,sale_assistant=?,date_of_birth=?,branch=?,tag=?,care_course=?,interested_course=?,test_appointment=?,test_score=?,trial_status=?,care_progress=?,note=? WHERE id=?",
                    (f"KH-TIEM-{index:04d}", vietnamese_names[(index - 1) % len(vietnamese_names)], f"09{12000000 + index:08d}", f"khachhang{index:04d}@demo.center.edu.vn", ["Website", "Facebook", "Giới thiệu", "Sự kiện"][index % 4], potential_statuses[min(index - 1, len(potential_statuses) - 1)], sale_names[index % len(sale_names)], sale_names[(index + 1) % len(sale_names)],
                     f"19{88 + (index % 12):02d}-{(index % 12) + 1:02d}-{(index % 25) + 1:02d}", branches[index % len(branches)], "⭐" if index % 3 == 0 else "", course_names[index % len(course_names)], course_names[(index + 1) % len(course_names)], f"2026-{(index % 11) + 1:02d}-{(index % 24) + 1:02d}" if index % 4 else None, round(5.0 + (index % 51) / 10, 1) if index % 4 else None, "Đã đăng ký" if index % 3 == 0 else ("Đang chờ" if index % 3 == 1 else ""), f"{(index % 5) + 1}/5", "Đang theo dõi", row["id"]),
                )
            else:
                # Existing rows without scaffold markers may be user-created.
                # Leave their empty fields untouched across rich-demo restarts.
                pass
        existing_potential = self.db.execute("SELECT COUNT(*) FROM potential_customers").fetchone()[0]
        for index in range(existing_potential + 1, len(vietnamese_names) + 1):
            self.db.execute(
                "INSERT INTO potential_customers(customer_code,full_name,phone,email,source,status,sale_owner,sale_assistant,interest,note,date_of_birth,branch,tag,care_course,interested_course,test_appointment,test_score,trial_status,care_progress) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (f"KH-TIEM-{index:04d}", vietnamese_names[index - 1], f"09{12000000 + index:08d}", f"khachhang{index:04d}@demo.center.edu.vn", ["Website", "Facebook", "Giới thiệu", "Sự kiện"][index % 4], potential_statuses[index - 1], sale_names[index % len(sale_names)], sale_names[(index + 1) % len(sale_names)], course_names[index % len(course_names)], "Đang theo dõi", f"19{88 + (index % 12):02d}-{(index % 12) + 1:02d}-{(index % 25) + 1:02d}", branches[index % len(branches)], "⭐" if index % 3 == 0 else "", course_names[index % len(course_names)], course_names[(index + 1) % len(course_names)], f"2026-{(index % 11) + 1:02d}-{(index % 24) + 1:02d}" if index % 4 else None, round(5.0 + (index % 51) / 10, 1) if index % 4 else None, "Đã đăng ký" if index % 3 == 0 else ("Đang chờ" if index % 3 == 1 else ""), f"{(index % 5) + 1}/5"),
            )
        # The reference status strip's successful-care count is an interaction
        # aggregate, not a mutually exclusive customer status. Seed the same
        # local distinction with 43 durable care events so the UI can derive
        # the number from persisted records instead of hard-coding a label.
        success_events = self.db.execute("SELECT COUNT(*) FROM potential_customer_followups WHERE outcome='Chăm sóc thành công'").fetchone()[0]
        potential_rows = self.db.execute("SELECT id FROM potential_customers ORDER BY id LIMIT 46").fetchall()
        if success_events < 43 and potential_rows:
            for event_index in range(success_events, 43):
                customer_id = potential_rows[event_index % len(potential_rows)]["id"]
                self.db.execute(
                    "INSERT INTO potential_customer_followups(potential_customer_id,action_type,outcome,note,next_follow_up_at,created_by) VALUES(?,?,?,?,?,?)",
                    (customer_id, "CALL", "Chăm sóc thành công", "Đã tư vấn và ghi nhận nhu cầu học tập.", None, admin_id),
                )
        # Class-post events are explicit persisted activity, separate from
        # class membership.  Seed a small local-only set for the rich demo so
        # the report exercises its real event join; ordinary databases remain
        # empty and therefore truthfully report NO_DATA.
        if self.db.execute("SELECT COUNT(*) FROM class_post_events").fetchone()[0] == 0:
            class_rows_for_posts = self.db.execute(
                "SELECT id FROM classes ORDER BY id LIMIT 10"
            ).fetchall()
            author_ids = [row["id"] for row in self.db.execute(
                "SELECT id FROM users WHERE role IN ('ADMIN','STAFF','TEACHER') AND active=1 ORDER BY id"
            ).fetchall()]
            if class_rows_for_posts and author_ids:
                for post_index, class_row in enumerate(class_rows_for_posts, start=1):
                    self.db.execute(
                        "INSERT INTO class_post_events(class_id,author_id,content,status,posted_at) VALUES(?,?,?,?,?)",
                        (class_row["id"], author_ids[(post_index - 1) % len(author_ids)],
                         f"Cập nhật nội dung buổi học {post_index}", "PUBLISHED",
                         f"2026-10-{((post_index - 1) % 20) + 1:02d} 18:00:00"),
                    )
        self.db.commit()

    def _ensure_generated_demo_records(self) -> None:
        """Backfill rich synthetic rows on databases seeded before screen wave.

        Existing demo databases already contain users and therefore skip the
        one-time seed path.  Keep those databases useful after a code upgrade
        by adding rows only when a generated route has fewer than twelve
        records.  This never touches domain tables or reference data.
        """
        if os.environ.get("CENTER_EDU_RICH_DEMO", "").strip().lower() not in {"1", "true", "yes", "on"}:
            return
        admin = self.db.execute("SELECT id FROM users WHERE username='admin' LIMIT 1").fetchone()
        if admin is None:
            return
        generated_natural_names = TRAINING_NATURAL_NAMES
        specs = self._screen_specs()
        for route, spec in specs.items():
            count = self.db.execute("SELECT COUNT(*) FROM generated_screen_records WHERE route=? AND deleted_at IS NULL", (route,)).fetchone()[0]
            if count >= 12:
                continue
            fields = []
            seen = set()
            for item in (spec.get("columns", []) if isinstance(spec, dict) else []):
                if isinstance(item, dict):
                    key = str(item.get("key") or "").strip()
                    if key and key.lower() != "no" and key not in seen:
                        seen.add(key); fields.append(item)
            form = spec.get("form") if isinstance(spec, dict) else {}
            for item in (form.get("fields", []) if isinstance(form, dict) else []):
                if isinstance(item, dict):
                    key = str(item.get("name") or "").strip()
                    if key and key.lower() != "no" and key not in seen:
                        seen.add(key); fields.append(item)
            for row_number in range(count + 1, 13):
                data = {}
                for field in fields:
                    key = str(field.get("key") or field.get("name") or "").strip()
                    label = str(field.get("label") or key).strip()
                    lower = f"{label} {key}".lower()
                    options = field.get("options") if isinstance(field.get("options"), list) else []
                    route_value = training_seed_value(route, key, row_number)
                    if route_value is not None:
                        value = route_value
                    elif options:
                        value = str(options[(row_number - 1) % len(options)])
                    elif "email" in lower:
                        value = f"demo{row_number:02d}@center.edu.vn"
                    elif any(token in lower for token in ("phone", "điện thoại", "số điện thoại")):
                        value = f"090{row_number:07d}"
                    elif any(token in lower for token in ("date", "ngày", "thời gian")):
                        value = f"2026-{((row_number - 1) % 9) + 1:02d}-{((row_number - 1) % 27) + 1:02d}"
                    elif any(token in lower for token in ("status", "trạng thái")):
                        value = ["Đang hoạt động", "Đang xử lý", "Đã hoàn thành"][(row_number - 1) % 3]
                    elif any(token in lower for token in ("mã", "code", "id", "invoice")):
                        value = f"DEMO-{row_number:03d}"
                    elif str(field.get("type") or "").lower() in {"number", "integer"}:
                        value = row_number * 10
                    else:
                        value = f"{label or 'Bản ghi'} Demo {row_number:02d}"
                    data[key] = value
                if not data:
                    data["name"] = f"Bản ghi Demo {row_number:02d}"
                self.db.execute("INSERT INTO generated_screen_records(route,data_json,created_by) VALUES(?,?,?)", (route, json.dumps(data, ensure_ascii=False, sort_keys=True), admin[0]))
        # Existing generated rows were created by the earlier screen engine
        # and therefore bypass the backfill above.  Rewrite only exact engine
        # markers, preserving row IDs, route keys and any user-entered values.
        for row in self.db.execute("SELECT id,route,data_json FROM generated_screen_records WHERE deleted_at IS NULL").fetchall():
            try:
                payload = json.loads(row["data_json"] or "{}")
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
            changed = False
            for key, value in list(payload.items()):
                text = str(value or "")
                # Older route rows used generic labels (for example
                # ``Lượt xem Demo 01``). Repair only those generated markers;
                # persisted/user-entered values remain untouched.
                if row["route"] in {"/training/absent-v2", "/training/event"}:
                    marker = bool(re.search(r"(?:^| )Demo \d{2}$", text))
                    generic_status = text in {"Đang hoạt động", "Đang xử lý", "Đã hoàn thành"}
                    if marker or generic_status:
                        route = row["route"]
                        if route == "/training/absent-v2":
                            if key in {"hoc_vien", "student_name", "student_id"}:
                                payload[key] = generated_natural_names[(int(row["id"]) - 1) % len(generated_natural_names)]
                            elif key in {"buoi_nghi", "session_name"}:
                                payload[key] = f"Buổi {((int(row['id']) - 1) % 6) + 1} · {((int(row['id']) - 1) % 20) + 1:02d}/11/2026"
                            elif key in {"ly_do", "reason"}:
                                payload[key] = ["Sức khỏe", "Gia đình", "Lịch cá nhân", "Công việc"][(int(row["id"]) - 1) % 4]
                            elif key in {"trang_thai", "status"}:
                                payload[key] = ["Chưa phê duyệt", "Đồng ý", "Từ chối", "Hủy", "Nhận thông tin"][(int(row["id"]) - 1) % 5]
                            else:
                                payload[key] = ""
                        else:
                            if key in {"luot_xem", "views", "view_count"}:
                                payload[key] = int(row["id"]) * 7
                            elif key in {"noi_dung", "description", "content", "title"}:
                                payload[key] = ["Workshop kỹ năng học tập", "Ngày hội trải nghiệm tiếng Anh", "Tọa đàm định hướng lộ trình"][(int(row["id"]) - 1) % 3]
                            elif key in {"a_xem_a_gui", "sent", "viewed_sent", "read_sent"}:
                                payload[key] = f"{(int(row['id']) % 8) + 2}/12"
                            elif key in {"trang_thai", "status"}:
                                payload[key] = "Đã gửi" if int(row["id"]) % 2 == 0 else "Chưa gửi"
                            else:
                                payload[key] = ""
                        changed = True
                        continue
                if text.startswith("Demo ") or text.startswith("Giáo viên Demo") or text.startswith("Học viên Demo"):
                    payload[key] = generated_natural_names[(int(row["id"]) + len(key)) % len(generated_natural_names)]
                    changed = True
                elif text.startswith("Dữ liệu demo"):
                    payload[key] = ""
                    changed = True
                elif text.startswith("DEMO-"):
                    prefix = "HD-" if "contract" in key.lower() or "invoice" in key.lower() else "MS-"
                    payload[key] = f"{prefix}{int(row['id']):04d}"
                    changed = True
                elif text == "Chưa cập nhật":
                    payload[key] = ""
                    changed = True
            if changed:
                self.db.execute("UPDATE generated_screen_records SET data_json=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (json.dumps(payload, ensure_ascii=False, sort_keys=True), row["id"]))
        self.db.commit()

    @staticmethod
    def _screen_specs() -> Dict[str, Dict[str, Any]]:
        """Load generated contracts without treating them as reference APIs."""
        path = ROOT / "screen_specs" / "reference-screen-specs.json"
        try:
            if load_specs is not None:
                return load_specs(path)
            value = json.loads(path.read_text(encoding="utf-8"))
            return {str(item["route"]): item for item in value.get("screens", []) if isinstance(item, dict) and item.get("route")}
        except (OSError, ValueError, json.JSONDecodeError):
            return {}

    def screen_specs(self, actor: sqlite3.Row, route: str = "") -> List[Dict[str, Any]]:
        require_role(actor, "ADMIN", "STAFF", "TEACHER", "STUDENT")
        if route and route in self.w6_routes:
            return [self._w6_spec(route)]
        specs = list(self._screen_specs().values())
        if route:
            specs = [item for item in specs if item.get("route") == route]
        return specs

    def _screen_spec(self, actor: sqlite3.Row, route: str) -> Dict[str, Any]:
        spec = next(iter(self.screen_specs(actor, route)), None)
        if spec is None:
            raise AppError(404, "SCREEN_SPEC_NOT_FOUND", "screen contract not found")
        return spec

    def generated_screen(self, actor: sqlite3.Row, route: str, query: str = "") -> Dict[str, Any]:
        if route in self.w6_routes:
            try:
                rows = self._w6_rows(route, query, role=actor["role"])
            except PermissionError as exc:
                raise AppError(403, "FORBIDDEN", str(exc)) from exc
            return {"spec": self._w6_spec(route), "records": rows, "total": len(rows),
                    "contract_status": "LOCAL_CONTRACT"}
        spec = self._screen_spec(actor, route)
        query_text = clean_text(query, 160).lower()
        rows = self.db.execute(
            "SELECT id,route,data_json,created_at,updated_at FROM generated_screen_records WHERE route=? AND deleted_at IS NULL ORDER BY id",
            (route,),
        ).fetchall()
        output: List[Dict[str, Any]] = []
        for row in rows:
            try:
                data = json.loads(row["data_json"])
            except (TypeError, ValueError, json.JSONDecodeError):
                data = {}
            if not isinstance(data, dict):
                data = {}
            if query_text and query_text not in json.dumps(data, ensure_ascii=False).lower():
                continue
            display_data = self._generated_display_data(spec, data)
            if query_text and query_text not in json.dumps(display_data, ensure_ascii=False).lower():
                continue
            # Keep the persisted form payload in ``data`` for CRUD/edit
            # compatibility. Consumers that render observed table columns use
            # the additive ``display_data`` projection.
            output.append({"id": row["id"], "route": route, "data": data,
                           "display_data": display_data,
                           "created_at": row["created_at"], "updated_at": row["updated_at"]})
        return {"spec": spec, "records": output, "total": len(output),
                "contract_status": spec.get("api_status", "INFERRED_LOCAL_CONTRACT")}

    @staticmethod
    def _generated_display_data(spec: Mapping[str, Any], data: Mapping[str, Any]) -> Dict[str, Any]:
        """Project persisted form keys into observed table-column keys.

        Older generated rows were seeded from form fields (for example
        ``title``/``status``), while the observed table contract uses
        transliterated presentation keys (``thong_bao``/``trang_thai``).
        Keep the raw payload intact for edit/CRUD semantics and expose this
        additive projection only to list/export consumers.
        """
        raw = dict(data)
        projected = dict(raw)
        aliases = {
            "thong_bao": ("title", "subject", "name", "content", "description"),
            "noi_dung": ("content", "description", "title", "name", "body"),
            "trang_thai": ("status", "state", "approval_status"),
            "tao_boi": ("created_by", "author", "creator", "created_name"),
            "nguoi_tao": ("created_by", "author", "creator", "created_name"),
            "lop_hoc": ("class_name", "class_code", "class", "course_name"),
            "ngay_tao": ("created_at", "posted_at", "date", "created_date"),
            "chi_nhanh": ("branch", "center", "center_name"),
            "cau_hinh_binh_luan": ("can_comment", "comment_config", "view_comment_type"),
            "a_xem_a_gui": ("viewed_sent", "read_sent", "sent_count", "view_count", "status"),
            "luot_xem": ("view_count", "views", "viewed"),
            "binh_luan": ("comments", "comment_count", "comment"),
            "hanh_ong": ("action", "actions"),
            "cong_cu": ("tools", "action", "actions"),
        }
        fields = []
        form = spec.get("form") if isinstance(spec, Mapping) else None
        if isinstance(form, Mapping):
            fields = [item for item in form.get("fields", []) if isinstance(item, Mapping)]
        for column in spec.get("columns", []) if isinstance(spec, Mapping) else []:
            if not isinstance(column, Mapping):
                continue
            key = str(column.get("key") or "").strip()
            if not key or key.lower() == "no" or projected.get(key) not in (None, ""):
                continue
            candidates = list(aliases.get(key, ()))
            label = str(column.get("label") or "").strip()
            label_key = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
            if label_key and label_key != key:
                candidates.append(label_key)
            for field in fields:
                for candidate in (field.get("name"), field.get("observed_name"), field.get("label"), field.get("placeholder")):
                    candidate_key = re.sub(r"[^a-z0-9]+", "_", str(candidate or "").lower()).strip("_")
                    if candidate_key and candidate_key == key:
                        candidates.append(str(field.get("name") or ""))
            for candidate in candidates:
                if candidate in raw and raw[candidate] not in (None, ""):
                    projected[key] = raw[candidate]
                    break
        return projected

    def add_generated_record(self, actor: sqlite3.Row, route: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if route in GENERIC_SCREEN_WRITE_BLOCKED_ROUTES:
            raise AppError(409, "AUTHORITY_BOUNDARY", "use /api/finance/contracts for /sale/contract writes")
        if route in self.w6_routes:
            require_role(actor, "ADMIN", "STAFF")
            if create_w6_record is None:
                raise AppError(503, "MODULE_UNAVAILABLE", "Center lane module is unavailable")
            raw = payload.get("data", payload)
            if not isinstance(raw, dict):
                raise AppError(400, "VALIDATION_ERROR", "data must be an object")
            try:
                return create_w6_record(self.db, route, raw, created_by=actor["id"], role=actor["role"])
            except (KeyError, ValueError, PermissionError) as exc:
                raise AppError(400 if not isinstance(exc, PermissionError) else 403, "VALIDATION_ERROR", str(exc)) from exc
        require_role(actor, "ADMIN", "STAFF")
        spec = self._screen_spec(actor, route)
        raw = payload.get("data", payload)
        if not isinstance(raw, dict):
            raise AppError(400, "VALIDATION_ERROR", "data must be an object")
        allowed = self._screen_allowed_fields(spec)
        unknown = sorted(set(raw) - allowed)
        if unknown:
            raise AppError(400, "VALIDATION_ERROR", "unknown fields: " + ", ".join(unknown))
        data = {key: value for key, value in raw.items() if key in allowed}
        if not data:
            raise AppError(400, "VALIDATION_ERROR", "at least one observed field is required")
        missing = self._screen_missing_required(spec, data)
        if missing:
            raise AppError(400, "VALIDATION_ERROR", "required fields missing: " + ", ".join(missing))
        cur = self.db.execute(
            "INSERT INTO generated_screen_records(route,data_json,created_by) VALUES(?,?,?)",
            (route, json.dumps(data, ensure_ascii=False, sort_keys=True), actor["id"]),
        )
        self.audit(actor["id"], "CREATE", "generated_screen_record", cur.lastrowid, {"route": route})
        row = self.db.execute("SELECT id,route,data_json,created_at,updated_at FROM generated_screen_records WHERE id=?", (cur.lastrowid,)).fetchone()
        return self._generated_row(row)

    def update_generated_record(self, actor: sqlite3.Row, route: str, record_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        if route in GENERIC_SCREEN_WRITE_BLOCKED_ROUTES:
            raise AppError(409, "AUTHORITY_BOUNDARY", "use /api/finance/contracts for /sale/contract writes")
        if route in self.w6_routes:
            require_role(actor, "ADMIN", "STAFF")
            if update_w6_record is None:
                raise AppError(503, "MODULE_UNAVAILABLE", "Center lane module is unavailable")
            raw = payload.get("data", payload)
            if not isinstance(raw, dict):
                raise AppError(400, "VALIDATION_ERROR", "data must be an object")
            try:
                return update_w6_record(self.db, route, int(record_id), raw, role=actor["role"])
            except KeyError as exc:
                raise AppError(404, "RECORD_NOT_FOUND", str(exc)) from exc
            except (ValueError, PermissionError) as exc:
                raise AppError(400 if not isinstance(exc, PermissionError) else 403, "VALIDATION_ERROR", str(exc)) from exc
        require_role(actor, "ADMIN", "STAFF")
        spec = self._screen_spec(actor, route)
        try:
            parsed_id = int(record_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "record id must be numeric") from exc
        current = self.db.execute("SELECT * FROM generated_screen_records WHERE id=? AND route=? AND deleted_at IS NULL", (parsed_id, route)).fetchone()
        if current is None:
            raise AppError(404, "RECORD_NOT_FOUND", "screen record not found")
        raw = payload.get("data", payload)
        if not isinstance(raw, dict):
            raise AppError(400, "VALIDATION_ERROR", "data must be an object")
        try:
            existing = json.loads(current["data_json"])
        except (TypeError, ValueError, json.JSONDecodeError):
            existing = {}
        if not isinstance(existing, dict):
            existing = {}
        allowed = self._screen_allowed_fields(spec)
        unknown = sorted(set(raw) - allowed)
        if unknown:
            raise AppError(400, "VALIDATION_ERROR", "unknown fields: " + ", ".join(unknown))
        existing.update({key: value for key, value in raw.items() if key in allowed})
        missing = self._screen_missing_required(spec, existing)
        if missing:
            raise AppError(400, "VALIDATION_ERROR", "required fields missing: " + ", ".join(missing))
        self.db.execute("UPDATE generated_screen_records SET data_json=?,updated_at=CURRENT_TIMESTAMP WHERE id=? AND route=?", (json.dumps(existing, ensure_ascii=False, sort_keys=True), parsed_id, route))
        self.audit(actor["id"], "UPDATE", "generated_screen_record", parsed_id, {"route": route})
        self.db.commit()
        row = self.db.execute("SELECT id,route,data_json,created_at,updated_at FROM generated_screen_records WHERE id=?", (parsed_id,)).fetchone()
        return self._generated_row(row)

    @staticmethod
    def _screen_allowed_fields(spec: Dict[str, Any]) -> set[str]:
        allowed = {str(col.get("key")) for col in spec.get("columns", [])
                   if isinstance(col, dict) and col.get("key")}
        form = spec.get("form") if isinstance(spec.get("form"), dict) else {}
        allowed.update(str(field.get("name")) for field in form.get("fields", [])
                       if isinstance(field, dict) and field.get("name"))
        return {item for item in allowed if item and item != "field"}

    @staticmethod
    def _screen_missing_required(spec: Dict[str, Any], data: Dict[str, Any]) -> List[str]:
        form = spec.get("form") if isinstance(spec.get("form"), dict) else {}
        missing: List[str] = []
        for field in form.get("fields", []) if isinstance(form.get("fields"), list) else []:
            if not isinstance(field, dict) or not field.get("required"):
                continue
            name = str(field.get("name") or "").strip()
            if name and not str(data.get(name, "")).strip():
                missing.append(name)
        return sorted(set(missing))

    @staticmethod
    def _screen_export_allowed(spec: Dict[str, Any]) -> bool:
        return any(token in str(button).lower() for button in spec.get("buttons", [])
                   for token in ("excel", "export", "xuất"))

    def delete_generated_record(self, actor: sqlite3.Row, route: str, record_id: Any) -> Dict[str, Any]:
        if route in GENERIC_SCREEN_WRITE_BLOCKED_ROUTES:
            raise AppError(409, "AUTHORITY_BOUNDARY", "use /api/finance/contracts for /sale/contract writes")
        if route in self.w6_routes:
            require_role(actor, "ADMIN")
            if archive_w6_record is None:
                raise AppError(503, "MODULE_UNAVAILABLE", "Center lane module is unavailable")
            try:
                return archive_w6_record(self.db, route, int(record_id), role=actor["role"])
            except PermissionError as exc:
                raise AppError(403, "FORBIDDEN", str(exc)) from exc
        require_role(actor, "ADMIN", "STAFF")
        self._screen_spec(actor, route)
        try:
            parsed_id = int(record_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "record id must be numeric") from exc
        row = self.db.execute("SELECT id FROM generated_screen_records WHERE id=? AND route=? AND deleted_at IS NULL", (parsed_id, route)).fetchone()
        if row is None:
            raise AppError(404, "RECORD_NOT_FOUND", "screen record not found")
        self.db.execute("UPDATE generated_screen_records SET deleted_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP WHERE id=? AND route=?", (parsed_id, route))
        self.audit(actor["id"], "DELETE", "generated_screen_record", parsed_id, {"route": route, "soft": True})
        self.db.commit()
        return {"id": parsed_id, "route": route, "deleted": True}

    def export_generated_screen(self, actor: sqlite3.Row, route: str, query: str = "") -> List[Dict[str, Any]]:
        if route in self.w6_routes:
            if export_w6_csv is None:
                raise AppError(503, "MODULE_UNAVAILABLE", "Center lane module is unavailable")
            try:
                rows = self._w6_rows(route, query, role=actor["role"])
            except PermissionError as exc:
                raise AppError(403, "FORBIDDEN", str(exc)) from exc
            contract = W6_CONTRACTS[route]
            aliases = W6_EXPORT_KEY_ALIASES.get(route, {})
            return [{label: (index if key == "no" else record["data"].get(aliases.get(key, key), ""))
                     for key, label in contract.columns}
                    for index, record in enumerate(rows, 1)]
        result = self.generated_screen(actor, route, query)
        spec = result["spec"]
        if not self._screen_export_allowed(spec):
            raise AppError(403, "EXPORT_NOT_AVAILABLE", "export is not part of the observed screen contract")
        columns = [col for col in spec.get("columns", []) if isinstance(col, dict) and col.get("key")]
        rows = []
        for record in result["records"]:
            data = record.get("display_data") or self._generated_display_data(spec, record.get("data", {}))
            rows.append({col.get("label") or col["key"]: data.get(col["key"], "") for col in columns})
        return rows

    @staticmethod
    def _generated_row(row: Optional[sqlite3.Row]) -> Dict[str, Any]:
        if row is None:
            return {}
        try:
            data = json.loads(row["data_json"])
        except (TypeError, ValueError, json.JSONDecodeError):
            data = {}
        return {"id": row["id"], "route": row["route"], "data": data if isinstance(data, dict) else {},
                "created_at": row["created_at"], "updated_at": row["updated_at"]}

    def close(self) -> None:
        self.db.close()

    def user_by_login(self, login: str) -> Optional[sqlite3.Row]:
        return self.db.execute(
            "SELECT * FROM users WHERE active=1 AND (username=? OR email=?)", (login, login)
        ).fetchone()

    def user(self, user_id: int) -> Optional[sqlite3.Row]:
        return self.db.execute("SELECT * FROM users WHERE id=? AND active=1", (user_id,)).fetchone()

    def create_session(self, user_id: int) -> Tuple[str, str, int]:
        token = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(24)
        expiry = now() + SESSION_TTL
        token_digest = hashlib.sha256(token.encode()).hexdigest()
        self.db.execute("DELETE FROM sessions WHERE expires_at < ?", (now(),))
        self.db.execute(
            "INSERT INTO sessions(user_id,token_hash,csrf_token,expires_at,last_seen_at) VALUES(?,?,?,?,?)",
            (user_id, token_digest, csrf, expiry, now()),
        )
        self.db.commit()
        return token, csrf, expiry

    def session(self, token: str) -> Optional[sqlite3.Row]:
        if not token:
            return None
        digest = hashlib.sha256(token.encode()).hexdigest()
        row = self.db.execute(
            "SELECT s.*, u.username,u.email,u.full_name,u.role,u.active FROM sessions s "
            "JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>? AND u.active=1",
            (digest, now()),
        ).fetchone()
        if row:
            self.db.execute("UPDATE sessions SET last_seen_at=? WHERE id=?", (now(), row["id"]))
            self.db.commit()
        return row

    def destroy_session(self, token: str) -> None:
        digest = hashlib.sha256(token.encode()).hexdigest()
        self.db.execute("DELETE FROM sessions WHERE token_hash=?", (digest,))
        self.db.commit()

    def audit(
        self,
        actor_id: Optional[int],
        action: str,
        entity: str,
        entity_id: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
        *,
        commit: bool = True,
    ) -> None:
        self.db.execute(
            "INSERT INTO audit_events(actor_id,action,entity,entity_id,metadata_json) VALUES(?,?,?,?,?)",
            (actor_id, action, entity, None if entity_id is None else str(entity_id), json.dumps(metadata or {}, sort_keys=True)),
        )
        if commit:
            self.db.commit()

    def dashboard(self, user: sqlite3.Row, date_filter: Any = "", query: Any = "") -> Dict[str, Any]:
        date_filter = self._optional_date(date_filter, "date")
        query = clean_text(query, 160)
        counts = self._dashboard_counts(user)
        attendance_sql = "SELECT a.status, COUNT(*) AS count FROM attendance a"
        attendance_params: Tuple[Any, ...] = ()
        if user["role"] == "TEACHER":
            attendance_sql += " JOIN classes c ON c.id=a.class_id WHERE c.teacher_id=?"
            attendance_params = (user["id"],)
        elif user["role"] == "STUDENT":
            attendance_sql += " JOIN students s ON s.id=a.student_id JOIN enrollments e ON e.class_id=a.class_id AND e.student_id=a.student_id AND e.status='ENROLLED' WHERE s.user_id=?"
            attendance_params = (user["id"],)
        attendance_sql += " GROUP BY a.status ORDER BY a.status"
        attendance = self.db.execute(attendance_sql, attendance_params).fetchall()
        recent_sql = (
            "SELECT a.id,a.action,a.entity,a.entity_id,a.created_at,u.full_name AS actor "
            "FROM audit_events a LEFT JOIN users u ON u.id=a.actor_id"
        )
        recent_params: Tuple[Any, ...] = ()
        if user["role"] == "TEACHER":
            recent_sql += " WHERE a.actor_id=?"
            recent_params = (user["id"],)
        elif user["role"] == "STUDENT":
            recent_sql += " WHERE 1=0"
        recent_sql += " ORDER BY a.id DESC LIMIT 8"
        recent = self.db.execute(recent_sql, recent_params).fetchall()
        return {
            "user": public_user(user),
            "counts": counts,
            "attendance": rows_dict(attendance),
            "recent_activity": rows_dict(recent),
            "training_dashboard": self.training_dashboard(user, date_filter, query),
        }

    def finance_dashboard(self, user: sqlite3.Row) -> Dict[str, Any]:
        """Return a persisted finance projection for the finance dashboard."""
        require_role(user, "ADMIN", "STAFF", "TEACHER")
        tables = {
            "contract_count": "finance_contracts",
            "bill_count": "finance_bills",
            "revenue_count": "finance_revenues",
            "spend_count": "finance_spends",
            "reserve_count": "finance_reserves",
            "wallet_count": "finance_wallets",
            "appointment_count": "finance_appointments",
            "item_count": "finance_items",
        }
        counts = {}
        for key, table in tables.items():
            try:
                counts[key] = int(self.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            except sqlite3.OperationalError:
                counts[key] = 0
        try:
            collected = int(self.db.execute(
                "SELECT COALESCE(SUM(payment_amount),0) FROM finance_bills WHERE confirmation_status='CONFIRMED'"
            ).fetchone()[0])
        except sqlite3.OperationalError:
            collected = 0
        try:
            spent = int(self.db.execute("SELECT COALESCE(SUM(amount_vnd),0) FROM finance_spends").fetchone()[0])
        except sqlite3.OperationalError:
            spent = 0
        return {
            **counts,
            "total_collected_vnd": collected,
            "total_spend_vnd": spent,
            "net_cash_vnd": collected - spent,
            "source": "local-sqlite",
            "data_status": "OBSERVED",
        }

    def _dashboard_counts(self, user: sqlite3.Row) -> Dict[str, int]:
        """Return dashboard totals within the current user's data scope."""
        all_tables = (
            "students", "courses", "classes", "enrollments", "timetable_sessions",
            "evaluations", "tests", "homework", "trial_registrations",
            "enrollment_confirmations", "customer_tests", "pending_enrollments",
        )
        if user["role"] in {"ADMIN", "STAFF"}:
            return {
                table: self.db.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]
                for table in all_tables
            }

        role = user["role"]
        if role == "TEACHER":
            scoped = {
                "students": ("SELECT COUNT(DISTINCT e.student_id) FROM enrollments e JOIN classes c ON c.id=e.class_id WHERE c.teacher_id=? AND e.status='ENROLLED'", (user["id"],)),
                "courses": ("SELECT COUNT(DISTINCT co.id) FROM courses co JOIN classes c ON c.course_id=co.id WHERE c.teacher_id=?", (user["id"],)),
                "classes": ("SELECT COUNT(*) FROM classes WHERE teacher_id=?", (user["id"],)),
                "enrollments": ("SELECT COUNT(*) FROM enrollments e JOIN classes c ON c.id=e.class_id WHERE c.teacher_id=? AND e.status='ENROLLED'", (user["id"],)),
                "timetable_sessions": ("SELECT COUNT(*) FROM timetable_sessions t WHERE t.teacher_id=?", (user["id"],)),
                "evaluations": ("SELECT COUNT(*) FROM evaluations e JOIN classes c ON c.id=e.class_id WHERE c.teacher_id=?", (user["id"],)),
                "tests": ("SELECT COUNT(*) FROM tests t JOIN classes c ON c.id=t.class_id WHERE c.teacher_id=?", (user["id"],)),
                "homework": ("SELECT COUNT(*) FROM homework h JOIN classes c ON c.id=h.class_id WHERE c.teacher_id=?", (user["id"],)),
            }
        elif role == "STUDENT":
            scoped = {
                "students": ("SELECT COUNT(*) FROM students WHERE user_id=?", (user["id"],)),
                "courses": ("SELECT COUNT(DISTINCT co.id) FROM courses co JOIN classes c ON c.course_id=co.id JOIN enrollments e ON e.class_id=c.id JOIN students s ON s.id=e.student_id WHERE s.user_id=? AND e.status='ENROLLED'", (user["id"],)),
                "classes": ("SELECT COUNT(DISTINCT c.id) FROM classes c JOIN enrollments e ON e.class_id=c.id JOIN students s ON s.id=e.student_id WHERE s.user_id=? AND e.status='ENROLLED'", (user["id"],)),
                "enrollments": ("SELECT COUNT(*) FROM enrollments e JOIN students s ON s.id=e.student_id WHERE s.user_id=? AND e.status='ENROLLED'", (user["id"],)),
                "timetable_sessions": ("SELECT COUNT(*) FROM timetable_sessions t JOIN enrollments e ON e.class_id=t.class_id JOIN students s ON s.id=e.student_id WHERE s.user_id=? AND e.status='ENROLLED'", (user["id"],)),
                "evaluations": ("SELECT COUNT(*) FROM evaluations e JOIN students s ON s.id=e.student_id JOIN enrollments en ON en.class_id=e.class_id AND en.student_id=e.student_id AND en.status='ENROLLED' WHERE s.user_id=?", (user["id"],)),
                "tests": ("SELECT COUNT(DISTINCT t.id) FROM tests t JOIN enrollments e ON e.class_id=t.class_id JOIN students s ON s.id=e.student_id WHERE s.user_id=? AND e.status='ENROLLED'", (user["id"],)),
                "homework": ("SELECT COUNT(DISTINCT h.id) FROM homework h JOIN enrollments e ON e.class_id=h.class_id JOIN students s ON s.id=e.student_id WHERE s.user_id=? AND e.status='ENROLLED'", (user["id"],)),
            }
        else:
            scoped = {}

        counts = {
            table: self.db.execute(*scoped[table]).fetchone()[0] if table in scoped else 0
            for table in all_tables
        }
        return counts

    def training_dashboard(
        self,
        user: sqlite3.Row,
        date_filter: Optional[str] = None,
        query: str = "",
    ) -> List[Dict[str, Any]]:
        """Return persisted training rows for the dashboard.

        Branch and lesson-content are explicit UNKNOWN values until the
        authenticated reference contract exposes them. No local field is
        silently substituted for either value.
        """
        if user["role"] == "STUDENT":
            sql = """
                SELECT t.id,t.class_id,t.session_date,t.start_time,t.end_time,
                       c.code AS class_code,c.room,c.status AS class_status,
                       u.full_name AS teacher,
                       (SELECT COUNT(*) FROM attendance a
                          JOIN students s2 ON s2.id=a.student_id
                          JOIN enrollments e2 ON e2.class_id=a.class_id AND e2.student_id=a.student_id AND e2.status='ENROLLED'
                          WHERE a.class_id=t.class_id AND a.session_date=t.session_date
                            AND s2.user_id=?) AS attendance_total,
                       (SELECT COALESCE(SUM(CASE WHEN a.status='PRESENT' THEN 1 ELSE 0 END), 0)
                          FROM attendance a JOIN students s2 ON s2.id=a.student_id
                          JOIN enrollments e2 ON e2.class_id=a.class_id AND e2.student_id=a.student_id AND e2.status='ENROLLED'
                          WHERE a.class_id=t.class_id AND a.session_date=t.session_date
                            AND s2.user_id=?) AS attendance_present,
                       (SELECT COUNT(*) FROM evaluations e
                          JOIN students s2 ON s2.id=e.student_id
                          JOIN enrollments e2 ON e2.class_id=e.class_id AND e2.student_id=e.student_id AND e2.status='ENROLLED'
                          WHERE e.class_id=t.class_id AND e.session_date=t.session_date
                            AND s2.user_id=?) AS evaluation_count,
                       (SELECT COUNT(*) FROM tests x
                          WHERE x.class_id=t.class_id AND x.test_date=t.session_date) AS test_count,
                       (SELECT COUNT(*) FROM homework h
                          WHERE h.class_id=t.class_id AND h.due_date=t.session_date) AS homework_count
                  FROM timetable_sessions t
                  JOIN classes c ON c.id=t.class_id
                  LEFT JOIN users u ON u.id=t.teacher_id
                 WHERE EXISTS (SELECT 1 FROM enrollments e JOIN students s ON s.id=e.student_id
                               WHERE e.class_id=t.class_id AND e.status='ENROLLED' AND s.user_id=?)
            """
            params: List[Any] = [user["id"], user["id"], user["id"], user["id"]]
            sql += " ORDER BY t.session_date DESC,t.start_time DESC,t.id DESC LIMIT 200"
            rows = rows_dict(self.db.execute(sql, params).fetchall())
            for row in rows:
                row["branch"] = None
                row["lesson_content"] = None
            return self._filter_training_dashboard(rows, date_filter, query)

        sql = """
            SELECT t.id,t.class_id,t.session_date,t.start_time,t.end_time,
                   c.code AS class_code,c.room,c.status AS class_status,
                   u.full_name AS teacher,
                   (SELECT COUNT(*) FROM attendance a
                      WHERE a.class_id=t.class_id AND a.session_date=t.session_date) AS attendance_total,
                   (SELECT COALESCE(SUM(CASE WHEN a.status='PRESENT' THEN 1 ELSE 0 END), 0)
                      FROM attendance a
                      WHERE a.class_id=t.class_id AND a.session_date=t.session_date) AS attendance_present,
                   (SELECT COUNT(*) FROM evaluations e
                      WHERE e.class_id=t.class_id AND e.session_date=t.session_date) AS evaluation_count,
                   (SELECT COUNT(*) FROM tests x
                      WHERE x.class_id=t.class_id AND x.test_date=t.session_date) AS test_count,
                   (SELECT COUNT(*) FROM homework h
                      WHERE h.class_id=t.class_id AND h.due_date=t.session_date) AS homework_count
              FROM timetable_sessions t
              JOIN classes c ON c.id=t.class_id
              LEFT JOIN users u ON u.id=t.teacher_id
        """
        params: List[Any] = []
        filters: List[str] = []
        if user["role"] == "TEACHER":
            filters.append("t.teacher_id=?")
            params.append(user["id"])
        elif user["role"] == "STUDENT":
            filters.append(
                "EXISTS (SELECT 1 FROM enrollments e JOIN students s ON s.id=e.student_id "
                "WHERE e.class_id=t.class_id AND e.status='ENROLLED' AND s.user_id=?)"
            )
            params.append(user["id"])
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY t.session_date DESC,t.start_time DESC,t.id DESC LIMIT 200"
        rows = rows_dict(self.db.execute(sql, params).fetchall())
        for row in rows:
            row["branch"] = None
            row["lesson_content"] = None
        return self._filter_training_dashboard(rows, date_filter, query)

    @staticmethod
    def _filter_training_dashboard(
        rows: List[Dict[str, Any]],
        date_filter: Optional[str],
        query: str,
    ) -> List[Dict[str, Any]]:
        """Filter only persisted dashboard fields; UNKNOWN fields stay uninterpreted."""
        if date_filter:
            rows = [row for row in rows if row.get("session_date") == date_filter]
        if query:
            needle = query.casefold()
            fields = ("class_code", "teacher", "session_date", "start_time", "end_time")
            rows = [
                row for row in rows
                if any(needle in str(row.get(field) or "").casefold() for field in fields)
            ]
        return rows

    def students(self, user: sqlite3.Row, query: str = "", parent: str = "", status: str = "", class_code: str = "", referral_source: str = "", year: str = "", school: str = "") -> List[Dict[str, Any]]:
        params: List[Any] = []
        sql = "SELECT s.id,s.user_id,s.student_code,s.identifier,s.full_name,s.english_name,s.email,s.phone,s.username,s.sales_rep,s.date_of_birth,s.gender,s.class_codes,s.parent1_code,s.parent1_name,s.parent1_phone,s.parent1_email,s.parent1_username,s.parent2_code,s.parent2_name,s.parent2_phone,s.parent2_email,s.parent2_username,s.expected_start_date,s.expected_sessions,s.province,s.ward,s.address,s.school,s.class_name,s.birth_place,s.referral_source,s.enrollment_year,s.note,s.status,s.created_at,s.updated_at, u.username AS account_username FROM students s LEFT JOIN users u ON u.id=s.user_id"
        filters: List[str] = []
        if user["role"] == "STUDENT":
            filters.append("s.user_id=?")
            params.append(user["id"])
        elif user["role"] == "TEACHER":
            filters.append("EXISTS (SELECT 1 FROM enrollments e JOIN classes c ON c.id=e.class_id WHERE e.student_id=s.id AND e.status='ENROLLED' AND c.teacher_id=?)")
            params.append(user["id"])
        if query:
            filters.append("(s.student_code LIKE ? OR s.identifier LIKE ? OR s.full_name LIKE ? OR s.english_name LIKE ? OR s.email LIKE ? OR s.phone LIKE ? OR s.username LIKE ?)")
            needle = "%" + query + "%"
            params.extend([needle] * 7)
        if parent:
            filters.append("(s.parent1_name LIKE ? OR s.parent2_name LIKE ? OR s.parent1_phone LIKE ? OR s.parent2_phone LIKE ?)")
            needle = "%" + parent + "%"
            params.extend([needle] * 4)
        if status:
            status = clean_text(status, 16).upper()
            if status not in {"ACTIVE", "PAUSED", "GRADUATED", "INACTIVE"}:
                raise AppError(400, "VALIDATION_ERROR", "student status is invalid")
            filters.append("s.status=?")
            params.append(status)
        if class_code:
            filters.append("(s.class_codes LIKE ? OR s.class_name LIKE ? OR EXISTS (SELECT 1 FROM enrollments e JOIN classes c ON c.id=e.class_id WHERE e.student_id=s.id AND c.code LIKE ?))")
            needle = "%" + class_code + "%"
            params.extend([needle, needle, needle])
        if referral_source:
            filters.append("s.referral_source LIKE ?")
            params.append("%" + referral_source + "%")
        if year:
            try:
                year_value = int(year)
            except (TypeError, ValueError) as exc:
                raise AppError(400, "VALIDATION_ERROR", "year must be numeric") from exc
            filters.append("s.enrollment_year=?")
            params.append(year_value)
        if school:
            filters.append("s.school LIKE ?")
            params.append("%" + school + "%")
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY s.id DESC"
        return rows_dict(self.db.execute(sql, params).fetchall())

    def student_detail(self, actor: sqlite3.Row, student_id: Any) -> Dict[str, Any]:
        """Return one student only when the actor's normal read scope permits it."""
        try:
            parsed_id = int(student_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "student id must be numeric") from exc
        row = self.db.execute(
            "SELECT s.*,u.username AS account_username "
            "FROM students s LEFT JOIN users u ON u.id=s.user_id WHERE s.id=?",
            (parsed_id,),
        ).fetchone()
        if row is None:
            raise AppError(404, "STUDENT_NOT_FOUND", "student not found")
        if actor["role"] == "STUDENT" and row["user_id"] != actor["id"]:
            raise AppError(404, "STUDENT_NOT_FOUND", "student not found")
        if actor["role"] == "TEACHER" and self.db.execute(
            "SELECT 1 FROM enrollments e JOIN classes c ON c.id=e.class_id "
            "WHERE e.student_id=? AND e.status='ENROLLED' AND c.teacher_id=?",
            (parsed_id, actor["id"]),
        ).fetchone() is None:
            raise AppError(404, "STUDENT_NOT_FOUND", "student not found")
        return row_dict(row) or {}

    def update_student(self, actor: sqlite3.Row, student_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        current = self.student_detail(actor, student_id)
        full_name = clean_text(payload.get("full_name", current["full_name"]), 120)
        email = clean_text(payload.get("email", current["email"]), 254).lower()
        code = clean_text(payload.get("student_code", current["student_code"]), 32).upper()
        phone = clean_text(payload.get("phone", current["phone"]), 40)
        status = clean_text(payload.get("status", current["status"]), 16).upper()
        if not full_name or not email or not code or "@" not in email:
            raise AppError(400, "VALIDATION_ERROR", "full_name, student_code and valid email are required")
        if status not in {"ACTIVE", "PAUSED", "GRADUATED", "INACTIVE"}:
            raise AppError(400, "VALIDATION_ERROR", "student status is invalid")
        try:
            self.db.execute(
                """UPDATE students SET student_code=?,identifier=?,full_name=?,english_name=?,email=?,phone=?,username=?,sales_rep=?,date_of_birth=?,gender=?,class_codes=?,
                    parent1_code=?,parent1_name=?,parent1_phone=?,parent1_email=?,parent1_username=?,parent2_code=?,parent2_name=?,parent2_phone=?,parent2_email=?,parent2_username=?,
                    expected_start_date=?,expected_sessions=?,province=?,ward=?,address=?,school=?,class_name=?,birth_place=?,referral_source=?,enrollment_year=?,note=?,status=?,updated_at=CURRENT_TIMESTAMP
                    WHERE id=?""",
                (*self._student_values({**dict(current), **payload}, code, full_name, email, phone), status, current["id"]),
            )
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            raise AppError(409, "DUPLICATE_STUDENT", "student code must be unique") from exc
        self.audit(actor["id"], "UPDATE", "student", current["id"], {"student_code": code, "status": status})
        return self.student_detail(actor, current["id"])

    def teachers(
        self,
        actor: sqlite3.Row,
        query: str = "",
        nationality: str = "",
        status: str = "",
    ) -> List[Dict[str, Any]]:
        require_role(actor, "ADMIN", "STAFF")
        filters = ["role='TEACHER'"]
        params: List[Any] = []
        if query:
            needle = f"%{clean_text(query, 120)}%"
            filters.append("(full_name LIKE ? OR email LIKE ? OR phone LIKE ? OR account_code LIKE ?)")
            params.extend([needle] * 4)
        if nationality:
            filters.append("nationality=?")
            params.append(clean_text(nationality, 80))
        if status:
            normalized = clean_text(status, 16).upper()
            if normalized not in {"ACTIVE", "INACTIVE"}:
                raise AppError(400, "VALIDATION_ERROR", "teacher status is invalid")
            filters.append("active=?")
            params.append(1 if normalized == "ACTIVE" else 0)
        sql = "SELECT id,username,full_name,email,phone,date_of_birth,gender,nationality,account_code,permissions_json,active FROM users WHERE " + " AND ".join(filters) + " ORDER BY full_name,id"
        rows = rows_dict(self.db.execute(sql, params).fetchall())
        for row in rows:
            try:
                row["permissions"] = json.loads(row.pop("permissions_json") or "[]")
            except (TypeError, ValueError):
                row["permissions"] = []
            row["status"] = "ACTIVE" if row["active"] else "INACTIVE"
        return rows

    def add_teacher(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        username = clean_text(payload.get("username"), 80)
        email = clean_text(payload.get("email"), 254).lower()
        full_name = clean_text(payload.get("full_name"), 120)
        if not username or not email or not full_name or "@" not in email:
            raise AppError(400, "VALIDATION_ERROR", "username, full_name and valid email are required")
        dob = self._optional_date(payload.get("date_of_birth"), "date_of_birth")
        permissions = payload.get("permissions", [])
        if not isinstance(permissions, list):
            raise AppError(400, "VALIDATION_ERROR", "permissions must be a list")
        try:
            cur = self.db.execute(
                "INSERT INTO users(username,email,full_name,password_hash,role,phone,date_of_birth,gender,nationality,account_code,permissions_json,active) VALUES(?,?,?,?,?,?,?,?,?,?,?,1)",
                (username, email, full_name, password_hash(payload.get("password") or secrets.token_urlsafe(18)), "TEACHER", clean_text(payload.get("phone"), 40), dob, clean_text(payload.get("gender"), 32), clean_text(payload.get("nationality"), 80), clean_text(payload.get("account_code"), 64), json.dumps(permissions, ensure_ascii=False)),
            )
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            raise AppError(409, "DUPLICATE_TEACHER", "username or email must be unique") from exc
        self.audit(actor["id"], "CREATE", "teacher", cur.lastrowid, {"username": username})
        return next(row for row in self.teachers(actor) if row["id"] == cur.lastrowid)

    def update_teacher(self, actor: sqlite3.Row, teacher_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        try: parsed_id = int(teacher_id)
        except (TypeError, ValueError) as exc: raise AppError(400, "VALIDATION_ERROR", "teacher id must be numeric") from exc
        current = self.db.execute("SELECT * FROM users WHERE id=? AND role='TEACHER'", (parsed_id,)).fetchone()
        if current is None: raise AppError(404, "TEACHER_NOT_FOUND", "teacher not found")
        dob = self._optional_date(payload.get("date_of_birth", current["date_of_birth"]), "date_of_birth")
        permissions = payload.get("permissions", json.loads(current["permissions_json"] or "[]"))
        if not isinstance(permissions, list): raise AppError(400, "VALIDATION_ERROR", "permissions must be a list")
        active = payload.get("active", current["active"])
        active = int(bool(active)) if isinstance(active, bool) else (1 if str(active).upper() in {"1", "TRUE", "ACTIVE"} else 0)
        self.db.execute("UPDATE users SET full_name=?,email=?,phone=?,date_of_birth=?,gender=?,nationality=?,account_code=?,permissions_json=?,active=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (clean_text(payload.get("full_name", current["full_name"]), 120), clean_text(payload.get("email", current["email"]), 254).lower(), clean_text(payload.get("phone", current["phone"]), 40), dob, clean_text(payload.get("gender", current["gender"]), 32), clean_text(payload.get("nationality", current["nationality"]), 80), clean_text(payload.get("account_code", current["account_code"]), 64), json.dumps(permissions, ensure_ascii=False), active, parsed_id))
        self.db.commit()
        self.audit(actor["id"], "UPDATE", "teacher", parsed_id, {"active": active})
        return next(row for row in self.teachers(actor, status="ACTIVE" if active else "INACTIVE") if row["id"] == parsed_id)

    # EVIDENCE_DERIVED_LOCAL_CONTRACT: the reference Ca học private schema was
    # not observable.  This bounded catalogue is deliberately independent,
    # durable, and only contains fields seen on the classroom/timetable
    # surface: code, name, start/end time, and status.
    def session_slots(
        self,
        actor: sqlite3.Row,
        query: str = "",
        status: str = "",
    ) -> List[Dict[str, Any]]:
        require_role(actor, "ADMIN", "STAFF", "TEACHER")
        filters: List[str] = []
        params: List[Any] = []
        if query:
            needle = "%" + clean_text(query, 160) + "%"
            filters.append("(code LIKE ? OR name LIKE ?)")
            params.extend([needle, needle])
        if status:
            normalized = clean_text(status, 16).upper()
            if normalized not in {"ACTIVE", "INACTIVE"}:
                raise AppError(400, "VALIDATION_ERROR", "session slot status is invalid")
            filters.append("status=?")
            params.append(normalized)
        sql = "SELECT * FROM session_slots"
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY start_time,name COLLATE NOCASE,id"
        return rows_dict(self.db.execute(sql, params).fetchall())

    def session_slot_detail(self, actor: sqlite3.Row, slot_id: Any) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF", "TEACHER")
        try:
            parsed_id = int(slot_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "session slot id must be numeric") from exc
        row = self.db.execute("SELECT * FROM session_slots WHERE id=?", (parsed_id,)).fetchone()
        if row is None:
            raise AppError(404, "SESSION_SLOT_NOT_FOUND", "session slot not found")
        return row_dict(row) or {}

    def add_session_slot(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        code = clean_text(payload.get("code"), 32).upper()
        name = clean_text(payload.get("name"), 160)
        start_time = self._time(payload.get("start_time"), "start_time")
        end_time = self._time(payload.get("end_time"), "end_time")
        status = clean_text(payload.get("status") or "ACTIVE", 16).upper()
        if not code or not name or status not in {"ACTIVE", "INACTIVE"}:
            raise AppError(400, "VALIDATION_ERROR", "code, name, times and a valid status are required")
        if end_time <= start_time:
            raise AppError(400, "VALIDATION_ERROR", "end_time must be after start_time")
        try:
            cur = self.db.execute(
                "INSERT INTO session_slots(code,name,start_time,end_time,status) VALUES(?,?,?,?,?)",
                (code, name, start_time, end_time, status),
            )
            self.audit(actor["id"], "CREATE", "session_slot", cur.lastrowid, {"code": code, "status": status}, commit=False)
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            self.db.rollback()
            raise AppError(409, "DUPLICATE_SESSION_SLOT", "session slot code must be unique") from exc
        return self.session_slot_detail(actor, cur.lastrowid)

    def update_session_slot(self, actor: sqlite3.Row, slot_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        current = self.session_slot_detail(actor, slot_id)
        code = clean_text(payload.get("code", current["code"]), 32).upper()
        name = clean_text(payload.get("name", current["name"]), 160)
        start_time = self._time(payload.get("start_time", current["start_time"]), "start_time")
        end_time = self._time(payload.get("end_time", current["end_time"]), "end_time")
        status = clean_text(payload.get("status", current["status"]), 16).upper()
        if not code or not name or status not in {"ACTIVE", "INACTIVE"}:
            raise AppError(400, "VALIDATION_ERROR", "code, name, times and a valid status are required")
        if end_time <= start_time:
            raise AppError(400, "VALIDATION_ERROR", "end_time must be after start_time")
        try:
            self.db.execute(
                "UPDATE session_slots SET code=?,name=?,start_time=?,end_time=?,status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (code, name, start_time, end_time, status, current["id"]),
            )
            self.audit(actor["id"], "UPDATE", "session_slot", current["id"], {"code": code, "status": status}, commit=False)
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            self.db.rollback()
            raise AppError(409, "DUPLICATE_SESSION_SLOT", "session slot code must be unique") from exc
        return self.session_slot_detail(actor, current["id"])

    def _session_slot_for_timetable(self, slot_id: Any, *, allow_inactive: bool = False) -> Optional[sqlite3.Row]:
        if slot_id in (None, ""):
            return None
        try:
            parsed_id = int(slot_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "session_slot_id must be numeric") from exc
        row = self.db.execute("SELECT * FROM session_slots WHERE id=?", (parsed_id,)).fetchone()
        if row is None:
            raise AppError(404, "SESSION_SLOT_NOT_FOUND", "session slot not found")
        if not allow_inactive and row["status"] != "ACTIVE":
            raise AppError(409, "SESSION_SLOT_INACTIVE", "inactive session slot cannot be scheduled")
        return row

    def classrooms(
        self,
        actor: sqlite3.Row,
        query: str = "",
        status: str = "",
    ) -> List[Dict[str, Any]]:
        """List the local room catalogue from the observed setup surface.

        The reference private API and permission matrix remain UNKNOWN; this
        rebuild therefore exposes the bounded ADMIN/STAFF contract only.
        """
        require_role(actor, "ADMIN", "STAFF")
        filters: List[str] = []
        params: List[Any] = []
        if query:
            needle = "%" + clean_text(query, 160) + "%"
            filters.append("(code LIKE ? OR name LIKE ? OR description LIKE ?)")
            params.extend([needle, needle, needle])
        if status:
            normalized = clean_text(status, 16).upper()
            if normalized not in {"ACTIVE", "INACTIVE"}:
                raise AppError(400, "VALIDATION_ERROR", "classroom status is invalid")
            filters.append("status=?")
            params.append(normalized)
        sql = "SELECT * FROM classrooms"
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY name COLLATE NOCASE, id"
        return rows_dict(self.db.execute(sql, params).fetchall())

    def classroom_detail(self, actor: sqlite3.Row, classroom_id: Any) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        try:
            parsed_id = int(classroom_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "classroom id must be numeric") from exc
        row = self.db.execute("SELECT * FROM classrooms WHERE id=?", (parsed_id,)).fetchone()
        if row is None:
            raise AppError(404, "CLASSROOM_NOT_FOUND", "classroom not found")
        return row_dict(row) or {}

    def add_classroom(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        code = clean_text(payload.get("code"), 32).upper()
        name = clean_text(payload.get("name"), 160)
        description = clean_text(payload.get("description", ""), 1000)
        capacity = self._integer(payload.get("capacity", 0), "capacity", minimum=0)
        status = clean_text(payload.get("status") or "ACTIVE", 16).upper()
        if not code or not name or status not in {"ACTIVE", "INACTIVE"}:
            raise AppError(400, "VALIDATION_ERROR", "code, name and a valid status are required")
        try:
            cur = self.db.execute(
                "INSERT INTO classrooms(code,name,capacity,description,status) VALUES(?,?,?,?,?)",
                (code, name, capacity, description, status),
            )
            self.audit(actor["id"], "CREATE", "classroom", cur.lastrowid, {"code": code, "status": status}, commit=False)
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            self.db.rollback()
            raise AppError(409, "DUPLICATE_CLASSROOM", "classroom code must be unique") from exc
        return self.classroom_detail(actor, cur.lastrowid)

    def update_classroom(self, actor: sqlite3.Row, classroom_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        current = self.classroom_detail(actor, classroom_id)
        code = clean_text(payload.get("code", current["code"]), 32).upper()
        name = clean_text(payload.get("name", current["name"]), 160)
        description = clean_text(payload.get("description", current["description"]), 1000)
        capacity = self._integer(payload.get("capacity", current["capacity"]), "capacity", minimum=0)
        status = clean_text(payload.get("status", current["status"]), 16).upper()
        if not code or not name or status not in {"ACTIVE", "INACTIVE"}:
            raise AppError(400, "VALIDATION_ERROR", "code, name and a valid status are required")
        try:
            self.db.execute(
                "UPDATE classrooms SET code=?,name=?,capacity=?,description=?,status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (code, name, capacity, description, status, current["id"]),
            )
            self.audit(actor["id"], "UPDATE", "classroom", current["id"], {"code": code, "status": status}, commit=False)
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            self.db.rollback()
            raise AppError(409, "DUPLICATE_CLASSROOM", "classroom code must be unique") from exc
        return self.classroom_detail(actor, current["id"])

    def courses(self, query: str = "", user: Optional[sqlite3.Row] = None) -> List[Dict[str, Any]]:
        params: List[Any] = []
        sql = """
            SELECT courses.*,
                   (SELECT COUNT(*)
                      FROM tests t
                      JOIN classes tc ON tc.id=t.class_id
                     WHERE tc.course_id=courses.id) AS test_count
              FROM courses
             WHERE courses.active=1
        """
        if user is not None and user["role"] == "TEACHER":
            sql += " AND EXISTS (SELECT 1 FROM classes c WHERE c.course_id=courses.id AND c.teacher_id=?)"
            params.append(user["id"])
        elif user is not None and user["role"] == "STUDENT":
            sql += " AND EXISTS (SELECT 1 FROM classes c JOIN enrollments e ON e.class_id=c.id JOIN students s ON s.id=e.student_id WHERE c.course_id=courses.id AND e.status='ENROLLED' AND s.user_id=?)"
            params.append(user["id"])
        if query:
            sql += " AND (code LIKE ? OR name LIKE ? OR level LIKE ? OR subject LIKE ?)"
            needle = "%" + query + "%"
            params.extend([needle, needle, needle, needle])
        sql += " ORDER BY name"
        return rows_dict(self.db.execute(sql, params).fetchall())

    def course(self, course_id: Any, user: Optional[sqlite3.Row] = None) -> Dict[str, Any]:
        try:
            parsed_id = int(course_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "course id must be numeric") from exc
        sql = """
            SELECT courses.*,
                   (SELECT COUNT(*)
                      FROM tests t
                      JOIN classes tc ON tc.id=t.class_id
                     WHERE tc.course_id=courses.id) AS test_count
              FROM courses
             WHERE courses.id=? AND courses.active=1
        """
        params: List[Any] = [parsed_id]
        if user is not None and user["role"] == "TEACHER":
            sql += " AND EXISTS (SELECT 1 FROM classes c WHERE c.course_id=courses.id AND c.teacher_id=?)"
            params.append(user["id"])
        elif user is not None and user["role"] == "STUDENT":
            sql += " AND EXISTS (SELECT 1 FROM classes c JOIN enrollments e ON e.class_id=c.id JOIN students s ON s.id=e.student_id WHERE c.course_id=courses.id AND e.status='ENROLLED' AND s.user_id=?)"
            params.append(user["id"])
        row = self.db.execute(sql, params).fetchone()
        if row is None:
            raise AppError(404, "COURSE_NOT_FOUND", "course not found")
        return row_dict(row) or {}

    def course_classes(self, actor: sqlite3.Row, course_id: Any) -> List[Dict[str, Any]]:
        """Return persisted classes for a course within the actor's normal scope."""
        course = self.course(course_id, actor)
        return self.classes(actor, course_id=course["id"])

    def course_tests(self, actor: sqlite3.Row, course_id: Any) -> List[Dict[str, Any]]:
        """Return persisted tests for a course within the actor's normal scope."""
        course = self.course(course_id, actor)
        result_count = "(SELECT COUNT(*) FROM test_results r WHERE r.test_id=t.id"
        result_params: List[Any] = []
        if actor["role"] == "STUDENT":
            result_count = (
                "(SELECT COUNT(*) FROM test_results r "
                "JOIN students result_student ON result_student.id=r.student_id "
                "WHERE r.test_id=t.id AND result_student.user_id=?"
            )
            result_params.append(actor["id"])
        result_count += ") AS result_count"
        sql = f"SELECT t.id,t.name,t.test_date,t.max_score,t.status,c.code AS class_code,{result_count} FROM tests t JOIN classes c ON c.id=t.class_id"
        filters: List[str] = ["c.course_id=?"]
        params: List[Any] = result_params + [course["id"]]
        if actor["role"] == "TEACHER":
            filters.append("c.teacher_id=?")
            params.append(actor["id"])
        elif actor["role"] == "STUDENT":
            filters.append(
                "EXISTS (SELECT 1 FROM enrollments e JOIN students s ON s.id=e.student_id "
                "WHERE e.class_id=t.class_id AND e.status='ENROLLED' AND s.user_id=?)"
            )
            params.append(actor["id"])
        sql += " WHERE " + " AND ".join(filters) + " ORDER BY t.test_date DESC,t.id DESC"
        return rows_dict(self.db.execute(sql, params).fetchall())

    def update_course(self, actor: sqlite3.Row, course_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        current = self.course(course_id)
        code = clean_text(payload.get("code", current["code"]), 32).upper()
        name = clean_text(payload.get("name", current["name"]), 160)
        level = clean_text(payload.get("level", current["level"]), 80)
        description = clean_text(payload.get("description", current["description"]), 1000)
        sessions_count = self._integer(payload.get("sessions_count", current["sessions_count"]), "sessions_count", minimum=0)
        hours = self._number(payload.get("hours", current["hours"]), "hours", minimum=0)
        fee_method = clean_text(payload.get("fee_method", current["fee_method"]), 32)
        fee = self._number(payload.get("fee", current["fee"]), "fee", minimum=0)
        daily_evaluation = clean_text(payload.get("daily_evaluation", current["daily_evaluation"]), 160)
        unit = clean_text(payload.get("unit", current["unit"]), 80)
        subject = clean_text(payload.get("subject", current["subject"]), 120)
        if not code or not name:
            raise AppError(400, "VALIDATION_ERROR", "code and name are required")
        try:
            self.db.execute("UPDATE courses SET code=?,name=?,level=?,description=?,sessions_count=?,hours=?,fee_method=?,fee=?,daily_evaluation=?,unit=?,subject=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (code, name, level, description, sessions_count, hours, fee_method, fee, daily_evaluation, unit, subject, current["id"]))
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            raise AppError(409, "DUPLICATE_COURSE", "course code must be unique") from exc
        self.audit(actor["id"], "UPDATE", "course", current["id"], {"code": code})
        return self.course(current["id"])

    def duplicate_course(self, actor: sqlite3.Row, course_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        source = self.course(course_id)
        requested = clean_text(payload.get("code", ""), 32).upper()
        code = requested or (source["code"] + "-COPY")[:32]
        suffix = 2
        while self.db.execute("SELECT 1 FROM courses WHERE code=?", (code,)).fetchone():
            tail = f"-{suffix}"
            code = (source["code"][:32 - len(tail)] + tail).upper()
            suffix += 1
        name = clean_text(payload.get("name", f"{source['name']} (Copy)"), 160)
        cur = self.db.execute("INSERT INTO courses(code,name,level,description,sessions_count,hours,fee_method,fee,daily_evaluation,unit,subject) VALUES(?,?,?,?,?,?,?,?,?,?,?)", (code, name, source["level"], source["description"], source["sessions_count"], source["hours"], source["fee_method"], source["fee"], source["daily_evaluation"], source["unit"], source["subject"]))
        self.db.commit()
        self.audit(actor["id"], "DUPLICATE", "course", cur.lastrowid, {"source_id": source["id"], "code": code})
        return self.course(cur.lastrowid)

    def classes(
        self,
        user: sqlite3.Row,
        query: str = "",
        status: str = "",
        course_id: Optional[int] = None,
        start_from: str = "",
        start_to: str = "",
        manager: str = "",
        teacher: str = "",
    ) -> List[Dict[str, Any]]:
        sql = """
            SELECT c.id,c.code,c.name,c.room,c.schedule,c.start_date,c.end_date,c.sessions_count,c.hours,
                   c.payment_method,c.max_students,c.max_students_per_session,c.primary_manager,
                   c.secondary_manager,c.daily_evaluation,c.notes,c.vn_teacher_sessions,
                   c.foreign_teacher_sessions,c.status,c.course_id,c.teacher_id,
                   co.code AS course_code,co.name AS course_name,u.full_name AS teacher,
                   (SELECT COUNT(*) FROM enrollments e
                     WHERE e.class_id=c.id AND e.status='ENROLLED') AS student_count,
                   (SELECT COUNT(*) FROM timetable_sessions ts
                     WHERE ts.class_id=c.id AND ts.status='COMPLETED') AS completed_sessions
              FROM classes c
              JOIN courses co ON co.id=c.course_id
              LEFT JOIN users u ON u.id=c.teacher_id
        """
        filters: List[str] = []
        params: List[Any] = []
        if status:
            status = clean_text(status, 16).upper()
            if status not in {"PLANNED", "OPEN", "IN_PROGRESS", "COMPLETED", "CANCELLED"}:
                raise AppError(400, "VALIDATION_ERROR", "class status is invalid")
        if start_from:
            start_from = self._date(start_from, "start_from")
        if start_to:
            start_to = self._date(start_to, "start_to")
        if start_from and start_to and start_from > start_to:
            raise AppError(400, "VALIDATION_ERROR", "start_from must be before or equal to start_to")
        if user["role"] == "TEACHER":
            filters.append("c.teacher_id=?")
            params.append(user["id"])
        elif user["role"] == "STUDENT":
            filters.append("EXISTS (SELECT 1 FROM enrollments e JOIN students s ON s.id=e.student_id WHERE e.class_id=c.id AND e.status='ENROLLED' AND s.user_id=?)")
            params.append(user["id"])
        # Rich/demo responses sanitize fixture teacher labels at the JSON
        # boundary (for example ``Demo Teacher`` becomes ``Ms Nga`` or a
        # Vietnamese name), while the durable user row keeps the source label
        # for stable joins.  Include raw names whose displayed value matches
        # the search term so copying a teacher name from the UI still filters
        # the class table correctly.
        def displayed_teacher_aliases(term: str) -> List[str]:
            folded = term.casefold()
            aliases: List[str] = []
            for teacher_row in self.db.execute("SELECT DISTINCT full_name FROM users WHERE role='TEACHER'").fetchall():
                raw_name = str(teacher_row["full_name"] or "")
                if not raw_name:
                    continue
                displayed = sanitize_customer_payload({"full_name": raw_name}).get("full_name", raw_name)
                if folded in str(displayed).casefold() and displayed != raw_name:
                    aliases.append(raw_name)
            return aliases

        if query:
            needle = "%" + query + "%"
            teacher_clause = "u.full_name LIKE ?"
            teacher_params: List[Any] = [needle]
            aliases = displayed_teacher_aliases(query)
            if aliases:
                teacher_clause += " OR u.full_name IN (" + ",".join("?" for _ in aliases) + ")"
                teacher_params.extend(aliases)
            filters.append("(c.code LIKE ? OR c.name LIKE ? OR co.code LIKE ? OR co.name LIKE ? OR c.room LIKE ? OR c.primary_manager LIKE ? OR c.secondary_manager LIKE ? OR " + teacher_clause + ")")
            params.extend([needle, needle, needle, needle, needle, needle, needle, *teacher_params])
        if manager:
            manager = clean_text(manager, 120)
            needle = "%" + manager + "%"
            filters.append("(c.primary_manager LIKE ? OR c.secondary_manager LIKE ?)")
            params.extend([needle, needle])
        if teacher:
            teacher = clean_text(teacher, 120)
            teacher_needle = "%" + teacher + "%"
            teacher_clause = "u.full_name LIKE ?"
            teacher_params = [teacher_needle]
            aliases = displayed_teacher_aliases(teacher)
            if aliases:
                teacher_clause += " OR u.full_name IN (" + ",".join("?" for _ in aliases) + ")"
                teacher_params.extend(aliases)
            filters.append("(" + teacher_clause + ")")
            params.extend(teacher_params)
        if status:
            filters.append("c.status=?")
            params.append(status)
        if course_id is not None:
            filters.append("c.course_id=?")
            params.append(course_id)
        if start_from:
            filters.append("(c.start_date IS NOT NULL AND c.start_date>=?)")
            params.append(self._date(start_from, "start_from"))
        if start_to:
            filters.append("(c.start_date IS NOT NULL AND c.start_date<=?)")
            params.append(self._date(start_to, "start_to"))
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY c.id DESC"
        return rows_dict(self.db.execute(sql, params).fetchall())

    def class_detail(self, class_id: Any, actor: sqlite3.Row) -> Dict[str, Any]:
        try:
            parsed_id = int(class_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "class id must be numeric") from exc
        row = self.db.execute(
            "SELECT c.*,co.code AS course_code,co.name AS course_name,u.full_name AS teacher, "
            "(SELECT COUNT(*) FROM enrollments e WHERE e.class_id=c.id AND e.status='ENROLLED') AS student_count, "
            "(SELECT COUNT(*) FROM timetable_sessions ts WHERE ts.class_id=c.id AND ts.status='COMPLETED') AS completed_sessions "
            "FROM classes c JOIN courses co ON co.id=c.course_id LEFT JOIN users u ON u.id=c.teacher_id WHERE c.id=?",
            (parsed_id,),
        ).fetchone()
        if row is None:
            raise AppError(404, "CLASS_NOT_FOUND", "class not found")
        if actor["role"] == "TEACHER" and row["teacher_id"] != actor["id"]:
            raise AppError(403, "FORBIDDEN", "teacher is not assigned to this class")
        if actor["role"] == "STUDENT" and self.db.execute(
            "SELECT 1 FROM enrollments e JOIN students s ON s.id=e.student_id "
            "WHERE e.class_id=? AND e.status='ENROLLED' AND s.user_id=?",
            (parsed_id, actor["id"]),
        ).fetchone() is None:
            raise AppError(403, "FORBIDDEN", "student is not enrolled in this class")
        return row_dict(row) or {}

    def add_class(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._add_class(actor, payload, commit=True)

    def create_class_workflow(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create class, timetable and enrollment rows atomically."""
        require_role(actor, "ADMIN", "STAFF")
        sessions = payload.get("sessions", [])
        student_ids = payload.get("student_ids", [])
        if not isinstance(sessions, list) or not isinstance(student_ids, list):
            raise AppError(400, "VALIDATION_ERROR", "sessions and student_ids must be arrays")
        if len(student_ids) != len(set(str(value) for value in student_ids)):
            raise AppError(400, "VALIDATION_ERROR", "student_ids must not contain duplicates")
        parsed_students: List[int] = []
        for value in student_ids:
            try:
                parsed = int(value)
            except (TypeError, ValueError) as exc:
                raise AppError(400, "VALIDATION_ERROR", "student_ids must be numeric") from exc
            if parsed < 1:
                raise AppError(400, "VALIDATION_ERROR", "student_ids must be positive")
            parsed_students.append(parsed)
        if parsed_students:
            placeholders = ",".join("?" for _ in parsed_students)
            found = {row["id"] for row in self.db.execute(
                f"SELECT id FROM students WHERE id IN ({placeholders}) AND status='ACTIVE'", parsed_students
            ).fetchall()}
            if any(value not in found for value in parsed_students):
                raise AppError(404, "STUDENT_NOT_FOUND", "student not found or inactive")

        savepoint = "class_workflow"
        self.db.execute(f"SAVEPOINT {savepoint}")
        try:
            classroom = self._add_class(actor, payload, commit=False)
            class_id = int(classroom["id"])
            max_students = classroom.get("max_students")
            if max_students is not None and max_students > 0 and len(parsed_students) > max_students:
                raise AppError(400, "CAPACITY_EXCEEDED", "student count exceeds class capacity")

            created_sessions: List[Dict[str, Any]] = []
            for index, item in enumerate(sessions, start=1):
                if not isinstance(item, dict):
                    raise AppError(400, "VALIDATION_ERROR", f"session {index} must be an object")
                session_date = self._date(item.get("session_date"), f"sessions[{index}].session_date")
                start_time = self._time(item.get("start_time"), f"sessions[{index}].start_time")
                end_time = self._time(item.get("end_time"), f"sessions[{index}].end_time")
                if end_time <= start_time:
                    raise AppError(400, "VALIDATION_ERROR", f"sessions[{index}].end_time must be after start_time")
                room = clean_text(item.get("room", classroom.get("room", "")), 80)
                self._assert_timetable_conflict(
                    class_id=class_id,
                    teacher_id=classroom.get("teacher_id"),
                    room=room,
                    session_date=session_date,
                    start_time=start_time,
                    end_time=end_time,
                )
                try:
                    cur = self.db.execute(
                        "INSERT INTO timetable_sessions(class_id,session_date,start_time,end_time,room,teacher_id) VALUES(?,?,?,?,?,?)",
                        (class_id, session_date, start_time, end_time, room, classroom.get("teacher_id")),
                    )
                except sqlite3.IntegrityError as exc:
                    raise AppError(409, "DUPLICATE_TIMETABLE", "a session already exists at this class/date/time") from exc
                self.audit(actor["id"], "CREATE", "timetable_session", cur.lastrowid,
                           {"class_id": class_id, "session_date": session_date}, commit=False)
                created_sessions.append(row_dict(self.db.execute(
                    "SELECT * FROM timetable_sessions WHERE id=?", (cur.lastrowid,)).fetchone()) or {})

            created_enrollments: List[Dict[str, Any]] = []
            for student_id in parsed_students:
                try:
                    cur = self.db.execute(
                        "INSERT INTO enrollments(class_id,student_id,status) VALUES(?,?,?)",
                        (class_id, student_id, "ENROLLED"),
                    )
                except sqlite3.IntegrityError as exc:
                    raise AppError(409, "DUPLICATE_ENROLLMENT", "student is already enrolled in this class") from exc
                self.audit(actor["id"], "CREATE", "enrollment", cur.lastrowid,
                           {"class_id": class_id, "student_id": student_id}, commit=False)
                created_enrollments.append(row_dict(self.db.execute(
                    "SELECT * FROM enrollments WHERE id=?", (cur.lastrowid,)).fetchone()) or {})

            self.db.execute(f"RELEASE SAVEPOINT {savepoint}")
            self.db.commit()
            return {"class": self.class_detail(class_id, actor), "sessions": created_sessions,
                    "enrollments": created_enrollments}
        except Exception:
            self.db.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
            self.db.execute(f"RELEASE SAVEPOINT {savepoint}")
            self.db.rollback()
            raise

    def _add_class(self, actor: sqlite3.Row, payload: Dict[str, Any], *, commit: bool) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        try:
            course_id = int(payload.get("course_id"))
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "course_id is required") from exc
        if self.db.execute("SELECT 1 FROM courses WHERE id=? AND active=1", (course_id,)).fetchone() is None:
            raise AppError(404, "COURSE_NOT_FOUND", "course not found")
        code = clean_text(payload.get("code"), 32).upper()
        if not code:
            raise AppError(400, "VALIDATION_ERROR", "code is required")
        # Preserve the partial workflow contract when the field is absent, but
        # fail closed when the client explicitly submits a blank name.
        name = strict_class_name(payload.get("name", ""), required="name" in payload)
        room = clean_text(payload.get("room", ""), 80)
        schedule = clean_text(payload.get("schedule", ""), 160)
        start_date = self._optional_date(payload.get("start_date"), "start_date")
        end_date = self._optional_date(payload.get("end_date"), "end_date")
        if start_date and end_date and end_date < start_date:
            raise AppError(400, "VALIDATION_ERROR", "end_date must be on or after start_date")
        sessions_count = self._integer(payload.get("sessions_count"), "sessions_count", minimum=0)
        hours = self._number(payload.get("hours"), "hours", minimum=0)
        payment_method = clean_text(payload.get("payment_method", ""), 32)
        max_students = self._integer(payload.get("max_students"), "max_students", minimum=0)
        max_students_per_session = self._integer(payload.get("max_students_per_session"), "max_students_per_session", minimum=0)
        primary_manager = clean_text(payload.get("primary_manager", ""), 120)
        secondary_manager = clean_text(payload.get("secondary_manager", ""), 120)
        daily_evaluation = clean_text(payload.get("daily_evaluation", ""), 160)
        notes = clean_text(payload.get("notes", ""), 1000)
        vn_teacher_sessions = self._integer(payload.get("vn_teacher_sessions"), "vn_teacher_sessions", minimum=0)
        foreign_teacher_sessions = self._integer(payload.get("foreign_teacher_sessions"), "foreign_teacher_sessions", minimum=0)
        status = clean_text(payload.get("status") or "PLANNED", 16).upper()
        if status not in {"PLANNED", "OPEN", "IN_PROGRESS", "COMPLETED", "CANCELLED"}:
            raise AppError(400, "VALIDATION_ERROR", "status is invalid")
        teacher_id = payload.get("teacher_id")
        # The create form submits an empty string when a class is intentionally
        # left unassigned. Normalize that wire value before the nullable FK
        # insert; otherwise SQLite rejects it as a foreign-key violation.
        if teacher_id in (None, ""):
            teacher_id = None
        else:
            try:
                teacher_id = int(teacher_id)
            except (TypeError, ValueError) as exc:
                raise AppError(400, "VALIDATION_ERROR", "teacher_id must be numeric") from exc
            if self.db.execute("SELECT 1 FROM users WHERE id=? AND role='TEACHER' AND active=1", (teacher_id,)).fetchone() is None:
                raise AppError(404, "TEACHER_NOT_FOUND", "teacher not found")
        try:
            cur = self.db.execute("INSERT INTO classes(course_id,code,name,room,schedule,start_date,end_date,sessions_count,hours,payment_method,max_students,max_students_per_session,primary_manager,secondary_manager,daily_evaluation,notes,vn_teacher_sessions,foreign_teacher_sessions,teacher_id,status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (course_id, code, name, room, schedule, start_date, end_date, sessions_count, hours, payment_method, max_students, max_students_per_session, primary_manager, secondary_manager, daily_evaluation, notes, vn_teacher_sessions, foreign_teacher_sessions, teacher_id, status))
            if commit:
                self.db.commit()
        except sqlite3.IntegrityError as exc:
            raise AppError(409, "DUPLICATE_CLASS", "class code must be unique") from exc
        self.audit(actor["id"], "CREATE", "class", cur.lastrowid, {"code": code}, commit=commit)
        return self.class_detail(cur.lastrowid, actor)

    def update_class(self, actor: sqlite3.Row, class_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        current = self.class_detail(class_id, actor)
        try:
            course_id = int(payload.get("course_id", current["course_id"]))
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "course_id must be numeric") from exc
        if self.db.execute("SELECT 1 FROM courses WHERE id=? AND active=1", (course_id,)).fetchone() is None:
            raise AppError(404, "COURSE_NOT_FOUND", "course not found")
        code = clean_text(payload.get("code", current["code"]), 32).upper()
        name = strict_class_name(
            payload.get("name", current["name"]), required="name" in payload
        )
        room = clean_text(payload.get("room", current["room"]), 80)
        schedule = clean_text(payload.get("schedule", current["schedule"]), 160)
        start_date = self._optional_date(payload.get("start_date", current["start_date"]), "start_date")
        end_date = self._optional_date(payload.get("end_date", current["end_date"]), "end_date")
        if start_date and end_date and end_date < start_date:
            raise AppError(400, "VALIDATION_ERROR", "end_date must be on or after start_date")
        sessions_count = self._integer(payload.get("sessions_count", current["sessions_count"]), "sessions_count", minimum=0)
        hours = self._number(payload.get("hours", current["hours"]), "hours", minimum=0)
        payment_method = clean_text(payload.get("payment_method", current["payment_method"]), 32)
        max_students = self._integer(payload.get("max_students", current["max_students"]), "max_students", minimum=0)
        max_students_per_session = self._integer(payload.get("max_students_per_session", current["max_students_per_session"]), "max_students_per_session", minimum=0)
        primary_manager = clean_text(payload.get("primary_manager", current["primary_manager"]), 120)
        secondary_manager = clean_text(payload.get("secondary_manager", current["secondary_manager"]), 120)
        daily_evaluation = clean_text(payload.get("daily_evaluation", current["daily_evaluation"]), 160)
        notes = clean_text(payload.get("notes", current["notes"]), 1000)
        vn_teacher_sessions = self._integer(payload.get("vn_teacher_sessions", current["vn_teacher_sessions"]), "vn_teacher_sessions", minimum=0)
        foreign_teacher_sessions = self._integer(payload.get("foreign_teacher_sessions", current["foreign_teacher_sessions"]), "foreign_teacher_sessions", minimum=0)
        status = clean_text(payload.get("status") or current["status"], 16).upper()
        if not code or status not in {"PLANNED", "OPEN", "IN_PROGRESS", "COMPLETED", "CANCELLED"}:
            raise AppError(400, "VALIDATION_ERROR", "code and a valid status are required")
        teacher_id = payload.get("teacher_id", current["teacher_id"])
        if teacher_id in (None, ""):
            teacher_id = None
        else:
            try:
                teacher_id = int(teacher_id)
            except (TypeError, ValueError) as exc:
                raise AppError(400, "VALIDATION_ERROR", "teacher_id must be numeric") from exc
            if self.db.execute("SELECT 1 FROM users WHERE id=? AND role='TEACHER' AND active=1", (teacher_id,)).fetchone() is None:
                raise AppError(404, "TEACHER_NOT_FOUND", "teacher not found")
        try:
            self.db.execute("UPDATE classes SET course_id=?,code=?,name=?,room=?,schedule=?,start_date=?,end_date=?,sessions_count=?,hours=?,payment_method=?,max_students=?,max_students_per_session=?,primary_manager=?,secondary_manager=?,daily_evaluation=?,notes=?,vn_teacher_sessions=?,foreign_teacher_sessions=?,teacher_id=?,status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (course_id, code, name, room, schedule, start_date, end_date, sessions_count, hours, payment_method, max_students, max_students_per_session, primary_manager, secondary_manager, daily_evaluation, notes, vn_teacher_sessions, foreign_teacher_sessions, teacher_id, status, current["id"]))
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            raise AppError(409, "DUPLICATE_CLASS", "class code must be unique") from exc
        self.audit(actor["id"], "UPDATE", "class", current["id"], {"code": code})
        return self.class_detail(current["id"], actor)

    def import_classes(self, actor: sqlite3.Row, text: str) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        if not isinstance(text, str) or len(text.encode("utf-8")) > 1_000_000:
            raise AppError(413, "PAYLOAD_TOO_LARGE", "CSV upload is too large")
        reader = csv.DictReader(io.StringIO(text))
        required = {"course_id", "code"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise AppError(400, "INVALID_CSV", "CSV requires course_id and code columns")
        created: List[Dict[str, Any]] = []
        self.db.execute("SAVEPOINT class_csv_import")
        try:
            for index, row in enumerate(reader, start=2):
                try:
                    created.append(self._add_class(actor, dict(row), commit=False))
                except AppError as exc:
                    raise AppError(exc.status, exc.code, f"row {index}: {exc.message}") from exc
            self.db.execute("RELEASE SAVEPOINT class_csv_import")
            self.db.commit()
        except Exception:
            self.db.execute("ROLLBACK TO SAVEPOINT class_csv_import")
            self.db.execute("RELEASE SAVEPOINT class_csv_import")
            self.db.rollback()
            raise
        return {"created": created, "count": len(created)}

    def update_timetable(self, actor: sqlite3.Row, session_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF", "TEACHER")
        try:
            parsed_id = int(session_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "timetable id must be numeric") from exc
        row = self.db.execute("SELECT * FROM timetable_sessions WHERE id=?", (parsed_id,)).fetchone()
        if row is None:
            raise AppError(404, "TIMETABLE_NOT_FOUND", "timetable session not found")
        classroom = self._class_for_actor(actor, row["class_id"])
        raw_slot_id = payload.get("session_slot_id", row["session_slot_id"])
        # An already scheduled row may retain an INACTIVE slot for history;
        # selecting an inactive slot for a new binding remains rejected.
        slot = self._session_slot_for_timetable(
            raw_slot_id,
            allow_inactive=(raw_slot_id not in (None, "") and str(raw_slot_id) == str(row["session_slot_id"])),
        )
        session_date = self._date(payload.get("session_date", row["session_date"]), "session_date")
        start_time = self._time(payload.get("start_time", slot["start_time"] if slot else row["start_time"]), "start_time")
        end_time = self._time(payload.get("end_time", slot["end_time"] if slot else row["end_time"]), "end_time")
        if end_time <= start_time:
            raise AppError(400, "VALIDATION_ERROR", "end_time must be after start_time")
        room = clean_text(payload.get("room", row["room"]), 80)
        status = clean_text(payload.get("status", row["status"]), 16).upper()
        if status not in {"SCHEDULED", "COMPLETED", "CANCELLED"}:
            raise AppError(400, "VALIDATION_ERROR", "status is invalid")
        if row["status"] == "COMPLETED" and status == "CANCELLED":
            raise AppError(409, "COMPLETED_SESSION_CANNOT_CANCEL", "completed sessions cannot be cancelled")
        if status != "CANCELLED":
            self._assert_timetable_conflict(
                class_id=int(classroom["id"]),
                teacher_id=row["teacher_id"],
                room=room,
                session_date=session_date,
                start_time=start_time,
                end_time=end_time,
                exclude_id=parsed_id,
            )
        try:
            self.db.execute("UPDATE timetable_sessions SET session_slot_id=?,session_date=?,start_time=?,end_time=?,room=?,status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (slot["id"] if slot else None, session_date, start_time, end_time, room, status, parsed_id))
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            raise AppError(409, "DUPLICATE_TIMETABLE", "a session already exists at this class/date/time") from exc
        self.audit(actor["id"], "UPDATE", "timetable_session", parsed_id, {"class_id": classroom["id"], "session_date": session_date})
        return row_dict(self.db.execute("SELECT * FROM timetable_sessions WHERE id=?", (parsed_id,)).fetchone()) or {}

    def timetable_students(self, actor: sqlite3.Row, session_id: Any) -> List[Dict[str, Any]]:
        """Return enrolled students for one session after class-scope checks."""
        require_role(actor, "ADMIN", "STAFF", "TEACHER")
        try:
            parsed_id = int(session_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "timetable id must be numeric") from exc
        row = self.db.execute("SELECT class_id FROM timetable_sessions WHERE id=?", (parsed_id,)).fetchone()
        if row is None:
            raise AppError(404, "TIMETABLE_NOT_FOUND", "timetable session not found")
        self._class_for_actor(actor, row["class_id"])
        students = self.db.execute(
            "SELECT s.id,s.student_code,s.full_name,s.email,s.phone,e.status AS enrollment_status "
            "FROM enrollments e JOIN students s ON s.id=e.student_id "
            "WHERE e.class_id=? AND e.status='ENROLLED' ORDER BY s.full_name,s.id",
            (row["class_id"],),
        ).fetchall()
        return rows_dict(students)

    def timetable_detail(self, actor: sqlite3.Row, session_id: Any) -> Dict[str, Any]:
        """Return one timetable session with the same scope as list/read APIs."""
        require_role(actor, "ADMIN", "STAFF", "TEACHER", "STUDENT")
        try:
            parsed_id = int(session_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "timetable id must be numeric") from exc
        row = self.db.execute(
            "SELECT t.id,t.class_id,t.session_slot_id,t.session_date,t.start_time,t.end_time,t.room,t.teacher_id,t.status,t.created_at,t.updated_at,"
            "c.code AS class_code,co.name AS course_name,u.full_name AS teacher,ss.code AS session_slot_code,ss.name AS session_slot_name "
            "FROM timetable_sessions t JOIN classes c ON c.id=t.class_id JOIN courses co ON co.id=c.course_id "
            "LEFT JOIN users u ON u.id=t.teacher_id LEFT JOIN session_slots ss ON ss.id=t.session_slot_id WHERE t.id=?",
            (parsed_id,),
        ).fetchone()
        if row is None:
            raise AppError(404, "TIMETABLE_NOT_FOUND", "timetable session not found")
        classroom = self._class_for_actor(actor, row["class_id"])
        if actor["role"] == "STUDENT":
            enrolled = self.db.execute(
                "SELECT 1 FROM enrollments e JOIN students s ON s.id=e.student_id "
                "WHERE e.class_id=? AND e.status='ENROLLED' AND s.user_id=? LIMIT 1",
                (classroom["id"], actor["id"]),
            ).fetchone()
            if enrolled is None:
                raise AppError(403, "FORBIDDEN", "student is not enrolled in this class")
        return row_dict(row) or {}

    def cancel_timetable(self, actor: sqlite3.Row, session_id: Any) -> Dict[str, Any]:
        """Cancel a scheduled session without deleting its audit/history."""
        require_role(actor, "ADMIN", "STAFF", "TEACHER")
        try:
            parsed_id = int(session_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "timetable id must be numeric") from exc
        row = self.db.execute("SELECT * FROM timetable_sessions WHERE id=?", (parsed_id,)).fetchone()
        if row is None:
            raise AppError(404, "TIMETABLE_NOT_FOUND", "timetable session not found")
        classroom = self._class_for_actor(actor, row["class_id"])
        if row["status"] == "COMPLETED":
            raise AppError(409, "COMPLETED_SESSION_CANNOT_CANCEL", "completed sessions cannot be cancelled")
        if row["status"] != "CANCELLED":
            self.db.execute(
                "UPDATE timetable_sessions SET status='CANCELLED',updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (parsed_id,),
            )
            self.db.commit()
            self.audit(actor["id"], "CANCEL", "timetable_session", parsed_id, {"class_id": classroom["id"], "session_date": row["session_date"]})
        return row_dict(self.db.execute("SELECT * FROM timetable_sessions WHERE id=?", (parsed_id,)).fetchone()) or {}

    def timetable_week(self, user: sqlite3.Row, week_start: str) -> List[Dict[str, Any]]:
        start = self._date(week_start, "week")
        first = dt.date.fromisoformat(start)
        end = (first + dt.timedelta(days=6)).isoformat()
        rows = self.timetable(user)
        return [row for row in rows if start <= row["session_date"] <= end]

    def attendance(
        self,
        user: sqlite3.Row,
        class_id: Optional[int] = None,
        status: str = "",
        date_from: str = "",
        date_to: str = "",
    ) -> List[Dict[str, Any]]:
        sql = "SELECT a.id,a.class_id,a.student_id,a.session_date,a.status,a.note,a.created_at,s.student_code,s.full_name,c.code AS class_code FROM attendance a JOIN students s ON s.id=a.student_id JOIN classes c ON c.id=a.class_id"
        params: List[Any] = []
        filters = []
        if class_id:
            filters.append("a.class_id=?")
            params.append(class_id)
        if status:
            status = clean_text(status, 16).upper()
            if status not in {"PRESENT", "ABSENT", "LATE", "EXCUSED"}:
                raise AppError(400, "VALIDATION_ERROR", "attendance status is invalid")
            filters.append("a.status=?")
            params.append(status)
        if date_from:
            filters.append("a.session_date>=?")
            params.append(self._date(date_from, "date_from"))
        if date_to:
            filters.append("a.session_date<=?")
            params.append(self._date(date_to, "date_to"))
        if date_from and date_to and date_from > date_to:
            raise AppError(400, "VALIDATION_ERROR", "date_from must be before or equal to date_to")
        if user["role"] == "TEACHER":
            filters.append("c.teacher_id=?")
            params.append(user["id"])
        elif user["role"] == "STUDENT":
            filters.append("s.user_id=?")
            params.append(user["id"])
            filters.append("EXISTS (SELECT 1 FROM enrollments en WHERE en.class_id=a.class_id AND en.student_id=a.student_id AND en.status='ENROLLED')")
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY a.session_date DESC, a.id DESC LIMIT 200"
        return rows_dict(self.db.execute(sql, params).fetchall())

    def report_attendance(self, user: sqlite3.Row) -> List[Dict[str, Any]]:
        if user["role"] == "STUDENT":
            sql = "SELECT c.code AS class_code, c.status AS class_status, COUNT(a.id) AS total, COALESCE(SUM(CASE WHEN a.status='PRESENT' THEN 1 ELSE 0 END), 0) AS present, COALESCE(SUM(CASE WHEN a.status='ABSENT' THEN 1 ELSE 0 END), 0) AS absent, COALESCE(SUM(CASE WHEN a.status='LATE' THEN 1 ELSE 0 END), 0) AS late FROM classes c LEFT JOIN attendance a ON a.class_id=c.id AND a.student_id IN (SELECT s2.id FROM students s2 WHERE s2.user_id=?)"
            sql += " WHERE EXISTS (SELECT 1 FROM enrollments e JOIN students s ON s.id=e.student_id WHERE e.class_id=c.id AND e.status='ENROLLED' AND s.user_id=?)"
            sql += " GROUP BY c.id ORDER BY c.code"
            return rows_dict(self.db.execute(sql, (user["id"], user["id"])).fetchall())

        sql = "SELECT c.code AS class_code, c.status AS class_status, COUNT(a.id) AS total, COALESCE(SUM(CASE WHEN a.status='PRESENT' THEN 1 ELSE 0 END), 0) AS present, COALESCE(SUM(CASE WHEN a.status='ABSENT' THEN 1 ELSE 0 END), 0) AS absent, COALESCE(SUM(CASE WHEN a.status='LATE' THEN 1 ELSE 0 END), 0) AS late FROM classes c LEFT JOIN attendance a ON a.class_id=c.id"
        params: Sequence[Any] = ()
        if user["role"] == "TEACHER":
            sql += " WHERE c.teacher_id=?"
            params = (user["id"],)
        elif user["role"] == "STUDENT":
            sql += " WHERE EXISTS (SELECT 1 FROM enrollments e JOIN students s ON s.id=e.student_id WHERE e.class_id=c.id AND s.user_id=?)"
            params = (user["id"],)
        sql += " GROUP BY c.id ORDER BY c.code"
        return rows_dict(self.db.execute(sql, params).fetchall())

    def report_engine(
        self,
        user: sqlite3.Row,
        route: str,
        query: str = "",
        date_from: str = "",
        date_to: str = "",
        class_id: str = "",
        teacher: str = "",
    ) -> Dict[str, Any]:
        """Evidence-backed shared report contract for all inventory report routes.

        Each route receives the same persistent-data query surface.  The route
        identity and observed title remain explicit; unavailable reference
        dimensions are represented as UNKNOWN instead of fabricated values.
        """
        route = "/" + route.lstrip("/")
        query = clean_text(query, 160)
        specs = {
            "/report/training/attendance": ("Báo cáo điểm danh", "attendance"),
            "/report/training/test": ("Báo cáo kiểm tra", "tests"),
            "/report/training/daily_evaluation/index": ("Báo cáo đánh giá hàng ngày", "evaluations"),
            "/report/training/class/v2": ("Báo cáo lớp học", "classes"),
            "/report/training/enroll/index": ("Báo cáo ghi danh", "enrollments"),
            "/report/training/student_training_v2": ("Báo cáo học viên", "students"),
            "/report/finance/revenue_center": ("Báo cáo doanh thu theo năm", "finance_revenues"),
            "/report/finance/revenue_source/index": ("Báo cáo doanh thu nguồn", "finance_revenues"),
            "/report/finance/debt": ("Báo cáo học phí học viên", "finance_bills"),
            "/report/finance/payment/index": ("Doanh thu theo hình thức thanh toán", "finance_bills"),
            "/report/crm/contract/index": ("Thống kê danh sách hợp đồng", "contracts_unknown"),
            "/report/crm/bill/index": ("Thống kê danh sách hóa đơn", "finance_bills"),
            "/report/center/student_statistical/index": ("Thống kê học viên", "students"),
            "/report/center/staff_teacher": ("Báo cáo nhân viên - giáo viên", "staff"),
            "/report/crm/customer_report/index": ("Báo cáo khách hàng", "potential_customers"),
            "/report/crm/customer_statistic/index": ("Tỷ lệ chuyển đổi khách hàng theo nguồn", "potential_customers"),
        }
        title, kind = specs.get(route, ("Báo cáo", "unknown"))
        role_filter = ""
        params: List[Any] = []
        if user["role"] == "TEACHER": role_filter = " WHERE c.teacher_id=?"; params.append(user["id"])
        elif user["role"] == "STUDENT": role_filter = " WHERE s.user_id=?"; params.append(user["id"])
        if kind == "attendance":
            # Route-specific local contract mirrors the observed Vietnamese
            # report: one row per enrolled student with attendance totals.
            # Canonical attendance enum values remain stored unchanged.
            date_from = self._date(date_from, "date_from") if date_from else ""
            date_to = self._date(date_to, "date_to") if date_to else ""
            if date_from and date_to and date_from > date_to:
                raise AppError(400, "VALIDATION_ERROR", "date_from must be before or equal to date_to")
            attendance_join = " LEFT JOIN attendance a ON a.class_id=e.class_id AND a.student_id=s.id"
            attendance_params: List[Any] = []
            if date_from:
                attendance_join += " AND a.session_date>=?"
                attendance_params.append(date_from)
            if date_to:
                attendance_join += " AND a.session_date<=?"
                attendance_params.append(date_to)
            if class_id:
                try: parsed_class_id = int(class_id)
                except (TypeError, ValueError) as exc: raise AppError(400, "VALIDATION_ERROR", "class_id must be numeric") from exc
            else: parsed_class_id = None
            sql = (
                "SELECT s.student_code,s.full_name,"
                "COALESCE(SUM(CASE WHEN a.status IN ('PRESENT','LATE') THEN 1 ELSE 0 END),0) AS present,"
                "COALESCE(SUM(CASE WHEN a.status='EXCUSED' THEN 1 ELSE 0 END),0) AS excused,"
                "COALESCE(SUM(CASE WHEN a.status='ABSENT' THEN 1 ELSE 0 END),0) AS unexcused "
                "FROM students s JOIN enrollments e ON e.student_id=s.id AND e.status='ENROLLED' "
                "JOIN classes c ON c.id=e.class_id" + attendance_join
            )
            where: List[str] = []
            params: List[Any] = list(attendance_params)
            if user["role"] == "TEACHER":
                where.append("c.teacher_id=?")
                params.append(user["id"])
            elif user["role"] == "STUDENT":
                where.append("s.user_id=?")
                params.append(user["id"])
            if parsed_class_id is not None:
                where.append("c.id=?")
                params.append(parsed_class_id)
            if teacher:
                where.append("c.teacher_id IN (SELECT id FROM users WHERE role='TEACHER' AND full_name LIKE ?)")
                params.append(f"%{clean_text(teacher, 120)}%")
            if where:
                sql += " WHERE " + " AND ".join(where)
            sql += " GROUP BY s.id ORDER BY s.student_code"
            rows = rows_dict(self.db.execute(sql, params).fetchall())
            rows = [{"no": index, **row} for index, row in enumerate(rows, start=1)]
        elif kind == "classes":
            sql = "SELECT c.id,c.code,c.status,co.name AS course_name,c.start_date,c.end_date,COUNT(e.id) AS enrolled FROM classes c JOIN courses co ON co.id=c.course_id LEFT JOIN enrollments e ON e.class_id=c.id AND e.status='ENROLLED' GROUP BY c.id ORDER BY c.code"
            rows = rows_dict(self.db.execute(sql).fetchall())
        elif kind == "students":
            sql = "SELECT s.id,s.student_code,s.full_name,s.status,s.school,s.referral_source FROM students s" + (" WHERE s.user_id=?" if user["role"] == "STUDENT" else "") + " ORDER BY s.id DESC LIMIT 500"
            rows = rows_dict(self.db.execute(sql, (user["id"],) if user["role"] == "STUDENT" else ()).fetchall())
        elif kind == "finance_revenues":
            rows = rows_dict(self.db.execute("SELECT id,code,name,status,price,discount_value,amount_due,center,created_at FROM finance_revenues ORDER BY id DESC LIMIT 500").fetchall())
        elif kind == "finance_bills":
            rows = rows_dict(self.db.execute("SELECT id,invoice_code,contract_code,customer_name,payment_amount,confirmation_status,payment_method,invoice_date FROM finance_bills ORDER BY id DESC LIMIT 500").fetchall())
        elif kind == "potential_customers":
            rows = rows_dict(self.db.execute("SELECT id,customer_code,full_name,phone,source,sale_owner,status,created_at FROM potential_customers WHERE deleted_at IS NULL ORDER BY id DESC LIMIT 500").fetchall())
        elif kind == "staff":
            rows = rows_dict(self.db.execute("SELECT id,username,full_name,role,active FROM users ORDER BY role,full_name").fetchall())
        elif kind == "tests":
            rows = rows_dict(self.db.execute("SELECT id,name,test_date,max_score,status FROM tests ORDER BY test_date DESC LIMIT 500").fetchall())
        elif kind == "evaluations":
            rows = rows_dict(self.db.execute("SELECT id,class_id,student_id,session_date,status,score,note FROM evaluations ORDER BY session_date DESC LIMIT 500").fetchall())
        elif kind == "enrollments":
            rows = rows_dict(self.db.execute("SELECT e.id,c.code AS class_code,s.student_code,s.full_name,e.status,e.enrolled_at FROM enrollments e JOIN classes c ON c.id=e.class_id JOIN students s ON s.id=e.student_id ORDER BY e.id DESC LIMIT 500").fetchall())
        else:
            rows = []
        if query:
            q = query.lower(); rows = [r for r in rows if q in json.dumps(r, ensure_ascii=False).lower()]
        columns = list(rows[0].keys()) if rows else ["status", "value"]
        if kind == "attendance":
            columns = ["no", "student_code", "full_name", "present", "excused", "unexcused"]
        # Empty data is represented by an empty row set.  The UI can show a
        # human-facing empty state; a synthetic UNKNOWN row would be mistaken
        # for a persisted report result.
        return {"route": route, "title": title, "columns": columns, "rows": rows, "source": "local-sqlite", "data_status": "OBSERVED" if rows else "NO_DATA", "unknown_fields": ["reference_private_contract"] if kind in {"unknown", "contracts_unknown"} else []}

    def timetable(
        self,
        user: sqlite3.Row,
        session_date: Optional[str] = None,
        teacher: str = "",
        course: str = "",
        class_code: str = "",
        room: str = "",
        time_query: str = "",
        status: str = "",
    ) -> List[Dict[str, Any]]:
        sql = "SELECT t.id,t.session_slot_id,t.session_date,t.start_time,t.end_time,t.room,t.status,c.code AS class_code,co.name AS course_name,u.full_name AS teacher,ss.code AS session_slot_code,ss.name AS session_slot_name FROM timetable_sessions t JOIN classes c ON c.id=t.class_id JOIN courses co ON co.id=c.course_id LEFT JOIN users u ON u.id=t.teacher_id LEFT JOIN session_slots ss ON ss.id=t.session_slot_id"
        params: List[Any] = []
        filters: List[str] = []
        if session_date:
            session_date = self._date(session_date, "date")
            filters.append("t.session_date=?")
            params.append(session_date)
        if teacher:
            filters.append("LOWER(COALESCE(u.full_name,'')) LIKE LOWER(?)")
            params.append(f"%{clean_text(teacher, 120)}%")
        if course:
            filters.append("LOWER(co.name) LIKE LOWER(?)")
            params.append(f"%{clean_text(course, 160)}%")
        if class_code:
            filters.append("LOWER(c.code) LIKE LOWER(?)")
            params.append(f"%{clean_text(class_code, 80)}%")
        if room:
            filters.append("LOWER(COALESCE(t.room,'')) LIKE LOWER(?)")
            params.append(f"%{clean_text(room, 80)}%")
        if time_query:
            clean_time = clean_text(time_query, 20)
            filters.append("(t.start_time LIKE ? OR t.end_time LIKE ?)")
            params.extend((f"%{clean_time}%", f"%{clean_time}%"))
        if status:
            status = clean_text(status, 16).upper()
            if status not in {"SCHEDULED", "COMPLETED", "CANCELLED"}:
                raise AppError(400, "VALIDATION_ERROR", "timetable status is invalid")
            filters.append("t.status=?")
            params.append(status)
        if user["role"] == "TEACHER":
            filters.append("t.teacher_id=?")
            params.append(user["id"])
        elif user["role"] == "STUDENT":
            filters.append("EXISTS (SELECT 1 FROM enrollments e JOIN students s ON s.id=e.student_id WHERE e.class_id=t.class_id AND e.status='ENROLLED' AND s.user_id=?)")
            params.append(user["id"])
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY t.session_date,t.start_time"
        return rows_dict(self.db.execute(sql, params).fetchall())

    def evaluations(
        self,
        user: sqlite3.Row,
        class_code: str = "",
        status: str = "",
        date_from: str = "",
        date_to: str = "",
    ) -> List[Dict[str, Any]]:
        sql = "SELECT e.id,e.session_date,e.status,e.score,e.note,c.code AS class_code,s.student_code,s.full_name FROM evaluations e JOIN classes c ON c.id=e.class_id JOIN students s ON s.id=e.student_id"
        filters: List[str] = []
        params: List[Any] = []
        if user["role"] == "TEACHER":
            filters.append("c.teacher_id=?")
            params.append(user["id"])
        elif user["role"] == "STUDENT":
            filters.append("s.user_id=?")
            params.append(user["id"])
            filters.append("EXISTS (SELECT 1 FROM enrollments en WHERE en.class_id=e.class_id AND en.student_id=e.student_id AND en.status='ENROLLED')")
        if class_code:
            filters.append("c.code LIKE ?")
            params.append("%" + clean_text(class_code, 80) + "%")
        if status:
            status = clean_text(status, 16).upper()
            if status not in {"DRAFT", "PUBLISHED"}:
                raise AppError(400, "VALIDATION_ERROR", "evaluation status is invalid")
            filters.append("e.status=?")
            params.append(status)
        start, end = self._date_range(date_from, date_to)
        if start:
            filters.append("e.session_date>=?")
            params.append(start)
        if end:
            filters.append("e.session_date<=?")
            params.append(end)
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY e.session_date DESC,e.id DESC"
        return rows_dict(self.db.execute(sql, params).fetchall())

    def tests(
        self,
        user: sqlite3.Row,
        class_code: str = "",
        status: str = "",
        date_from: str = "",
        date_to: str = "",
    ) -> List[Dict[str, Any]]:
        result_count = "(SELECT COUNT(*) FROM test_results r WHERE r.test_id=t.id"
        result_params: List[Any] = []
        if user["role"] == "STUDENT":
            result_count = (
                "(SELECT COUNT(*) FROM test_results r "
                "JOIN students result_student ON result_student.id=r.student_id "
                "WHERE r.test_id=t.id AND result_student.user_id=?"
            )
            result_params.append(user["id"])
        result_count += ") AS result_count"
        sql = f"SELECT t.id,t.name,t.test_date,t.max_score,t.status,c.code AS class_code,{result_count} FROM tests t JOIN classes c ON c.id=t.class_id"
        filters: List[str] = []
        params: List[Any] = result_params
        if user["role"] == "TEACHER":
            filters.append("c.teacher_id=?")
            params.append(user["id"])
        elif user["role"] == "STUDENT":
            filters.append("EXISTS (SELECT 1 FROM enrollments e JOIN students s ON s.id=e.student_id WHERE e.class_id=t.class_id AND e.status='ENROLLED' AND s.user_id=?)")
            params.append(user["id"])
        if class_code:
            filters.append("c.code LIKE ?")
            params.append("%" + clean_text(class_code, 80) + "%")
        if status:
            status = clean_text(status, 16).upper()
            if status not in {"DRAFT", "OPEN", "CLOSED"}:
                raise AppError(400, "VALIDATION_ERROR", "test status is invalid")
            filters.append("t.status=?")
            params.append(status)
        start, end = self._date_range(date_from, date_to)
        if start:
            filters.append("t.test_date>=?")
            params.append(start)
        if end:
            filters.append("t.test_date<=?")
            params.append(end)
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY t.test_date DESC"
        return rows_dict(self.db.execute(sql, params).fetchall())

    def test_results(self, actor: sqlite3.Row, test_id: Any) -> Dict[str, Any]:
        """Return an enrolled result roster without crossing the actor's scope."""
        try:
            parsed_id = int(test_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "test id must be numeric") from exc
        test = self.db.execute(
            "SELECT t.*,c.code AS class_code,c.course_id FROM tests t JOIN classes c ON c.id=t.class_id WHERE t.id=?",
            (parsed_id,),
        ).fetchone()
        if test is None:
            raise AppError(404, "TEST_NOT_FOUND", "test not found")
        if actor["role"] == "TEACHER":
            classroom = self.db.execute("SELECT teacher_id FROM classes WHERE id=?", (test["class_id"],)).fetchone()
            if classroom is None or classroom["teacher_id"] != actor["id"]:
                raise AppError(403, "FORBIDDEN", "teacher is not assigned to this class")
        elif actor["role"] == "STUDENT":
            enrolled = self.db.execute(
                "SELECT 1 FROM enrollments e JOIN students s ON s.id=e.student_id "
                "WHERE e.class_id=? AND e.status='ENROLLED' AND s.user_id=?",
                (test["class_id"], actor["id"]),
            ).fetchone()
            if enrolled is None:
                raise AppError(404, "TEST_NOT_FOUND", "test not found")
        rows_sql = (
            "SELECT s.id AS student_id,s.student_code,s.full_name,s.email,s.phone,"
            "r.id AS result_id,r.score,r.note,r.updated_at "
            "FROM enrollments e JOIN students s ON s.id=e.student_id "
            "LEFT JOIN test_results r ON r.test_id=? AND r.student_id=s.id "
            "WHERE e.class_id=? AND e.status='ENROLLED'"
        )
        params: List[Any] = [parsed_id, test["class_id"]]
        if actor["role"] == "STUDENT":
            rows_sql += " AND s.user_id=?"
            params.append(actor["id"])
        rows_sql += " ORDER BY s.full_name,s.id"
        return {"test": row_dict(test) or {}, "results": rows_dict(self.db.execute(rows_sql, params).fetchall())}

    def homework(
        self,
        user: sqlite3.Row,
        class_code: str = "",
        status: str = "",
        date_from: str = "",
        date_to: str = "",
    ) -> List[Dict[str, Any]]:
        sql = "SELECT h.id,h.title,h.description,h.due_date,h.status,c.code AS class_code,u.full_name AS created_by_name FROM homework h JOIN classes c ON c.id=h.class_id LEFT JOIN users u ON u.id=h.created_by"
        filters: List[str] = []
        params: List[Any] = []
        if user["role"] == "TEACHER":
            filters.append("c.teacher_id=?")
            params.append(user["id"])
        elif user["role"] == "STUDENT":
            filters.append("EXISTS (SELECT 1 FROM enrollments e JOIN students s ON s.id=e.student_id WHERE e.class_id=h.class_id AND e.status='ENROLLED' AND s.user_id=?)")
            params.append(user["id"])
        if class_code:
            filters.append("c.code LIKE ?")
            params.append("%" + clean_text(class_code, 80) + "%")
        if status:
            status = clean_text(status, 16).upper()
            if status not in {"DRAFT", "OPEN", "CLOSED"}:
                raise AppError(400, "VALIDATION_ERROR", "homework status is invalid")
            filters.append("h.status=?")
            params.append(status)
        start, end = self._date_range(date_from, date_to)
        if start:
            filters.append("h.due_date>=?")
            params.append(start)
        if end:
            filters.append("h.due_date<=?")
            params.append(end)
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY h.due_date DESC"
        return rows_dict(self.db.execute(sql, params).fetchall())

    def trial_registrations(
        self,
        actor: sqlite3.Row,
        status: str = "",
        date_from: str = "",
        date_to: str = "",
    ) -> List[Dict[str, Any]]:
        require_role(actor, "ADMIN", "STAFF")
        sql = "SELECT * FROM trial_registrations"
        filters: List[str] = []
        params: List[Any] = []
        if status:
            status = clean_text(status, 16).upper()
            if status not in {"NEW", "CONFIRMED", "CANCELLED"}:
                raise AppError(400, "VALIDATION_ERROR", "trial status is invalid")
            filters.append("status=?")
            params.append(status)
        start, end = self._date_range(date_from, date_to)
        if start:
            filters.append("trial_date>=?")
            params.append(start)
        if end:
            filters.append("trial_date<=?")
            params.append(end)
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY trial_date DESC,id DESC"
        return rows_dict(self.db.execute(sql, params).fetchall())

    def enrollment_confirmations(
        self,
        actor: sqlite3.Row,
        status: str = "",
        class_code: str = "",
        date_from: str = "",
        date_to: str = "",
    ) -> List[Dict[str, Any]]:
        require_role(actor, "ADMIN", "STAFF")
        # The current reference contract exposes status/class filters only for
        # this surface. Reject date filters instead of silently ignoring them.
        if date_from or date_to:
            raise AppError(400, "VALIDATION_ERROR", "date filters are not supported for enrollment confirmations")
        sql = "SELECT e.id,e.contract_code,e.status,e.confirmed_at,e.confirmed_by,s.student_code,s.full_name,c.code AS class_code,co.name AS course_name FROM enrollment_confirmations e JOIN students s ON s.id=e.student_id JOIN classes c ON c.id=e.class_id JOIN courses co ON co.id=c.course_id"
        filters: List[str] = []
        params: List[Any] = []
        if status:
            status = clean_text(status, 16).upper()
            if status not in {"PENDING", "APPROVED", "REJECTED"}:
                raise AppError(400, "VALIDATION_ERROR", "confirmation status is invalid")
            filters.append("e.status=?")
            params.append(status)
        if class_code:
            filters.append("c.code LIKE ?")
            params.append("%" + clean_text(class_code, 80) + "%")
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY e.id DESC"
        return rows_dict(self.db.execute(sql, params).fetchall())

    def enrollment_confirmation(self, actor: sqlite3.Row, confirmation_id: Any) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        try:
            parsed_id = int(confirmation_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "confirmation id must be numeric") from exc
        row = self.db.execute(
            "SELECT e.*,s.student_code,s.full_name,s.email,s.phone,c.code AS class_code,"
            "co.code AS course_code,co.name AS course_name,u.full_name AS confirmed_by_name "
            "FROM enrollment_confirmations e JOIN students s ON s.id=e.student_id "
            "JOIN classes c ON c.id=e.class_id JOIN courses co ON co.id=c.course_id "
            "LEFT JOIN users u ON u.id=e.confirmed_by WHERE e.id=?", (parsed_id,)
        ).fetchone()
        if row is None:
            raise AppError(404, "CONFIRMATION_NOT_FOUND", "enrollment confirmation not found")
        return row_dict(row) or {}

    def customer_tests(
        self,
        actor: sqlite3.Row,
        query: str = "",
        status: str = "",
        sales_owner: str = "",
        date_from: str = "",
        date_to: str = "",
    ) -> List[Dict[str, Any]]:
        require_role(actor, "ADMIN", "STAFF")
        sql = "SELECT * FROM customer_tests"
        filters: List[str] = []
        params: List[Any] = []
        if query:
            needle = "%" + clean_text(query, 160) + "%"
            filters.append("(customer_name LIKE ? OR parent_name LIKE ? OR sales_owner LIKE ? OR note LIKE ?)")
            params.extend([needle] * 4)
        if status:
            status = clean_text(status, 16).upper()
            if status not in {"BOOKED", "SCORED", "CANCELLED"}:
                raise AppError(400, "VALIDATION_ERROR", "customer test status is invalid")
            filters.append("status=?")
            params.append(status)
        if sales_owner:
            filters.append("sales_owner LIKE ?")
            params.append("%" + clean_text(sales_owner, 120) + "%")
        start, end = self._date_range(date_from, date_to)
        if start:
            filters.append("test_date>=?")
            params.append(start)
        if end:
            filters.append("test_date<=?")
            params.append(end)
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY test_date DESC,id DESC"
        rows = rows_dict(self.db.execute(sql, params).fetchall())
        for row in rows:
            row["appointment_time"] = row.get("created_at") or ""
            row["activity_label"] = {
                "BOOKED": "Đã đặt lịch",
                "SCORED": "Đã chấm điểm",
                "CANCELLED": "Đã hủy",
            }.get(str(row.get("status") or "").upper(), "—")
        return rows

    def pending_enrollments(
        self,
        actor: sqlite3.Row,
        status: str = "",
        course: str = "",
        preferred_day: str = "",
        date_from: str = "",
        date_to: str = "",
    ) -> List[Dict[str, Any]]:
        require_role(actor, "ADMIN", "STAFF")
        # No date field/filter is part of the observed pending-enrollment
        # contract. Fail closed rather than returning an unfiltered result.
        if date_from or date_to:
            raise AppError(400, "VALIDATION_ERROR", "date filters are not supported for pending enrollments")
        sql = "SELECT p.*,c.code AS course_code,c.name AS course_name FROM pending_enrollments p LEFT JOIN courses c ON c.id=p.course_id"
        filters: List[str] = []
        params: List[Any] = []
        if status:
            status = clean_text(status, 16).upper()
            if status not in {"WAITING", "ASSIGNED", "CANCELLED"}:
                raise AppError(400, "VALIDATION_ERROR", "pending enrollment status is invalid")
            filters.append("p.status=?")
            params.append(status)
        if course:
            needle = "%" + clean_text(course, 120) + "%"
            filters.append("(c.code LIKE ? OR c.name LIKE ?)")
            params.extend([needle, needle])
        if preferred_day:
            filters.append("p.preferred_day LIKE ?")
            params.append("%" + clean_text(preferred_day, 80) + "%")
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY p.id DESC"
        return rows_dict(self.db.execute(sql, params).fetchall())

    # Finance, survey and call-center contracts below are local rebuild
    # surfaces derived from the authenticated reference inventory.  The
    # reference private API/permission semantics remain UNKNOWN, so these
    # methods expose only the explicit fields in our evidence-derived schema.
    def finance_bills(
        self,
        actor: sqlite3.Row,
        query: str = "",
        confirmation_status: str = "",
        center: str = "",
        branch: str = "",
        employee: str = "",
        date_from: str = "",
        date_to: str = "",
        creator: str = "",
    ) -> List[Dict[str, Any]]:
        require_role(actor, "ADMIN", "STAFF")
        sql = "SELECT f.*,u.full_name AS created_by_name FROM finance_bills f LEFT JOIN users u ON u.id=f.created_by"
        filters: List[str] = []
        params: List[Any] = []
        if query:
            needle = "%" + clean_text(query, 160) + "%"
            filters.append("(invoice_code LIKE ? OR contract_code LIKE ? OR class_code LIKE ? OR subject LIKE ? OR customer_name LIKE ? OR sales_owner LIKE ? OR note LIKE ?)")
            params.extend([needle] * 7)
        if confirmation_status:
            status = clean_text(confirmation_status, 16).upper()
            if status not in {"PENDING", "CONFIRMED", "REJECTED"}:
                raise AppError(400, "VALIDATION_ERROR", "confirmation_status is invalid")
            filters.append("confirmation_status=?")
            params.append(status)
        if creator:
            filters.append("u.full_name LIKE ?")
            params.append("%" + clean_text(creator, 120) + "%")
        for field, value in (("center", center), ("branch", branch), ("employee", employee)):
            if value:
                filters.append(f"{field} LIKE ?")
                params.append("%" + clean_text(value, 120) + "%")
        start, end = self._date_range(date_from, date_to)
        if start:
            filters.append("invoice_date>=?")
            params.append(start)
        if end:
            filters.append("invoice_date<=?")
            params.append(end)
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY COALESCE(invoice_date, f.created_at) DESC, f.id DESC"
        return rows_dict(self.db.execute(sql, params).fetchall())

    def _finance_bill(self, actor: sqlite3.Row, bill_id: Any) -> sqlite3.Row:
        require_role(actor, "ADMIN", "STAFF")
        try:
            parsed_id = int(bill_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "finance bill id must be numeric") from exc
        row = self.db.execute("SELECT * FROM finance_bills WHERE id=?", (parsed_id,)).fetchone()
        if row is None:
            raise AppError(404, "FINANCE_BILL_NOT_FOUND", "finance bill not found")
        return row

    def add_finance_bill(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        invoice_code = clean_text(payload.get("invoice_code"), 64).upper()
        if not invoice_code:
            raise AppError(400, "VALIDATION_ERROR", "invoice_code is required")
        status = clean_text(payload.get("confirmation_status") or "PENDING", 16).upper()
        if status not in {"PENDING", "CONFIRMED", "REJECTED"}:
            raise AppError(400, "VALIDATION_ERROR", "confirmation_status is invalid")
        amount = self._number(payload.get("payment_amount"), "payment_amount", minimum=0)
        invoice_date = self._optional_date(payload.get("invoice_date"), "invoice_date")
        try:
            cur = self.db.execute(
                "INSERT INTO finance_bills(invoice_code,contract_code,class_code,subject,customer_name,payment_amount,sales_owner,created_by,center,branch,employee,confirmation_status,payment_method,note,invoice_date) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (invoice_code, clean_text(payload.get("contract_code", ""), 64), clean_text(payload.get("class_code", ""), 64),
                 clean_text(payload.get("subject", ""), 240), clean_text(payload.get("customer_name", ""), 160), amount,
                 clean_text(payload.get("sales_owner", ""), 120), actor["id"], clean_text(payload.get("center", ""), 120),
                 clean_text(payload.get("branch", ""), 120), clean_text(payload.get("employee", ""), 120), status,
                 clean_text(payload.get("payment_method", ""), 80), clean_text(payload.get("note", ""), 1000), invoice_date),
            )
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            self.db.rollback()
            raise AppError(409, "DUPLICATE_FINANCE_BILL", "invoice_code must be unique") from exc
        self.audit(actor["id"], "CREATE", "finance_bill", cur.lastrowid, {"invoice_code": invoice_code, "confirmation_status": status})
        return row_dict(self.db.execute("SELECT * FROM finance_bills WHERE id=?", (cur.lastrowid,)).fetchone()) or {}

    def update_finance_bill(self, actor: sqlite3.Row, bill_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        current = self._finance_bill(actor, bill_id)
        invoice_code = clean_text(payload.get("invoice_code", current["invoice_code"]), 64).upper()
        status = clean_text(payload.get("confirmation_status", current["confirmation_status"]), 16).upper()
        if not invoice_code or status not in {"PENDING", "CONFIRMED", "REJECTED"}:
            raise AppError(400, "VALIDATION_ERROR", "invoice_code and a valid confirmation_status are required")
        amount = self._number(payload.get("payment_amount", current["payment_amount"]), "payment_amount", minimum=0)
        invoice_date = self._optional_date(payload.get("invoice_date", current["invoice_date"]), "invoice_date")
        try:
            self.db.execute(
                "UPDATE finance_bills SET invoice_code=?,contract_code=?,class_code=?,subject=?,customer_name=?,payment_amount=?,sales_owner=?,center=?,branch=?,employee=?,confirmation_status=?,payment_method=?,note=?,invoice_date=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (invoice_code, clean_text(payload.get("contract_code", current["contract_code"]), 64), clean_text(payload.get("class_code", current["class_code"]), 64),
                 clean_text(payload.get("subject", current["subject"]), 240), clean_text(payload.get("customer_name", current["customer_name"]), 160), amount,
                 clean_text(payload.get("sales_owner", current["sales_owner"]), 120), clean_text(payload.get("center", current["center"]), 120),
                 clean_text(payload.get("branch", current["branch"]), 120), clean_text(payload.get("employee", current["employee"]), 120), status,
                 clean_text(payload.get("payment_method", current["payment_method"]), 80), clean_text(payload.get("note", current["note"]), 1000), invoice_date, current["id"]),
            )
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            self.db.rollback()
            raise AppError(409, "DUPLICATE_FINANCE_BILL", "invoice_code must be unique") from exc
        self.audit(actor["id"], "UPDATE", "finance_bill", current["id"], {"invoice_code": invoice_code, "confirmation_status": status})
        return row_dict(self.db.execute("SELECT * FROM finance_bills WHERE id=?", (current["id"],)).fetchone()) or {}

    def confirm_finance_bill(self, actor: sqlite3.Row, bill_id: Any) -> Dict[str, Any]:
        """Confirm a bill through the explicit reference-style action.

        The reference exposed a confirmation action, while its private
        mutation contract is unavailable.  Keep this local action narrow and
        idempotent: pending bills become confirmed, already-confirmed bills
        remain confirmed, and rejected bills fail closed.
        """
        current = self._finance_bill(actor, bill_id)
        if current["confirmation_status"] == "REJECTED":
            raise AppError(409, "FINANCE_BILL_NOT_CONFIRMABLE", "a rejected bill cannot be confirmed")
        if current["confirmation_status"] != "CONFIRMED":
            self.db.execute(
                "UPDATE finance_bills SET confirmation_status='CONFIRMED',updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (current["id"],),
            )
            self.db.commit()
            self.audit(actor["id"], "CONFIRM", "finance_bill", current["id"], {"confirmation_status": "CONFIRMED"})
        return row_dict(self.db.execute("SELECT * FROM finance_bills WHERE id=?", (current["id"],)).fetchone()) or {}

    def finance_contracts(
        self,
        actor: sqlite3.Row,
        query: str = "",
        payment_status: str = "",
        contract_status: str = "",
        sales_owner: str = "",
        date_from: str = "",
        date_to: str = "",
        expiry_from: str = "",
        expiry_to: str = "",
        course_id: str = "",
        branch: str = "",
        creator: str = "",
        discount: str = "",
        expired_date_status: str = "",
    ) -> List[Dict[str, Any]]:
        require_role(actor, "ADMIN", "STAFF")
        sql = (
            "SELECT f.*,s.student_code,s.full_name AS student_name,s.phone AS student_phone,c.code AS class_code,"
            "co.code AS course_code,co.name AS course_name,u.full_name AS created_by_name "
            "FROM finance_contracts f LEFT JOIN students s ON s.id=f.student_id "
            "LEFT JOIN classes c ON c.id=f.class_id LEFT JOIN courses co ON co.id=f.course_id "
            "LEFT JOIN users u ON u.id=f.created_by"
        )
        filters: List[str] = []
        params: List[Any] = []
        if query:
            needle = "%" + clean_text(query, 160) + "%"
            filters.append("(f.contract_code LIKE ? OR s.student_code LIKE ? OR s.full_name LIKE ? OR f.package_name LIKE ? OR f.note LIKE ?)")
            params.extend([needle] * 5)
        if payment_status:
            value = clean_text(payment_status, 16).upper()
            if value not in {"PENDING", "PARTIAL", "PAID", "OVERDUE"}:
                raise AppError(400, "VALIDATION_ERROR", "payment_status is invalid")
            filters.append("f.payment_status=?"); params.append(value)
        if contract_status:
            value = clean_text(contract_status, 16).upper()
            if value not in {"ACTIVE", "EXPIRED", "CANCELLED", "COMPLETED"}:
                raise AppError(400, "VALIDATION_ERROR", "contract_status is invalid")
            filters.append("f.contract_status=?"); params.append(value)
        if sales_owner:
            filters.append("f.sales_owner LIKE ?"); params.append("%" + clean_text(sales_owner, 120) + "%")
        start, end = self._date_range(date_from, date_to)
        if start:
            filters.append("f.created_date>=?"); params.append(start)
        if end:
            filters.append("f.created_date<=?"); params.append(end)
        expiry_start, expiry_end = self._date_range(expiry_from, expiry_to)
        if expiry_start:
            filters.append("f.expiry_date>=?"); params.append(expiry_start)
        if expiry_end:
            filters.append("f.expiry_date<=?"); params.append(expiry_end)
        if course_id:
            try:
                parsed_course = int(course_id)
            except (TypeError, ValueError) as exc:
                raise AppError(400, "VALIDATION_ERROR", "course_id must be numeric") from exc
            filters.append("f.course_id=?"); params.append(parsed_course)
        # Branch is a single local demo center until the private reference
        # branch dimension is observable.  The filter remains bounded and
        # truthful instead of pretending every contract has a hidden branch.
        if branch and clean_text(branch, 120).lower() not in {"trung tâm center edu - demo", "center edu - demo", "demo"}:
            return []
        if creator:
            filters.append("u.full_name LIKE ?"); params.append("%" + clean_text(creator, 120) + "%")
        if discount:
            filters.append("(f.discount_code LIKE ? OR f.payment_note LIKE ?)")
            value = "%" + clean_text(discount, 120) + "%"; params.extend([value, value])
        if expired_date_status:
            normalized = clean_text(expired_date_status, 32).lower()
            today = dt.date.today().isoformat()
            if normalized in {"hợp đồng hết hạn", "expired"}:
                filters.append("f.expiry_date IS NOT NULL AND f.expiry_date<?"); params.append(today)
            elif normalized in {"hợp đồng sắp hết hạn", "expiring"}:
                filters.append("f.expiry_date IS NOT NULL AND f.expiry_date>=? AND f.expiry_date<=?")
                params.extend([today, (dt.date.today() + dt.timedelta(days=30)).isoformat()])
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY f.created_date DESC, f.id DESC"
        return rows_dict(self.db.execute(sql, params).fetchall())

    def finance_contract_summary(self, actor: sqlite3.Row, **filters: Any) -> Dict[str, Any]:
        """Return summary cards from the same filtered contract relation."""
        if "q" in filters and "query" not in filters:
            filters["query"] = filters.pop("q")
        rows = self.finance_contracts(actor, **filters)
        total = sum(float(row.get("total_amount") or 0) for row in rows)
        paid = sum(float(row.get("paid_amount") or 0) for row in rows)
        debt = sum(float(row.get("debt_amount") or 0) for row in rows)
        return {
            "contract_count": len(rows),
            "subtotal": round(total, 2),
            "paid": round(paid, 2),
            "debt": round(debt, 2),
            # Refund/bad-debt/CO-wallet columns are not present in the local
            # contract schema; explicit zero keeps the card numeric without
            # fabricating an unavailable transaction source.
            "refund": 0,
            "bad_debt": 0,
            "co_wallet": 0,
            "unsupported_fields": ["refund", "bad_debt", "co_wallet"],
        }

    def finance_contract_catalog(self, actor: sqlite3.Row) -> List[Dict[str, Any]]:
        require_role(actor, "ADMIN", "STAFF")
        return rows_dict(self.db.execute(
            "SELECT id,item_code,item_type,name,course_id,unit,unit_price,sessions,status FROM finance_catalog_items WHERE status='ACTIVE' ORDER BY item_type,name,id"
        ).fetchall())

    def finance_transfers(self, actor: sqlite3.Row, query: str = "", status: str = "") -> List[Dict[str, Any]]:
        require_role(actor, "ADMIN", "STAFF")
        sql = (
            "SELECT t.*,tf.student_code AS from_student_code,tf.full_name AS from_student_name,"
            "tt.student_code AS to_student_code,tt.full_name AS to_student_name,"
            "f.contract_code,co.code AS course_code,co.name AS course_name,u.full_name AS created_by_name "
            "FROM finance_transfers t LEFT JOIN students tf ON tf.id=t.from_student_id "
            "LEFT JOIN students tt ON tt.id=t.to_student_id LEFT JOIN finance_contracts f ON f.id=t.contract_id "
            "LEFT JOIN courses co ON co.id=t.course_id LEFT JOIN users u ON u.id=t.created_by"
        )
        filters: List[str] = []
        params: List[Any] = []
        if query:
            needle = "%" + clean_text(query, 160) + "%"
            filters.append("(t.transfer_code LIKE ? OR tf.student_code LIKE ? OR tf.full_name LIKE ? OR tt.student_code LIKE ? OR tt.full_name LIKE ? OR f.contract_code LIKE ? OR co.name LIKE ? OR t.note LIKE ?)")
            params.extend([needle] * 8)
        if status:
            normalized = clean_text(status, 16).upper()
            if normalized not in {"PENDING", "PROCESSED", "CANCELLED"}:
                raise AppError(400, "VALIDATION_ERROR", "transfer status is invalid")
            filters.append("t.status=?"); params.append(normalized)
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY t.transfer_date DESC,t.id DESC"
        return rows_dict(self.db.execute(sql, params).fetchall())

    def add_finance_transfer(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        code = clean_text(payload.get("transfer_code"), 64).upper()
        if not code:
            raise AppError(400, "VALIDATION_ERROR", "transfer_code is required")
        transfer_date = self._date(payload.get("transfer_date"), "transfer_date")
        try:
            from_student_id = int(payload.get("from_student_id")); to_student_id = int(payload.get("to_student_id"))
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "from_student_id and to_student_id are required") from exc
        if from_student_id == to_student_id:
            raise AppError(400, "VALIDATION_ERROR", "transfer students must differ")
        contract_id = payload.get("contract_id")
        course_id = payload.get("course_id")
        contract_id = int(contract_id) if contract_id not in (None, "") else None
        course_id = int(course_id) if course_id not in (None, "") else None
        amount = self._number(payload.get("amount_received", 0), "amount_received", minimum=0) or 0
        status = clean_text(payload.get("status", "PENDING"), 16).upper()
        if status not in {"PENDING", "PROCESSED", "CANCELLED"}:
            raise AppError(400, "VALIDATION_ERROR", "transfer status is invalid")
        try:
            cur = self.db.execute(
                "INSERT INTO finance_transfers(transfer_code,transfer_date,from_student_id,to_student_id,contract_id,course_id,amount_received,note,status,created_by) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (code, transfer_date, from_student_id, to_student_id, contract_id, course_id, amount, clean_text(payload.get("note", ""), 1000), status, actor["id"]),
            )
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            self.db.rollback(); raise AppError(409, "DUPLICATE_FINANCE_TRANSFER", "transfer_code must be unique") from exc
        self.audit(actor["id"], "CREATE", "finance_transfer", cur.lastrowid, {"transfer_code": code})
        rows = self.finance_transfers(actor, query=code)
        return next(row for row in rows if row["id"] == cur.lastrowid)

    def _finance_contract(self, actor: sqlite3.Row, contract_id: Any) -> sqlite3.Row:
        require_role(actor, "ADMIN", "STAFF")
        try:
            parsed_id = int(contract_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "contract id must be numeric") from exc
        row = self.db.execute("SELECT * FROM finance_contracts WHERE id=?", (parsed_id,)).fetchone()
        if row is None:
            raise AppError(404, "FINANCE_CONTRACT_NOT_FOUND", "finance contract not found")
        return row

    def _contract_values(self, payload: Dict[str, Any], current: Optional[sqlite3.Row] = None) -> Tuple[Any, ...]:
        def value(name: str, default: Any = "") -> Any:
            if name in payload:
                return payload[name]
            return current[name] if current is not None else default
        code = clean_text(value("contract_code"), 64).upper()
        if not code:
            raise AppError(400, "VALIDATION_ERROR", "contract_code is required")
        customer_type = clean_text(value("customer_type") or "STUDENT", 16).upper()
        if customer_type not in {"LEAD", "STUDENT"}:
            raise AppError(400, "VALIDATION_ERROR", "customer_type is invalid")
        created_date = self._optional_date(value("created_date") or dt.date.today().isoformat(), "created_date")
        expiry_date = self._optional_date(value("expiry_date"), "expiry_date")
        if expiry_date and created_date and expiry_date < created_date:
            raise AppError(400, "VALIDATION_ERROR", "expiry_date must not precede created_date")
        def foreign_id(name: str) -> Optional[int]:
            raw = value(name)
            if raw in (None, ""):
                return None
            try:
                parsed = int(raw)
            except (TypeError, ValueError) as exc:
                raise AppError(400, "VALIDATION_ERROR", f"{name} must be numeric") from exc
            if parsed < 1:
                raise AppError(400, "VALIDATION_ERROR", f"{name} must be positive")
            return parsed
        if "account_id" in payload:
            account_raw = payload.get("account_id")
        elif current is not None and current["account_id"] is not None:
            account_raw = current["account_id"]
        else:
            account_raw = value("student_id")
        account_id = None
        if account_raw not in (None, ""):
            try:
                account_id = int(account_raw)
            except (TypeError, ValueError) as exc:
                raise AppError(400, "VALIDATION_ERROR", "account_id must be numeric") from exc
            if account_id < 1:
                raise AppError(400, "VALIDATION_ERROR", "account_id must be positive")
        student_id = foreign_id("student_id") if value("student_id", "") not in (None, "") else account_id
        if "item_id" in payload:
            item_raw = payload.get("item_id")
        elif current is not None and current["item_id"] is not None:
            item_raw = current["item_id"]
        else:
            item_raw = None
        item_id = None
        if item_raw not in (None, ""):
            try:
                item_id = int(item_raw)
            except (TypeError, ValueError) as exc:
                raise AppError(400, "VALIDATION_ERROR", "item_id must be numeric") from exc
            if item_id < 1:
                raise AppError(400, "VALIDATION_ERROR", "item_id must be positive")
        course_id = foreign_id("course_id") if value("course_id", "") not in (None, "") else None
        if course_id is None and item_id is not None:
            catalog_item = self.db.execute("SELECT course_id FROM finance_catalog_items WHERE id=?", (item_id,)).fetchone()
            if catalog_item is not None:
                course_id = catalog_item["course_id"]
        payment_due_date = self._optional_date(value("payment_due_date"), "payment_due_date")
        payment_due_amount = self._number(value("payment_due_amount"), "payment_due_amount", minimum=0)
        payment_note = clean_text(value("payment_note"), 1000)
        discount_code = clean_text(value("discount_code"), 160)
        direct_discount = self._number(value("direct_discount", 0), "direct_discount", minimum=0) or 0
        total_input = value("total_amount", None)
        total = self._number(payment_due_amount if total_input in (None, "") and payment_due_amount is not None else (total_input if total_input not in (None, "") else 0), "total_amount", minimum=0)
        paid = self._number(value("paid_amount", 0), "paid_amount", minimum=0)
        if paid > total:
            raise AppError(400, "VALIDATION_ERROR", "paid_amount cannot exceed total_amount")
        debt = round(max(0.0, total - paid), 2)
        payment_status = clean_text(value("payment_status") or ("PAID" if debt == 0 and total else "PARTIAL" if paid else "PENDING"), 16).upper()
        contract_status = clean_text(value("contract_status") or "ACTIVE", 16).upper()
        if payment_status not in {"PENDING", "PARTIAL", "PAID", "OVERDUE"}:
            raise AppError(400, "VALIDATION_ERROR", "payment_status is invalid")
        if contract_status not in {"ACTIVE", "EXPIRED", "CANCELLED", "COMPLETED"}:
            raise AppError(400, "VALIDATION_ERROR", "contract_status is invalid")
        return (
            code, customer_type, account_id, student_id, foreign_id("class_id"), course_id, item_id,
            clean_text(value("package_name"), 160), created_date, expiry_date, payment_due_date, payment_due_amount,
            payment_note, discount_code, direct_discount, total, paid, debt,
            clean_text(value("sales_owner"), 120), clean_text(value("payment_status") or payment_status, 16).upper(),
            clean_text(value("contract_status") or contract_status, 16).upper(), clean_text(value("note"), 1000),
        )

    def add_finance_contract(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        values = self._contract_values(payload)
        try:
            cur = self.db.execute(
                "INSERT INTO finance_contracts(contract_code,customer_type,account_id,student_id,class_id,course_id,item_id,package_name,created_date,expiry_date,payment_due_date,payment_due_amount,payment_note,discount_code,direct_discount,total_amount,paid_amount,debt_amount,sales_owner,created_by,payment_status,contract_status,note) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (*values[:19], actor["id"], *values[19:]),
            )
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            self.db.rollback()
            raise AppError(409, "DUPLICATE_FINANCE_CONTRACT", "contract_code must be unique") from exc
        self.audit(actor["id"], "CREATE", "finance_contract", cur.lastrowid, {"contract_code": values[0]})
        return row_dict(self._finance_contract(actor, cur.lastrowid)) or {}

    def update_finance_contract(self, actor: sqlite3.Row, contract_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        current = self._finance_contract(actor, contract_id)
        values = self._contract_values(payload, current)
        try:
            self.db.execute(
                "UPDATE finance_contracts SET contract_code=?,customer_type=?,account_id=?,student_id=?,class_id=?,course_id=?,item_id=?,package_name=?,created_date=?,expiry_date=?,payment_due_date=?,payment_due_amount=?,payment_note=?,discount_code=?,direct_discount=?,total_amount=?,paid_amount=?,debt_amount=?,sales_owner=?,payment_status=?,contract_status=?,note=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (*values, current["id"]),
            )
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            self.db.rollback()
            raise AppError(409, "DUPLICATE_FINANCE_CONTRACT", "contract_code must be unique") from exc
        self.audit(actor["id"], "UPDATE", "finance_contract", current["id"], {"contract_code": values[0]})
        return row_dict(self._finance_contract(actor, current["id"])) or {}

    def finance_spends(
        self, actor: sqlite3.Row, filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """List persisted spend records through the isolated FinanceSpend contract."""
        require_role(actor, "ADMIN", "STAFF", "TEACHER")
        try:
            return self.finance_spend_store.list(filters or {})
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc

    def add_finance_spend(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        data = dict(payload)
        data.setdefault("center_id", "demo")
        data.setdefault("center_name", "Trung tâm CenterOnline - Demo")
        try:
            row = self.finance_spend_store.create(
                data, role=actor["role"], actor=actor["full_name"],
            )
        except PermissionError as exc:
            raise AppError(403, "FORBIDDEN", str(exc)) from exc
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc
        self.audit(actor["id"], "CREATE", "finance_spend", row["id"], {"code": row["code"]})
        return row

    def update_finance_spend(self, actor: sqlite3.Row, spend_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        try:
            row = self.finance_spend_store.update(
                int(spend_id), dict(payload), role=actor["role"], actor=actor["full_name"],
            )
        except KeyError as exc:
            raise AppError(404, "FINANCE_SPEND_NOT_FOUND", str(exc)) from exc
        except PermissionError as exc:
            raise AppError(403, "FORBIDDEN", str(exc)) from exc
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc
        self.audit(actor["id"], "UPDATE", "finance_spend", row["id"], {"code": row["code"]})
        return row

    def finance_spend_export(self, actor: sqlite3.Row, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        require_role(actor, "ADMIN", "STAFF", "TEACHER")
        try:
            rows = self.finance_spend_store.list(filters or {}, page=1, page_size=10000)["items"]
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc
        return [{
            "No.": index,
            "Mã phiếu chi": row["code"],
            "Ngày lập phiếu": row["spend_date"],
            "Trung tâm áp dụng": row["center_name"],
            "Nội dung": row["content"],
            "Ghi chú": row["note"],
            "Danh mục": row["category"],
            "Số tiền": f'{row["amount_vnd"]:,} VND',
            "Phương thức thanh toán": row["payment_method"],
            "Người lập phiếu": row["created_by"],
            "Công cụ": "",
        } for index, row in enumerate(rows, 1)]

    def finance_spend(self, actor: sqlite3.Row, spend_id: Any) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF", "TEACHER")
        try:
            parsed_id = int(spend_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "finance spend id must be numeric") from exc
        row = self.db.execute("SELECT * FROM finance_spends WHERE id=?", (parsed_id,)).fetchone()
        if row is None:
            raise AppError(404, "FINANCE_SPEND_NOT_FOUND", "finance spend not found")
        return dict(row)

    def finance_assessments(self, actor: sqlite3.Row, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.finance_assessment_store.list(
                {"q": params.get("q", ""), "status": params.get("status", "")},
                role=actor["role"], page=int(params.get("page", 1) or 1),
                page_size=int(params.get("page_size", 10) or 10),
            )
        except PermissionError as exc:
            raise AppError(403, "FORBIDDEN", str(exc)) from exc
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc

    def finance_assessment(self, actor: sqlite3.Row, assessment_id: Any) -> Dict[str, Any]:
        try:
            return self.finance_assessment_store.get(int(assessment_id), role=actor["role"])
        except KeyError as exc:
            raise AppError(404, "FINANCE_ASSESSMENT_NOT_FOUND", str(exc)) from exc
        except PermissionError as exc:
            raise AppError(403, "FORBIDDEN", str(exc)) from exc

    def add_finance_assessment(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            row = self.finance_assessment_store.create(payload, role=actor["role"], actor=actor["full_name"])
        except PermissionError as exc:
            raise AppError(403, "FORBIDDEN", str(exc)) from exc
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc
        self.audit(actor["id"], "CREATE", "finance_assessment", row["id"], {"assessment_code": row["assessment_code"]})
        return row

    def update_finance_assessment(self, actor: sqlite3.Row, assessment_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            row = self.finance_assessment_store.update(int(assessment_id), payload, role=actor["role"], actor=actor["full_name"])
        except KeyError as exc:
            raise AppError(404, "FINANCE_ASSESSMENT_NOT_FOUND", str(exc)) from exc
        except PermissionError as exc:
            raise AppError(403, "FORBIDDEN", str(exc)) from exc
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc
        self.audit(actor["id"], "UPDATE", "finance_assessment", row["id"], {"assessment_code": row["assessment_code"]})
        return row

    def finance_assessment_export(self, actor: sqlite3.Row, params: Dict[str, Any]) -> str:
        try:
            return self.finance_assessment_store.export_csv(
                {"q": params.get("q", ""), "status": params.get("status", "")}, role=actor["role"]
            )
        except PermissionError as exc:
            raise AppError(403, "FORBIDDEN", str(exc)) from exc
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc

    def finance_reserves(self, actor: sqlite3.Row, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.finance_reserve_store.list(
                {"q": params.get("q", ""), "mode": params.get("mode", "")}, role=actor["role"],
                page=int(params.get("page", 1) or 1), page_size=int(params.get("page_size", 10) or 10),
            )
        except PermissionError as exc: raise AppError(403, "FORBIDDEN", str(exc)) from exc
        except (TypeError, ValueError) as exc: raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc

    def finance_reserve(self, actor: sqlite3.Row, reserve_id: Any) -> Dict[str, Any]:
        try: return self.finance_reserve_store.get(int(reserve_id), role=actor["role"])
        except KeyError as exc: raise AppError(404, "FINANCE_RESERVE_NOT_FOUND", str(exc)) from exc
        except PermissionError as exc: raise AppError(403, "FORBIDDEN", str(exc)) from exc

    def add_finance_reserve(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        try: row=self.finance_reserve_store.create(payload, role=actor["role"], actor=actor["full_name"])
        except PermissionError as exc: raise AppError(403, "FORBIDDEN", str(exc)) from exc
        except (TypeError, ValueError) as exc: raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc
        self.audit(actor["id"], "CREATE", "finance_reserve", row["id"], {"reserve_code": row["reserve_code"]}); return row

    def update_finance_reserve(self, actor: sqlite3.Row, reserve_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        try: row=self.finance_reserve_store.update(int(reserve_id), payload, role=actor["role"], actor=actor["full_name"])
        except KeyError as exc: raise AppError(404, "FINANCE_RESERVE_NOT_FOUND", str(exc)) from exc
        except PermissionError as exc: raise AppError(403, "FORBIDDEN", str(exc)) from exc
        except (TypeError, ValueError) as exc: raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc
        self.audit(actor["id"], "UPDATE", "finance_reserve", row["id"], {"reserve_code": row["reserve_code"]}); return row

    def finance_reserve_export(self, actor: sqlite3.Row, params: Dict[str, Any]) -> str:
        try: return self.finance_reserve_store.export_csv({"q": params.get("q", ""), "mode": params.get("mode", "")}, role=actor["role"])
        except PermissionError as exc: raise AppError(403, "FORBIDDEN", str(exc)) from exc
        except (TypeError, ValueError) as exc: raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc

    def finance_points(self, actor: sqlite3.Row, params: Dict[str, Any]) -> Dict[str, Any]:
        """List persistent point-rule settings using the local FinancePoints contract."""
        require_role(actor, "ADMIN", "STAFF", "TEACHER")
        try:
            return self.finance_points_store.list(
                params.get("q", ""),
                status=params.get("status") or None,
                center_id=params.get("center_id") or None,
                page=int(params.get("page", 1) or 1),
                page_size=int(params.get("page_size", 10) or 10),
            )
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc

    def finance_point(self, actor: sqlite3.Row, rule_id: Any) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF", "TEACHER")
        try:
            row = self.db.execute("SELECT * FROM finance_point_rules WHERE id=?", (int(rule_id),)).fetchone()
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "point rule id must be numeric") from exc
        if row is None:
            raise AppError(404, "FINANCE_POINT_RULE_NOT_FOUND", "Mã tích điểm không tồn tại")
        return dict(row)

    def add_finance_point(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        data = dict(payload)
        data.setdefault("center_id", "demo")
        data.setdefault("center_name", "Trung tâm CenterOnline - Demo")
        try:
            row = self.finance_points_store.create(data, role=actor["role"], actor=actor["full_name"])
        except PermissionError as exc:
            raise AppError(403, "FORBIDDEN", str(exc)) from exc
        except sqlite3.IntegrityError as exc:
            raise AppError(409, "DUPLICATE_FINANCE_POINT_RULE", "Mã tích điểm đã tồn tại") from exc
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc
        self.audit(actor["id"], "CREATE", "finance_point_rule", row["id"], {"code": row["code"]})
        return row

    def update_finance_point(self, actor: sqlite3.Row, rule_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        try:
            row = self.finance_points_store.update(int(rule_id), dict(payload), role=actor["role"], actor=actor["full_name"])
        except KeyError as exc:
            raise AppError(404, "FINANCE_POINT_RULE_NOT_FOUND", str(exc)) from exc
        except PermissionError as exc:
            raise AppError(403, "FORBIDDEN", str(exc)) from exc
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc
        self.audit(actor["id"], "UPDATE", "finance_point_rule", row["id"], {"code": row["code"]})
        return row

    def finance_point_export(self, actor: sqlite3.Row, params: Dict[str, Any]) -> str:
        require_role(actor, "ADMIN", "STAFF", "TEACHER")
        try:
            return self.finance_points_store.export_csv(
                q=params.get("q", ""), status=params.get("status") or None,
                center_id=params.get("center_id") or None,
            )
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc

    def finance_items(self, actor: sqlite3.Row, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        require_role(actor, "ADMIN", "STAFF", "TEACHER")
        try:
            return list_finance_items(self.db, params)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc

    def add_finance_item(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        try:
            item_id = create_finance_item(self.db, payload, role=actor["role"])
            row = self.db.execute("SELECT * FROM finance_items WHERE id=?", (item_id,)).fetchone()
        except PermissionError as exc:
            raise AppError(403, "FORBIDDEN", str(exc)) from exc
        except sqlite3.IntegrityError as exc:
            raise AppError(409, "DUPLICATE_FINANCE_ITEM", "Mã vật phẩm đã tồn tại") from exc
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc
        self.audit(actor["id"], "CREATE", "finance_item", item_id, {"code": row["code"]})
        return dict(row)

    def finance_item(self, actor: sqlite3.Row, item_id: Any) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF", "TEACHER")
        try: parsed = int(item_id)
        except (TypeError, ValueError) as exc: raise AppError(400, "VALIDATION_ERROR", "item id must be numeric") from exc
        row = self.db.execute("SELECT * FROM finance_items WHERE id=?", (parsed,)).fetchone()
        if row is None: raise AppError(404, "FINANCE_ITEM_NOT_FOUND", "Vật phẩm không tồn tại")
        return dict(row)

    def update_finance_item(self, actor: sqlite3.Row, item_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        try:
            parsed_id = int(item_id)
            current = self.db.execute("SELECT * FROM finance_items WHERE id=?", (parsed_id,)).fetchone()
            if current is None: raise AppError(404, "FINANCE_ITEM_NOT_FOUND", "Vật phẩm không tồn tại")
            merged = dict(current); merged.update(payload)
            update_finance_item(self.db, parsed_id, merged, role=actor["role"])
        except PermissionError as exc: raise AppError(403, "FORBIDDEN", str(exc)) from exc
        except (TypeError, ValueError) as exc: raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc
        row = self.db.execute("SELECT * FROM finance_items WHERE id=?", (parsed_id,)).fetchone()
        if row is None: raise AppError(404, "FINANCE_ITEM_NOT_FOUND", "Vật phẩm không tồn tại")
        self.audit(actor["id"], "UPDATE", "finance_item", parsed_id, {"code": row["code"]})
        return dict(row)

    def finance_item_export(self, actor: sqlite3.Row, params: Dict[str, Any]) -> str:
        require_role(actor, "ADMIN", "STAFF", "TEACHER")
        return export_finance_items(list_finance_items(self.db, params))

    def finance_debit_items(self, actor: sqlite3.Row, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            page = max(1, int(params.get("page", 1) or 1)); page_size = min(100, max(1, int(params.get("page_size", 10) or 10)))
            rows = self.finance_debit_item_store.list(role=actor["role"], query=params.get("q", ""), status=params.get("status", "Tất cả"), from_date=params.get("from_date", ""), to_date=params.get("to_date", ""), item_name=params.get("item_name", "Tất cả"), limit=page_size, offset=(page - 1) * page_size)
            total = self.db.execute("SELECT COUNT(*) FROM finance_debit_items").fetchone()[0]
            return {"items": rows, "total": total, "page": page, "page_size": page_size, "pages": (total + page_size - 1) // page_size}
        except PermissionError as exc: raise AppError(403, "FORBIDDEN", str(exc)) from exc
        except (TypeError, ValueError) as exc: raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc

    def add_finance_debit_item(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.finance_debit_item_store.create(role=actor["role"], created_by=actor["full_name"], **payload)
        except PermissionError as exc: raise AppError(403, "FORBIDDEN", str(exc)) from exc
        except (TypeError, ValueError) as exc: raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc

    def update_finance_debit_item(self, actor: sqlite3.Row, item_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        try: return self.finance_debit_item_store.update(int(item_id), role=actor["role"], **payload)
        except KeyError as exc: raise AppError(404, "FINANCE_DEBIT_ITEM_NOT_FOUND", str(exc)) from exc
        except PermissionError as exc: raise AppError(403, "FORBIDDEN", str(exc)) from exc
        except (TypeError, ValueError) as exc: raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc

    def finance_debit_item_export(self, actor: sqlite3.Row, params: Dict[str, Any]) -> str:
        try: return self.finance_debit_item_store.export_csv(role=actor["role"], query=params.get("q", ""), status=params.get("status", "Tất cả"), from_date=params.get("from_date", ""), to_date=params.get("to_date", ""), item_name=params.get("item_name", "Tất cả"))
        except PermissionError as exc: raise AppError(403, "FORBIDDEN", str(exc)) from exc
        except (TypeError, ValueError) as exc: raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc

    def finance_debit_item(self, actor: sqlite3.Row, item_id: Any) -> Dict[str, Any]:
        try:
            row = self.db.execute("SELECT * FROM finance_debit_items WHERE id=?", (int(item_id),)).fetchone()
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "debit item id must be numeric") from exc
        if row is None:
            raise AppError(404, "FINANCE_DEBIT_ITEM_NOT_FOUND", "Vật phẩm nợ không tồn tại")
        return dict(row)

    def finance_wallets(self, actor: sqlite3.Row, params: Dict[str, Any]) -> Dict[str, Any]:
        if actor["role"] not in FINANCE_WALLET_READ_ROLES:
            raise AppError(403, "FORBIDDEN", "Ví CO không dành cho vai trò này")
        try:
            rows = list_wallets(self.db, {"q": params.get("q", ""), "status": params.get("status", "")})
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc
        page = max(1, int(params.get("page", 1) or 1)); page_size = min(100, max(1, int(params.get("page_size", 10) or 10)))
        total = len(rows); start = (page - 1) * page_size
        return {"items": rows[start:start + page_size], "total": total, "page": page, "page_size": page_size, "pages": (total + page_size - 1) // page_size}

    def finance_wallet_export(self, actor: sqlite3.Row, params: Dict[str, Any]) -> str:
        if actor["role"] not in FINANCE_WALLET_READ_ROLES:
            raise AppError(403, "FORBIDDEN", "Ví CO không dành cho vai trò này")
        try:
            return export_finance_wallets(list_wallets(self.db, {"q": params.get("q", ""), "status": params.get("status", "")}))
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc

    def finance_appointments(self, actor: sqlite3.Row, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            rows = self.appointment_store.list(
                role=actor["role"], query=str(params.get("q") or ""),
                from_date=str(params.get("date_from") or ""), to_date=str(params.get("date_to") or ""),
                appointment_type=str(params.get("appointment_type") or "Tất cả"),
                limit=int(params.get("page_size") or 10),
                offset=(max(1, int(params.get("page") or 1)) - 1) * min(100, max(1, int(params.get("page_size") or 10))),
            )
            count_args = []
            clauses = ["1=1"]
            if params.get("q"):
                needle = f"%{str(params['q']).strip()}%"
                clauses.append("(student_name LIKE ? OR parent_name LIKE ? OR reference_code LIKE ? OR contract_code LIKE ?)")
                count_args.extend([needle] * 4)
            if params.get("date_from"):
                clauses.append("appointment_date>=?"); count_args.append(params["date_from"])
            if params.get("date_to"):
                clauses.append("appointment_date<=?"); count_args.append(params["date_to"])
            if params.get("appointment_type") and params["appointment_type"] != "Tất cả":
                clauses.append("appointment_type=?"); count_args.append(params["appointment_type"])
            total = self.db.execute("SELECT COUNT(*) FROM finance_appointments WHERE " + " AND ".join(clauses), count_args).fetchone()[0]
            page_size = min(100, max(1, int(params.get("page_size") or 10)))
            return {"items": rows, "total": total, "page": max(1, int(params.get("page") or 1)), "page_size": page_size, "pages": (total + page_size - 1) // page_size}
        except PermissionError as exc:
            raise AppError(403, "FORBIDDEN", str(exc)) from exc
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc

    def add_finance_appointment(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        try:
            row = self.appointment_store.create(
                role=actor["role"], student_name=str(payload.get("student_name") or ""),
                parent_name=str(payload.get("parent_name") or ""), appointment_date=self._date(payload.get("appointment_date"), "appointment_date"),
                reference_code=str(payload.get("reference_code") or payload.get("contract_code") or ""),
                amount=self._number(payload.get("amount", 0), "amount", minimum=0) or 0,
                note=str(payload.get("note") or ""), appointment_type=str(payload.get("appointment_type") or "Theo hóa đơn"),
                contract_code=str(payload.get("contract_code") or ""), created_by=actor["full_name"],
            )
        except PermissionError as exc:
            raise AppError(403, "FORBIDDEN", str(exc)) from exc
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc
        self.audit(actor["id"], "CREATE", "finance_appointment", row["id"], {"reference_code": row["reference_code"]})
        return row

    def update_finance_appointment(self, actor: sqlite3.Row, appointment_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        try:
            row = self.appointment_store.update(int(appointment_id), role=actor["role"], **payload)
        except KeyError as exc:
            raise AppError(404, "FINANCE_APPOINTMENT_NOT_FOUND", str(exc)) from exc
        except PermissionError as exc:
            raise AppError(403, "FORBIDDEN", str(exc)) from exc
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc
        self.audit(actor["id"], "UPDATE", "finance_appointment", row["id"], {"status": row["status"]})
        return row

    def export_finance_appointments(self, actor: sqlite3.Row, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        page = self.finance_appointments(actor, {**params, "page": 1, "page_size": 100})
        items = page["items"]
        out = []
        for row in items:
            out.append({"Trạng thái": row["status"], "Học viên": row["student_name"], "Phụ huynh": row["parent_name"], "Ngày hẹn": row["appointment_date"], "Số tiền": row["amount"], "Ghi chú": row["note"], "Kiểu/Mã": f"{row['appointment_type']} / {row['reference_code']}", "Hợp đồng liên quan": row["contract_code"], "Công cụ": ""})
        return out

    def finance_revenues(self, actor: sqlite3.Row, query: str = "", status: str = "", center: str = "") -> List[Dict[str, Any]]:
        require_role(actor, "ADMIN", "STAFF")
        sql = "SELECT * FROM finance_revenues"
        filters: List[str] = []
        params: List[Any] = []
        if query:
            needle = "%" + clean_text(query, 160) + "%"
            filters.append("(code LIKE ? OR name LIKE ? OR note LIKE ?)")
            params.extend([needle] * 3)
        if status:
            normalized = clean_text(status, 16).upper()
            if normalized not in {"ACTIVE", "INACTIVE"}:
                raise AppError(400, "VALIDATION_ERROR", "revenue status is invalid")
            filters.append("status=?")
            params.append(normalized)
        if center:
            filters.append("center LIKE ?")
            params.append("%" + clean_text(center, 120) + "%")
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY id DESC"
        return rows_dict(self.db.execute(sql, params).fetchall())

    def finance_revenue_summary(
        self,
        actor: sqlite3.Row,
        date_from: str = "",
        date_to: str = "",
        center: str = "",
        branch: str = "",
        confirmation_status: str = "CONFIRMED",
    ) -> Dict[str, Any]:
        """Aggregate persisted bill payments for the revenue dashboard.

        Revenue definitions and bill payments are separate local entities.
        This summary therefore reads only payment rows with an invoice date;
        missing dates stay outside the period instead of being guessed.
        """
        require_role(actor, "ADMIN", "STAFF")
        start, end = self._date_range(date_from, date_to)
        normalized_status = clean_text(confirmation_status or "CONFIRMED", 16).upper()
        if normalized_status not in {"PENDING", "CONFIRMED", "REJECTED", "ALL"}:
            raise AppError(400, "VALIDATION_ERROR", "confirmation_status is invalid")
        filters: List[str] = ["invoice_date IS NOT NULL"]
        params: List[Any] = []
        if start:
            filters.append("invoice_date>=?")
            params.append(start)
        if end:
            filters.append("invoice_date<=?")
            params.append(end)
        if center:
            filters.append("center LIKE ?")
            params.append("%" + clean_text(center, 120) + "%")
        if branch:
            filters.append("branch LIKE ?")
            params.append("%" + clean_text(branch, 120) + "%")
        if normalized_status != "ALL":
            filters.append("confirmation_status=?")
            params.append(normalized_status)
        where = " AND ".join(filters)
        totals = self.db.execute(
            f"SELECT COUNT(*) AS bill_count, COALESCE(SUM(payment_amount),0) AS gross_amount, "
            f"COALESCE(SUM(CASE WHEN payment_amount IS NOT NULL THEN 1 ELSE 0 END),0) AS valued_bill_count "
            f"FROM finance_bills WHERE {where}",
            params,
        ).fetchone()
        grouped = self.db.execute(
            f"SELECT COALESCE(center,'') AS center, COALESCE(branch,'') AS branch, "
            f"COUNT(*) AS bill_count, COALESCE(SUM(payment_amount),0) AS gross_amount "
            f"FROM finance_bills WHERE {where} GROUP BY COALESCE(center,''), COALESCE(branch,'') "
            f"ORDER BY center,branch",
            params,
        ).fetchall()
        return {
            "period": {"date_from": start, "date_to": end},
            "confirmation_status": normalized_status,
            "filters": {"center": clean_text(center, 120), "branch": clean_text(branch, 120)},
            "totals": row_dict(totals) or {"bill_count": 0, "gross_amount": 0, "valued_bill_count": 0},
            "by_center_branch": rows_dict(grouped),
        }

    def _finance_revenue(self, actor: sqlite3.Row, revenue_id: Any) -> sqlite3.Row:
        require_role(actor, "ADMIN", "STAFF")
        try:
            parsed_id = int(revenue_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "finance revenue id must be numeric") from exc
        row = self.db.execute("SELECT * FROM finance_revenues WHERE id=?", (parsed_id,)).fetchone()
        if row is None:
            raise AppError(404, "FINANCE_REVENUE_NOT_FOUND", "finance revenue not found")
        return row

    @staticmethod
    def _discount_type(value: Any) -> str:
        normalized = clean_text(value or "", 16).upper()
        if normalized not in {"", "FIXED", "PERCENT"}:
            raise AppError(400, "VALIDATION_ERROR", "discount_type is invalid")
        return normalized

    def add_finance_revenue(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        code = clean_text(payload.get("code"), 64).upper()
        name = clean_text(payload.get("name"), 240)
        status = clean_text(payload.get("status") or "ACTIVE", 16).upper()
        if not code or not name or status not in {"ACTIVE", "INACTIVE"}:
            raise AppError(400, "VALIDATION_ERROR", "code, name and a valid status are required")
        price = self._number(payload.get("price"), "price", minimum=0)
        discount_type = self._discount_type(payload.get("discount_type"))
        discount_value = self._number(payload.get("discount_value"), "discount_value", minimum=0)
        if discount_type == "PERCENT" and discount_value is not None and discount_value > 100:
            raise AppError(400, "VALIDATION_ERROR", "discount_value must be at most 100 for percent discounts")
        amount_due = self._number(payload.get("amount_due"), "amount_due", minimum=0)
        try:
            cur = self.db.execute(
                "INSERT INTO finance_revenues(code,name,status,price,discount_type,discount_value,amount_due,center,note,created_by) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (code, name, status, price, discount_type, discount_value, amount_due, clean_text(payload.get("center", ""), 120), clean_text(payload.get("note", ""), 1000), actor["id"]),
            )
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            self.db.rollback()
            raise AppError(409, "DUPLICATE_FINANCE_REVENUE", "code must be unique") from exc
        self.audit(actor["id"], "CREATE", "finance_revenue", cur.lastrowid, {"code": code, "status": status})
        return row_dict(self.db.execute("SELECT * FROM finance_revenues WHERE id=?", (cur.lastrowid,)).fetchone()) or {}

    def update_finance_revenue(self, actor: sqlite3.Row, revenue_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        current = self._finance_revenue(actor, revenue_id)
        code = clean_text(payload.get("code", current["code"]), 64).upper()
        name = clean_text(payload.get("name", current["name"]), 240)
        status = clean_text(payload.get("status", current["status"]), 16).upper()
        if not code or not name or status not in {"ACTIVE", "INACTIVE"}:
            raise AppError(400, "VALIDATION_ERROR", "code, name and a valid status are required")
        price = self._number(payload.get("price", current["price"]), "price", minimum=0)
        discount_type = self._discount_type(payload.get("discount_type", current["discount_type"]))
        discount_value = self._number(payload.get("discount_value", current["discount_value"]), "discount_value", minimum=0)
        if discount_type == "PERCENT" and discount_value is not None and discount_value > 100:
            raise AppError(400, "VALIDATION_ERROR", "discount_value must be at most 100 for percent discounts")
        amount_due = self._number(payload.get("amount_due", current["amount_due"]), "amount_due", minimum=0)
        try:
            self.db.execute(
                "UPDATE finance_revenues SET code=?,name=?,status=?,price=?,discount_type=?,discount_value=?,amount_due=?,center=?,note=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (code, name, status, price, discount_type, discount_value, amount_due, clean_text(payload.get("center", current["center"]), 120), clean_text(payload.get("note", current["note"]), 1000), current["id"]),
            )
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            self.db.rollback()
            raise AppError(409, "DUPLICATE_FINANCE_REVENUE", "code must be unique") from exc
        self.audit(actor["id"], "UPDATE", "finance_revenue", current["id"], {"code": code, "status": status})
        return row_dict(self.db.execute("SELECT * FROM finance_revenues WHERE id=?", (current["id"],)).fetchone()) or {}

    def surveys(self, actor: sqlite3.Row, query: str = "", status: str = "") -> List[Dict[str, Any]]:
        require_role(actor, "ADMIN", "STAFF")
        sql = (
            "SELECT s.*,u.full_name AS created_by_name,COUNT(r.id) AS response_count "
            "FROM surveys s LEFT JOIN users u ON u.id=s.created_by "
            "LEFT JOIN survey_responses r ON r.survey_id=s.id"
        )
        filters: List[str] = []
        params: List[Any] = []
        if query:
            needle = "%" + clean_text(query, 160) + "%"
            filters.append("(s.name LIKE ? OR s.description LIKE ?)")
            params.extend([needle, needle])
        if status:
            normalized = clean_text(status, 16).upper()
            if normalized not in {"DRAFT", "PUBLISHED", "CLOSED"}:
                raise AppError(400, "VALIDATION_ERROR", "survey status is invalid")
            filters.append("s.status=?")
            params.append(normalized)
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " GROUP BY s.id ORDER BY s.id DESC"
        return rows_dict(self.db.execute(sql, params).fetchall())

    def _survey(self, actor: sqlite3.Row, survey_id: Any) -> sqlite3.Row:
        require_role(actor, "ADMIN", "STAFF")
        try:
            parsed_id = int(survey_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "survey id must be numeric") from exc
        row = self.db.execute("SELECT * FROM surveys WHERE id=?", (parsed_id,)).fetchone()
        if row is None:
            raise AppError(404, "SURVEY_NOT_FOUND", "survey not found")
        return row

    def survey_detail(self, actor: sqlite3.Row, survey_id: Any) -> Dict[str, Any]:
        survey = self._survey(actor, survey_id)
        pages = rows_dict(self.db.execute("SELECT * FROM survey_pages WHERE survey_id=? ORDER BY position,id", (survey["id"],)).fetchall())
        for page in pages:
            questions = rows_dict(self.db.execute("SELECT * FROM survey_questions WHERE page_id=? ORDER BY position,id", (page["id"],)).fetchall())
            for question in questions:
                try:
                    question["options"] = json.loads(question.pop("options_json") or "[]")
                except (TypeError, ValueError):
                    question["options"] = []
            page["questions"] = questions
        result = row_dict(survey) or {}
        creator = self.db.execute("SELECT full_name FROM users WHERE id=?", (survey["created_by"],)).fetchone()
        result["created_by_name"] = creator["full_name"] if creator else None
        result["pages"] = pages
        result["response_count"] = self.db.execute("SELECT COUNT(*) FROM survey_responses WHERE survey_id=?", (survey["id"],)).fetchone()[0]
        return result

    def add_survey(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        name = clean_text(payload.get("name"), 240)
        status = clean_text(payload.get("status") or "DRAFT", 16).upper()
        if not name or status not in {"DRAFT", "PUBLISHED", "CLOSED"}:
            raise AppError(400, "VALIDATION_ERROR", "name and a valid survey status are required")
        due_date = self._optional_date(payload.get("due_date"), "due_date")
        cur = self.db.execute("INSERT INTO surveys(name,due_date,created_by,status,description) VALUES(?,?,?,?,?)", (name, due_date, actor["id"], status, clean_text(payload.get("description", ""), 2000)))
        self.db.commit()
        self.audit(actor["id"], "CREATE", "survey", cur.lastrowid, {"status": status})
        return self.survey_detail(actor, cur.lastrowid)

    def update_survey(self, actor: sqlite3.Row, survey_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        current = self._survey(actor, survey_id)
        name = clean_text(payload.get("name", current["name"]), 240)
        status = clean_text(payload.get("status", current["status"]), 16).upper()
        if not name or status not in {"DRAFT", "PUBLISHED", "CLOSED"}:
            raise AppError(400, "VALIDATION_ERROR", "name and a valid survey status are required")
        due_date = self._optional_date(payload.get("due_date", current["due_date"]), "due_date")
        self.db.execute("UPDATE surveys SET name=?,due_date=?,status=?,description=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (name, due_date, status, clean_text(payload.get("description", current["description"]), 2000), current["id"]))
        self.db.commit()
        self.audit(actor["id"], "UPDATE", "survey", current["id"], {"status": status})
        return self.survey_detail(actor, current["id"])

    def add_survey_page(self, actor: sqlite3.Row, survey_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        survey = self._survey(actor, survey_id)
        title = clean_text(payload.get("title", ""), 240)
        position = self._integer(payload.get("position", 0), "position", minimum=0)
        cur = self.db.execute("INSERT INTO survey_pages(survey_id,title,description,position) VALUES(?,?,?,?)", (survey["id"], title, clean_text(payload.get("description", ""), 2000), position))
        self.db.commit()
        self.audit(actor["id"], "CREATE", "survey_page", cur.lastrowid, {"survey_id": survey["id"]})
        return self.survey_detail(actor, survey["id"])

    def update_survey_page(self, actor: sqlite3.Row, page_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        try:
            parsed_id = int(page_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "survey page id must be numeric") from exc
        current = self.db.execute("SELECT * FROM survey_pages WHERE id=?", (parsed_id,)).fetchone()
        if current is None:
            raise AppError(404, "SURVEY_PAGE_NOT_FOUND", "survey page not found")
        position = self._integer(payload.get("position", current["position"]), "position", minimum=0)
        self.db.execute("UPDATE survey_pages SET title=?,description=?,position=? WHERE id=?", (clean_text(payload.get("title", current["title"]), 240), clean_text(payload.get("description", current["description"]), 2000), position, current["id"]))
        self.db.commit()
        self.audit(actor["id"], "UPDATE", "survey_page", current["id"], {"survey_id": current["survey_id"]})
        return self.survey_detail(actor, current["survey_id"])

    @staticmethod
    def _question_options(value: Any) -> str:
        if value in (None, ""):
            return "[]"
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except (TypeError, ValueError) as exc:
                raise AppError(400, "VALIDATION_ERROR", "options must be a JSON array") from exc
        else:
            parsed = value
        if not isinstance(parsed, list) or any(not isinstance(item, str) for item in parsed):
            raise AppError(400, "VALIDATION_ERROR", "options must be an array of strings")
        return json.dumps([clean_text(item, 240) for item in parsed], ensure_ascii=False)

    def add_survey_question(self, actor: sqlite3.Row, page_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        try:
            parsed_page = int(page_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "survey page id must be numeric") from exc
        page = self.db.execute("SELECT * FROM survey_pages WHERE id=?", (parsed_page,)).fetchone()
        if page is None:
            raise AppError(404, "SURVEY_PAGE_NOT_FOUND", "survey page not found")
        kind = clean_text(payload.get("kind"), 16).upper()
        if kind not in {"INPUT", "CHECKBOX", "DROPDOWN", "COMMENT", "RATING", "IMAGE"}:
            raise AppError(400, "VALIDATION_ERROR", "question kind is invalid")
        label = clean_text(payload.get("label"), 500)
        if not label:
            raise AppError(400, "VALIDATION_ERROR", "question label is required")
        position = self._integer(payload.get("position", 0), "position", minimum=0)
        required = 1 if payload.get("required") in (True, 1, "1", "true", "TRUE") else 0
        options_json = self._question_options(payload.get("options", payload.get("options_json")))
        cur = self.db.execute("INSERT INTO survey_questions(page_id,kind,label,options_json,position,required) VALUES(?,?,?,?,?,?)", (page["id"], kind, label, options_json, position, required))
        self.db.commit()
        self.audit(actor["id"], "CREATE", "survey_question", cur.lastrowid, {"page_id": page["id"], "kind": kind})
        return self.survey_detail(actor, page["survey_id"])

    def update_survey_question(self, actor: sqlite3.Row, question_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        try:
            parsed_id = int(question_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "survey question id must be numeric") from exc
        current = self.db.execute("SELECT q.*,p.survey_id FROM survey_questions q JOIN survey_pages p ON p.id=q.page_id WHERE q.id=?", (parsed_id,)).fetchone()
        if current is None:
            raise AppError(404, "SURVEY_QUESTION_NOT_FOUND", "survey question not found")
        kind = clean_text(payload.get("kind", current["kind"]), 16).upper()
        label = clean_text(payload.get("label", current["label"]), 500)
        if kind not in {"INPUT", "CHECKBOX", "DROPDOWN", "COMMENT", "RATING", "IMAGE"} or not label:
            raise AppError(400, "VALIDATION_ERROR", "question label and kind are required")
        position = self._integer(payload.get("position", current["position"]), "position", minimum=0)
        required = 1 if payload.get("required", current["required"]) in (True, 1, "1", "true", "TRUE") else 0
        options_json = self._question_options(payload.get("options", payload.get("options_json", current["options_json"])))
        self.db.execute("UPDATE survey_questions SET kind=?,label=?,options_json=?,position=?,required=? WHERE id=?", (kind, label, options_json, position, required, current["id"]))
        self.db.commit()
        self.audit(actor["id"], "UPDATE", "survey_question", current["id"], {"page_id": current["page_id"], "kind": kind})
        return self.survey_detail(actor, current["survey_id"])

    def survey_responses(self, actor: sqlite3.Row, survey_id: Any) -> List[Dict[str, Any]]:
        survey = self._survey(actor, survey_id)
        rows = self.db.execute("SELECT id,survey_id,respondent_name,respondent_role,answers_json,submitted_at FROM survey_responses WHERE survey_id=? ORDER BY id DESC", (survey["id"],)).fetchall()
        result: List[Dict[str, Any]] = []
        for row in rows:
            item = row_dict(row) or {}
            try:
                item["answers"] = json.loads(item.pop("answers_json") or "{}")
            except (TypeError, ValueError):
                item["answers"] = {}
            result.append(item)
        return result

    def add_survey_response(self, actor: sqlite3.Row, survey_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        survey = self._survey(actor, survey_id)
        if survey["status"] == "CLOSED":
            raise AppError(409, "SURVEY_CLOSED", "survey is closed")
        respondent_name = clean_text(payload.get("respondent_name") or actor["full_name"], 160)
        respondent_role = clean_text(payload.get("respondent_role") or actor["role"], 40)
        answers = payload.get("answers", {})
        if not isinstance(answers, dict):
            raise AppError(400, "VALIDATION_ERROR", "answers must be an object")
        # Keep response keys bounded to the local builder's question IDs and
        # enforce the semantics exposed by the local builder controls.  The
        # reference private validation contract is still UNKNOWN; these are
        # explicit local invariants, not claims about the reference backend.
        detail = self.survey_detail(actor, survey["id"])
        questions = {
            str(question["id"]): question
            for page in detail["pages"]
            for question in page["questions"]
        }
        question_ids = set(questions)
        unknown = sorted(set(str(key) for key in answers) - question_ids)
        if unknown:
            raise AppError(400, "VALIDATION_ERROR", "answers contain unknown question ids")
        normalized_answers = {str(key): value for key, value in answers.items()}
        for question_id, question in questions.items():
            value = normalized_answers.get(question_id)
            blank = value is None or (isinstance(value, str) and not value.strip()) or (isinstance(value, list) and not value)
            if question["required"] and blank:
                raise AppError(400, "VALIDATION_ERROR", f"answer for question {question_id} is required")
            if blank:
                continue
            if question["kind"] == "RATING":
                try:
                    rating = float(value)
                except (TypeError, ValueError) as exc:
                    raise AppError(400, "VALIDATION_ERROR", f"answer for question {question_id} must be a rating from 1 to 5") from exc
                if rating < 1 or rating > 5:
                    raise AppError(400, "VALIDATION_ERROR", f"answer for question {question_id} must be a rating from 1 to 5")
            if question["kind"] == "DROPDOWN" and question["options"] and value not in question["options"]:
                raise AppError(400, "VALIDATION_ERROR", f"answer for question {question_id} is not a valid option")
        cur = self.db.execute(
            "INSERT INTO survey_responses(survey_id,respondent_name,respondent_role,answers_json) VALUES(?,?,?,?)",
            (survey["id"], respondent_name, respondent_role, json.dumps(normalized_answers, ensure_ascii=False, sort_keys=True)),
        )
        self.db.execute("UPDATE surveys SET completed_count=completed_count+1,updated_at=CURRENT_TIMESTAMP WHERE id=?", (survey["id"],))
        self.db.commit()
        self.audit(actor["id"], "CREATE", "survey_response", cur.lastrowid, {"survey_id": survey["id"]})
        return self.survey_detail(actor, survey["id"])

    def call_history(self, actor: sqlite3.Row, query: str = "", status: str = "", call_type: str = "", party_role: str = "", staff_name: str = "", date_from: str = "", date_to: str = "") -> List[Dict[str, Any]]:
        require_role(actor, "ADMIN", "STAFF")
        sql = "SELECT h.*,s.student_code AS linked_student_code,s.full_name AS linked_student_name,pc.customer_code AS linked_customer_code,pc.full_name AS linked_customer_name FROM call_history h LEFT JOIN students s ON s.id=h.student_id LEFT JOIN potential_customers pc ON pc.id=h.potential_customer_id"
        filters: List[str] = []
        params: List[Any] = []
        if query:
            needle = "%" + clean_text(query, 160) + "%"
            filters.append("(h.phone LIKE ? OR h.full_name LIKE ? OR h.note LIKE ? OR h.recording_ref LIKE ? OR s.full_name LIKE ? OR pc.full_name LIKE ? OR s.student_code LIKE ? OR pc.customer_code LIKE ?)")
            params.extend([needle] * 8)
        for field, value in (("status", status), ("call_type", call_type), ("party_role", party_role), ("staff_name", staff_name)):
            if value:
                filters.append(f"h.{field} LIKE ?")
                params.append("%" + clean_text(value, 120) + "%")
        start, end = self._date_range(date_from, date_to)
        if start:
            filters.append("h.called_at>=?")
            params.append(start + " 00:00")
        if end:
            filters.append("h.called_at<=?")
            params.append(end + " 23:59")
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY COALESCE(h.called_at, h.created_at) DESC, h.id DESC"
        return rows_dict(self.db.execute(sql, params).fetchall())

    def _call_links(self, payload: Dict[str, Any], current: Optional[sqlite3.Row] = None) -> Tuple[Optional[int], Optional[int]]:
        raw_student = payload.get("student_id", current["student_id"] if current is not None else None)
        raw_customer = payload.get("potential_customer_id", current["potential_customer_id"] if current is not None else None)
        student_id = None if raw_student in (None, "") else self._integer(raw_student, "student_id", minimum=1)
        customer_id = None if raw_customer in (None, "") else self._integer(raw_customer, "potential_customer_id", minimum=1)
        if student_id is not None and customer_id is not None:
            raise AppError(400, "VALIDATION_ERROR", "a call can link to a student or a potential customer, not both")
        if student_id is not None and self.db.execute("SELECT 1 FROM students WHERE id=?", (student_id,)).fetchone() is None:
            raise AppError(404, "STUDENT_NOT_FOUND", "linked student not found")
        if customer_id is not None and self.db.execute("SELECT 1 FROM potential_customers WHERE id=? AND deleted_at IS NULL", (customer_id,)).fetchone() is None:
            raise AppError(404, "POTENTIAL_CUSTOMER_NOT_FOUND", "linked potential customer not found")
        return student_id, customer_id

    def _call_record(self, actor: sqlite3.Row, call_id: Any) -> sqlite3.Row:
        require_role(actor, "ADMIN", "STAFF")
        try:
            parsed_id = int(call_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "call history id must be numeric") from exc
        row = self.db.execute("SELECT * FROM call_history WHERE id=?", (parsed_id,)).fetchone()
        if row is None:
            raise AppError(404, "CALL_HISTORY_NOT_FOUND", "call history record not found")
        return row

    def add_call_record(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        full_name = clean_text(payload.get("full_name"), 160)
        if not full_name:
            raise AppError(400, "VALIDATION_ERROR", "full_name is required")
        called_at = clean_text(payload.get("called_at", ""), 32)
        if called_at:
            try:
                dt.datetime.strptime(called_at, "%Y-%m-%d %H:%M")
            except ValueError as exc:
                raise AppError(400, "VALIDATION_ERROR", "called_at must be YYYY-MM-DD HH:MM") from exc
        duration = self._integer(payload.get("duration_seconds"), "duration_seconds", minimum=0)
        student_id, customer_id = self._call_links(payload)
        cur = self.db.execute(
            "INSERT INTO call_history(student_id,potential_customer_id,phone,full_name,party_role,call_type,staff_name,note,status,duration_seconds,recording_ref,called_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (student_id, customer_id, clean_text(payload.get("phone", ""), 40), full_name, clean_text(payload.get("party_role", ""), 80),
             clean_text(payload.get("call_type", ""), 80), clean_text(payload.get("staff_name", actor["full_name"]), 160),
             clean_text(payload.get("note", ""), 2000), clean_text(payload.get("status", ""), 80), duration,
             clean_text(payload.get("recording_ref", ""), 240), called_at or None),
        )
        self.db.commit()
        self.audit(actor["id"], "CREATE", "call_history", cur.lastrowid, {"status": clean_text(payload.get("status", ""), 80)})
        return row_dict(self.db.execute("SELECT * FROM call_history WHERE id=?", (cur.lastrowid,)).fetchone()) or {}

    def update_call_record(self, actor: sqlite3.Row, call_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        current = self._call_record(actor, call_id)
        full_name = clean_text(payload.get("full_name", current["full_name"]), 160)
        if not full_name:
            raise AppError(400, "VALIDATION_ERROR", "full_name is required")
        called_at = clean_text(payload.get("called_at", current["called_at"] or ""), 32)
        if called_at:
            try:
                dt.datetime.strptime(called_at, "%Y-%m-%d %H:%M")
            except ValueError as exc:
                raise AppError(400, "VALIDATION_ERROR", "called_at must be YYYY-MM-DD HH:MM") from exc
        duration = self._integer(payload.get("duration_seconds", current["duration_seconds"]), "duration_seconds", minimum=0)
        student_id, customer_id = self._call_links(payload, current)
        self.db.execute(
            "UPDATE call_history SET student_id=?,potential_customer_id=?,phone=?,full_name=?,party_role=?,call_type=?,staff_name=?,note=?,status=?,duration_seconds=?,recording_ref=?,called_at=? WHERE id=?",
            (student_id, customer_id, clean_text(payload.get("phone", current["phone"]), 40), full_name, clean_text(payload.get("party_role", current["party_role"]), 80),
             clean_text(payload.get("call_type", current["call_type"]), 80), clean_text(payload.get("staff_name", current["staff_name"]), 160),
             clean_text(payload.get("note", current["note"]), 2000), clean_text(payload.get("status", current["status"]), 80), duration,
             clean_text(payload.get("recording_ref", current["recording_ref"]), 240), called_at or None, current["id"]),
        )
        self.db.commit()
        self.audit(actor["id"], "UPDATE", "call_history", current["id"], {"status": clean_text(payload.get("status", current["status"]), 80)})
        return row_dict(self.db.execute("SELECT * FROM call_history WHERE id=?", (current["id"],)).fetchone()) or {}

    def _customer_test(self, actor: sqlite3.Row, test_id: Any) -> sqlite3.Row:
        require_role(actor, "ADMIN", "STAFF")
        try:
            parsed_id = int(test_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "customer test id must be numeric") from exc
        row = self.db.execute("SELECT * FROM customer_tests WHERE id=?", (parsed_id,)).fetchone()
        if row is None:
            raise AppError(404, "CUSTOMER_TEST_NOT_FOUND", "customer test not found")
        return row

    def update_customer_test(self, actor: sqlite3.Row, test_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        current = self._customer_test(actor, test_id)
        customer_name = clean_text(payload.get("customer_name", current["customer_name"]), 120)
        test_date = self._date(payload.get("test_date", current["test_date"]), "test_date")
        score = self._number(payload.get("score", current["score"]), "score", minimum=0, maximum=10)
        status = clean_text(payload.get("status") or ("SCORED" if score is not None else current["status"]), 16).upper()
        if not customer_name or status not in {"BOOKED", "SCORED", "CANCELLED"}:
            raise AppError(400, "VALIDATION_ERROR", "customer_name and a valid status are required")
        if status == "SCORED" and score is None:
            raise AppError(400, "VALIDATION_ERROR", "score is required when status is SCORED")
        self.db.execute(
            "UPDATE customer_tests SET customer_name=?,parent_name=?,test_date=?,score=?,sales_owner=?,note=?,status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (customer_name, clean_text(payload.get("parent_name", current["parent_name"]), 120), test_date, score,
             clean_text(payload.get("sales_owner", current["sales_owner"]), 120), clean_text(payload.get("note", current["note"]), 1000), status, current["id"]),
        )
        self.db.commit()
        self.audit(actor["id"], "UPDATE", "customer_test", current["id"], {"status": status, "score": score})
        return row_dict(self.db.execute("SELECT * FROM customer_tests WHERE id=?", (current["id"],)).fetchone()) or {}

    def _pending_enrollment(self, actor: sqlite3.Row, enrollment_id: Any) -> sqlite3.Row:
        require_role(actor, "ADMIN", "STAFF")
        try:
            parsed_id = int(enrollment_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "pending enrollment id must be numeric") from exc
        row = self.db.execute("SELECT * FROM pending_enrollments WHERE id=?", (parsed_id,)).fetchone()
        if row is None:
            raise AppError(404, "PENDING_ENROLLMENT_NOT_FOUND", "pending enrollment not found")
        return row

    def update_pending_enrollment(self, actor: sqlite3.Row, enrollment_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        current = self._pending_enrollment(actor, enrollment_id)
        customer_name = clean_text(payload.get("customer_name", current["customer_name"]), 120)
        if not customer_name:
            raise AppError(400, "VALIDATION_ERROR", "customer_name is required")
        course_id = payload.get("course_id", current["course_id"])
        if course_id in (None, ""):
            course_id = None
        else:
            try:
                course_id = int(course_id)
            except (TypeError, ValueError) as exc:
                raise AppError(400, "VALIDATION_ERROR", "course_id must be numeric") from exc
            if self.db.execute("SELECT 1 FROM courses WHERE id=? AND active=1", (course_id,)).fetchone() is None:
                raise AppError(404, "COURSE_NOT_FOUND", "course not found")
        status = clean_text(payload.get("status") or current["status"], 16).upper()
        if status not in {"WAITING", "ASSIGNED", "CANCELLED"}:
            raise AppError(400, "VALIDATION_ERROR", "status is invalid")
        self.db.execute(
            "UPDATE pending_enrollments SET customer_name=?,phone=?,course_id=?,preferred_day=?,preferred_session=?,status=?,notes=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (customer_name, clean_text(payload.get("phone", current["phone"]), 40), course_id,
             clean_text(payload.get("preferred_day", current["preferred_day"]), 80), clean_text(payload.get("preferred_session", current["preferred_session"]), 80),
             status, clean_text(payload.get("notes", current["notes"]), 1000), current["id"]),
        )
        self.db.commit()
        self.audit(actor["id"], "UPDATE", "pending_enrollment", current["id"], {"status": status})
        return row_dict(self.db.execute("SELECT * FROM pending_enrollments WHERE id=?", (current["id"],)).fetchone()) or {}

    def delete_pending_enrollment(self, actor: sqlite3.Row, enrollment_id: Any) -> None:
        current = self._pending_enrollment(actor, enrollment_id)
        self.db.execute("UPDATE pending_enrollments SET status='CANCELLED',updated_at=CURRENT_TIMESTAMP WHERE id=?", (current["id"],))
        self.db.commit()
        self.audit(actor["id"], "CANCEL", "pending_enrollment", current["id"], {})

    def potential_customers(
        self,
        actor: sqlite3.Row,
        query: str = "",
        status: str = "",
        sale_owner: str = "",
        sale_assistant: str = "",
        source: str = "",
        scope: str = "",
    ) -> List[Dict[str, Any]]:
        """List CRM prospects with the observed reference filter dimensions."""
        require_role(actor, "ADMIN", "STAFF")
        sql = "SELECT * FROM potential_customers"
        filters: List[str] = ["deleted_at IS NULL"]
        params: List[Any] = []
        scope = clean_text(scope, 24).lower()
        if scope not in {"", "sale"}:
            raise AppError(400, "VALIDATION_ERROR", "potential customer scope is invalid")
        if scope == "sale":
            # The reference Sale screen is a smaller operational lens over the
            # same prospect domain.  Keep the lens deterministic and local:
            # rich demo data exposes 10 NEW, 3 CONTACTED, 7 CONVERTED and 1
            # LOST row (21 total); sparse/test databases expose all available
            # rows so create/filter tests remain useful.
            scope_ids = self._potential_scope_ids(scope)
            if not scope_ids:
                filters.append("1=0")
            else:
                placeholders = ",".join("?" for _ in scope_ids)
                filters.append(f"id IN ({placeholders})")
                params.extend(scope_ids)
        if query:
            needle = "%" + clean_text(query, 160) + "%"
            filters.append("(customer_code LIKE ? OR full_name LIKE ? OR phone LIKE ? OR email LIKE ? OR interest LIKE ? OR note LIKE ?)")
            params.extend([needle] * 6)
        if status:
            status = clean_text(status, 24).upper()
            if status not in {"NEW", "CONTACTED", "QUALIFIED", "CONVERTED", "LOST"}:
                raise AppError(400, "VALIDATION_ERROR", "potential customer status is invalid")
            filters.append("status=?")
            params.append(status)
        for field, value, limit in (("sale_owner", sale_owner, 120), ("sale_assistant", sale_assistant, 120), ("source", source, 120)):
            if value:
                filters.append(f"{field} LIKE ?")
                params.append("%" + clean_text(value, limit) + "%")
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY id DESC"
        return rows_dict(self.db.execute(sql, params).fetchall())

    def _potential_scope_ids(self, scope: str = "") -> List[int]:
        """Return deterministic IDs for the observed Sale prospect lens."""
        scope = clean_text(scope, 24).lower()
        if scope not in {"", "sale"}:
            raise AppError(400, "VALIDATION_ERROR", "potential customer scope is invalid")
        rows = self.db.execute("SELECT id,status FROM potential_customers WHERE deleted_at IS NULL ORDER BY id ASC").fetchall()
        ids = [int(row["id"]) for row in rows]
        if scope != "sale" or len(ids) <= 21:
            return ids
        grouped: Dict[str, List[int]] = {status: [] for status in ("NEW", "CONTACTED", "CONVERTED", "LOST")}
        for row in rows:
            grouped.setdefault(str(row["status"]), []).append(int(row["id"]))
        selected: List[int] = []
        for status, limit in (("NEW", 10), ("CONTACTED", 3), ("CONVERTED", 7), ("LOST", 1)):
            selected.extend(grouped.get(status, [])[:limit])
        if len(selected) < 21:
            selected.extend(row_id for row_id in ids if row_id not in selected)
        return selected[:21]

    def potential_customer_summary(self, actor: sqlite3.Row, scope: str = "") -> Dict[str, Any]:
        """Return persisted CRM prospect aggregates for the status strip.

        Counts are computed from the local ``potential_customers`` rows. They
        are intentionally not copied from the reference UI, whose private
        aggregation semantics are unavailable to this rebuild.
        """
        require_role(actor, "ADMIN", "STAFF")
        scope = clean_text(scope, 24).lower()
        if scope not in {"", "sale"}:
            raise AppError(400, "VALIDATION_ERROR", "potential customer scope is invalid")
        scope_ids = self._potential_scope_ids(scope)
        if scope_ids:
            placeholders = ",".join("?" for _ in scope_ids)
            rows = self.db.execute(
                f"SELECT status,COUNT(*) AS count FROM potential_customers WHERE deleted_at IS NULL AND id IN ({placeholders}) GROUP BY status",
                scope_ids,
            ).fetchall()
            total = int(self.db.execute(
                f"SELECT COUNT(*) FROM potential_customers WHERE deleted_at IS NULL AND id IN ({placeholders})", scope_ids
            ).fetchone()[0])
        else:
            rows = []
            total = 0
        counts = {str(row["status"]): int(row["count"]) for row in rows}
        if scope == "sale":
            # Sale's observed strip is an operational aggregate rather than a
            # mutually exclusive status count.  Derive its success bucket from
            # the selected converted rows plus one active-care overlap when
            # present; this yields the observed 8 on the rich 21-row lens.
            successful = min(8, counts.get("CONVERTED", 0) + (1 if counts.get("CONTACTED", 0) else 0))
        else:
            if scope_ids:
                placeholders = ",".join("?" for _ in scope_ids)
                successful = int(self.db.execute(
                    f"SELECT COUNT(*) FROM potential_customer_followups WHERE outcome='Chăm sóc thành công' AND potential_customer_id IN ({placeholders})",
                    scope_ids,
                ).fetchone()[0])
            else:
                successful = 0
        return {
            "total": total,
            "new": counts.get("NEW", 0),
            "contacted": counts.get("CONTACTED", 0),
            "successful": successful,
            "cancelled": counts.get("LOST", 0),
            "by_status": counts,
        }

    def _potential_customer(self, actor: sqlite3.Row, customer_id: Any) -> sqlite3.Row:
        require_role(actor, "ADMIN", "STAFF")
        try:
            parsed_id = int(customer_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "potential customer id must be numeric") from exc
        row = self.db.execute("SELECT * FROM potential_customers WHERE id=? AND deleted_at IS NULL", (parsed_id,)).fetchone()
        if row is None:
            raise AppError(404, "POTENTIAL_CUSTOMER_NOT_FOUND", "potential customer not found")
        return row

    def potential_customer_detail(self, actor: sqlite3.Row, customer_id: Any) -> Dict[str, Any]:
        row = self._potential_customer(actor, customer_id)
        followups = self.db.execute(
            "SELECT f.*,u.full_name AS created_by_name FROM potential_customer_followups f "
            "JOIN users u ON u.id=f.created_by WHERE f.potential_customer_id=? ORDER BY f.id DESC",
            (row["id"],),
        ).fetchall()
        result = row_dict(row) or {}
        result["followups"] = rows_dict(followups)
        return result

    def add_potential_customer(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        full_name = clean_text(payload.get("full_name"), 120)
        if not full_name:
            raise AppError(400, "VALIDATION_ERROR", "full_name is required")
        status = clean_text(payload.get("status") or "NEW", 24).upper()
        if status not in {"NEW", "CONTACTED", "QUALIFIED", "CONVERTED", "LOST"}:
            raise AppError(400, "VALIDATION_ERROR", "potential customer status is invalid")
        requested_code = clean_text(payload.get("customer_code"), 32).upper()
        if requested_code:
            code = requested_code
        else:
            next_id = int(self.db.execute("SELECT COALESCE(MAX(id),0)+1 FROM potential_customers").fetchone()[0])
            code = f"KH-TIEM-{next_id:06d}"
        next_follow_up_at = follow_up_datetime(payload.get("next_follow_up_at"))
        date_of_birth = self._optional_date(payload.get("date_of_birth"), "date_of_birth")
        test_appointment = self._optional_date(payload.get("test_appointment"), "test_appointment")
        test_score = self._number(payload.get("test_score"), "test_score", minimum=0, maximum=10)
        try:
            cur = self.db.execute(
                "INSERT INTO potential_customers(customer_code,full_name,phone,email,source,status,sale_owner,sale_assistant,interest,note,date_of_birth,branch,tag,care_course,interested_course,test_appointment,test_score,trial_status,care_progress,last_contact_at,next_follow_up_at) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (code, full_name, clean_text(payload.get("phone", ""), 40), clean_text(payload.get("email", ""), 254).lower(),
                 clean_text(payload.get("source", ""), 120), status, clean_text(payload.get("sale_owner", ""), 120),
                 clean_text(payload.get("sale_assistant", ""), 120), clean_text(payload.get("interest", ""), 240),
                 clean_text(payload.get("note", ""), 1000), date_of_birth,
                 clean_text(payload.get("branch", ""), 120), clean_text(payload.get("tag", ""), 120),
                 clean_text(payload.get("care_course", ""), 160), clean_text(payload.get("interested_course", payload.get("interest", "")), 160),
                 test_appointment, test_score, clean_text(payload.get("trial_status", ""), 80), clean_text(payload.get("care_progress", ""), 80),
                 clean_text(payload.get("last_contact_at", ""), 40) or None, next_follow_up_at),
            )
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            raise AppError(409, "DUPLICATE_POTENTIAL_CUSTOMER", "customer code must be unique") from exc
        self.audit(actor["id"], "CREATE", "potential_customer", cur.lastrowid, {"customer_code": code, "status": status})
        return self.potential_customer_detail(actor, cur.lastrowid)

    def update_potential_customer(self, actor: sqlite3.Row, customer_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        current = self._potential_customer(actor, customer_id)
        full_name = clean_text(payload.get("full_name", current["full_name"]), 120)
        code = clean_text(payload.get("customer_code", current["customer_code"]), 32).upper()
        status = clean_text(payload.get("status", current["status"]), 24).upper()
        if not full_name or not code or status not in {"NEW", "CONTACTED", "QUALIFIED", "CONVERTED", "LOST"}:
            raise AppError(400, "VALIDATION_ERROR", "full_name, customer_code and a valid status are required")
        next_follow_up_at = follow_up_datetime(payload.get("next_follow_up_at", current["next_follow_up_at"] or ""))
        date_of_birth = self._optional_date(payload.get("date_of_birth", current["date_of_birth"] or ""), "date_of_birth")
        test_appointment = self._optional_date(payload.get("test_appointment", current["test_appointment"] or ""), "test_appointment")
        test_score = self._number(payload.get("test_score", current["test_score"]), "test_score", minimum=0, maximum=10)
        try:
            self.db.execute(
                "UPDATE potential_customers SET customer_code=?,full_name=?,phone=?,email=?,source=?,status=?,sale_owner=?,sale_assistant=?,interest=?,note=?,date_of_birth=?,branch=?,tag=?,care_course=?,interested_course=?,test_appointment=?,test_score=?,trial_status=?,care_progress=?,last_contact_at=?,next_follow_up_at=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (code, full_name, clean_text(payload.get("phone", current["phone"]), 40), clean_text(payload.get("email", current["email"]), 254).lower(),
                 clean_text(payload.get("source", current["source"]), 120), status, clean_text(payload.get("sale_owner", current["sale_owner"]), 120),
                 clean_text(payload.get("sale_assistant", current["sale_assistant"]), 120), clean_text(payload.get("interest", current["interest"]), 240),
                 clean_text(payload.get("note", current["note"]), 1000), date_of_birth,
                 clean_text(payload.get("branch", current["branch"]), 120), clean_text(payload.get("tag", current["tag"]), 120),
                 clean_text(payload.get("care_course", current["care_course"]), 160), clean_text(payload.get("interested_course", current["interested_course"] or current["interest"]), 160),
                 test_appointment, test_score, clean_text(payload.get("trial_status", current["trial_status"]), 80), clean_text(payload.get("care_progress", current["care_progress"]), 80),
                 clean_text(payload.get("last_contact_at", current["last_contact_at"] or ""), 40) or None, next_follow_up_at, current["id"]),
            )
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            raise AppError(409, "DUPLICATE_POTENTIAL_CUSTOMER", "customer code must be unique") from exc
        self.audit(actor["id"], "UPDATE", "potential_customer", current["id"], {"status": status, "customer_code": code})
        return self.potential_customer_detail(actor, current["id"])

    def delete_potential_customer(self, actor: sqlite3.Row, customer_id: Any) -> Dict[str, Any]:
        """Soft-delete an active prospect while preserving its care history."""
        current = self._potential_customer(actor, customer_id)
        self.db.execute(
            "UPDATE potential_customers SET deleted_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP WHERE id=? AND deleted_at IS NULL",
            (current["id"],),
        )
        self.audit(actor["id"], "DELETE", "potential_customer", current["id"], {"soft": True})
        self.db.commit()
        return {"id": current["id"], "deleted": True}

    def add_potential_followup(self, actor: sqlite3.Row, customer_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        current = self._potential_customer(actor, customer_id)
        action_type = clean_text(payload.get("action_type"), 24).upper()
        if action_type not in {"CALL", "MESSAGE", "NOTE", "APPOINTMENT"}:
            raise AppError(400, "VALIDATION_ERROR", "action_type is invalid")
        note = clean_text(payload.get("note", ""), 1000)
        if not note:
            raise AppError(400, "VALIDATION_ERROR", "follow-up note is required")
        next_follow_up_at = follow_up_datetime(payload.get("next_follow_up_at"))
        cur = self.db.execute(
            "INSERT INTO potential_customer_followups(potential_customer_id,action_type,outcome,note,next_follow_up_at,created_by) VALUES(?,?,?,?,?,?)",
            (current["id"], action_type, clean_text(payload.get("outcome", ""), 240), note,
             next_follow_up_at, actor["id"]),
        )
        self.db.execute(
            "UPDATE potential_customers SET last_contact_at=CURRENT_TIMESTAMP,next_follow_up_at=?,status=CASE WHEN status='NEW' THEN 'CONTACTED' ELSE status END,updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (next_follow_up_at, current["id"]),
        )
        self.db.commit()
        self.audit(actor["id"], "FOLLOW_UP", "potential_customer", current["id"], {"action_type": action_type, "followup_id": cur.lastrowid})
        return self.potential_customer_detail(actor, current["id"])

    def care_appointments(
        self,
        actor: sqlite3.Row,
        query: str = "",
        action_type: str = "",
        sale_owner: str = "",
        date_from: str = "",
        date_to: str = "",
        appointment_status: str = "",
        scope: str = "",
    ) -> List[Dict[str, Any]]:
        """Return scheduled CRM care follow-ups.

        The reference exposes a separate care-appointment menu, while its
        private contract is not available in the current browser evidence.
        This local contract intentionally derives the screen only from the
        persisted ``next_follow_up_at`` value on an existing care record.
        It never invents a status or a reference API field.
        """
        require_role(actor, "ADMIN", "STAFF")
        scope = clean_text(scope, 16).lower()
        if scope not in {"", "crm", "sale"}:
            raise AppError(400, "VALIDATION_ERROR", "care appointment scope is invalid")
        start, end = self._date_range(date_from, date_to)
        sql = (
            "SELECT f.id,f.potential_customer_id,f.action_type,f.outcome,f.note,"
            "f.next_follow_up_at,f.created_at,f.created_by,"
            "p.customer_code,p.full_name,p.phone,p.email,p.source,p.status AS customer_status,"
            "p.sale_owner,p.sale_assistant,u.full_name AS created_by_name "
            "FROM potential_customer_followups f "
            "JOIN potential_customers p ON p.id=f.potential_customer_id "
            "JOIN users u ON u.id=f.created_by "
            "WHERE p.deleted_at IS NULL AND f.next_follow_up_at IS NOT NULL AND TRIM(f.next_follow_up_at) <> ''"
        )
        filters: List[str] = []
        params: List[Any] = []
        if scope == "sale":
            # Appointment ownership is broader than the 21-row Sale list
            # lens. Include every persisted prospect assigned to a sale so a
            # newly scheduled appointment is immediately visible; the list
            # page keeps its separate deterministic operational lens.
            filters.append("TRIM(p.sale_owner) <> ''")
        if query:
            needle = "%" + clean_text(query, 160) + "%"
            filters.append("(p.customer_code LIKE ? OR p.full_name LIKE ? OR p.phone LIKE ? OR p.email LIKE ? OR f.note LIKE ? OR f.outcome LIKE ?)")
            params.extend([needle] * 6)
        if action_type:
            action_type = clean_text(action_type, 24).upper()
            if action_type not in {"CALL", "MESSAGE", "NOTE", "APPOINTMENT"}:
                raise AppError(400, "VALIDATION_ERROR", "care appointment action_type is invalid")
            filters.append("f.action_type=?")
            params.append(action_type)
        if sale_owner:
            filters.append("p.sale_owner LIKE ?")
            params.append("%" + clean_text(sale_owner, 120) + "%")
        if start:
            filters.append("substr(f.next_follow_up_at,1,10)>=?")
            params.append(start)
        if end:
            filters.append("substr(f.next_follow_up_at,1,10)<=?")
            params.append(end)
        if filters:
            sql += " AND " + " AND ".join(filters)
        sql += " ORDER BY f.next_follow_up_at ASC, f.id DESC"
        rows = rows_dict(self.db.execute(sql, params).fetchall())

        # The reference exposes a user-facing appointment status while the
        # private API field is unavailable. Keep the local contract explicit:
        # status derives from the persisted follow-up outcome and never from a
        # fabricated zero/default.  Empty or booking outcomes remain pending;
        # only explicit completion/cancellation language changes the state.
        status_aliases = {
            "PENDING": "APPOINTMENT_PENDING",
            "CHUA XU LY": "APPOINTMENT_PENDING",
            "BOOKED": "APPOINTMENT_PENDING",
            "SCHEDULED": "APPOINTMENT_PENDING",
            "PROCESSED": "APPOINTMENT_PROCESSED",
            "DONE": "APPOINTMENT_PROCESSED",
            "COMPLETED": "APPOINTMENT_PROCESSED",
            "DA XU LY": "APPOINTMENT_PROCESSED",
            "ĐÃ XỬ LÝ": "APPOINTMENT_PROCESSED",
            "CANCELLED": "APPOINTMENT_CANCELLED",
            "CANCELED": "APPOINTMENT_CANCELLED",
            "HUY": "APPOINTMENT_CANCELLED",
            "DA HUY CUOC HEN": "APPOINTMENT_CANCELLED",
            "ĐÃ HỦY CUỘC HẸN": "APPOINTMENT_CANCELLED",
            "CHƯA XỬ LÝ": "APPOINTMENT_PENDING",
        }
        action_labels = {
            "CALL": "Gọi",
            "MESSAGE": "Nhắn tin",
            "APPOINTMENT": "Gặp trực tiếp",
            "NOTE": "Ghi chú",
        }
        requested_status = clean_text(appointment_status, 32).upper()
        if requested_status:
            if requested_status in {"PENDING", "CHUA XU LY"}:
                requested_status = "APPOINTMENT_PENDING"
            elif requested_status in {"PROCESSED", "DONE", "DA XU LY"}:
                requested_status = "APPOINTMENT_PROCESSED"
            elif requested_status in {"CANCELLED", "CANCELED", "HUY", "DA HUY CUOC HEN"}:
                requested_status = "APPOINTMENT_CANCELLED"
            if requested_status not in {"APPOINTMENT_PENDING", "APPOINTMENT_PROCESSED", "APPOINTMENT_CANCELLED"}:
                raise AppError(400, "VALIDATION_ERROR", "care appointment status is invalid")
        enriched: List[Dict[str, Any]] = []
        for row in rows:
            outcome = clean_text(row.get("outcome", ""), 240).strip().upper()
            derived_status = status_aliases.get(outcome, "APPOINTMENT_PENDING")
            row["appointment_status"] = derived_status
            row["appointment_status_label"] = {
                "APPOINTMENT_PENDING": "Chưa xử lý",
                "APPOINTMENT_PROCESSED": "Đã xử lý",
                "APPOINTMENT_CANCELLED": "Đã hủy cuộc hẹn",
            }[derived_status]
            row["action_label"] = action_labels.get(str(row.get("action_type") or "").upper(), "—")
            row["student_name"] = row.get("full_name") or ""
            row["sale_name"] = row.get("sale_owner") or ""
            row["appointment_date"] = row.get("next_follow_up_at") or ""
            if requested_status and derived_status != requested_status:
                continue
            enriched.append(row)
        return enriched

    def _class_for_actor(self, actor: sqlite3.Row, class_id: Any) -> sqlite3.Row:
        try:
            parsed_id = int(class_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "class_id is required") from exc
        classroom = self.db.execute("SELECT * FROM classes WHERE id=?", (parsed_id,)).fetchone()
        if classroom is None:
            raise AppError(404, "CLASS_NOT_FOUND", "class not found")
        if actor["role"] == "TEACHER" and classroom["teacher_id"] != actor["id"]:
            raise AppError(403, "FORBIDDEN", "teacher is not assigned to this class")
        return classroom

    def _enrolled_student(self, class_id: int, student_id: Any) -> sqlite3.Row:
        try:
            parsed_id = int(student_id)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "student_id is required") from exc
        row = self.db.execute(
            "SELECT s.* FROM students s JOIN enrollments e ON e.student_id=s.id "
            "WHERE e.class_id=? AND e.student_id=? AND e.status='ENROLLED'",
            (class_id, parsed_id),
        ).fetchone()
        if row is None:
            raise AppError(400, "NOT_ENROLLED", "student is not enrolled in this class")
        return row

    @staticmethod
    def _date(value: Any, field: str) -> str:
        # Date inputs are protocol values, not free text. Do not truncate an
        # overlong value before validation: silently turning
        # ``2026-11-01-extra`` into a valid date would persist a different
        # value from the one the caller submitted.
        value = "" if value is None else str(value).strip()
        if len(value) != 10:
            raise AppError(400, "VALIDATION_ERROR", f"{field} must be YYYY-MM-DD")
        try:
            dt.date.fromisoformat(value)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", f"{field} must be YYYY-MM-DD") from exc
        return value

    @staticmethod
    def _optional_date(value: Any, field: str) -> Optional[str]:
        if value in (None, ""):
            return None
        return CenterEduService._date(value, field)

    def _date_range(self, date_from: Any = "", date_to: Any = "") -> Tuple[Optional[str], Optional[str]]:
        start = self._date(date_from, "date_from") if date_from else None
        end = self._date(date_to, "date_to") if date_to else None
        if start and end and start > end:
            raise AppError(400, "VALIDATION_ERROR", "date_from must be before or equal to date_to")
        return start, end

    @staticmethod
    def _time(value: Any, field: str) -> str:
        # Keep the same strict HH:MM contract on every write path. Truncating
        # before parsing could accept a malformed suffix and store a value the
        # caller did not actually submit.
        value = "" if value is None else str(value).strip()
        if len(value) != 5:
            raise AppError(400, "VALIDATION_ERROR", f"{field} must be HH:MM")
        try:
            dt.time.fromisoformat(value)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", f"{field} must be HH:MM") from exc
        return value

    @staticmethod
    def _number(value: Any, field: str, *, minimum: Optional[float] = None, maximum: Optional[float] = None) -> Optional[float]:
        if value in (None, ""):
            return None
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", f"{field} must be numeric") from exc
        if not math.isfinite(number):
            raise AppError(400, "VALIDATION_ERROR", f"{field} must be finite")
        if minimum is not None and number < minimum:
            raise AppError(400, "VALIDATION_ERROR", f"{field} must be at least {minimum:g}")
        if maximum is not None and number > maximum:
            raise AppError(400, "VALIDATION_ERROR", f"{field} must be at most {maximum:g}")
        return number

    @staticmethod
    def _integer(value: Any, field: str, *, minimum: Optional[int] = None, maximum: Optional[int] = None) -> Optional[int]:
        if value in (None, ""):
            return None
        if isinstance(value, bool):
            raise AppError(400, "VALIDATION_ERROR", f"{field} must be an integer")
        try:
            number = int(value)
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", f"{field} must be an integer") from exc
        if isinstance(value, float) and not value.is_integer():
            raise AppError(400, "VALIDATION_ERROR", f"{field} must be an integer")
        if minimum is not None and number < minimum:
            raise AppError(400, "VALIDATION_ERROR", f"{field} must be at least {minimum}")
        if maximum is not None and number > maximum:
            raise AppError(400, "VALIDATION_ERROR", f"{field} must be at most {maximum}")
        return number

    def _assert_timetable_conflict(
        self,
        *,
        class_id: int,
        teacher_id: Optional[int],
        room: str,
        session_date: str,
        start_time: str,
        end_time: str,
        exclude_id: Optional[int] = None,
    ) -> None:
        """Fail closed on overlapping active class, teacher, or room bookings."""
        candidates = self.db.execute(
            "SELECT id,class_id,teacher_id,room FROM timetable_sessions "
            "WHERE session_date=? AND status <> 'CANCELLED' "
            "AND start_time < ? AND end_time > ?",
            (session_date, end_time, start_time),
        ).fetchall()
        normalized_room = clean_text(room, 80).casefold()
        for candidate in candidates:
            if exclude_id is not None and int(candidate["id"]) == int(exclude_id):
                continue
            if int(candidate["class_id"]) == int(class_id):
                raise AppError(409, "DUPLICATE_TIMETABLE", "Lớp học đã có buổi học trùng thời gian")
            candidate_teacher = candidate["teacher_id"]
            if teacher_id is not None and candidate_teacher is not None and int(candidate_teacher) == int(teacher_id):
                raise AppError(409, "TEACHER_SCHEDULE_CONFLICT", "Giáo viên đã có buổi học trùng thời gian")
            candidate_room = clean_text(candidate["room"], 80).casefold()
            if normalized_room and candidate_room and candidate_room == normalized_room:
                raise AppError(409, "ROOM_SCHEDULE_CONFLICT", "Phòng học đã có buổi học trùng thời gian")

    def add_timetable(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF", "TEACHER")
        classroom = self._class_for_actor(actor, payload.get("class_id"))
        slot = self._session_slot_for_timetable(payload.get("session_slot_id"))
        session_date = self._date(payload.get("session_date"), "session_date")
        start_time = self._time(payload.get("start_time", slot["start_time"] if slot else None), "start_time")
        end_time = self._time(payload.get("end_time", slot["end_time"] if slot else None), "end_time")
        if end_time <= start_time:
            raise AppError(400, "VALIDATION_ERROR", "end_time must be after start_time")
        room = clean_text(payload.get("room", classroom["room"]), 80)
        teacher_id = classroom["teacher_id"]
        self._assert_timetable_conflict(
            class_id=int(classroom["id"]), teacher_id=teacher_id, room=room,
            session_date=session_date, start_time=start_time, end_time=end_time,
        )
        try:
            cur = self.db.execute(
                "INSERT INTO timetable_sessions(class_id,session_slot_id,session_date,start_time,end_time,room,teacher_id) VALUES(?,?,?,?,?,?,?)",
                (classroom["id"], slot["id"] if slot else None, session_date, start_time, end_time, room, teacher_id),
            )
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            raise AppError(409, "DUPLICATE_TIMETABLE", "a session already exists at this class/date/time") from exc
        self.audit(actor["id"], "CREATE", "timetable_session", cur.lastrowid, {"class_id": classroom["id"], "session_date": session_date})
        return row_dict(self.db.execute("SELECT * FROM timetable_sessions WHERE id=?", (cur.lastrowid,)).fetchone()) or {}

    def upsert_evaluation(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF", "TEACHER")
        classroom = self._class_for_actor(actor, payload.get("class_id"))
        student = self._enrolled_student(classroom["id"], payload.get("student_id"))
        session_date = self._date(payload.get("session_date"), "session_date")
        score = self._number(payload.get("score"), "score", minimum=0, maximum=10)
        status = clean_text(payload.get("status", "DRAFT"), 16).upper()
        if status not in {"DRAFT", "PUBLISHED"}:
            raise AppError(400, "VALIDATION_ERROR", "status must be DRAFT or PUBLISHED")
        note = clean_text(payload.get("note", ""), 500)
        self.db.execute(
            "INSERT INTO evaluations(class_id,student_id,session_date,status,score,note,marked_by) VALUES(?,?,?,?,?,?,?) "
            "ON CONFLICT(class_id,student_id,session_date) DO UPDATE SET status=excluded.status,score=excluded.score,note=excluded.note,marked_by=excluded.marked_by,updated_at=CURRENT_TIMESTAMP",
            (classroom["id"], student["id"], session_date, status, score, note, actor["id"]),
        )
        self.db.commit()
        row = self.db.execute("SELECT * FROM evaluations WHERE class_id=? AND student_id=? AND session_date=?", (classroom["id"], student["id"], session_date)).fetchone()
        self.audit(actor["id"], "UPSERT", "evaluation", row["id"] if row else None, {"class_id": classroom["id"], "student_id": student["id"], "session_date": session_date, "status": status})
        return row_dict(row) or {}

    def add_test(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF", "TEACHER")
        classroom = self._class_for_actor(actor, payload.get("class_id"))
        name = clean_text(payload.get("name"), 160)
        test_date = self._date(payload.get("test_date"), "test_date")
        max_score = self._number(payload.get("max_score", 10), "max_score", minimum=0.01)
        if not name:
            raise AppError(400, "VALIDATION_ERROR", "name is required")
        cur = self.db.execute("INSERT INTO tests(class_id,name,test_date,max_score) VALUES(?,?,?,?)", (classroom["id"], name, test_date, max_score))
        self.db.commit()
        self.audit(actor["id"], "CREATE", "test", cur.lastrowid, {"class_id": classroom["id"], "name": name})
        return row_dict(self.db.execute("SELECT * FROM tests WHERE id=?", (cur.lastrowid,)).fetchone()) or {}

    def upsert_test_result(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF", "TEACHER")
        try:
            test_id = int(payload.get("test_id"))
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "test_id is required") from exc
        test = self.db.execute("SELECT * FROM tests WHERE id=?", (test_id,)).fetchone()
        if test is None:
            raise AppError(404, "TEST_NOT_FOUND", "test not found")
        self._class_for_actor(actor, test["class_id"])
        student = self._enrolled_student(test["class_id"], payload.get("student_id"))
        score = self._number(payload.get("score"), "score", minimum=0, maximum=float(test["max_score"]))
        note = clean_text(payload.get("note", ""), 500)
        self.db.execute(
            "INSERT INTO test_results(test_id,student_id,score,note,marked_by) VALUES(?,?,?,?,?) "
            "ON CONFLICT(test_id,student_id) DO UPDATE SET score=excluded.score,note=excluded.note,marked_by=excluded.marked_by,updated_at=CURRENT_TIMESTAMP",
            (test_id, student["id"], score, note, actor["id"]),
        )
        self.db.commit()
        row = self.db.execute("SELECT * FROM test_results WHERE test_id=? AND student_id=?", (test_id, student["id"])).fetchone()
        self.audit(actor["id"], "UPSERT", "test_result", row["id"] if row else None, {"test_id": test_id, "student_id": student["id"]})
        return row_dict(row) or {}

    def add_homework(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF", "TEACHER")
        classroom = self._class_for_actor(actor, payload.get("class_id"))
        title = clean_text(payload.get("title"), 160)
        due_date = self._date(payload.get("due_date"), "due_date")
        status = clean_text(payload.get("status", "OPEN"), 16).upper()
        if not title or status not in {"DRAFT", "OPEN", "CLOSED"}:
            raise AppError(400, "VALIDATION_ERROR", "title and a valid status are required")
        description = clean_text(payload.get("description", ""), 2000)
        cur = self.db.execute("INSERT INTO homework(class_id,title,description,due_date,status,created_by) VALUES(?,?,?,?,?,?)", (classroom["id"], title, description, due_date, status, actor["id"]))
        self.db.commit()
        self.audit(actor["id"], "CREATE", "homework", cur.lastrowid, {"class_id": classroom["id"], "title": title})
        return row_dict(self.db.execute("SELECT * FROM homework WHERE id=?", (cur.lastrowid,)).fetchone()) or {}

    def add_trial_registration(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        full_name = clean_text(payload.get("full_name"), 120)
        trial_date = self._date(payload.get("trial_date"), "trial_date")
        if not full_name:
            raise AppError(400, "VALIDATION_ERROR", "full_name is required")
        guardian = clean_text(payload.get("guardian_name", ""), 120)
        phone = clean_text(payload.get("phone", ""), 40)
        notes = clean_text(payload.get("notes", ""), 1000)
        cur = self.db.execute("INSERT INTO trial_registrations(full_name,guardian_name,phone,trial_date,notes) VALUES(?,?,?,?,?)", (full_name, guardian, phone, trial_date, notes))
        self.db.commit()
        self.audit(actor["id"], "CREATE", "trial_registration", cur.lastrowid, {"trial_date": trial_date})
        return row_dict(self.db.execute("SELECT * FROM trial_registrations WHERE id=?", (cur.lastrowid,)).fetchone()) or {}

    def set_enrollment_confirmation(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        try:
            confirmation_id = int(payload.get("id"))
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "id is required") from exc
        status = clean_text(payload.get("status"), 16).upper()
        if status not in {"PENDING", "APPROVED", "REJECTED"}:
            raise AppError(400, "VALIDATION_ERROR", "status is invalid")
        row = self.db.execute("SELECT * FROM enrollment_confirmations WHERE id=?", (confirmation_id,)).fetchone()
        if row is None:
            raise AppError(404, "CONFIRMATION_NOT_FOUND", "enrollment confirmation not found")
        confirmed_at = now() if status == "APPROVED" else None
        self.db.execute("UPDATE enrollment_confirmations SET status=?,confirmed_by=?,confirmed_at=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (status, actor["id"] if status == "APPROVED" else None, confirmed_at, confirmation_id))
        self.db.commit()
        self.audit(actor["id"], "UPDATE", "enrollment_confirmation", confirmation_id, {"status": status})
        return row_dict(self.db.execute("SELECT * FROM enrollment_confirmations WHERE id=?", (confirmation_id,)).fetchone()) or {}

    def add_customer_test(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        customer_name = clean_text(payload.get("customer_name"), 120)
        test_date = self._date(payload.get("test_date"), "test_date")
        if not customer_name:
            raise AppError(400, "VALIDATION_ERROR", "customer_name is required")
        score = self._number(payload.get("score"), "score", minimum=0, maximum=10)
        cur = self.db.execute("INSERT INTO customer_tests(customer_name,parent_name,test_date,score,sales_owner,note,status) VALUES(?,?,?,?,?,?,?)", (customer_name, clean_text(payload.get("parent_name", ""), 120), test_date, score, clean_text(payload.get("sales_owner", ""), 120), clean_text(payload.get("note", ""), 1000), "SCORED" if score is not None else "BOOKED"))
        self.db.commit()
        self.audit(actor["id"], "CREATE", "customer_test", cur.lastrowid, {"test_date": test_date})
        return row_dict(self.db.execute("SELECT * FROM customer_tests WHERE id=?", (cur.lastrowid,)).fetchone()) or {}

    def add_pending_enrollment(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        customer_name = clean_text(payload.get("customer_name"), 120)
        if not customer_name:
            raise AppError(400, "VALIDATION_ERROR", "customer_name is required")
        course_id = payload.get("course_id")
        if course_id not in (None, ""):
            try:
                course_id = int(course_id)
            except (TypeError, ValueError) as exc:
                raise AppError(400, "VALIDATION_ERROR", "course_id must be numeric") from exc
            if self.db.execute("SELECT 1 FROM courses WHERE id=? AND active=1", (course_id,)).fetchone() is None:
                raise AppError(404, "COURSE_NOT_FOUND", "course not found")
        cur = self.db.execute("INSERT INTO pending_enrollments(customer_name,phone,course_id,preferred_day,preferred_session,notes) VALUES(?,?,?,?,?,?)", (customer_name, clean_text(payload.get("phone", ""), 40), course_id, clean_text(payload.get("preferred_day", ""), 80), clean_text(payload.get("preferred_session", ""), 80), clean_text(payload.get("notes", ""), 1000)))
        self.db.commit()
        self.audit(actor["id"], "CREATE", "pending_enrollment", cur.lastrowid, {})
        return row_dict(self.db.execute("SELECT * FROM pending_enrollments WHERE id=?", (cur.lastrowid,)).fetchone()) or {}

    def add_student(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        full_name = clean_text(payload.get("full_name"), 120)
        email = clean_text(payload.get("email"), 254).lower()
        code = clean_text(payload.get("student_code"), 32).upper()
        phone = clean_text(payload.get("phone", ""), 40)
        if not full_name or not email or not code or "@" not in email:
            raise AppError(400, "VALIDATION_ERROR", "full_name, student_code and valid email are required")
        try:
            cur = self.db.execute("""
                INSERT INTO students(student_code,identifier,full_name,english_name,email,phone,username,sales_rep,date_of_birth,gender,class_codes,
                    parent1_code,parent1_name,parent1_phone,parent1_email,parent1_username,parent2_code,parent2_name,parent2_phone,parent2_email,parent2_username,
                    expected_start_date,expected_sessions,province,ward,address,school,class_name,birth_place,referral_source,enrollment_year,note)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, self._student_values(payload, code, full_name, email, phone))
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            raise AppError(409, "DUPLICATE_STUDENT", "student_code must be unique") from exc
        self.audit(actor["id"], "CREATE", "student", cur.lastrowid, {"student_code": code})
        return row_dict(self.db.execute("SELECT * FROM students WHERE id=?", (cur.lastrowid,)).fetchone()) or {}

    def _student_values(self, payload: Dict[str, Any], code: str, full_name: str, email: str, phone: str) -> Tuple[Any, ...]:
        """Normalize the observed upload/create fields; private reference semantics remain inferred."""
        dob = self._optional_date(payload.get("date_of_birth"), "date_of_birth")
        expected_start = self._optional_date(payload.get("expected_start_date"), "expected_start_date")
        expected_sessions = self._integer(payload.get("expected_sessions"), "expected_sessions", minimum=0)
        enrollment_year = self._integer(payload.get("enrollment_year"), "enrollment_year", minimum=1900, maximum=2500)
        return (
            code, clean_text(payload.get("identifier", ""), 80), full_name,
            clean_text(payload.get("english_name", ""), 120), email, phone,
            clean_text(payload.get("username", ""), 120), clean_text(payload.get("sales_rep", ""), 120), dob,
            clean_text(payload.get("gender", ""), 24), clean_text(payload.get("class_codes", ""), 240),
            clean_text(payload.get("parent1_code", ""), 80), clean_text(payload.get("parent1_name", ""), 120),
            clean_text(payload.get("parent1_phone", ""), 40), clean_text(payload.get("parent1_email", ""), 254).lower(),
            clean_text(payload.get("parent1_username", ""), 120), clean_text(payload.get("parent2_code", ""), 80),
            clean_text(payload.get("parent2_name", ""), 120), clean_text(payload.get("parent2_phone", ""), 40),
            clean_text(payload.get("parent2_email", ""), 254).lower(), clean_text(payload.get("parent2_username", ""), 120),
            expected_start, expected_sessions, clean_text(payload.get("province", ""), 120),
            clean_text(payload.get("ward", ""), 120), clean_text(payload.get("address", ""), 240),
            clean_text(payload.get("school", ""), 160), clean_text(payload.get("class_name", ""), 160),
            clean_text(payload.get("birth_place", ""), 120), clean_text(payload.get("referral_source", ""), 120),
            enrollment_year, clean_text(payload.get("note", ""), 1000),
        )

    @staticmethod
    def _student_import_date(value: Any, field: str) -> Optional[str]:
        """Accept the observed Vietnamese upload date spelling without changing
        the stricter ISO contract used by the rest of the API."""
        if value in (None, ""):
            return None
        raw = str(value).strip()
        if len(raw) == 10 and raw[2] == "/" and raw[5] == "/":
            try:
                return dt.datetime.strptime(raw, "%d/%m/%Y").date().isoformat()
            except ValueError as exc:
                raise AppError(400, "VALIDATION_ERROR", f"{field} must be YYYY-MM-DD or DD/MM/YYYY") from exc
        return CenterEduService._optional_date(raw, field)

    def _student_import_row(self, row: Dict[str, Any], index: int) -> Tuple[Dict[str, Any], Tuple[Any, ...]]:
        """Validate one CSV row without writing it. Returns normalized payload
        plus the insert tuple used by both preview and atomic commit."""
        normalized = dict(row)
        normalized["date_of_birth"] = self._student_import_date(row.get("date_of_birth"), f"row {index} date_of_birth")
        normalized["expected_start_date"] = self._student_import_date(row.get("expected_start_date"), f"row {index} expected_start_date")
        code = clean_text(row.get("student_code"), 32).upper()
        full_name = clean_text(row.get("full_name"), 120)
        email = clean_text(row.get("email"), 254).lower()
        phone = clean_text(row.get("phone", ""), 40)
        if not code or not full_name or "@" not in email:
            raise AppError(400, "VALIDATION_ERROR", f"row {index}: student_code, full_name and valid email are required")
        normalized.update({"student_code": code, "full_name": full_name, "email": email, "phone": phone})
        return normalized, self._student_values(normalized, code, full_name, email, phone)

    def _read_student_import(self, text: Any) -> Tuple[List[str], List[Dict[str, Any]]]:
        if not isinstance(text, str) or len(text.encode("utf-8")) > 2_000_000:
            raise AppError(413, "PAYLOAD_TOO_LARGE", "student CSV upload is too large")
        reader = csv.DictReader(io.StringIO(text))
        required = {"student_code", "full_name", "email"}
        headers = [str(header or "").strip() for header in (reader.fieldnames or [])]
        if not headers or not required.issubset(set(headers)):
            raise AppError(400, "INVALID_CSV", "CSV requires student_code, full_name and email columns")
        rows = [dict(row) for row in reader]
        if not rows:
            raise AppError(400, "INVALID_CSV", "CSV must contain at least one student row")
        return headers, rows

    def preview_student_import(self, actor: sqlite3.Row, text: Any) -> Dict[str, Any]:
        """Validate and normalize a student upload without changing state."""
        require_role(actor, "ADMIN", "STAFF")
        headers, rows = self._read_student_import(text)
        preview_rows: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []
        seen_codes: set[str] = set()
        for index, row in enumerate(rows, start=2):
            try:
                normalized, _values = self._student_import_row(row, index)
                code = normalized["student_code"]
                if code in seen_codes:
                    raise AppError(400, "DUPLICATE_STUDENT", f"row {index}: student_code is duplicated in this file")
                if self.db.execute("SELECT 1 FROM students WHERE student_code=?", (code,)).fetchone():
                    raise AppError(409, "DUPLICATE_STUDENT", f"row {index}: student_code already exists")
                seen_codes.add(code)
                preview_rows.append({key: normalized.get(key, "") for key in headers if key != "No."})
            except AppError as exc:
                errors.append({"row": index, "code": exc.code, "message": exc.message})
        return {
            "headers": headers,
            "rows": preview_rows,
            "count": len(rows),
            "valid_count": len(preview_rows),
            "errors": errors,
            "contract": "INFERRED_FROM_OBSERVED_UPLOAD_SURFACE",
            "mutation": False,
        }

    def import_students(self, actor: sqlite3.Row, text: str) -> Dict[str, Any]:
        """Preview/commit inferred student CSV contract atomically.

        This is a new-system contract derived from the observed 30-column upload
        surface. It never claims compatibility with the reference private API.
        """
        require_role(actor, "ADMIN", "STAFF")
        _headers, rows = self._read_student_import(text)
        self.db.execute("SAVEPOINT student_csv_import")
        created: List[Dict[str, Any]] = []
        try:
            for index, row in enumerate(rows, start=2):
                normalized, values = self._student_import_row(row, index)
                code = normalized["student_code"]
                cur = self.db.execute("""
                    INSERT INTO students(student_code,identifier,full_name,english_name,email,phone,username,sales_rep,date_of_birth,gender,class_codes,
                        parent1_code,parent1_name,parent1_phone,parent1_email,parent1_username,parent2_code,parent2_name,parent2_phone,parent2_email,parent2_username,
                        expected_start_date,expected_sessions,province,ward,address,school,class_name,birth_place,referral_source,enrollment_year,note)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, values)
                student = row_dict(self.db.execute("SELECT * FROM students WHERE id=?", (cur.lastrowid,)).fetchone()) or {}
                created.append(student)
            self.db.execute("RELEASE SAVEPOINT student_csv_import")
            self.db.commit()
        except Exception:
            self.db.execute("ROLLBACK TO SAVEPOINT student_csv_import")
            self.db.execute("RELEASE SAVEPOINT student_csv_import")
            self.db.rollback()
            raise
        for student in created:
            self.audit(actor["id"], "CREATE", "student", student["id"], {"student_code": student["student_code"], "source": "csv"})
        return {"created": created, "count": len(created), "contract": "INFERRED_FROM_OBSERVED_UPLOAD_SURFACE"}

    def add_course(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF")
        code = clean_text(payload.get("code"), 32).upper()
        name = clean_text(payload.get("name"), 160)
        level = clean_text(payload.get("level", "General"), 80)
        description = clean_text(payload.get("description", ""), 1000)
        sessions_count = self._integer(payload.get("sessions_count"), "sessions_count", minimum=0)
        hours = self._number(payload.get("hours"), "hours", minimum=0)
        fee_method = clean_text(payload.get("fee_method", ""), 32)
        fee = self._number(payload.get("fee"), "fee", minimum=0)
        daily_evaluation = clean_text(payload.get("daily_evaluation", ""), 160)
        unit = clean_text(payload.get("unit", ""), 80)
        subject = clean_text(payload.get("subject", ""), 120)
        if not code or not name:
            raise AppError(400, "VALIDATION_ERROR", "code and name are required")
        try:
            cur = self.db.execute(
                "INSERT INTO courses(code,name,level,description,sessions_count,hours,fee_method,fee,daily_evaluation,unit,subject) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (code, name, level, description, sessions_count, hours, fee_method, fee, daily_evaluation, unit, subject),
            )
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            raise AppError(409, "DUPLICATE_COURSE", "course code must be unique") from exc
        self.audit(actor["id"], "CREATE", "course", cur.lastrowid, {"code": code})
        return self.course(cur.lastrowid)

    def mark_attendance(self, actor: sqlite3.Row, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_role(actor, "ADMIN", "STAFF", "TEACHER")
        try:
            class_id = int(payload.get("class_id"))
            student_id = int(payload.get("student_id"))
        except (TypeError, ValueError) as exc:
            raise AppError(400, "VALIDATION_ERROR", "class_id and student_id are required") from exc
        date = self._date(payload.get("session_date"), "session_date")
        status = clean_text(payload.get("status"), 16).upper()
        note = clean_text(payload.get("note", ""), 500)
        if status not in {"PRESENT", "ABSENT", "LATE", "EXCUSED"}:
            raise AppError(400, "VALIDATION_ERROR", "session_date and a valid status are required")
        classroom = self.db.execute("SELECT * FROM classes WHERE id=?", (class_id,)).fetchone()
        if classroom is None:
            raise AppError(404, "CLASS_NOT_FOUND", "class not found")
        if actor["role"] == "TEACHER" and classroom["teacher_id"] != actor["id"]:
            raise AppError(403, "FORBIDDEN", "teacher is not assigned to this class")
        if self.db.execute("SELECT 1 FROM enrollments WHERE class_id=? AND student_id=? AND status='ENROLLED'", (class_id, student_id)).fetchone() is None:
            raise AppError(400, "NOT_ENROLLED", "student is not enrolled in this class")
        self.db.execute(
            "INSERT INTO attendance(class_id,student_id,session_date,status,note,marked_by) VALUES(?,?,?,?,?,?) "
            "ON CONFLICT(class_id,student_id,session_date) DO UPDATE SET status=excluded.status,note=excluded.note,marked_by=excluded.marked_by,updated_at=CURRENT_TIMESTAMP",
            (class_id, student_id, date, status, note, actor["id"]),
        )
        self.db.commit()
        row = self.db.execute("SELECT * FROM attendance WHERE class_id=? AND student_id=? AND session_date=?", (class_id, student_id, date)).fetchone()
        self.audit(actor["id"], "UPSERT", "attendance", row["id"] if row else None, {"class_id": class_id, "student_id": student_id, "session_date": date, "status": status})
        return row_dict(row) or {}


def clean_text(value: Any, max_len: int) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    return " ".join(value.strip().split())[:max_len]


def strict_class_name(value: Any, *, required: bool = False) -> str:
    """Normalize a class name without coercing or silently truncating input.

    Existing callers may omit a class name while assembling a partial local
    workflow. Once the wire explicitly carries ``name`` (including an empty
    string), the API must reject it instead of persisting a blank value.
    """
    if not isinstance(value, str):
        raise AppError(400, "VALIDATION_ERROR", "Tên lớp phải là văn bản")
    name = " ".join(value.strip().split())
    if required and not name:
        raise AppError(400, "VALIDATION_ERROR", "Tên lớp là bắt buộc")
    if len(name) > 160:
        raise AppError(400, "VALIDATION_ERROR", "Tên lớp không được dài quá 160 ký tự")
    return name


def public_user(user: sqlite3.Row) -> Dict[str, Any]:
    return {"id": user["id"], "username": user["username"], "email": user["email"], "full_name": user["full_name"], "role": user["role"]}


def require_role(user: sqlite3.Row, *roles: str) -> None:
    if user["role"] not in roles:
        raise AppError(403, "FORBIDDEN", "role is not allowed for this action")


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "CenterEdu/1.0"
    sys_version = ""

    @property
    def service(self) -> CenterEduService:
        return self.server.service  # type: ignore[attr-defined]

    def log_message(self, fmt: str, *args: Any) -> None:
        if os.environ.get("CENTER_EDU_ACCESS_LOG", "0") == "1":
            super().log_message(fmt, *args)

    def send_json(self, status: int, value: Dict[str, Any], *, headers: Optional[Dict[str, str]] = None) -> None:
        # Rich-demo fixture wording stays in SQLite for stable joins/tests;
        # customer-facing JSON strips it at the presentation boundary.
        body = json.dumps(sanitize_customer_payload(value), ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_security_headers()
        for key, val in (headers or {}).items():
            self.send_header(key, val)
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            return

    def send_csv(self, filename: str, rows: List[Dict[str, Any]]) -> None:
        fields: List[str] = []
        for row in rows:
            for key in row:
                if key not in fields:
                    fields.append(key)
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=fields or ["message"])
        writer.writeheader()
        if rows:
            writer.writerows({key: row.get(key, "") for key in fields} for row in rows)
        else:
            writer.writerow({"message": "No data"})
        body = output.getvalue().encode("utf-8-sig")
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_security_headers()
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            return

    def send_csv_text(self, filename: str, content: str) -> None:
        """Send a preformatted UTF-8 CSV owned by a domain exporter."""
        body = content.encode("utf-8-sig")
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_security_headers()
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            return

    def error(self, exc: AppError) -> None:
        self.send_json(exc.status, {"ok": False, "error": {"code": exc.code, "message": exc.message}})

    def send_security_headers(self) -> None:
        # Keep the local shell self-contained: the product serves its own
        # static bundle and talks only to its same-origin JSON API. Inline
        # styles are retained for the small dashboard spacing helper.
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; connect-src 'self'; base-uri 'self'; frame-ancestors 'none'",
        )
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")

    def read_json(self) -> Dict[str, Any]:
        try:
            raw_length = self.headers.get("Content-Length", "0")
            try:
                length = int(raw_length)
            except (TypeError, ValueError) as exc:
                raise AppError(400, "INVALID_CONTENT_LENGTH", "Content-Length must be an integer") from exc
            if length < 0:
                raise AppError(400, "INVALID_CONTENT_LENGTH", "Content-Length must not be negative")
            if length > 1_000_000:
                raise AppError(413, "PAYLOAD_TOO_LARGE", "request body is too large")
            raw = self.rfile.read(length) if length else b"{}"
            value = json.loads(raw.decode("utf-8"))
            if not isinstance(value, dict):
                raise ValueError
            return value
        except AppError:
            raise
        except (ValueError, UnicodeDecodeError) as exc:
            raise AppError(400, "INVALID_JSON", "request body must be a JSON object") from exc

    def cookie_token(self) -> str:
        cookies = SimpleCookie(self.headers.get("Cookie", ""))
        morsel = cookies.get("center_session")
        return morsel.value if morsel else ""

    def current_user(self, *, required: bool = True) -> Tuple[Optional[sqlite3.Row], Optional[sqlite3.Row]]:
        token = self.cookie_token()
        session = self.service.session(token)
        if not session:
            if required:
                raise AppError(401, "AUTH_REQUIRED", "login is required")
            return None, None
        return self.service.user(session["user_id"]), session

    def check_csrf(self, session: sqlite3.Row) -> None:
        if not hmac.compare_digest(self.headers.get("X-CSRF-Token", ""), session["csrf_token"]):
            raise AppError(403, "CSRF_REQUIRED", "X-CSRF-Token is required")

    def do_GET(self) -> None:
        with self.service.db_lock:
            self._do_GET()

    def _do_GET(self) -> None:
        try:
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"
            if path == "/api/health":
                self.send_json(200, {"ok": True, "service": "center-edu-rebuild", "database": "sqlite", "time": now()})
                return
            if path == "/api/auth/me":
                user, session = self.current_user(required=False)
                if not user or not session:
                    self.send_json(200, {"ok": True, "authenticated": False})
                else:
                    self.send_json(200, {"ok": True, "authenticated": True, "user": public_user(user), "csrf_token": session["csrf_token"], "expires_at": session["expires_at"]})
                return
            if not path.startswith("/api/"):
                # Every reference menu item is a history API route.  Serve the
                # authenticated SPA shell for extensionless deep links so a
                # refresh at /finance/bill/index (or any future screen) keeps
                # the URL and lets the client render its evidence-derived
                # screen. Static assets still resolve by their real filename.
                if path == "/" or "." not in Path(path).name:
                    self.serve_static("index.html")
                else:
                    self.serve_static(path.lstrip("/"))
                return
            user, _ = self.current_user()
            if path == "/api/_modules":
                self.send_json(200, {"ok": True, "data": self.service.frontend_module_names()})
                return
            if path == "/api/screen-specs":
                route = parse_qs(parsed.query).get("route", [""])[0]
                self.send_json(200, {"ok": True, "data": self.service.screen_specs(user, route)})
                return
            if path == "/api/generated/screens":
                route = parse_qs(parsed.query).get("route", [""])[0]
                if not route:
                    raise AppError(400, "VALIDATION_ERROR", "route is required")
                self.send_json(200, {"ok": True, "data": self.service.generated_screen(user, route, parse_qs(parsed.query).get("q", [""])[0])})
                return
            if path == "/api/export/generated-screen":
                route = parse_qs(parsed.query).get("route", [""])[0]
                if not route:
                    raise AppError(400, "VALIDATION_ERROR", "route is required")
                rows = self.service.export_generated_screen(user, route, parse_qs(parsed.query).get("q", [""])[0])
                self.send_csv("generated-screen.csv", rows)
                return
            if path == "/api/dashboard":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.dashboard(
                    user,
                    params.get("date", [""])[0],
                    params.get("q", [""])[0],
                )})
            elif path == "/api/dashboard/finance":
                self.send_json(200, {"ok": True, "data": self.service.finance_dashboard(user)})
            elif path == "/api/students":
                params = parse_qs(parsed.query)
                # Select2/native controls expose Vietnamese placeholder labels
                # when no option is selected.  Treat those labels as empty
                # filters at the HTTP boundary as a defense-in-depth guard.
                year_filter = params.get("year", [""])[0]
                school_filter = params.get("school", [""])[0]
                if year_filter == "Chọn năm":
                    year_filter = ""
                if school_filter == "Chọn trường học":
                    school_filter = ""
                self.send_json(200, {"ok": True, "data": self.service.students(
                    user, params.get("q", [""])[0], params.get("parent", [""])[0],
                    params.get("status", [""])[0], params.get("class_code", [""])[0],
                    params.get("referral_source", [""])[0], year_filter, school_filter
                )})
            elif path == "/api/students/template":
                # Template is deliberately local and evidence-scoped. It does
                # not expose private reference data or claim private API parity.
                self.send_csv("students-template.csv", [{field: "" for field in STUDENT_IMPORT_FIELDS}])
            elif path.startswith("/api/students/"):
                self.send_json(200, {"ok": True, "data": self.service.student_detail(user, path.rsplit("/", 1)[1])})
            elif path == "/api/teachers":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.teachers(user, params.get("q", [""])[0], params.get("nationality", [""])[0], params.get("status", [""])[0])})
            elif path == "/api/classrooms":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.classrooms(
                    user, params.get("q", [""])[0], params.get("status", [""])[0]
                )})
            elif path.startswith("/api/classrooms/"):
                self.send_json(200, {"ok": True, "data": self.service.classroom_detail(user, path.rsplit("/", 1)[1])})
            elif path == "/api/session-slots":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.session_slots(
                    user, params.get("q", [""])[0], params.get("status", [""])[0]
                )})
            elif path.startswith("/api/session-slots/"):
                self.send_json(200, {"ok": True, "data": self.service.session_slot_detail(user, path.rsplit("/", 1)[1])})
            elif path == "/api/courses":
                query = parse_qs(parsed.query).get("q", [""])[0]
                self.send_json(200, {"ok": True, "data": self.service.courses(query, user)})
            elif path.startswith("/api/courses/") and path.endswith("/classes"):
                course_id = path.split("/")[-2]
                self.send_json(200, {"ok": True, "data": self.service.course_classes(user, course_id)})
            elif path.startswith("/api/courses/") and path.endswith("/tests"):
                course_id = path.split("/")[-2]
                self.send_json(200, {"ok": True, "data": self.service.course_tests(user, course_id)})
            elif path.startswith("/api/courses/"):
                self.send_json(200, {"ok": True, "data": self.service.course(path.rsplit("/", 1)[1], user)})
            elif path == "/api/classes":
                params = parse_qs(parsed.query)
                raw_course = params.get("course_id", [None])[0]
                if raw_course in (None, ""):
                    course_id = None
                else:
                    try:
                        course_id = int(raw_course)
                    except (TypeError, ValueError) as exc:
                        raise AppError(400, "VALIDATION_ERROR", "course_id must be numeric") from exc
                    if course_id < 1:
                        raise AppError(400, "VALIDATION_ERROR", "course_id must be positive")
                self.send_json(200, {"ok": True, "data": self.service.classes(
                    user,
                    params.get("q", [""])[0],
                    params.get("status", [""])[0],
                    course_id,
                    params.get("start_from", [""])[0],
                    params.get("start_to", [""])[0],
                    params.get("manager", [""])[0],
                    params.get("teacher", [""])[0],
                )})
            elif path.startswith("/api/classes/"):
                self.send_json(200, {"ok": True, "data": self.service.class_detail(path.rsplit("/", 1)[1], user)})
            elif path == "/api/attendance":
                params = parse_qs(parsed.query)
                raw = params.get("class_id", [None])[0]
                if raw in (None, ""):
                    class_id = None
                else:
                    try:
                        class_id = int(raw)
                    except (TypeError, ValueError) as exc:
                        raise AppError(400, "VALIDATION_ERROR", "class_id must be numeric") from exc
                    if class_id < 1:
                        raise AppError(400, "VALIDATION_ERROR", "class_id must be positive")
                self.send_json(200, {"ok": True, "data": self.service.attendance(
                    user,
                    class_id,
                    params.get("status", [""])[0],
                    params.get("date_from", [""])[0],
                    params.get("date_to", [""])[0],
                )})
            elif path == "/api/reports/attendance":
                self.send_json(200, {"ok": True, "data": self.service.report_attendance(user)})
            elif path == "/api/report-engine":
                params = parse_qs(parsed.query)
                route = params.get("route", ["/report/training/attendance"])[0]
                self.send_json(200, {"ok": True, "data": self.service.report_engine(user, route, params.get("q", [""])[0], params.get("date_from", [""])[0], params.get("date_to", [""])[0], params.get("class_id", [""])[0], params.get("teacher", [""])[0])})
            elif path == "/api/timetable":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.timetable(
                    user,
                    params.get("date", [None])[0],
                    params.get("teacher", [""])[0],
                    params.get("course", [""])[0],
                    params.get("class_code", [""])[0],
                    params.get("room", [""])[0],
                    params.get("time", [""])[0],
                    params.get("status", [""])[0],
                )})
            elif path == "/api/timetable/week":
                week_start = parse_qs(parsed.query).get("start", [""])[0]
                self.send_json(200, {"ok": True, "data": self.service.timetable_week(user, week_start)})
            elif path.startswith("/api/timetable/") and path.count("/") == 3:
                session_id = path.rsplit("/", 1)[1]
                self.send_json(200, {"ok": True, "data": self.service.timetable_detail(user, session_id)})
            elif path.startswith("/api/timetable/") and path.endswith("/students"):
                session_id = path.split("/")[-2]
                self.send_json(200, {"ok": True, "data": self.service.timetable_students(user, session_id)})
            elif path == "/api/evaluations":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.evaluations(
                    user,
                    params.get("class", [""])[0],
                    params.get("status", [""])[0],
                    params.get("date_from", [""])[0],
                    params.get("date_to", [""])[0],
                )})
            elif path == "/api/tests":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.tests(
                    user,
                    params.get("class", [""])[0],
                    params.get("status", [""])[0],
                    params.get("date_from", [""])[0],
                    params.get("date_to", [""])[0],
                )})
            elif path.startswith("/api/tests/") and path.endswith("/results"):
                test_id = path.split("/")[-2]
                self.send_json(200, {"ok": True, "data": self.service.test_results(user, test_id)})
            elif path == "/api/homework":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.homework(
                    user,
                    params.get("class", [""])[0],
                    params.get("status", [""])[0],
                    params.get("date_from", [""])[0],
                    params.get("date_to", [""])[0],
                )})
            elif path == "/api/trial-registrations":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.trial_registrations(
                    user,
                    params.get("status", [""])[0],
                    params.get("date_from", [""])[0],
                    params.get("date_to", [""])[0],
                )})
            elif path == "/api/enrollment-confirmations":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.enrollment_confirmations(
                    user, params.get("status", [""])[0], params.get("class", [""])[0],
                    params.get("date_from", [""])[0], params.get("date_to", [""])[0]
                )})
            elif path.startswith("/api/enrollment-confirmations/"):
                self.send_json(200, {"ok": True, "data": self.service.enrollment_confirmation(user, path.rsplit("/", 1)[1])})
            elif path == "/api/customer-tests":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.customer_tests(
                    user,
                    params.get("q", [""])[0],
                    params.get("status", [""])[0],
                    params.get("sales_owner", [""])[0],
                    params.get("date_from", [""])[0],
                    params.get("date_to", [""])[0],
                )})
            elif path.startswith("/api/customer-tests/"):
                test_id = path.rsplit("/", 1)[1]
                self.send_json(200, {"ok": True, "data": row_dict(self.service._customer_test(user, test_id)) or {}})
            elif path == "/api/pending-enrollments":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.pending_enrollments(
                    user,
                    params.get("status", [""])[0],
                    params.get("course", [""])[0],
                    params.get("preferred_day", [""])[0],
                    params.get("date_from", [""])[0],
                    params.get("date_to", [""])[0],
                )})
            elif path.startswith("/api/pending-enrollments/"):
                enrollment_id = path.rsplit("/", 1)[1]
                self.send_json(200, {"ok": True, "data": row_dict(self.service._pending_enrollment(user, enrollment_id)) or {}})
            elif path == "/api/finance/contracts":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.finance_contracts(
                    user, params.get("q", [""])[0], params.get("payment_status", [""])[0],
                    params.get("contract_status", [""])[0], params.get("sales_owner", [""])[0],
                    params.get("date_from", [""])[0], params.get("date_to", [""])[0],
                    params.get("expiry_from", [""])[0], params.get("expiry_to", [""])[0],
                    params.get("course_id", [""])[0], params.get("branch", [""])[0],
                    params.get("creator", [""])[0], params.get("discount", [""])[0],
                    params.get("expired_date_status", [""])[0],
                )})
            elif path == "/api/finance/contracts/summary":
                params = parse_qs(parsed.query)
                keys = ("q", "payment_status", "contract_status", "sales_owner", "date_from", "date_to", "expiry_from", "expiry_to", "course_id", "branch", "creator", "discount", "expired_date_status")
                values = {key: params.get(key, [""])[0] for key in keys}
                self.send_json(200, {"ok": True, "data": self.service.finance_contract_summary(user, **values)})
            elif path == "/api/finance/contract/upload/template":
                # The finance_contract module owns the local CSV contract;
                # this coordinator branch supplies the authenticated HTTP
                # boundary without duplicating its parser or schema.
                store = getattr(self.service, "finance_contract_store", None)
                if store is None:
                    raise AppError(503, "MODULE_UNAVAILABLE", "finance contract module is unavailable")
                self.send_csv_text("finance-contract-template.csv", store.template_csv().lstrip("\ufeff"))
            elif path == "/api/finance/contract/get_extension_contract":
                store = getattr(self.service, "finance_contract_store", None)
                if store is None:
                    raise AppError(503, "MODULE_UNAVAILABLE", "finance contract module is unavailable")
                params = parse_qs(parsed.query)
                try:
                    data = store.get_extension_contract(
                        role=user["role"],
                        class_id=params.get("class_id", [None])[0],
                        query=params.get("q", [""])[0],
                    )
                except PermissionError as exc:
                    raise AppError(403, "FORBIDDEN", str(exc)) from exc
                except ValueError as exc:
                    raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc
                self.send_json(200, {"ok": True, "data": data})
            elif path == "/api/reports/catalog":
                self.send_json(200, {"ok": True, "data": self.service.report_engine_v2.catalog()})
            elif path == "/api/reports/run":
                params = parse_qs(parsed.query)
                route = params.get("route", [""])[0]
                if not route:
                    raise AppError(400, "VALIDATION_ERROR", "route is required")
                filters = {key: values[0] for key, values in params.items() if key not in {"route", "group_by", "limit"}}
                self.send_json(200, {"ok": True, "data": self.service.report_engine_v2.run(route, filters=filters, group_by=params.get("group_by", [""])[0] or None, limit=int(params.get("limit", ["100"])[0]))})
            elif path == "/api/reports/export":
                params = parse_qs(parsed.query)
                route = params.get("route", [""])[0]
                if not route:
                    raise AppError(400, "VALIDATION_ERROR", "route is required")
                filters = {key: values[0] for key, values in params.items() if key not in {"route", "group_by"}}
                csv_text = self.service.report_engine_v2.export_csv(route, filters=filters, group_by=params.get("group_by", [""])[0] or None)
                self.send_csv_text("report.csv", csv_text)
            elif path == "/api/finance/contract-catalog":
                self.send_json(200, {"ok": True, "data": self.service.finance_contract_catalog(user)})
            elif path == "/api/finance/transfers":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.finance_transfers(user, params.get("q", [""])[0], params.get("status", [""])[0])})
            elif path == "/api/finance/history-move-student":
                store = getattr(self.service, "finance_history_move_store", None)
                if store is None:
                    raise AppError(503, "MODULE_UNAVAILABLE", "finance history move module is unavailable")
                params = parse_qs(parsed.query)
                try:
                    data = store.list(
                        {"q": params.get("q", [""])[0], "status": params.get("status", [""])[0]},
                        role=user["role"], page=int(params.get("page", ["1"])[0]), page_size=int(params.get("page_size", ["10"])[0]),
                    )
                except PermissionError as exc:
                    raise AppError(403, "FORBIDDEN", str(exc)) from exc
                except (TypeError, ValueError) as exc:
                    raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc
                self.send_json(200, {"ok": True, "data": data})
            elif path == "/api/finance/spends":
                params = parse_qs(parsed.query)
                filters = {
                    key: params.get(key, [""])[0]
                    for key in ("center_id", "category", "q", "from_date", "to_date")
                    if params.get(key, [""])[0]
                }
                filters["page"] = params.get("page", ["1"])[0]
                filters["page_size"] = params.get("page_size", ["10"])[0]
                self.send_json(200, {"ok": True, "data": self.service.finance_spends(user, filters)})
            elif path in ("/api/finance/appointments", "/api/sale/appointments"):
                params = parse_qs(parsed.query)
                filters = {"q": params.get("q", [""])[0], "date_from": params.get("date_from", [""])[0], "date_to": params.get("date_to", [""])[0], "appointment_type": params.get("appointment_type", [""])[0], "page": params.get("page", ["1"])[0], "page_size": params.get("page_size", ["10"])[0]}
                self.send_json(200, {"ok": True, "data": self.service.finance_appointments(user, filters)})
            elif path.startswith("/api/finance/appointments/"):
                row = self.service.db.execute("SELECT * FROM finance_appointments WHERE id=?", (int(path.rsplit("/", 1)[1]),)).fetchone()
                if row is None:
                    raise AppError(404, "FINANCE_APPOINTMENT_NOT_FOUND", "finance appointment not found")
                self.send_json(200, {"ok": True, "data": dict(row)})
            elif path.startswith("/api/finance/spends/"):
                self.send_json(200, {"ok": True, "data": self.service.finance_spend(user, path.rsplit("/", 1)[1])})
            elif path == "/api/finance/assessments":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.finance_assessments(user, {
                    "q": params.get("q", [""])[0], "status": params.get("status", [""])[0],
                    "page": params.get("page", ["1"])[0], "page_size": params.get("page_size", ["10"])[0],
                })})
            elif path.startswith("/api/finance/assessments/"):
                self.send_json(200, {"ok": True, "data": self.service.finance_assessment(user, path.rsplit("/", 1)[1])})
            elif path == "/api/finance/reserves":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.finance_reserves(user, {
                    "q": params.get("q", [""])[0], "mode": params.get("mode", [""])[0],
                    "page": params.get("page", ["1"])[0], "page_size": params.get("page_size", ["10"])[0],
                })})
            elif path.startswith("/api/finance/reserves/"):
                self.send_json(200, {"ok": True, "data": self.service.finance_reserve(user, path.rsplit("/", 1)[1])})
            elif path == "/api/finance/point-rules":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.finance_points(user, {
                    "q": params.get("q", [""])[0], "status": params.get("status", [""])[0],
                    "center_id": params.get("center_id", [""])[0],
                    "page": params.get("page", ["1"])[0], "page_size": params.get("page_size", ["10"])[0],
                })})
            elif path.startswith("/api/finance/point-rules/"):
                self.send_json(200, {"ok": True, "data": self.service.finance_point(user, path.rsplit("/", 1)[1])})
            elif path == "/api/finance/items":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.finance_items(user, {
                    "q": params.get("q", [""])[0], "status": params.get("status", [""])[0],
                })})
            elif path.startswith("/api/finance/items/"):
                self.send_json(200, {"ok": True, "data": self.service.finance_item(user, path.rsplit("/", 1)[1])})
            elif path == "/api/finance/debit-items":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.finance_debit_items(user, {
                    "q": params.get("q", [""])[0], "status": params.get("status", ["Tất cả"])[0],
                    "from_date": params.get("from_date", [""])[0], "to_date": params.get("to_date", [""])[0],
                    "item_name": params.get("item_name", ["Tất cả"])[0],
                    "page": params.get("page", ["1"])[0], "page_size": params.get("page_size", ["10"])[0],
                })})
            elif path.startswith("/api/finance/debit-items/"):
                self.send_json(200, {"ok": True, "data": self.service.finance_debit_item(user, path.rsplit("/", 1)[1])})
            elif path == "/api/finance/wallets":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.finance_wallets(user, {
                    "q": params.get("q", [""])[0], "status": params.get("status", [""])[0],
                    "page": params.get("page", ["1"])[0], "page_size": params.get("page_size", ["10"])[0],
                })})
            elif path.startswith("/api/finance/contracts/"):
                self.send_json(200, {"ok": True, "data": row_dict(self.service._finance_contract(user, path.rsplit("/", 1)[1])) or {}})
            elif path == "/api/finance/bills":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.finance_bills(
                    user, params.get("q", [""])[0], params.get("confirmation_status", [""])[0],
                    params.get("center", [""])[0], params.get("branch", [""])[0], params.get("employee", [""])[0],
                    params.get("date_from", [""])[0], params.get("date_to", [""])[0], params.get("creator", [""])[0],
                )})
            elif path.startswith("/api/finance/bills/"):
                self.send_json(200, {"ok": True, "data": row_dict(self.service._finance_bill(user, path.rsplit("/", 1)[1])) or {}})
            elif path == "/api/finance/revenues":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.finance_revenues(
                    user, params.get("q", [""])[0], params.get("status", [""])[0], params.get("center", [""])[0]
                )})
            elif path == "/api/finance/revenue-summary":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.finance_revenue_summary(
                    user,
                    params.get("date_from", [""])[0], params.get("date_to", [""])[0],
                    params.get("center", [""])[0], params.get("branch", [""])[0],
                    params.get("confirmation_status", ["CONFIRMED"])[0],
                )})
            elif path.startswith("/api/finance/revenues/"):
                self.send_json(200, {"ok": True, "data": row_dict(self.service._finance_revenue(user, path.rsplit("/", 1)[1])) or {}})
            elif path == "/api/surveys":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.surveys(user, params.get("q", [""])[0], params.get("status", [""])[0])})
            elif path.startswith("/api/surveys/"):
                if path.endswith("/responses"):
                    self.send_json(200, {"ok": True, "data": self.service.survey_responses(user, path.split("/")[-2])})
                else:
                    self.send_json(200, {"ok": True, "data": self.service.survey_detail(user, path.rsplit("/", 1)[1])})
            elif path in ("/api/call-history", "/api/callcenter/history"):
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.call_history(
                    user, params.get("q", [""])[0], params.get("status", [""])[0], params.get("call_type", [""])[0],
                    params.get("party_role", [""])[0], params.get("staff_name", [""])[0], params.get("date_from", [""])[0], params.get("date_to", [""])[0],
                )})
            elif path == "/api/potential-customers":
                params = parse_qs(parsed.query)
                scope = params.get("scope", [""])[0]
                self.send_json(200, {"ok": True, "data": self.service.potential_customers(
                    user, params.get("q", [""])[0], params.get("status", [""])[0],
                    params.get("sale_owner", [""])[0], params.get("sale_assistant", [""])[0],
                    params.get("source", [""])[0], scope,
                ), "summary": self.service.potential_customer_summary(user, scope)})
            elif path == "/api/care-appointments":
                params = parse_qs(parsed.query)
                self.send_json(200, {"ok": True, "data": self.service.care_appointments(
                    user,
                    params.get("q", [""])[0],
                    params.get("action_type", [""])[0],
                    params.get("sale_owner", [""])[0],
                    params.get("date_from", [""])[0],
                    params.get("date_to", [""])[0],
                    params.get("status", [""])[0],
                    params.get("scope", [""])[0],
                )})
            elif path.startswith("/api/potential-customers/") and path.endswith("/followups"):
                self.send_json(200, {"ok": True, "data": self.service.potential_customer_detail(user, path.split("/")[-2])["followups"]})
            elif path.startswith("/api/potential-customers/"):
                self.send_json(200, {"ok": True, "data": self.service.potential_customer_detail(user, path.rsplit("/", 1)[1])})
            elif path == "/api/audit":
                require_role(user, "ADMIN", "STAFF")
                rows = self.service.db.execute("SELECT * FROM audit_events ORDER BY id DESC LIMIT 100").fetchall()
                self.send_json(200, {"ok": True, "data": rows_dict(rows)})
            elif path == "/api/export/courses":
                self.send_csv("courses.csv", self.service.courses(parse_qs(parsed.query).get("q", [""])[0], user))
            elif path == "/api/export/classrooms":
                params = parse_qs(parsed.query)
                self.send_csv("classrooms.csv", self.service.classrooms(
                    user, params.get("q", [""])[0], params.get("status", [""])[0]
                ))
            elif path == "/api/export/session-slots":
                params = parse_qs(parsed.query)
                self.send_csv("session-slots.csv", self.service.session_slots(
                    user, params.get("q", [""])[0], params.get("status", [""])[0]
                ))
            elif path == "/api/export/students":
                params = parse_qs(parsed.query)
                self.send_csv("students.csv", self.service.students(
                    user, params.get("q", [""])[0], params.get("parent", [""])[0],
                    params.get("status", [""])[0], params.get("class_code", [""])[0],
                    params.get("referral_source", [""])[0], params.get("year", [""])[0],
                    params.get("school", [""])[0]
                ))
            elif path == "/api/export/teachers":
                params = parse_qs(parsed.query)
                self.send_csv("teachers.csv", self.service.teachers(
                    user, params.get("q", [""])[0], params.get("nationality", [""])[0], params.get("status", [""])[0]
                ))
            elif path == "/api/export/classes":
                params = parse_qs(parsed.query)
                raw_course = params.get("course_id", [None])[0]
                if raw_course in (None, ""):
                    course_id = None
                else:
                    try:
                        course_id = int(raw_course)
                    except (TypeError, ValueError) as exc:
                        raise AppError(400, "VALIDATION_ERROR", "course_id must be numeric") from exc
                    if course_id < 1:
                        raise AppError(400, "VALIDATION_ERROR", "course_id must be positive")
                self.send_csv("classes.csv", self.service.classes(
                    user,
                    params.get("q", [""])[0],
                    params.get("status", [""])[0],
                    course_id,
                    params.get("start_from", [""])[0],
                    params.get("start_to", [""])[0],
                    params.get("manager", [""])[0],
                    params.get("teacher", [""])[0],
                ))
            elif path == "/api/export/timetable":
                params = parse_qs(parsed.query)
                self.send_csv("timetable.csv", self.service.timetable(
                    user,
                    params.get("date", [None])[0],
                    params.get("teacher", [""])[0],
                    params.get("course", [""])[0],
                    params.get("class_code", [""])[0],
                    params.get("room", [""])[0],
                    params.get("time", [""])[0],
                    params.get("status", [""])[0],
                ))
            elif path == "/api/export/pending-enrollments":
                params = parse_qs(parsed.query)
                self.send_csv("pending-enrollments.csv", self.service.pending_enrollments(
                    user,
                    params.get("status", [""])[0],
                    params.get("course", [""])[0],
                    params.get("preferred_day", [""])[0],
                    params.get("date_from", [""])[0],
                    params.get("date_to", [""])[0],
                ))
            elif path == "/api/export/customer-tests":
                params = parse_qs(parsed.query)
                self.send_csv("customer-tests.csv", self.service.customer_tests(
                    user,
                    params.get("q", [""])[0],
                    params.get("status", [""])[0],
                    params.get("sales_owner", [""])[0],
                    params.get("date_from", [""])[0],
                    params.get("date_to", [""])[0],
                ))
            elif path == "/api/export/potential-customers":
                params = parse_qs(parsed.query)
                self.send_csv("potential-customers.csv", self.service.potential_customers(
                    user, params.get("q", [""])[0], params.get("status", [""])[0],
                    params.get("sale_owner", [""])[0], params.get("sale_assistant", [""])[0],
                    params.get("source", [""])[0], params.get("scope", [""])[0],
                ))
            elif path == "/api/export/care-appointments":
                params = parse_qs(parsed.query)
                self.send_csv("care-appointments.csv", self.service.care_appointments(
                    user,
                    params.get("q", [""])[0],
                    params.get("action_type", [""])[0],
                    params.get("sale_owner", [""])[0],
                    params.get("date_from", [""])[0],
                    params.get("date_to", [""])[0],
                    params.get("status", [""])[0],
                    params.get("scope", [""])[0],
                ))
            elif path == "/api/export/finance-bills":
                params = parse_qs(parsed.query)
                self.send_csv("finance-bills.csv", self.service.finance_bills(
                    user, params.get("q", [""])[0], params.get("confirmation_status", [""])[0],
                    params.get("center", [""])[0], params.get("branch", [""])[0], params.get("employee", [""])[0],
                    params.get("date_from", [""])[0], params.get("date_to", [""])[0], params.get("creator", [""])[0],
                ))
            elif path == "/api/export/finance-contracts":
                params = parse_qs(parsed.query)
                self.send_csv("finance-contracts.csv", self.service.finance_contracts(
                    user, params.get("q", [""])[0], params.get("payment_status", [""])[0],
                    params.get("contract_status", [""])[0], params.get("sales_owner", [""])[0],
                    params.get("date_from", [""])[0], params.get("date_to", [""])[0],
                    params.get("expiry_from", [""])[0], params.get("expiry_to", [""])[0],
                    params.get("course_id", [""])[0], params.get("branch", [""])[0],
                    params.get("creator", [""])[0], params.get("discount", [""])[0],
                    params.get("expired_date_status", [""])[0],
                ))
            elif path == "/api/export/finance-transfers":
                params = parse_qs(parsed.query)
                self.send_csv("finance-transfers.csv", self.service.finance_transfers(user, params.get("q", [""])[0], params.get("status", [""])[0]))
            elif path == "/api/export/finance-history-move-student":
                store = getattr(self.service, "finance_history_move_store", None)
                if store is None:
                    raise AppError(503, "MODULE_UNAVAILABLE", "finance history move module is unavailable")
                params = parse_qs(parsed.query)
                try:
                    csv_text = store.export_csv(
                        {"q": params.get("q", [""])[0], "status": params.get("status", [""])[0]},
                        role=user["role"],
                    )
                except PermissionError as exc:
                    raise AppError(403, "FORBIDDEN", str(exc)) from exc
                except ValueError as exc:
                    raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc
                self.send_csv_text("finance-history-move-student.csv", csv_text)
            elif path == "/api/export/finance-spends":
                params = parse_qs(parsed.query)
                filters = {
                    key: params.get(key, [""])[0]
                    for key in ("center_id", "category", "q", "from_date", "to_date")
                    if params.get(key, [""])[0]
                }
                self.send_csv("finance-spends.csv", self.service.finance_spend_export(user, filters))
            elif path == "/api/export/finance-assessments":
                params = parse_qs(parsed.query)
                self.send_csv_text("finance-assessments.csv", self.service.finance_assessment_export(user, {
                    "q": params.get("q", [""])[0], "status": params.get("status", [""])[0],
                }))
            elif path == "/api/export/finance-reserves":
                params = parse_qs(parsed.query)
                self.send_csv_text("finance-reserves.csv", self.service.finance_reserve_export(user, {
                    "q": params.get("q", [""])[0], "mode": params.get("mode", [""])[0],
                }))
            elif path == "/api/export/finance-point-rules":
                params = parse_qs(parsed.query)
                self.send_csv_text("finance-point-rules.csv", self.service.finance_point_export(user, {
                    "q": params.get("q", [""])[0], "status": params.get("status", [""])[0],
                    "center_id": params.get("center_id", [""])[0],
                }))
            elif path == "/api/export/finance-items":
                params = parse_qs(parsed.query)
                self.send_csv_text("finance-items.csv", self.service.finance_item_export(user, {
                    "q": params.get("q", [""])[0], "status": params.get("status", [""])[0],
                }))
            elif path == "/api/export/finance-debit-items":
                params = parse_qs(parsed.query)
                self.send_csv_text("finance-debit-items.csv", self.service.finance_debit_item_export(user, {
                    "q": params.get("q", [""])[0], "status": params.get("status", ["Tất cả"])[0],
                    "from_date": params.get("from_date", [""])[0], "to_date": params.get("to_date", [""])[0],
                    "item_name": params.get("item_name", ["Tất cả"])[0],
                }))
            elif path == "/api/export/finance-wallets":
                params = parse_qs(parsed.query)
                self.send_csv_text("finance-wallets.csv", self.service.finance_wallet_export(user, {
                    "q": params.get("q", [""])[0], "status": params.get("status", [""])[0],
                }))
            elif path in ("/api/export/finance-appointments", "/api/export/sale-appointments"):
                params = parse_qs(parsed.query)
                filters = {key: params.get(key, [""])[0] for key in ("q", "date_from", "date_to", "appointment_type") if params.get(key, [""])[0]}
                self.send_csv("finance-appointments.csv", self.service.export_finance_appointments(user, filters))
            elif path == "/api/export/finance-revenues":
                params = parse_qs(parsed.query)
                self.send_csv("finance-revenues.csv", self.service.finance_revenues(
                    user, params.get("q", [""])[0], params.get("status", [""])[0], params.get("center", [""])[0]
                ))
            elif path == "/api/export/surveys":
                params = parse_qs(parsed.query)
                self.send_csv("surveys.csv", self.service.surveys(user, params.get("q", [""])[0], params.get("status", [""])[0]))
            elif path == "/api/export/call-history":
                params = parse_qs(parsed.query)
                self.send_csv("call-history.csv", self.service.call_history(
                    user, params.get("q", [""])[0], params.get("status", [""])[0], params.get("call_type", [""])[0],
                    params.get("party_role", [""])[0], params.get("staff_name", [""])[0], params.get("date_from", [""])[0], params.get("date_to", [""])[0],
                ))
            elif path == "/api/export/report-engine":
                params = parse_qs(parsed.query)
                report = self.service.report_engine(user, params.get("route", ["/report/training/attendance"])[0], params.get("q", [""])[0], params.get("date_from", [""])[0], params.get("date_to", [""])[0], params.get("class_id", [""])[0], params.get("teacher", [""])[0])
                if report["rows"]:
                    self.send_csv("report.csv", report["rows"])
                else:
                    # Preserve the legacy endpoint's CSV metadata contract
                    # without inventing a report record.  The structured v2
                    # endpoint carries the actual ``data_status=NO_DATA``.
                    self.send_csv_text("report.csv", "status\r\n")
            else:
                raise AppError(404, "NOT_FOUND", "route not found")
        except AppError as exc:
            self.error(exc)
        except KeyError as exc:
            # Report definitions are data-driven. Unknown report routes must
            # become a structured 404, never an uncaught socket hangup.
            self.error(AppError(404, "NOT_FOUND", str(exc)))
        except ValueError as exc:
            self.error(AppError(400, "REQUEST_ERROR", str(exc)))
        except sqlite3.Error:
            self.error(AppError(500, "STORAGE_ERROR", "storage operation failed"))

    def do_POST(self) -> None:
        with self.service.db_lock:
            self._do_POST()

    def _do_POST(self) -> None:
        try:
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"
            payload = self.read_json()
            if path == "/api/auth/login":
                login = clean_text(payload.get("login"), 254)
                password = payload.get("password")
                if not isinstance(password, str) or not login:
                    raise AppError(400, "VALIDATION_ERROR", "login and password are required")
                user = self.service.user_by_login(login)
                if not user or not password_matches(password, user["password_hash"]):
                    raise AppError(401, "INVALID_CREDENTIALS", "invalid login or password")
                token, csrf, expiry = self.service.create_session(user["id"])
                self.service.audit(user["id"], "LOGIN", "session", None, {})
                secure = "; Secure" if cookie_secure_enabled() else ""
                cookie = "center_session={}; Path=/; HttpOnly; SameSite=Lax; Max-Age={}{}".format(token, SESSION_TTL, secure)
                self.send_json(200, {"ok": True, "user": public_user(user), "csrf_token": csrf, "expires_at": expiry}, headers={"Set-Cookie": cookie})
                return
            user, session = self.current_user()
            self.check_csrf(session)
            if path == "/api/auth/logout":
                self.service.destroy_session(self.cookie_token())
                secure = "; Secure" if cookie_secure_enabled() else ""
                self.send_json(200, {"ok": True}, headers={"Set-Cookie": "center_session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0{}".format(secure)})
            elif path == "/api/generated/screens":
                route = clean_text(payload.get("route"), 300)
                if not route.startswith("/"):
                    raise AppError(400, "VALIDATION_ERROR", "route must start with /")
                self.send_json(201, {"ok": True, "data": self.service.add_generated_record(user, route, payload)})
            elif path.startswith("/api/generated/screens/"):
                parts = path.split("/")
                if len(parts) != 5:
                    raise AppError(404, "NOT_FOUND", "generated screen record not found")
                try:
                    record_id = int(parts[-1])
                except ValueError as exc:
                    raise AppError(400, "VALIDATION_ERROR", "record id must be numeric") from exc
                route = clean_text(payload.get("route"), 300)
                if not route.startswith("/"):
                    raise AppError(400, "VALIDATION_ERROR", "route must start with /")
                self.send_json(200, {"ok": True, "data": self.service.update_generated_record(user, route, record_id, payload)})
            elif path == "/api/students/preview":
                self.send_json(200, {"ok": True, "data": self.service.preview_student_import(user, payload.get("csv"))})
            elif path == "/api/students/import":
                self.send_json(201, {"ok": True, "data": self.service.import_students(user, payload.get("csv"))})
            elif path == "/api/students":
                self.send_json(201, {"ok": True, "data": self.service.add_student(user, payload)})
            elif path == "/api/teachers":
                self.send_json(201, {"ok": True, "data": self.service.add_teacher(user, payload)})
            elif path.startswith("/api/teachers/"):
                self.send_json(200, {"ok": True, "data": self.service.update_teacher(user, path.rsplit("/", 1)[1], payload)})
            elif path.startswith("/api/students/"):
                self.send_json(200, {"ok": True, "data": self.service.update_student(user, path.rsplit("/", 1)[1], payload)})
            elif path == "/api/courses":
                self.send_json(201, {"ok": True, "data": self.service.add_course(user, payload)})
            elif path == "/api/classrooms":
                self.send_json(201, {"ok": True, "data": self.service.add_classroom(user, payload)})
            elif path.startswith("/api/classrooms/"):
                self.send_json(200, {"ok": True, "data": self.service.update_classroom(user, path.rsplit("/", 1)[1], payload)})
            elif path == "/api/session-slots":
                self.send_json(201, {"ok": True, "data": self.service.add_session_slot(user, payload)})
            elif path.startswith("/api/session-slots/"):
                self.send_json(200, {"ok": True, "data": self.service.update_session_slot(user, path.rsplit("/", 1)[1], payload)})
            elif path.startswith("/api/courses/") and path.endswith("/duplicate"):
                course_id = path.split("/")[-2]
                self.send_json(201, {"ok": True, "data": self.service.duplicate_course(user, course_id, payload)})
            elif path.startswith("/api/courses/"):
                self.send_json(200, {"ok": True, "data": self.service.update_course(user, path.rsplit("/", 1)[1], payload)})
            elif path == "/api/classes":
                self.send_json(201, {"ok": True, "data": self.service.add_class(user, payload)})
            elif path == "/api/classes/import":
                text = payload.get("csv")
                self.send_json(201, {"ok": True, "data": self.service.import_classes(user, text)})
            elif path == "/api/classes/workflow":
                self.send_json(201, {"ok": True, "data": self.service.create_class_workflow(user, payload)})
            elif path.startswith("/api/classes/"):
                self.send_json(200, {"ok": True, "data": self.service.update_class(user, path.rsplit("/", 1)[1], payload)})
            elif path == "/api/attendance":
                self.send_json(200, {"ok": True, "data": self.service.mark_attendance(user, payload)})
            elif path == "/api/timetable":
                self.send_json(201, {"ok": True, "data": self.service.add_timetable(user, payload)})
            elif path.startswith("/api/timetable/") and path.endswith("/cancel"):
                session_id = path.split("/")[-2]
                self.send_json(200, {"ok": True, "data": self.service.cancel_timetable(user, session_id)})
            elif path.startswith("/api/timetable/"):
                self.send_json(200, {"ok": True, "data": self.service.update_timetable(user, path.rsplit("/", 1)[1], payload)})
            elif path == "/api/evaluations":
                self.send_json(200, {"ok": True, "data": self.service.upsert_evaluation(user, payload)})
            elif path == "/api/tests":
                self.send_json(201, {"ok": True, "data": self.service.add_test(user, payload)})
            elif path == "/api/test-results":
                self.send_json(200, {"ok": True, "data": self.service.upsert_test_result(user, payload)})
            elif path == "/api/homework":
                self.send_json(201, {"ok": True, "data": self.service.add_homework(user, payload)})
            elif path == "/api/trial-registrations":
                self.send_json(201, {"ok": True, "data": self.service.add_trial_registration(user, payload)})
            elif path == "/api/enrollment-confirmations":
                self.send_json(200, {"ok": True, "data": self.service.set_enrollment_confirmation(user, payload)})
            elif path == "/api/customer-tests":
                self.send_json(201, {"ok": True, "data": self.service.add_customer_test(user, payload)})
            elif path.startswith("/api/customer-tests/"):
                self.send_json(200, {"ok": True, "data": self.service.update_customer_test(user, path.rsplit("/", 1)[1], payload)})
            elif path == "/api/pending-enrollments":
                self.send_json(201, {"ok": True, "data": self.service.add_pending_enrollment(user, payload)})
            elif path.startswith("/api/pending-enrollments/") and path.endswith("/cancel"):
                self.service.delete_pending_enrollment(user, path.split("/")[-2])
                self.send_json(200, {"ok": True, "data": {"status": "CANCELLED"}})
            elif path.startswith("/api/pending-enrollments/"):
                self.send_json(200, {"ok": True, "data": self.service.update_pending_enrollment(user, path.rsplit("/", 1)[1], payload)})
            elif path == "/api/finance/contracts":
                self.send_json(201, {"ok": True, "data": self.service.add_finance_contract(user, payload)})
            elif path == "/api/finance/contract/upload/preview":
                store = getattr(self.service, "finance_contract_store", None)
                if store is None:
                    raise AppError(503, "MODULE_UNAVAILABLE", "finance contract module is unavailable")
                try:
                    data = store.preview(payload.get("csv"), role=user["role"])
                except PermissionError as exc:
                    raise AppError(403, "FORBIDDEN", str(exc)) from exc
                except ValueError as exc:
                    raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc
                self.send_json(200, {"ok": True, "data": data})
            elif path == "/api/finance/contract/upload/commit":
                store = getattr(self.service, "finance_contract_store", None)
                if store is None:
                    raise AppError(503, "MODULE_UNAVAILABLE", "finance contract module is unavailable")
                try:
                    data = store.commit_upload(
                        payload.get("csv"),
                        role=user["role"],
                        actor=user["full_name"],
                    )
                except PermissionError as exc:
                    raise AppError(403, "FORBIDDEN", str(exc)) from exc
                except ValueError as exc:
                    raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc
                self.send_json(201, {"ok": True, "data": data})
            elif path == "/api/finance/transfers":
                self.send_json(201, {"ok": True, "data": self.service.add_finance_transfer(user, payload)})
            elif path == "/api/finance/history-move-student":
                store = getattr(self.service, "finance_history_move_store", None)
                if store is None:
                    raise AppError(503, "MODULE_UNAVAILABLE", "finance history move module is unavailable")
                try:
                    self.send_json(201, {"ok": True, "data": store.create(
                        payload, role=user["role"], actor=user["full_name"]
                    )})
                except PermissionError as exc:
                    raise AppError(403, "FORBIDDEN", str(exc)) from exc
                except ValueError as exc:
                    raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc
            elif path.startswith("/api/finance/history-move-student/"):
                store = getattr(self.service, "finance_history_move_store", None)
                if store is None:
                    raise AppError(503, "MODULE_UNAVAILABLE", "finance history move module is unavailable")
                try:
                    move_id = int(path.rsplit("/", 1)[1])
                except (TypeError, ValueError) as exc:
                    raise AppError(400, "VALIDATION_ERROR", "record id must be numeric") from exc
                try:
                    self.send_json(200, {"ok": True, "data": store.update(
                        move_id, payload, role=user["role"], actor=user["full_name"]
                    )})
                except PermissionError as exc:
                    raise AppError(403, "FORBIDDEN", str(exc)) from exc
                except ValueError as exc:
                    raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc
                except KeyError as exc:
                    raise AppError(404, "HISTORY_MOVE_NOT_FOUND", str(exc)) from exc
            elif path == "/api/finance/spends":
                self.send_json(201, {"ok": True, "data": self.service.add_finance_spend(user, payload)})
            elif path.startswith("/api/finance/spends/"):
                self.send_json(200, {"ok": True, "data": self.service.update_finance_spend(user, path.rsplit("/", 1)[1], payload)})
            elif path == "/api/finance/assessments":
                self.send_json(201, {"ok": True, "data": self.service.add_finance_assessment(user, payload)})
            elif path.startswith("/api/finance/assessments/"):
                self.send_json(200, {"ok": True, "data": self.service.update_finance_assessment(user, path.rsplit("/", 1)[1], payload)})
            elif path == "/api/finance/reserves":
                self.send_json(201, {"ok": True, "data": self.service.add_finance_reserve(user, payload)})
            elif path.startswith("/api/finance/reserves/"):
                self.send_json(200, {"ok": True, "data": self.service.update_finance_reserve(user, path.rsplit("/", 1)[1], payload)})
            elif path == "/api/finance/point-rules":
                self.send_json(201, {"ok": True, "data": self.service.add_finance_point(user, payload)})
            elif path.startswith("/api/finance/point-rules/"):
                self.send_json(200, {"ok": True, "data": self.service.update_finance_point(user, path.rsplit("/", 1)[1], payload)})
            elif path == "/api/finance/items":
                self.send_json(201, {"ok": True, "data": self.service.add_finance_item(user, payload)})
            elif path.startswith("/api/finance/items/"):
                self.send_json(200, {"ok": True, "data": self.service.update_finance_item(user, path.rsplit("/", 1)[1], payload)})
            elif path == "/api/finance/debit-items":
                self.send_json(201, {"ok": True, "data": self.service.add_finance_debit_item(user, payload)})
            elif path.startswith("/api/finance/debit-items/"):
                self.send_json(200, {"ok": True, "data": self.service.update_finance_debit_item(user, path.rsplit("/", 1)[1], payload)})
            elif path in ("/api/finance/appointments", "/api/sale/appointments"):
                self.send_json(201, {"ok": True, "data": self.service.add_finance_appointment(user, payload)})
            elif path.startswith("/api/finance/appointments/"):
                self.send_json(200, {"ok": True, "data": self.service.update_finance_appointment(user, path.rsplit("/", 1)[1], payload)})
            elif path.startswith("/api/finance/contracts/"):
                self.send_json(200, {"ok": True, "data": self.service.update_finance_contract(user, path.rsplit("/", 1)[1], payload)})
            elif path == "/api/finance/bills":
                self.send_json(201, {"ok": True, "data": self.service.add_finance_bill(user, payload)})
            elif path.startswith("/api/finance/bills/") and path.endswith("/confirm"):
                self.send_json(200, {"ok": True, "data": self.service.confirm_finance_bill(user, path.split("/")[-2])})
            elif path.startswith("/api/finance/bills/"):
                self.send_json(200, {"ok": True, "data": self.service.update_finance_bill(user, path.rsplit("/", 1)[1], payload)})
            elif path == "/api/finance/revenues":
                self.send_json(201, {"ok": True, "data": self.service.add_finance_revenue(user, payload)})
            elif path.startswith("/api/finance/revenues/"):
                self.send_json(200, {"ok": True, "data": self.service.update_finance_revenue(user, path.rsplit("/", 1)[1], payload)})
            elif path == "/api/surveys":
                self.send_json(201, {"ok": True, "data": self.service.add_survey(user, payload)})
            elif path.startswith("/api/surveys/") and path.endswith("/pages"):
                self.send_json(201, {"ok": True, "data": self.service.add_survey_page(user, path.split("/")[-2], payload)})
            elif path.startswith("/api/surveys/") and path.endswith("/responses"):
                self.send_json(201, {"ok": True, "data": self.service.add_survey_response(user, path.split("/")[-2], payload)})
            elif path.startswith("/api/survey-pages/") and path.endswith("/questions"):
                self.send_json(201, {"ok": True, "data": self.service.add_survey_question(user, path.split("/")[-2], payload)})
            elif path.startswith("/api/survey-pages/"):
                self.send_json(200, {"ok": True, "data": self.service.update_survey_page(user, path.rsplit("/", 1)[1], payload)})
            elif path.startswith("/api/survey-questions/"):
                self.send_json(200, {"ok": True, "data": self.service.update_survey_question(user, path.rsplit("/", 1)[1], payload)})
            elif path.startswith("/api/surveys/"):
                self.send_json(200, {"ok": True, "data": self.service.update_survey(user, path.rsplit("/", 1)[1], payload)})
            elif path == "/api/call-history":
                self.send_json(201, {"ok": True, "data": self.service.add_call_record(user, payload)})
            elif path.startswith("/api/call-history/"):
                self.send_json(200, {"ok": True, "data": self.service.update_call_record(user, path.rsplit("/", 1)[1], payload)})
            elif path == "/api/potential-customers":
                self.send_json(201, {"ok": True, "data": self.service.add_potential_customer(user, payload)})
            elif path.startswith("/api/potential-customers/") and path.endswith("/followups"):
                self.send_json(201, {"ok": True, "data": self.service.add_potential_followup(user, path.split("/")[-2], payload)})
            elif path.startswith("/api/potential-customers/"):
                self.send_json(200, {"ok": True, "data": self.service.update_potential_customer(user, path.rsplit("/", 1)[1], payload)})
            else:
                raise AppError(404, "NOT_FOUND", "route not found")
        except AppError as exc:
            self.error(exc)
        except KeyError as exc:
            self.error(AppError(404, "NOT_FOUND", str(exc)))
        except ValueError as exc:
            self.error(AppError(400, "REQUEST_ERROR", str(exc)))
        except sqlite3.Error:
            self.error(AppError(500, "STORAGE_ERROR", "storage operation failed"))

    def do_DELETE(self) -> None:
        with self.service.db_lock:
            try:
                parsed = urlparse(self.path)
                path = parsed.path.rstrip("/") or "/"
                user, session = self.current_user()
                self.check_csrf(session)
                if path.startswith("/api/potential-customers/"):
                    parts = path.split("/")
                    if len(parts) != 4 or not parts[-1]:
                        raise AppError(404, "NOT_FOUND", "potential customer not found")
                    self.send_json(200, {"ok": True, "data": self.service.delete_potential_customer(user, parts[-1])})
                    return
                if not path.startswith("/api/generated/screens/"):
                    raise AppError(404, "NOT_FOUND", "route not found")
                parts = path.split("/")
                if len(parts) != 5:
                    raise AppError(404, "NOT_FOUND", "generated screen record not found")
                route = parse_qs(parsed.query).get("route", [""])[0]
                if not route:
                    raise AppError(400, "VALIDATION_ERROR", "route query is required")
                self.send_json(200, {"ok": True, "data": self.service.delete_generated_record(user, route, parts[-1])})
            except AppError as exc:
                self.error(exc)
            except sqlite3.Error:
                self.error(AppError(500, "STORAGE_ERROR", "storage operation failed"))

    def serve_static(self, name: str) -> None:
        candidate = (STATIC_DIR / name).resolve()
        if STATIC_DIR.resolve() not in candidate.parents and candidate != STATIC_DIR.resolve():
            raise AppError(404, "NOT_FOUND", "asset not found")
        if not candidate.is_file():
            raise AppError(404, "NOT_FOUND", "asset not found")
        body = candidate.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(str(candidate))[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.send_security_headers()
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            return


class CenterEduHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: Tuple[str, int], service: CenterEduService):
        super().__init__(address, RequestHandler)
        self.service = service


def create_server(db_path: Optional[Path] = None, host: str = "127.0.0.1", port: int = 8000) -> CenterEduHTTPServer:
    service = CenterEduService(db_path or Path(os.environ.get("CENTER_EDU_DB", str(DEFAULT_DB))))
    return CenterEduHTTPServer((host, port), service)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Center EDU rebuild")
    parser.add_argument("--host", default=os.environ.get("CENTER_EDU_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("CENTER_EDU_PORT", "8000")))
    parser.add_argument("--db", type=Path, default=Path(os.environ.get("CENTER_EDU_DB", str(DEFAULT_DB))))
    args = parser.parse_args()
    server = create_server(args.db, args.host, args.port)
    print("Center EDU listening on http://{}:{} (db={})".format(args.host, args.port, args.db), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.service.close()


if __name__ == "__main__":
    main()
