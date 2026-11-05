"""Persistent CRM prospect and care appointment domain.

The HTTP application owns routing and session handling. This module owns the
durable records used by the ``/crm/potential`` and Sale appointment surfaces,
so either lane can mount the same SQLite contract without browser-only state.
"""
from __future__ import annotations

import csv
import io
import sqlite3
from datetime import datetime
from typing import Any

PROSPECT_ROUTES = ("/crm/potential/index", "/sale/potential/index")
APPOINTMENT_ROUTES = ("/crm/potential/appointment", "/sale/potential/appointment")
READ_ROLES = frozenset({"ADMIN", "STAFF"})
WRITE_ROLES = frozenset({"ADMIN", "STAFF"})
PROSPECT_STATUSES = ("Khách hàng mới", "Đang chăm sóc", "Đủ điều kiện", "Đã chuyển đổi", "Đã hủy tư vấn")
APPOINTMENT_ACTIONS = ("Gọi", "Nhắn tin", "Gặp trực tiếp", "Ghi chú")
APPOINTMENT_STATUSES = ("Chưa xử lý", "Đã xử lý", "Đã hủy cuộc hẹn")
PROSPECT_COLUMNS = ("STT", "Khách hàng", "Nhân viên sale", "Sale phụ", "Tag", "Khóa học chăm sóc", "Khóa học quan tâm", "Trạng thái", "Hẹn test", "Điểm test", "Học thử", "Ghi chú", "Chăm sóc")
APPOINTMENT_COLUMNS = ("STT", "Học viên", "Nhân viên sale", "Ngày hẹn", "Hành động", "Ghi chú", "Trạng thái")

SCHEMA = """
CREATE TABLE IF NOT EXISTS crm_prospects (
  id INTEGER PRIMARY KEY AUTOINCREMENT, customer_code TEXT NOT NULL UNIQUE,
  full_name TEXT NOT NULL, phone TEXT NOT NULL DEFAULT '', email TEXT NOT NULL DEFAULT '',
  source TEXT NOT NULL DEFAULT '', sale_owner TEXT NOT NULL DEFAULT '', sale_assistant TEXT NOT NULL DEFAULT '',
  tag TEXT NOT NULL DEFAULT '', care_course TEXT NOT NULL DEFAULT '', interested_course TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'Khách hàng mới', test_appointment TEXT, test_score REAL,
  trial_status TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '', care_progress TEXT NOT NULL DEFAULT '0/5',
  deleted_at TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CHECK(status IN ('Khách hàng mới','Đang chăm sóc','Đủ điều kiện','Đã chuyển đổi','Đã hủy tư vấn'))
);
CREATE INDEX IF NOT EXISTS idx_crm_prospects_status ON crm_prospects(status, id);
CREATE INDEX IF NOT EXISTS idx_crm_prospects_sale ON crm_prospects(sale_owner, id);
CREATE TABLE IF NOT EXISTS crm_care_appointments (
  id INTEGER PRIMARY KEY AUTOINCREMENT, prospect_id INTEGER NOT NULL REFERENCES crm_prospects(id) ON DELETE CASCADE,
  action_type TEXT NOT NULL, appointment_at TEXT NOT NULL, note TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'Chưa xử lý', created_by TEXT NOT NULL, deleted_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CHECK(action_type IN ('Gọi','Nhắn tin','Gặp trực tiếp','Ghi chú')),
  CHECK(status IN ('Chưa xử lý','Đã xử lý','Đã hủy cuộc hẹn'))
);
CREATE INDEX IF NOT EXISTS idx_crm_appointments_at ON crm_care_appointments(appointment_at, id);
CREATE INDEX IF NOT EXISTS idx_crm_appointments_status ON crm_care_appointments(status, id);
"""


def _text(value: Any, field: str, limit: int = 240, *, required: bool = False) -> str:
    text = "" if value is None else str(value).strip()
    if required and not text:
        raise ValueError(f"{field} là bắt buộc")
    if len(text) > limit:
        raise ValueError(f"{field} vượt quá {limit} ký tự")
    return text


def _date(value: Any, field: str, *, required: bool = False) -> str | None:
    text = _text(value, field, 16, required=required)
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date().isoformat()
    except ValueError as exc:
        raise ValueError(f"{field} phải theo dạng YYYY-MM-DD") from exc


def _datetime(value: Any, field: str = "appointment_at") -> str:
    text = _text(value, field, 16, required=True)
    try:
        return datetime.strptime(text, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M")
    except ValueError as exc:
        raise ValueError(f"{field} phải theo dạng YYYY-MM-DD HH:MM") from exc


def _score(value: Any) -> float | None:
    """Normalize an optional đầu vào điểm test without persisting text."""
    if value in (None, ""):
        return None
    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Điểm test phải là số") from exc
    if not 0 <= score <= 10:
        raise ValueError("Điểm test phải từ 0 đến 10")
    return int(score) if score.is_integer() else score


def _role(role: str, *, write: bool = False) -> None:
    if role not in (WRITE_ROLES if write else READ_ROLES):
        raise PermissionError("Bạn không có quyền truy cập dữ liệu CRM")


class CRMStore:
    """SQLite-backed prospect and care appointment store."""

    def __init__(self, connection: sqlite3.Connection):
        self.db = connection
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.db.commit()

    def _next_code(self) -> str:
        stamp = datetime.now().strftime("%Y%m%d")
        count = self.db.execute("SELECT COUNT(*) FROM crm_prospects WHERE customer_code LIKE ?", (f"KH-TIEM-{stamp}-%",)).fetchone()[0]
        return f"KH-TIEM-{stamp}-{int(count) + 1:04d}"

    def create_prospect(self, *, role: str, full_name: str, customer_code: str = "", phone: str = "", email: str = "", source: str = "", sale_owner: str = "", sale_assistant: str = "", tag: str = "", care_course: str = "", interested_course: str = "", status: str = "Khách hàng mới", test_appointment: str | None = None, test_score: float | None = None, trial_status: str = "", note: str = "", care_progress: str = "0/5") -> dict[str, Any]:
        _role(role, write=True)
        name = _text(full_name, "Họ tên", 120, required=True)
        status = _text(status, "Trạng thái", 32, required=True)
        if status not in PROSPECT_STATUSES:
            raise ValueError("Trạng thái khách hàng không hợp lệ")
        code = _text(customer_code, "Mã khách hàng", 40) or self._next_code()
        appointment = _date(test_appointment, "Hẹn test")
        score = _score(test_score)
        try:
            cur = self.db.execute("INSERT INTO crm_prospects(customer_code,full_name,phone,email,source,sale_owner,sale_assistant,tag,care_course,interested_course,status,test_appointment,test_score,trial_status,note,care_progress) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (code, name, _text(phone, "Điện thoại", 40), _text(email, "Email", 254), _text(source, "Nguồn", 120), _text(sale_owner, "Nhân viên sale", 120), _text(sale_assistant, "Sale phụ", 120), _text(tag, "Tag", 120), _text(care_course, "Khóa học chăm sóc", 160), _text(interested_course, "Khóa học quan tâm", 160), status, appointment, score, _text(trial_status, "Học thử", 80), _text(note, "Ghi chú", 1000), _text(care_progress, "Tiến độ chăm sóc", 20)))
        except sqlite3.IntegrityError as exc:
            raise ValueError("Mã khách hàng đã tồn tại") from exc
        self.db.commit()
        return self.get_prospect(cur.lastrowid, role=role)  # type: ignore[return-value]

    def list_prospects(self, *, role: str, query: str = "", status: str = "", sale_owner: str = "", sale_assistant: str = "", source: str = "", limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        _role(role); where = ["deleted_at IS NULL"]; args: list[Any] = []
        if query.strip():
            q = f"%{_text(query, 'Tìm kiếm', 160)}%"; where.append("(customer_code LIKE ? OR full_name LIKE ? OR phone LIKE ? OR email LIKE ? OR note LIKE ?)"); args.extend([q] * 5)
        if status:
            if status not in PROSPECT_STATUSES: raise ValueError("Trạng thái khách hàng không hợp lệ")
            where.append("status=?"); args.append(status)
        for column, value, label in (("sale_owner", sale_owner, "Nhân viên sale"), ("sale_assistant", sale_assistant, "Sale phụ"), ("source", source, "Nguồn")):
            if str(value or "").strip(): where.append(f"{column} LIKE ?"); args.append(f"%{_text(value, label, 120)}%")
        rows = self.db.execute("SELECT * FROM crm_prospects WHERE " + " AND ".join(where) + " ORDER BY id DESC LIMIT ? OFFSET ?", args + [max(1, min(int(limit), 500)), max(0, int(offset))]).fetchall()
        return [dict(row) for row in rows]

    def get_prospect(self, prospect_id: int, *, role: str) -> dict[str, Any] | None:
        _role(role); row = self.db.execute("SELECT * FROM crm_prospects WHERE id=? AND deleted_at IS NULL", (int(prospect_id),)).fetchone()
        if row is None: return None
        result = dict(row); result["appointments"] = self.list_appointments(role=role, prospect_id=int(prospect_id)); return result

    def update_prospect(self, prospect_id: int, *, role: str, **changes: Any) -> dict[str, Any]:
        _role(role, write=True); current = self.db.execute("SELECT * FROM crm_prospects WHERE id=? AND deleted_at IS NULL", (int(prospect_id),)).fetchone()
        if current is None: raise KeyError("Không tìm thấy khách hàng")
        allowed = {"customer_code", "full_name", "phone", "email", "source", "sale_owner", "sale_assistant", "tag", "care_course", "interested_course", "status", "test_appointment", "test_score", "trial_status", "note", "care_progress"}
        unknown = sorted(set(changes) - allowed)
        if unknown:
            raise ValueError("Trường CRM không được hỗ trợ: " + ", ".join(unknown))
        values = dict(current); values.update(changes)
        if values["status"] not in PROSPECT_STATUSES: raise ValueError("Trạng thái khách hàng không hợp lệ")
        values["customer_code"] = _text(values.get("customer_code"), "Mã khách hàng", 40, required=True)
        values["full_name"] = _text(values["full_name"], "Họ tên", 120, required=True)
        values["phone"] = _text(values.get("phone"), "Điện thoại", 40)
        values["email"] = _text(values.get("email"), "Email", 254)
        values["source"] = _text(values.get("source"), "Nguồn", 120)
        values["sale_owner"] = _text(values.get("sale_owner"), "Nhân viên sale", 120)
        values["sale_assistant"] = _text(values.get("sale_assistant"), "Sale phụ", 120)
        values["tag"] = _text(values.get("tag"), "Tag", 120)
        values["care_course"] = _text(values.get("care_course"), "Khóa học chăm sóc", 160)
        values["interested_course"] = _text(values.get("interested_course"), "Khóa học quan tâm", 160)
        values["test_appointment"] = _date(values.get("test_appointment"), "Hẹn test")
        values["test_score"] = _score(values.get("test_score"))
        values["trial_status"] = _text(values.get("trial_status"), "Học thử", 80)
        values["note"] = _text(values.get("note"), "Ghi chú", 1000)
        values["care_progress"] = _text(values.get("care_progress"), "Tiến độ chăm sóc", 20)
        columns = ["customer_code", "full_name", "phone", "email", "source", "sale_owner", "sale_assistant", "tag", "care_course", "interested_course", "status", "test_appointment", "test_score", "trial_status", "note", "care_progress"]
        args = [values[c] if c in {"test_score", "test_appointment"} else _text(values[c], c, 1000) for c in columns] + [int(prospect_id)]
        try: self.db.execute("UPDATE crm_prospects SET " + ",".join(f"{c}=?" for c in columns) + ",updated_at=CURRENT_TIMESTAMP WHERE id=?", args)
        except sqlite3.IntegrityError as exc: raise ValueError("Mã khách hàng đã tồn tại") from exc
        self.db.commit(); return self.get_prospect(prospect_id, role=role)  # type: ignore[return-value]

    def delete_prospect(self, prospect_id: int, *, role: str) -> None:
        _role(role, write=True); cur = self.db.execute("UPDATE crm_prospects SET deleted_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP WHERE id=? AND deleted_at IS NULL", (int(prospect_id),))
        if cur.rowcount != 1: raise KeyError("Không tìm thấy khách hàng")
        self.db.commit()

    def create_appointment(self, *, role: str, prospect_id: int, appointment_at: str, action_type: str, note: str, created_by: str, status: str = "Chưa xử lý") -> dict[str, Any]:
        _role(role, write=True)
        if self.get_prospect(prospect_id, role=role) is None: raise KeyError("Không tìm thấy khách hàng")
        if action_type not in APPOINTMENT_ACTIONS or status not in APPOINTMENT_STATUSES: raise ValueError("Hành động hoặc trạng thái lịch hẹn không hợp lệ")
        cur = self.db.execute("INSERT INTO crm_care_appointments(prospect_id,action_type,appointment_at,note,status,created_by) VALUES(?,?,?,?,?,?)", (int(prospect_id), action_type, _datetime(appointment_at), _text(note, "Ghi chú", 1000), status, _text(created_by, "Người tạo", 120, required=True)))
        self.db.commit(); return self.get_appointment(cur.lastrowid, role=role)  # type: ignore[return-value]

    def list_appointments(self, *, role: str, prospect_id: int | None = None, query: str = "", sale_owner: str = "", status: str = "", action_type: str = "", date_from: str = "", date_to: str = "", limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        _role(role); where = ["a.deleted_at IS NULL", "p.deleted_at IS NULL"]; args: list[Any] = []
        if prospect_id is not None: where.append("a.prospect_id=?"); args.append(int(prospect_id))
        if query.strip(): q = f"%{_text(query, 'Tìm kiếm', 160)}%"; where.append("(p.full_name LIKE ? OR p.customer_code LIKE ? OR p.phone LIKE ? OR a.note LIKE ?)"); args.extend([q] * 4)
        if sale_owner.strip(): where.append("p.sale_owner LIKE ?"); args.append(f"%{_text(sale_owner, 'Nhân viên sale', 120)}%")
        if status:
            if status not in APPOINTMENT_STATUSES: raise ValueError("Trạng thái lịch hẹn không hợp lệ")
            where.append("a.status=?"); args.append(status)
        if action_type:
            if action_type not in APPOINTMENT_ACTIONS: raise ValueError("Hành động lịch hẹn không hợp lệ")
            where.append("a.action_type=?"); args.append(action_type)
        start = _date(date_from, "Từ ngày"); end = _date(date_to, "Đến ngày")
        if start and end and start > end: raise ValueError("Khoảng ngày không hợp lệ")
        if start: where.append("substr(a.appointment_at,1,10)>=?"); args.append(start)
        if end: where.append("substr(a.appointment_at,1,10)<=?"); args.append(end)
        rows = self.db.execute("SELECT a.*,p.customer_code,p.full_name,p.phone,p.sale_owner FROM crm_care_appointments a JOIN crm_prospects p ON p.id=a.prospect_id WHERE " + " AND ".join(where) + " ORDER BY a.appointment_at DESC,a.id DESC LIMIT ? OFFSET ?", args + [max(1, min(int(limit), 500)), max(0, int(offset))]).fetchall()
        return [dict(row) for row in rows]

    def get_appointment(self, appointment_id: int, *, role: str) -> dict[str, Any] | None:
        _role(role); row = self.db.execute("SELECT a.*,p.customer_code,p.full_name,p.phone,p.sale_owner FROM crm_care_appointments a JOIN crm_prospects p ON p.id=a.prospect_id WHERE a.id=? AND a.deleted_at IS NULL AND p.deleted_at IS NULL", (int(appointment_id),)).fetchone(); return dict(row) if row else None

    def update_appointment(self, appointment_id: int, *, role: str, **changes: Any) -> dict[str, Any]:
        _role(role, write=True); current = self.get_appointment(appointment_id, role=role)
        if current is None: raise KeyError("Không tìm thấy lịch hẹn")
        allowed = {"action_type", "appointment_at", "note", "status"}
        unknown = sorted(set(changes) - allowed)
        if unknown:
            raise ValueError("Trường lịch hẹn không được hỗ trợ: " + ", ".join(unknown))
        action_type = changes.get("action_type", current["action_type"]); status = changes.get("status", current["status"])
        if action_type not in APPOINTMENT_ACTIONS or status not in APPOINTMENT_STATUSES: raise ValueError("Hành động hoặc trạng thái lịch hẹn không hợp lệ")
        self.db.execute("UPDATE crm_care_appointments SET action_type=?,appointment_at=?,note=?,status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (action_type, _datetime(changes.get("appointment_at", current["appointment_at"])), _text(changes.get("note", current["note"]), "Ghi chú", 1000), status, int(appointment_id))); self.db.commit(); return self.get_appointment(appointment_id, role=role)  # type: ignore[return-value]

    def delete_appointment(self, appointment_id: int, *, role: str) -> None:
        _role(role, write=True); cur = self.db.execute("UPDATE crm_care_appointments SET deleted_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP WHERE id=? AND deleted_at IS NULL", (int(appointment_id),))
        if cur.rowcount != 1: raise KeyError("Không tìm thấy lịch hẹn")
        self.db.commit()

    def export_prospects(self, *, role: str, **filters: Any) -> str:
        rows = self.list_prospects(role=role, limit=10000, **filters); output = io.StringIO(); writer = csv.writer(output); writer.writerow(PROSPECT_COLUMNS)
        for index, row in enumerate(rows, 1): writer.writerow([index, row["full_name"], row["sale_owner"] or "Chưa phân công", row["sale_assistant"] or "Chưa phân công", row["tag"], row["care_course"], row["interested_course"], row["status"], row["test_appointment"] or "Chưa hẹn test", row["test_score"] if row["test_score"] is not None else "Chưa chấm điểm", row["trial_status"] or "Chưa đăng ký học thử", row["note"], row["care_progress"]])
        return output.getvalue()

    def export_appointments(self, *, role: str, **filters: Any) -> str:
        rows = self.list_appointments(role=role, limit=10000, **filters); output = io.StringIO(); writer = csv.writer(output); writer.writerow(APPOINTMENT_COLUMNS)
        for index, row in enumerate(rows, 1): writer.writerow([index, row["full_name"], row["sale_owner"] or "Chưa phân công", row["appointment_at"], row["action_type"], row["note"], row["status"]])
        return output.getvalue()

    def summary(self, *, role: str) -> dict[str, Any]:
        """Return dashboard-safe CRM counts from the same persisted tables."""
        _role(role)
        status_rows = self.db.execute(
            "SELECT status, COUNT(*) AS total FROM crm_prospects "
            "WHERE deleted_at IS NULL GROUP BY status"
        ).fetchall()
        appointment_rows = self.db.execute(
            "SELECT a.status, COUNT(*) AS total FROM crm_care_appointments a "
            "JOIN crm_prospects p ON p.id=a.prospect_id "
            "WHERE a.deleted_at IS NULL AND p.deleted_at IS NULL GROUP BY a.status"
        ).fetchall()
        statuses = {row["status"]: row["total"] for row in status_rows}
        appointments = {row["status"]: row["total"] for row in appointment_rows}
        return {
            "prospect_count": sum(statuses.values()),
            "prospect_statuses": statuses,
            "appointment_count": sum(appointments.values()),
            "appointment_statuses": appointments,
        }


CRM = CRMStore


def route_contract() -> dict[str, Any]:
    return {"prospect_routes": list(PROSPECT_ROUTES), "appointment_routes": list(APPOINTMENT_ROUTES), "prospect_columns": list(PROSPECT_COLUMNS), "appointment_columns": list(APPOINTMENT_COLUMNS), "prospect_statuses": list(PROSPECT_STATUSES), "appointment_actions": list(APPOINTMENT_ACTIONS), "appointment_statuses": list(APPOINTMENT_STATUSES), "read_roles": sorted(READ_ROLES), "write_roles": sorted(WRITE_ROLES), "persistence": "sqlite"}


def register(app_or_router: Any = None, service: Any = None) -> dict[str, Any]:
    """Mount the persistent CRM store through the coordinator module seam.

    The host owns HTTP dispatch and authentication.  This hook only attaches
    one ``CRMStore`` to the host's existing SQLite connection and returns
    bounded route/schema metadata.  Repeated autoload calls reuse the store
    when the connection is unchanged, so registration is idempotent.
    """
    target = service if service is not None else app_or_router
    connection = getattr(target, "db", None)
    if connection is None:
        raise RuntimeError("CRM module requires the host SQLite connection")

    store = getattr(target, "crm_store", None)
    if not isinstance(store, CRMStore) or getattr(store, "db", None) is not connection:
        store = CRMStore(connection)
        setattr(target, "crm_store", store)

    metadata = {
        "routes": list(PROSPECT_ROUTES + APPOINTMENT_ROUTES),
        "source": "modules.crm_domain",
        "status": "PERSISTENT_LOCAL_CONTRACT",
        "schema": "crm_prospects,crm_care_appointments",
    }
    registrar = getattr(target, "register_module", None)
    if callable(registrar):
        return registrar("crm_domain", metadata=metadata)
    return {"name": "crm_domain", "registered": True, **metadata}


__all__ = ["CRM", "CRMStore", "SCHEMA", "PROSPECT_ROUTES", "APPOINTMENT_ROUTES", "PROSPECT_COLUMNS", "APPOINTMENT_COLUMNS", "PROSPECT_STATUSES", "APPOINTMENT_ACTIONS", "APPOINTMENT_STATUSES", "route_contract", "register"]
