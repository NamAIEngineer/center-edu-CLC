"""Configuration-driven screen contracts for the Center EDU rebuild.

The reference inventory is a read-only observation.  It provides presentation
shape (routes, labels, columns, filters, actions and tabs), not a private API
contract.  The generated local specs therefore keep provenance explicit and
never copy reference sample rows into the product.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any


PRODUCT_ROOT = Path(__file__).resolve().parent
REFERENCE_INVENTORY = Path("/Users/nam/claude-center-audit/ref/reference-inventory.json")
REFERENCE_FORMS = Path("/Users/nam/claude-center-audit/ref/forms/forms-inventory.json")
SPEC_PATH = PRODUCT_ROOT / "screen_specs" / "reference-screen-specs.json"


def _slug(value: str) -> str:
    """Stable ASCII slug for routes/entities and human labels.

    Reference labels contain Vietnamese diacritics.  Transliteration keeps
    keys readable and deterministic instead of collapsing them to fragments
    such as ``t-n-l-p``.
    """
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value.strip().lower()).strip("-")
    return value or "screen"


def _stable_key(*values: Any, fallback: str = "field") -> str:
    """Return a JSON/HTML-safe field key from observed name/label data."""
    for value in values:
        candidate = str(value or "").strip()
        # Browser captures often expose a generic placeholder name.  It is
        # metadata, not an identity for the observed control.
        if candidate and candidate.lower() not in {"field", "input", "select", "textarea"}:
            slug = _slug(candidate).replace("-", "_")
            if slug and slug != "screen":
                return slug
    return fallback


def _unique_key(base: str, used: set[str]) -> str:
    key = base or "field"
    if key not in used:
        used.add(key)
        return key
    index = 2
    while f"{key}_{index}" in used:
        index += 1
    key = f"{key}_{index}"
    used.add(key)
    return key


def _route(href: str) -> str:
    if not href:
        return "/"
    value = re.sub(r"^https?://[^/]+", "", href)
    value = value.split("?", 1)[0].split("#", 1)[0]
    return value or "/"


def _control_to_filter(control: dict[str, Any], key: str) -> dict[str, Any] | None:
    tag = str(control.get("tag", "")).lower()
    if tag not in {"input", "select", "textarea"}:
        return None
    kind = str(control.get("type", "text"))
    if kind in {"button", "submit", "file", "hidden"}:
        return None
    options = control.get("options") if isinstance(control.get("options"), list) else []
    return {
        "label": str(control.get("label") or control.get("placeholder") or ""),
        "placeholder": str(control.get("placeholder") or ""),
        "type": "select" if tag == "select" else kind,
        "name": key,
        "observed_name": str(control.get("name") or ""),
        "observed_label": str(control.get("label") or ""),
        "observed_placeholder": str(control.get("placeholder") or ""),
        "options": [str(item) for item in options if item is not None],
        "source_status": "OBSERVED",
    }


def _form_fields(forms: dict[str, dict[str, Any]], slug: str) -> list[dict[str, Any]]:
    form = forms.get(slug) or {}
    fields = form.get("fields") if isinstance(form.get("fields"), list) else []
    output: list[dict[str, Any]] = []
    used: set[str] = set()
    for index, field in enumerate(fields, start=1):
        if not isinstance(field, dict):
            continue
        observed_name = str(field.get("name") or "")
        observed_label = str(field.get("label") or "")
        observed_placeholder = str(field.get("placeholder") or "")
        name = _unique_key(
            _stable_key(observed_name, observed_label, observed_placeholder,
                        fallback=f"field_{index}"), used)
        options = field.get("options") if isinstance(field.get("options"), list) else []
        output.append({
            "name": name,
            "label": observed_label or observed_placeholder or name,
            "type": str(field.get("type") or "text"),
            "required": bool(field.get("required", False)),
            "placeholder": str(field.get("placeholder") or ""),
            "options": [str(item) for item in options if item is not None],
            "source_status": "OBSERVED",
            "observed_name": observed_name,
            "observed_label": observed_label,
            "observed_placeholder": observed_placeholder,
            "source_index": index,
        })
    return output


def build_specs(inventory: dict[str, Any], forms_inventory: dict[str, Any]) -> list[dict[str, Any]]:
    form_map = {
        str(item.get("slug")): item
        for item in (forms_inventory.get("forms") or [])
        if isinstance(item, dict) and item.get("slug")
    }
    specs: list[dict[str, Any]] = []
    inventory_captured_at = inventory.get("captured_at")
    forms_captured_at = forms_inventory.get("captured_at")
    for item in inventory.get("screens") or []:
        if not isinstance(item, dict):
            continue
        route = _route(str(item.get("href") or "/"))
        slug = str(item.get("slug") or _slug(route))
        tables = item.get("tables") if isinstance(item.get("tables"), list) else []
        headers: list[str] = []
        if tables and isinstance(tables[0], dict):
            headers = [str(value) for value in (tables[0].get("headers") or []) if value is not None]
        filters: list[dict[str, Any]] = []
        filter_keys: set[str] = set()
        for index, control in enumerate(item.get("controls") or [], start=1):
            if not isinstance(control, dict):
                continue
            candidate = _stable_key(control.get("name"), control.get("label"),
                                    control.get("placeholder"), fallback=f"filter_{index}")
            key = _unique_key(candidate, filter_keys)
            value = _control_to_filter(control, key)
            if value:
                value["source_index"] = index
                filters.append(value)
        buttons = [str(value) for value in (item.get("buttons") or []) if value]
        tabs = [str(value) for value in (item.get("tabs") or []) if value]
        form = form_map.get(slug, {})
        column_keys: set[str] = set()
        columns = []
        for index, value in enumerate(headers, start=1):
            key = _unique_key(_stable_key(value, fallback=f"column_{index}"), column_keys)
            columns.append({"label": value, "key": key, "observed_label": value, "source_index": index})
        specs.append({
            "slug": slug,
            "route": route,
            "title": str(item.get("title") or (item.get("menu_labels") or [slug])[-1] or slug),
            "menu_labels": [str(value) for value in (item.get("menu_labels") or []) if value],
            "entity": re.sub(r"[^a-z0-9_]+", "_", slug.lower()).strip("_") or "screen",
            "columns": columns,
            "filters": filters,
            "buttons": buttons,
            "tabs": tabs,
            "form": {
                "observed": bool(form),
                "url": form.get("form_url") if isinstance(form, dict) else None,
                "fields": _form_fields(form_map, slug),
            },
            "contract_status": "OBSERVED",
            "api_status": "INFERRED_LOCAL_CONTRACT",
            "runtime_status": "SOURCE_PRESENT",
            "observation": {
                "inventory_captured_at": inventory_captured_at,
                "forms_captured_at": forms_captured_at,
                "href": str(item.get("href") or ""),
                "final_url": str(item.get("final_url") or ""),
                "http_status": item.get("status"),
                "screenshot": str(item.get("screenshot") or ""),
                "form_screenshot": str(form.get("screenshot") or "") if isinstance(form, dict) else "",
                "observed": True,
            },
            "unknowns": ["reference private API, role matrix and mutation semantics"],
            "source_refs": [
                "/Users/nam/claude-center-audit/ref/reference-inventory.json",
                "/Users/nam/claude-center-audit/ref/forms/forms-inventory.json",
            ],
        })
    return specs


def load_specs(path: Path = SPEC_PATH) -> dict[str, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(item["route"]): item for item in data.get("screens", []) if isinstance(item, dict) and item.get("route")}


def generate() -> Path:
    inventory = json.loads(REFERENCE_INVENTORY.read_text(encoding="utf-8"))
    forms = json.loads(REFERENCE_FORMS.read_text(encoding="utf-8"))
    specs = build_specs(inventory, forms)
    SPEC_PATH.parent.mkdir(parents=True, exist_ok=True)
    SPEC_PATH.write_text(json.dumps({
        "schema_version": 1,
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "source_status": "READ_ONLY_REFERENCE_OBSERVATION",
        "total": len(specs),
        "screens": specs,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return SPEC_PATH


if __name__ == "__main__":
    print(generate())
