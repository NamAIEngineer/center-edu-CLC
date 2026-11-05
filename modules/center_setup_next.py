"""Center/Setup local contract for the teacher directory.

The host application can register this module without importing Flask or the
application database.  It keeps the route contract, validation and query
semantics in one place so the eventual registry adapter remains thin.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
import csv
import io
import sqlite3
from datetime import datetime
from typing import Any, Iterable, Mapping

ROUTE = "/center/teacher"
ENTITY = "center_teachers"
TABLE_SCHEMA = (
    "id INTEGER PRIMARY KEY",
    "full_name TEXT NOT NULL",
    "username TEXT NOT NULL UNIQUE",
    "phone TEXT NOT NULL DEFAULT ''",
    "email TEXT NOT NULL DEFAULT ''",
    "nationality TEXT NOT NULL DEFAULT 'Vietnamese'",
    "role TEXT NOT NULL DEFAULT 'Giáo viên'",
    "status TEXT NOT NULL DEFAULT 'Kích hoạt'",
    "branch TEXT NOT NULL DEFAULT ''",
    "created_at TEXT NOT NULL",
    "updated_at TEXT NOT NULL",
    "deleted_at TEXT",
)

SCHEMA = "CREATE TABLE IF NOT EXISTS center_teachers (" + ", ".join(TABLE_SCHEMA) + ");"

TABLE_COLUMNS = (
    "No.", "Giáo viên", "Tài khoản", "Liên hệ", "Quốc tịch",
    "Phân quyền", "Trạng thái", "Hành động",
)
FILTERS = (
    {"name": "q", "placeholder": "Tìm kiếm", "kind": "text"},
    {"name": "nationality", "placeholder": "Chọn quốc tịch", "kind": "select"},
    {"name": "status", "placeholder": "Chọn trạng thái", "kind": "select",
     "options": ("Kích hoạt", "Đang khóa")},
    {"name": "page_size", "label": "Hiển thị bản ghi", "kind": "page_size",
     "options": (10, 25, 50, 100)},
)
RBAC = {
    "ADMIN": {"read", "create", "update", "delete", "export"},
    "STAFF": {"read", "create", "update", "export"},
    "TEACHER": {"read"},
    "STUDENT": set(),
}


@dataclass
class Teacher:
    full_name: str
    username: str
    phone: str = ""
    email: str = ""
    nationality: str = "Vietnamese"
    role: str = "Giáo viên"
    status: str = "Kích hoạt"
    branch: str = ""
    id: int | None = None
    created_at: str = ""
    updated_at: str = ""

    def as_row(self, number: int) -> dict[str, Any]:
        return {
            "No.": number, "Giáo viên": self.full_name,
            "Tài khoản": self.username,
            "Liên hệ": " / ".join(v for v in (self.phone, self.email) if v),
            "Quốc tịch": self.nationality, "Phân quyền": self.role,
            "Trạng thái": self.status, "id": self.id,
        }


def can(role: str, action: str) -> bool:
    return action in RBAC.get((role or "").upper(), set())


def validate(payload: Mapping[str, Any], *, existing_id: int | None = None) -> dict[str, str]:
    errors: dict[str, str] = {}
    for key, label in (("full_name", "Giáo viên"), ("username", "Tài khoản")):
        if not str(payload.get(key, "")).strip():
            errors[key] = f"{label} là bắt buộc"
    status = str(payload.get("status", "Kích hoạt"))
    if status not in {"Kích hoạt", "Đang khóa"}:
        errors["status"] = "Trạng thái không hợp lệ"
    return errors


def filter_teachers(rows: Iterable[Mapping[str, Any]], filters: Mapping[str, Any]) -> list[dict[str, Any]]:
    q = str(filters.get("q", "")).strip().casefold()
    nationality = str(filters.get("nationality", "")).strip().casefold()
    status = str(filters.get("status", "")).strip().casefold()
    result = []
    for row in rows:
        haystack = " ".join(str(row.get(k, "")) for k in ("full_name", "username", "phone", "email"))
        if q and q not in haystack.casefold():
            continue
        if nationality and str(row.get("nationality", "")).casefold() != nationality:
            continue
        if status and str(row.get("status", "")).casefold() != status:
            continue
        result.append(dict(row))
    return result


def export_csv(rows: Iterable[Mapping[str, Any]]) -> str:
    """Return an Excel-compatible UTF-8 CSV; caller owns the HTTP response."""
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=TABLE_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for number, row in enumerate(rows, 1):
        writer.writerow(Teacher(
            full_name=str(row.get("full_name", row.get("Giáo viên", ""))),
            username=str(row.get("username", row.get("Tài khoản", ""))),
            phone=str(row.get("phone", "")), email=str(row.get("email", "")),
            nationality=str(row.get("nationality", row.get("Quốc tịch", ""))),
            role=str(row.get("role", row.get("Phân quyền", "Giáo viên"))),
            status=str(row.get("status", row.get("Trạng thái", ""))),
        ).as_row(number))
    return "\ufeff" + output.getvalue()


class TeacherStore:
    """SQLite persistence for the teacher directory contract.

    The host may mount this store on its existing connection.  No rows are
    seeded here; callers decide when a real teacher record is created.
    """

    def __init__(self, connection: sqlite3.Connection):
        self.db = connection
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        # Existing local databases may predate the soft-delete column.  Add
        # the nullable column idempotently so restart persistence remains
        # compatible without dropping or rewriting teacher data.
        columns = {row["name"] for row in self.db.execute("PRAGMA table_info(center_teachers)").fetchall()}
        if "deleted_at" not in columns:
            self.db.execute("ALTER TABLE center_teachers ADD COLUMN deleted_at TEXT")
        self.db.commit()

    @staticmethod
    def _payload(payload: Mapping[str, Any], current: Mapping[str, Any] | None = None) -> dict[str, str]:
        merged = dict(current or {})
        merged.update(payload)
        # Accept the observed form's ``fullname`` while storing the canonical
        # database field ``full_name``.
        if "fullname" in merged and "full_name" not in payload:
            merged["full_name"] = merged["fullname"]
        values = {
            "full_name": str(merged.get("full_name", "")).strip(),
            "username": str(merged.get("username", "")).strip(),
            "phone": str(merged.get("phone", "")).strip(),
            "email": str(merged.get("email", "")).strip(),
            "nationality": str(merged.get("nationality", "Vietnamese")).strip() or "Vietnamese",
            "role": str(merged.get("role", "Giáo viên")).strip() or "Giáo viên",
            "status": str(merged.get("status", "Kích hoạt")).strip() or "Kích hoạt",
            "branch": str(merged.get("branch", "")).strip(),
        }
        errors = validate(values)
        if errors:
            raise ValueError("; ".join(errors.values()))
        if values["nationality"] not in {"Vietnamese", "Việt Nam", "Hoa Kỳ", "Anh", "Úc"}:
            raise ValueError("Quốc tịch không hợp lệ")
        return values

    def create(self, payload: Mapping[str, Any], *, role: str = "ADMIN") -> dict[str, Any]:
        if not can(role, "create"):
            raise PermissionError(f"role {role or 'unknown'} cannot create teachers")
        values = self._payload(payload)
        now = datetime.utcnow().replace(microsecond=0).isoformat(sep=" ")
        try:
            cur = self.db.execute(
                "INSERT INTO center_teachers(full_name,username,phone,email,nationality,role,status,branch,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (*[values[key] for key in ("full_name", "username", "phone", "email", "nationality", "role", "status", "branch")], now, now),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("Tài khoản giáo viên đã tồn tại") from exc
        self.db.commit()
        return self.get(int(cur.lastrowid), role=role)  # type: ignore[return-value]

    def get(self, teacher_id: int, *, role: str = "ADMIN") -> dict[str, Any] | None:
        if not can(role, "read"):
            raise PermissionError(f"role {role or 'unknown'} cannot read teachers")
        row = self.db.execute("SELECT * FROM center_teachers WHERE id=? AND deleted_at IS NULL", (int(teacher_id),)).fetchone()
        return dict(row) if row else None

    def list(self, filters: Mapping[str, Any] | None = None, *, role: str = "ADMIN") -> list[dict[str, Any]]:
        if not can(role, "read"):
            raise PermissionError(f"role {role or 'unknown'} cannot read teachers")
        filters = filters or {}
        rows = self.db.execute("SELECT * FROM center_teachers WHERE deleted_at IS NULL ORDER BY id DESC").fetchall()
        result = filter_teachers([dict(row) for row in rows], filters)
        page_size = filters.get("page_size")
        if page_size not in (None, ""):
            try:
                result = result[: max(1, min(int(page_size), 100))]
            except (TypeError, ValueError) as exc:
                raise ValueError("Số bản ghi phải là số nguyên") from exc
        return result

    def update(self, teacher_id: int, payload: Mapping[str, Any], *, role: str = "ADMIN") -> dict[str, Any]:
        if not can(role, "update"):
            raise PermissionError(f"role {role or 'unknown'} cannot update teachers")
        current = self.get(teacher_id, role=role)
        if current is None:
            raise KeyError("Không tìm thấy giáo viên")
        values = self._payload(payload, current)
        now = datetime.utcnow().replace(microsecond=0).isoformat(sep=" ")
        try:
            self.db.execute("UPDATE center_teachers SET full_name=?,username=?,phone=?,email=?,nationality=?,role=?,status=?,branch=?,updated_at=? WHERE id=? AND deleted_at IS NULL", (*[values[key] for key in ("full_name", "username", "phone", "email", "nationality", "role", "status", "branch")], now, int(teacher_id)))
        except sqlite3.IntegrityError as exc:
            raise ValueError("Tài khoản giáo viên đã tồn tại") from exc
        self.db.commit()
        return self.get(teacher_id, role=role)  # type: ignore[return-value]

    def delete(self, teacher_id: int, *, role: str = "ADMIN") -> None:
        if not can(role, "delete"):
            raise PermissionError(f"role {role or 'unknown'} cannot delete teachers")
        cur = self.db.execute("UPDATE center_teachers SET deleted_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP WHERE id=? AND deleted_at IS NULL", (int(teacher_id),))
        if cur.rowcount != 1:
            raise KeyError("Không tìm thấy giáo viên")
        self.db.commit()

    def export(self, filters: Mapping[str, Any] | None = None, *, role: str = "ADMIN") -> str:
        if not can(role, "export"):
            raise PermissionError(f"role {role or 'unknown'} cannot export teachers")
        return export_csv(self.list(filters, role=role))


CONTRACT = {
    "route": ROUTE, "entity": ENTITY, "table_schema": TABLE_SCHEMA,
    "columns": TABLE_COLUMNS, "filters": FILTERS,
    "actions": ("create", "update", "delete", "export"),
    "rbac": RBAC, "maturity": "PERSISTENT_LOCAL_CONTRACT",
    "notes": "TeacherStore persists records on the caller SQLite connection.",
}


def register(app_or_router: Any = None, service: Any = None) -> dict[str, Any]:
    target = service or app_or_router
    connection = getattr(target, "db", None)
    if connection is None:
        raise RuntimeError("Center teacher module requires the host SQLite connection")
    store = getattr(target, "center_teacher_store", None)
    if not isinstance(store, TeacherStore) or store.db is not connection:
        store = TeacherStore(connection)
        setattr(target, "center_teacher_store", store)
    return {"route": ROUTE, "entity": ENTITY, "status": "PERSISTENT_LOCAL_CONTRACT", "schema": "center_teachers"}


__all__ = ["ROUTE", "ENTITY", "CONTRACT", "TABLE_SCHEMA", "SCHEMA", "Teacher", "TeacherStore", "can", "validate", "filter_teachers", "export_csv", "register"]
