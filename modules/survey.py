"""Persistent contract for the observed ``/survey`` surface.

The HTTP service already owns the application session and CSRF boundary.  This
module keeps the survey domain rules reusable and testable without importing
the server: schema creation, Vietnamese form normalization, CRUD, response
validation, RBAC and CSV export all operate on the caller's SQLite connection.

The reference application's private API is unavailable.  The contract below
therefore describes the observed table/form labels and the local persistence
semantics; it does not claim compatibility with a private reference endpoint.
"""

from __future__ import annotations

import csv
import io
import json
import sqlite3
from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable, Mapping, Sequence

ROUTE = "/survey"
CREATE_ROUTE = "/survey/create_survey"
ENTITY = "surveys"

STATUS_LABELS = {
    "DRAFT": "Bản nháp",
    "PUBLISHED": "Đã phát hành",
    "CLOSED": "Đã đóng",
}
STATUS_BY_LABEL = {label.casefold(): value for value, label in STATUS_LABELS.items()}
QUESTION_KINDS = {"INPUT", "CHECKBOX", "DROPDOWN", "COMMENT", "RATING", "IMAGE"}

RBAC = {
    "ADMIN": frozenset({"read", "create", "update", "archive", "export", "respond"}),
    "STAFF": frozenset({"read", "create", "update", "archive", "export", "respond"}),
    "TEACHER": frozenset(),
    "STUDENT": frozenset(),
}

COLUMNS = (
    "No.",
    "Tên khảo sát",
    "Hạn làm",
    "Đã làm / Đã gửi / Người nhận",
    "Người tạo",
    "Thống kê / Kết quả",
    "Hành động",
)

FILTERS = (
    {"name": "q", "label": "Tìm kiếm...", "kind": "text"},
    {"name": "status", "label": "Trạng thái", "kind": "select", "options": tuple(STATUS_LABELS.values())},
    {"name": "page_size", "label": "Hiển thị 5 10 25 50 bản ghi", "kind": "page_size", "options": (5, 10, 25, 50)},
)

FORM_FIELDS = (
    {"name": "name", "label": "Tên khảo sát", "type": "text", "required": True},
    {"name": "due_date", "label": "Hạn làm", "type": "date", "placeholder": "dd/mm/yyyy"},
    {"name": "status", "label": "Trạng thái", "type": "select", "options": tuple(STATUS_LABELS.values())},
    {"name": "description", "label": "Mô tả", "type": "textarea"},
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS surveys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    due_date TEXT,
    completed_count INTEGER NOT NULL DEFAULT 0,
    sent_count INTEGER NOT NULL DEFAULT 0,
    recipient_count INTEGER NOT NULL DEFAULT 0,
    created_by INTEGER,
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
"""


@dataclass(frozen=True)
class Survey:
    id: int
    name: str
    due_date: str | None
    status: str
    description: str
    completed_count: int
    sent_count: int
    recipient_count: int
    created_by_name: str = ""
    response_count: int = 0

    @property
    def status_label(self) -> str:
        return STATUS_LABELS.get(self.status, self.status)

    def as_row(self, number: int) -> dict[str, Any]:
        return {
            "No.": number,
            "Tên khảo sát": self.name,
            "Hạn làm": display_date(self.due_date),
            "Đã làm / Đã gửi / Người nhận": f"{self.completed_count} / {self.sent_count} / {self.recipient_count}",
            "Người tạo": self.created_by_name,
            "Thống kê / Kết quả": self.response_count,
            "Trạng thái": self.status_label,
            "id": self.id,
        }


class SurveyError(ValueError):
    """Raised for a local survey contract violation."""


def can(role: str, action: str) -> bool:
    return action in RBAC.get(str(role or "").upper(), frozenset())


def require(role: str, action: str) -> None:
    if not can(role, action):
        raise PermissionError(f"role {role or 'unknown'} cannot {action} surveys")


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Create only survey tables; never seed or overwrite user data."""
    conn.executescript(SCHEMA)
    conn.commit()


def normalize_status(value: Any = "DRAFT") -> str:
    text = str(value or "DRAFT").strip()
    upper = text.upper()
    if upper in STATUS_LABELS:
        return upper
    mapped = STATUS_BY_LABEL.get(text.casefold())
    if mapped:
        return mapped
    raise SurveyError("Trạng thái khảo sát không hợp lệ")


def normalize_date(value: Any) -> str | None:
    """Normalize observed ``dd/mm/yyyy`` input to the ISO storage value."""
    if value in (None, ""):
        return None
    text = str(value).strip()
    try:
        if len(text) == 10 and text[2] == "/" and text[5] == "/":
            parsed = date(int(text[6:]), int(text[3:5]), int(text[:2]))
        else:
            parsed = date.fromisoformat(text)
    except (TypeError, ValueError) as exc:
        raise SurveyError("Hạn làm phải theo định dạng dd/mm/yyyy") from exc
    return parsed.isoformat()


def display_date(value: Any) -> str:
    if not value:
        return ""
    text = str(value)
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        return text
    return parsed.strftime("%d/%m/%Y")


def _text(value: Any, field: str, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) > limit:
        raise SurveyError(f"{field} vượt quá {limit} ký tự")
    return text


def validate_payload(payload: Mapping[str, Any], *, current: Mapping[str, Any] | None = None) -> dict[str, Any]:
    current = current or {}
    name = _text(payload.get("name", current.get("name", "")), "Tên khảo sát", 240)
    if not name:
        raise SurveyError("Tên khảo sát là bắt buộc")
    status = normalize_status(payload.get("status", current.get("status", "DRAFT")))
    due_date = normalize_date(payload.get("due_date", current.get("due_date")))
    description = _text(payload.get("description", current.get("description", "")), "Mô tả", 2000)
    return {"name": name, "status": status, "due_date": due_date, "description": description}


def _dict(row: sqlite3.Row | Mapping[str, Any]) -> dict[str, Any]:
    return dict(row)


def _survey_row(conn: sqlite3.Connection, survey_id: int) -> dict[str, Any]:
    row = conn.execute(
        """SELECT s.*, COALESCE(u.full_name,'') AS created_by_name,
                  (SELECT COUNT(*) FROM survey_responses r WHERE r.survey_id=s.id) AS response_count
             FROM surveys s LEFT JOIN users u ON u.id=s.created_by WHERE s.id=?""",
        (survey_id,),
    ).fetchone()
    if row is None:
        raise SurveyError("Không tìm thấy khảo sát")
    return _dict(row)


def list_surveys(conn: sqlite3.Connection, filters: Mapping[str, Any] | None = None, *, role: str = "ADMIN") -> list[dict[str, Any]]:
    require(role, "read")
    filters = filters or {}
    sql = """SELECT s.*, COALESCE(u.full_name,'') AS created_by_name,
                    (SELECT COUNT(*) FROM survey_responses r WHERE r.survey_id=s.id) AS response_count
             FROM surveys s LEFT JOIN users u ON u.id=s.created_by"""
    clauses: list[str] = []
    params: list[Any] = []
    query = _text(filters.get("q", ""), "Tìm kiếm", 160)
    if query:
        clauses.append("(s.name LIKE ? OR s.description LIKE ?)")
        params.extend([f"%{query}%", f"%{query}%"])
    if filters.get("status"):
        clauses.append("s.status=?")
        params.append(normalize_status(filters["status"]))
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY s.id DESC"
    return [_dict(row) for row in conn.execute(sql, params).fetchall()]


def create_survey(conn: sqlite3.Connection, payload: Mapping[str, Any], *, created_by: int, role: str = "ADMIN") -> dict[str, Any]:
    require(role, "create")
    values = validate_payload(payload)
    cur = conn.execute(
        "INSERT INTO surveys(name,due_date,created_by,status,description) VALUES(?,?,?,?,?)",
        (values["name"], values["due_date"], created_by, values["status"], values["description"]),
    )
    conn.commit()
    return _survey_row(conn, int(cur.lastrowid))


def update_survey(conn: sqlite3.Connection, survey_id: int, payload: Mapping[str, Any], *, role: str = "ADMIN") -> dict[str, Any]:
    require(role, "update")
    current = _survey_row(conn, int(survey_id))
    values = validate_payload(payload, current=current)
    conn.execute(
        "UPDATE surveys SET name=?,due_date=?,status=?,description=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (values["name"], values["due_date"], values["status"], values["description"], int(survey_id)),
    )
    conn.commit()
    return _survey_row(conn, int(survey_id))


def archive_survey(conn: sqlite3.Connection, survey_id: int, *, role: str = "ADMIN") -> dict[str, Any]:
    """Archive a survey through the observed closed state."""
    require(role, "archive")
    return update_survey(conn, int(survey_id), {"status": "CLOSED"}, role=role)


def survey_detail(conn: sqlite3.Connection, survey_id: int, *, role: str = "ADMIN") -> dict[str, Any]:
    require(role, "read")
    result = _survey_row(conn, int(survey_id))
    pages: list[dict[str, Any]] = []
    for page in conn.execute("SELECT * FROM survey_pages WHERE survey_id=? ORDER BY position,id", (int(survey_id),)).fetchall():
        item = _dict(page)
        questions: list[dict[str, Any]] = []
        for question in conn.execute("SELECT * FROM survey_questions WHERE page_id=? ORDER BY position,id", (page["id"],)).fetchall():
            q = _dict(question)
            try:
                q["options"] = json.loads(q.pop("options_json") or "[]")
            except (TypeError, ValueError):
                q["options"] = []
            q["required"] = bool(q["required"])
            questions.append(q)
        item["questions"] = questions
        pages.append(item)
    result["pages"] = pages
    result["status_label"] = STATUS_LABELS.get(result["status"], result["status"])
    return result


def create_page(conn: sqlite3.Connection, survey_id: int, payload: Mapping[str, Any], *, role: str = "ADMIN") -> dict[str, Any]:
    require(role, "update")
    _survey_row(conn, int(survey_id))
    title = _text(payload.get("title", ""), "Tiêu đề trang", 240)
    if not title:
        raise SurveyError("Tiêu đề trang là bắt buộc")
    try:
        position = int(payload.get("position", 0))
    except (TypeError, ValueError) as exc:
        raise SurveyError("Vị trí trang phải là số nguyên") from exc
    if position < 0:
        raise SurveyError("Vị trí trang không hợp lệ")
    conn.execute(
        "INSERT INTO survey_pages(survey_id,title,description,position) VALUES(?,?,?,?)",
        (int(survey_id), title, _text(payload.get("description", ""), "Mô tả", 2000), position),
    )
    conn.commit()
    return survey_detail(conn, int(survey_id), role=role)


def create_question(conn: sqlite3.Connection, page_id: int, payload: Mapping[str, Any], *, role: str = "ADMIN") -> dict[str, Any]:
    require(role, "update")
    page = conn.execute("SELECT survey_id FROM survey_pages WHERE id=?", (int(page_id),)).fetchone()
    if page is None:
        raise SurveyError("Không tìm thấy trang khảo sát")
    kind = _text(payload.get("kind", "INPUT"), "Loại câu hỏi", 16).upper()
    if kind not in QUESTION_KINDS:
        raise SurveyError("Loại câu hỏi không hợp lệ")
    label = _text(payload.get("label", ""), "Nội dung câu hỏi", 500)
    if not label:
        raise SurveyError("Nội dung câu hỏi là bắt buộc")
    options = payload.get("options", [])
    if isinstance(options, str):
        options = [line.strip() for line in options.splitlines() if line.strip()]
    if not isinstance(options, Sequence) or isinstance(options, (bytes, bytearray)) or any(not isinstance(x, str) for x in options):
        raise SurveyError("Các lựa chọn phải là danh sách văn bản")
    options = [_text(x, "Lựa chọn", 240) for x in options]
    try:
        position = int(payload.get("position", 0))
    except (TypeError, ValueError) as exc:
        raise SurveyError("Vị trí câu hỏi phải là số nguyên") from exc
    if position < 0:
        raise SurveyError("Vị trí câu hỏi không hợp lệ")
    required = 1 if payload.get("required") in (True, 1, "1", "true", "TRUE", "Có") else 0
    conn.execute(
        "INSERT INTO survey_questions(page_id,kind,label,options_json,position,required) VALUES(?,?,?,?,?,?)",
        (int(page_id), kind, label, json.dumps(options, ensure_ascii=False), position, required),
    )
    conn.commit()
    return survey_detail(conn, int(page["survey_id"]), role=role)


def submit_response(conn: sqlite3.Connection, survey_id: int, payload: Mapping[str, Any], *, role: str = "ADMIN") -> dict[str, Any]:
    require(role, "respond")
    survey = _survey_row(conn, int(survey_id))
    if survey["status"] == "CLOSED":
        raise SurveyError("Khảo sát đã đóng")
    respondent_name = _text(payload.get("respondent_name", ""), "Người trả lời", 160) or "Người dùng nội bộ"
    respondent_role = _text(payload.get("respondent_role", ""), "Vai trò", 40) or "Nhân viên"
    answers = payload.get("answers", {})
    if not isinstance(answers, Mapping):
        raise SurveyError("Câu trả lời phải là một đối tượng")
    detail = survey_detail(conn, int(survey_id), role=role)
    questions = {str(q["id"]): q for page in detail["pages"] for q in page["questions"]}
    normalized = {str(k): v for k, v in answers.items()}
    unknown = sorted(set(normalized) - set(questions))
    if unknown:
        raise SurveyError("Câu trả lời chứa câu hỏi không tồn tại")
    for question_id, question in questions.items():
        value = normalized.get(question_id)
        blank = value is None or (isinstance(value, str) and not value.strip()) or (isinstance(value, list) and not value)
        if question["required"] and blank:
            raise SurveyError(f"Câu trả lời {question_id} là bắt buộc")
        if blank:
            continue
        if question["kind"] == "RATING":
            try:
                rating = float(value)
            except (TypeError, ValueError) as exc:
                raise SurveyError("Điểm đánh giá phải từ 1 đến 5") from exc
            if rating < 1 or rating > 5:
                raise SurveyError("Điểm đánh giá phải từ 1 đến 5")
        if question["kind"] == "DROPDOWN" and question["options"] and value not in question["options"]:
            raise SurveyError("Lựa chọn trả lời không hợp lệ")
    conn.execute(
        "INSERT INTO survey_responses(survey_id,respondent_name,respondent_role,answers_json) VALUES(?,?,?,?)",
        (int(survey_id), respondent_name, respondent_role, json.dumps(normalized, ensure_ascii=False, sort_keys=True)),
    )
    conn.execute("UPDATE surveys SET completed_count=completed_count+1,updated_at=CURRENT_TIMESTAMP WHERE id=?", (int(survey_id),))
    conn.commit()
    return survey_detail(conn, int(survey_id), role=role)


def export_csv(rows: Iterable[Mapping[str, Any]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for number, row in enumerate(rows, 1):
        survey = Survey(
            id=int(row.get("id", 0)), name=str(row.get("name", "")),
            due_date=row.get("due_date"), status=str(row.get("status", "DRAFT")),
            description=str(row.get("description", "")),
            completed_count=int(row.get("completed_count", 0) or 0),
            sent_count=int(row.get("sent_count", 0) or 0),
            recipient_count=int(row.get("recipient_count", 0) or 0),
            created_by_name=str(row.get("created_by_name", "")),
            response_count=int(row.get("response_count", 0) or 0),
        )
        writer.writerow(survey.as_row(number))
    return "\ufeff" + output.getvalue()


CONTRACT = {
    "route": ROUTE,
    "create_route": CREATE_ROUTE,
    "entity": ENTITY,
    "columns": COLUMNS,
    "filters": FILTERS,
    "form": FORM_FIELDS,
    "actions": ("read", "create", "update", "archive", "respond", "export"),
    "rbac": {role: tuple(actions) for role, actions in RBAC.items()},
    "maturity": "PERSISTENT_LOCAL_CONTRACT",
    "reference_status": "OBSERVED_DOM_PRIVATE_API_UNKNOWN",
}


def register(app_or_router: Any = None, service: Any = None) -> dict[str, Any]:
    """Register survey schema and route metadata with the host autoloader."""
    target = service or app_or_router
    conn = getattr(target, "db", None)
    if conn is not None:
        ensure_schema(conn)
        import os
        rich = os.environ.get("CENTER_EDU_RICH_DEMO", "").lower() in {"1", "true", "yes", "on"}
        if rich and not conn.execute("SELECT 1 FROM surveys LIMIT 1").fetchone():
            creator = conn.execute("SELECT id FROM users WHERE username='admin' LIMIT 1").fetchone()
            conn.execute("INSERT INTO surveys(name,due_date,created_by,status,description) VALUES(?,?,?,?,?)", ("Khảo sát mức độ hài lòng phụ huynh", "2026-11-30", creator[0] if creator else 1, "DRAFT", "Khảo sát phản hồi sau khóa học."))
            conn.commit()
    return {
        "routes": (ROUTE, CREATE_ROUTE),
        "source": "modules.survey",
        "status": "PERSISTENT_LOCAL_CONTRACT",
        "schema": "surveys,survey_pages,survey_questions,survey_responses",
    }

__all__ = [
    "ROUTE", "CREATE_ROUTE", "ENTITY", "COLUMNS", "FILTERS", "FORM_FIELDS", "RBAC", "CONTRACT",
    "SCHEMA", "Survey", "SurveyError", "can", "require", "ensure_schema", "normalize_date",
    "display_date", "normalize_status", "validate_payload", "list_surveys", "create_survey",
    "update_survey", "archive_survey", "survey_detail", "create_page", "create_question",
    "submit_response", "export_csv", "register",
]
