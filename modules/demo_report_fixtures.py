"""Small, isolated finance-report fixtures for disposable rich demo databases.

These rows are synthetic test facts, stored only when CENTER_EDU_RICH_DEMO is
explicitly enabled. They are not copied from reference rows or customer data.
"""
from __future__ import annotations

import os
import sqlite3
import json
import re
from typing import Any

FIXTURE_BILLS = (
    ("RPT-FIXTURE-2026-01", "2026-01-15", 1_100_000, "Sale fixture A", "Nhóm sale fixture A"),
    ("RPT-FIXTURE-2026-06", "2026-06-15", 1_250_000, "Sale fixture B", "Nhóm sale fixture B"),
    ("RPT-FIXTURE-2026-11", "2026-11-15", 1_400_000, "Sale fixture C", "Nhóm sale fixture C"),
)

TARGET_FIXTURES = (
    {"column_1": "›", "scope": "center", "thoi_gian": "2026-01-01", "doanh_thu": 0, "hop_ong": 0, "tai_tuc": 0, "hanh_ong": ""},
    {"column_1": "›", "scope": "center", "thoi_gian": "2026-05-01", "doanh_thu": 100_000_000, "hop_ong": 40, "tai_tuc": 60, "hanh_ong": ""},
    {"column_1": "›", "scope": "center", "thoi_gian": "2026-11-01", "doanh_thu": 0, "hop_ong": 0, "tai_tuc": 0, "hanh_ong": ""},
)


def _seed_target_fixtures(connection: sqlite3.Connection, admin_id: int | None) -> int:
    """Replace only generic generated fallback rows with three local target facts."""
    if admin_id is None:
        return 0
    # Focused fixture tests and older disposable schemas may omit this optional
    # generated-records table.  Finance fixtures remain usable in that case.
    table = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='generated_screen_records'"
    ).fetchone()
    if table is None:
        return 0
    rows = connection.execute(
        "SELECT id,data_json FROM generated_screen_records WHERE route=? AND deleted_at IS NULL",
        ("/crm/target/index",),
    ).fetchall()
    removable = []
    for row in rows:
        try:
            payload = json.loads(row[1] or "{}")
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
        values = [str(value or "") for value in payload.values()]
        # The generated fallback is identifiable by its repeated column-label
        # shape.  Do not remove arbitrary route data merely because a note or
        # customer-facing value happens to contain the word "Demo".
        generic_markers = [value for value in values if value]
        core_keys_match = all(
            re.fullmatch(r"(?:Column 1|column_1|Doanh thu|Hợp đồng|Tái tục|Hành động) Demo \d+", str(payload.get(key, "")))
            for key in ("column_1", "doanh_thu", "hop_ong", "tai_tuc", "hanh_ong")
        )
        is_generic = (
            len(generic_markers) >= 10
            and core_keys_match
        )
        if is_generic:
            removable.append((row[0],))
    if removable:
        connection.executemany("DELETE FROM generated_screen_records WHERE id=?", removable)
    existing = connection.execute(
        "SELECT COUNT(*) FROM generated_screen_records WHERE route=? AND deleted_at IS NULL",
        ("/crm/target/index",),
    ).fetchone()[0]
    if existing:
        return 0
    connection.executemany(
        "INSERT INTO generated_screen_records(route,data_json,created_by) VALUES(?,?,?)",
        [("/crm/target/index", json.dumps(payload, ensure_ascii=False), admin_id) for payload in TARGET_FIXTURES],
    )
    return len(TARGET_FIXTURES)


def seed(connection: sqlite3.Connection, *, rich_demo: bool) -> int:
    """Persist no more than three idempotent local-only report fixture bills."""
    connection.execute(
        """CREATE TABLE IF NOT EXISTS finance_report_team_memberships (
             invoice_code TEXT PRIMARY KEY,
             team_name TEXT NOT NULL,
             fixture_tag TEXT NOT NULL CHECK (fixture_tag = 'SYNTHETIC_LOCAL_REPORT_FIXTURE'),
             FOREIGN KEY(invoice_code) REFERENCES finance_bills(invoice_code) ON DELETE CASCADE
           )"""
    )
    connection.commit()
    if not rich_demo:
        return 0
    count = 0
    for invoice_code, invoice_date, amount, sale_name, team_name in FIXTURE_BILLS:
        exists = connection.execute("SELECT 1 FROM finance_bills WHERE invoice_code=?", (invoice_code,)).fetchone()
        if not exists:
            created_by = connection.execute("SELECT id FROM users WHERE username='admin' ORDER BY id LIMIT 1").fetchone()
            connection.execute(
                """INSERT INTO finance_bills
                   (invoice_code,contract_code,class_code,subject,customer_name,payment_amount,
                    sales_owner,created_by,center,branch,employee,confirmation_status,payment_method,note,invoice_date)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (invoice_code, "", "", "Bản ghi báo cáo tổng hợp", "Fixture tổng hợp",
                 amount, sale_name, created_by[0] if created_by else None, "Trung tâm fixture",
                 "Chi nhánh fixture", sale_name, "CONFIRMED", "Chuyển khoản",
                 "Synthetic local report fixture", invoice_date),
            )
            count += 1
        connection.execute(
            """INSERT OR IGNORE INTO finance_report_team_memberships
               (invoice_code,team_name,fixture_tag) VALUES(?,?,?)""",
            (invoice_code, team_name, "SYNTHETIC_LOCAL_REPORT_FIXTURE"),
        )
    connection.commit()
    admin = connection.execute("SELECT id FROM users WHERE username='admin' ORDER BY id LIMIT 1").fetchone()
    count += _seed_target_fixtures(connection, admin[0] if admin else None)
    connection.commit()
    return count


def register(app_or_router: Any = None, service: Any = None) -> dict[str, Any]:
    target = service if service is not None else app_or_router
    connection = getattr(target, "db", None)
    rich_demo = os.environ.get("CENTER_EDU_RICH_DEMO", "").strip().lower() in {"1", "true", "yes", "on"}
    seeded = seed(connection, rich_demo=rich_demo) if isinstance(connection, sqlite3.Connection) else 0
    return {
        "routes": [], "source": "isolated-rich-demo-fixtures", "status": "FIXTURES_READY",
        "schema": "finance_report_team_memberships,finance_bills", "seeded_rows": seeded,
    }
