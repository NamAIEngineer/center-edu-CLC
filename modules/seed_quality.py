"""Customer-facing sanitization for rich-demo presentation payloads.

The rich demo keeps deterministic fixture identifiers in storage so joins and
tests remain stable.  This module is deliberately a presentation boundary:
it removes fixture wording from values sent to a customer-facing view while
leaving database IDs and status enums untouched.  It does not mutate the
database and it never turns an unknown value into an invented value.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

_SYNTHETIC_NAME = re.compile(r"^Demo\s+(Learner|Customer|Prospect|Teacher|Student)\s*(\d*)$", re.I)
_VI_SYNTHETIC_NAME = re.compile(r"^(Giáo viên|Học viên)\s+Demo\s*(\d*)$", re.I)
_MARKER = re.compile(r"^(DEMO|HV-DEMO|ID-DEMO|LEAD-DEMO|CN-DEMO)-(.+)$", re.I)
# Some rich-demo modules use a domain prefix before ``-DEMO-`` (for example
# ``BL-DEMO-001`` or ``HD-DEMO-001``).  Keep the domain prefix and suffix,
# while removing only the fixture marker.
_DOMAIN_MARKER = re.compile(r"^(?P<head>[A-Z][A-Z0-9_]*)-DEMO-(?P<rest>.+)$", re.I)
_DOMAIN_PREFIXES = frozenset({"BL", "HD", "DG", "IT", "CTR"})

_NAMES = {
    "Learner": ("Nguyễn Minh Anh", "Trần Gia Hân", "Lê Hoàng Nam", "Phạm Khánh Linh"),
    "Customer": ("Nguyễn Văn Minh", "Trần Thị Lan", "Lê Quốc Bảo", "Phạm Thu Hà"),
    "Prospect": ("Trần Minh Đức", "Nguyễn Thùy Dương", "Phạm Gia Bảo", "Lê Ngọc Mai"),
    "Teacher": ("Nguyễn Văn Cường", "Ms Nga", "Trần Minh Quân", "Lê Thu Hà"),
    "Student": ("Nguyễn Minh Anh", "Trần Gia Hân", "Lê Hoàng Nam", "Phạm Khánh Linh"),
}

# These are transport values, not presentation copy.  Keep them byte-for-byte
# so callers can still branch on the stable state machine.
_ID_KEYS = frozenset({
    "id", "ids", "uuid", "record_id", "user_id", "student_id", "class_id", "account_id",
    "identifier", "identifiers", "stable_id", "stable_ids", "external_id", "external_ids",
    "recordid", "userid", "studentid", "classid", "accountid", "stableid", "externalid",
})
_ENUM_KEYS = frozenset({"status", "transport"})


def _is_id_key(key: str | None) -> bool:
    if not key:
        return False
    normalized = key.casefold()
    if normalized in _ID_KEYS or normalized.endswith("_id") or normalized.endswith("_ids"):
        return True
    # Keep common camel-case JSON keys opaque without treating ordinary words
    # such as ``valid`` as stable identifiers.
    return key.endswith(("Id", "ID", "Ids", "IDs"))


def _fixture_name(text: str) -> str | None:
    text = text.strip()
    match = _SYNTHETIC_NAME.match(text)
    if match:
        group, suffix = match.groups()
    else:
        match = _VI_SYNTHETIC_NAME.match(text)
        if not match:
            return None
        role, suffix = match.groups()
        group = "Teacher" if role.casefold() == "giáo viên" else "Student"
    names = _NAMES[group.title()]
    index = int(suffix or "1") - 1
    return names[index % len(names)]


def _fixture_code(text: str) -> str | None:
    match = _MARKER.match(text.strip())
    if match:
        prefix, rest = match.groups()
        prefix = prefix.upper()
        replacement = {
            "DEMO": "DL",
            "HV-DEMO": "HV",
            "ID-DEMO": "ID",
            "LEAD-DEMO": "KH",
            "CN-DEMO": "CN",
        }.get(prefix)
        if replacement:
            return f"{replacement}-{rest}"

    match = _DOMAIN_MARKER.match(text.strip())
    if match and match.group("head").upper() in _DOMAIN_PREFIXES:
        return f"{match.group('head').upper()}-{match.group('rest')}"
    return None


def sanitize_value(value: Any, *, field_name: str | None = None) -> Any:
    """Sanitize one customer-facing value without fabricating missing data.

    ``None`` and ``UNKNOWN`` remain unchanged.  Stable storage IDs remain
    unchanged when their key identifies them as an ID.  Status/enum strings
    are never translated here.
    """
    if value is None or not isinstance(value, str):
        return value
    normalized_field = field_name.casefold() if field_name else ""
    is_status_enum = normalized_field in _ENUM_KEYS or normalized_field.endswith("_status")
    is_transport_enum = normalized_field == "transport" or normalized_field.endswith("_transport")
    if value.casefold() == "unknown" or _is_id_key(field_name) or is_status_enum or is_transport_enum:
        return value
    text = value.strip()
    if text.casefold().startswith("dữ liệu demo"):
        return ""
    if text in {"Demo Sales", "Academic Team", "Center Administrator"}:
        return {"Demo Sales": "Phòng tư vấn", "Academic Team": "Phòng học vụ", "Center Administrator": "Quản trị trung tâm"}[text]
    name = _fixture_name(text)
    if name:
        return name
    code = _fixture_code(text)
    if code:
        return code
    return value


def sanitize_payload(payload: Any, *, field_name: str | None = None) -> Any:
    """Recursively sanitize dict/list payloads at the presentation boundary."""
    if isinstance(payload, Mapping):
        return {str(key): sanitize_payload(value, field_name=str(key)) for key, value in payload.items()}
    if isinstance(payload, list):
        return [sanitize_payload(item, field_name=field_name) for item in payload]
    if isinstance(payload, tuple):
        return tuple(sanitize_payload(item, field_name=field_name) for item in payload)
    return sanitize_value(payload, field_name=field_name)


__all__ = ["sanitize_payload", "sanitize_value"]
