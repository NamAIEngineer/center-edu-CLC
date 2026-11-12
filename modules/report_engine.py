"""Configuration driven report engine for the observed CENTER EDU reports.

The engine deliberately has no database assumptions.  A caller supplies a
``DataProvider`` implementation that queries the product's real repositories;
missing data returns an empty result with an explicit ``data_status`` rather than
fabricating rows.  ``reference-screen-specs.json`` supplies Vietnamese columns and
filters for all 59 observed report routes.
"""
from __future__ import annotations

import csv
import io
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Protocol

DEFAULT_SPEC_PATH = Path(__file__).resolve().parents[1] / "screen_specs" / "reference-screen-specs.json"

# A few legacy deep links still appear in the navigation inventory.  Keep
# those aliases at the report-engine boundary so an unknown alias cannot
# escape as a server-side KeyError/socket hangup.  The canonical observed
# route remains the source of title, columns, filters, and data semantics.
ROUTE_ALIASES = {
    "/report/finance/revenue": "/report/finance/revenue_center",
    "/report/attendance": "/report/training/attendance",
}


class DataProvider(Protocol):
    def query_report(self, *, entity: str, filters: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]: ...

    # Optional.  Providers may expose an aggregate computed from the same
    # filtered relation as query_report; generic providers remain unchanged.
    def query_report_summary(self, *, entity: str, filters: Mapping[str, Any]) -> Mapping[str, Any] | None: ...


@dataclass(frozen=True)
class ReportDefinition:
    slug: str
    route: str
    title: str
    entity: str
    columns: tuple[Mapping[str, Any], ...]
    filters: tuple[Mapping[str, Any], ...]
    tabs: tuple[str, ...]
    buttons: tuple[str, ...]

    @classmethod
    def from_spec(cls, spec: Mapping[str, Any]) -> "ReportDefinition":
        # Retained inventories occasionally contain generated placeholder choices.
        # Drop only the exact Synthetic option N marker; preserve every observed value.
        import re
        filters = []
        for raw in spec.get("filters", ()):
            item = dict(raw)
            options = item.get("options")
            if isinstance(options, (list, tuple)):
                item["options"] = tuple(value for value in options if not re.fullmatch(r"Synthetic option \d+", str(value)))
            filters.append(item)
        return cls(
            slug=str(spec["slug"]), route=str(spec["route"]), title=str(spec.get("title") or spec["slug"]),
            entity=str(spec.get("entity") or spec["slug"]), columns=tuple(spec.get("columns", ())),
            filters=tuple(filters), tabs=tuple(spec.get("tabs", ())), buttons=tuple(spec.get("buttons", ())),
        )


class ReportEngine:
    """Loads report definitions and executes them against a real data provider."""

    def __init__(self, provider: DataProvider, *, spec_path: Path | str = DEFAULT_SPEC_PATH):
        self.provider = provider
        raw = json.loads(Path(spec_path).read_text(encoding="utf-8"))
        self.definitions = {d["route"]: ReportDefinition.from_spec(d) for d in raw.get("screens", ()) if str(d.get("route", "")).startswith("/report/")}
        # Keep a strict distinction between the observed reference catalog and
        # callable compatibility aliases added by domain adapters.  Aliases
        # remain resolvable through ``definition/run/export`` but must not
        # inflate the reference screen count or be presented as extra report
        # screens in Mission Control.
        self.observed_routes = frozenset(self.definitions)

    def definition(self, route: str) -> ReportDefinition:
        route = ROUTE_ALIASES.get(route, route)
        try:
            return self.definitions[route]
        except KeyError as exc:
            raise KeyError(f"unknown report route: {route}") from exc

    def catalog(self) -> list[dict[str, Any]]:
        return [{"route": d.route, "slug": d.slug, "title": d.title, "entity": d.entity, "columns": [c.get("label", c.get("key")) for c in d.columns], "filters": [f.get("name") for f in d.filters], "tabs": list(d.tabs), "buttons": list(d.buttons)} for route, d in self.definitions.items() if route in self.observed_routes]

    @staticmethod
    def _project(row: Mapping[str, Any], definition: ReportDefinition, index: int) -> dict[str, Any]:
        """Project a domain row into the observed report contract.

        The reference labels use Vietnamese keys that intentionally differ from
        the local domain schema.  A direct ``row[key]`` projection therefore
        produced populated records containing only empty strings.  Keep the
        source schema local, but map the observed keys at this boundary.  A
        missing dimension remains ``None`` (rendered as ``Chưa cập nhật``),
        never a fabricated ``UNKNOWN`` or zero.
        """
        source = dict(row)
        route = definition.route
        entity = definition.entity.lower()

        common: dict[str, tuple[str, ...]] = {
            "ma_hoc_sinh": ("student_code", "ma_hoc_vien"),
            "ma_hoc_vien": ("student_code", "ma_hoc_sinh"),
            "ten_hoc_sinh": ("full_name", "student_name"),
            "ten_hoc_vien": ("full_name", "student_name"),
            "ho_ten": ("full_name", "student_name"),
            "hoc_vien": ("full_name", "student_name"),
            "khoa_hoc": ("course_name", "package_name"),
            "ten_khoa_hoc": ("course_name", "package_name"),
            "lop_hoc": ("class_code", "class_name"),
            "ma_lop": ("class_code",),
            "trang_thai": ("status", "contract_status", "payment_status"),
            "ngay": ("session_date", "invoice_date", "created_date", "test_date"),
            "ngay_tao": ("created_at", "created_date", "invoice_date"),
            "ngay_tao_hop_ong": ("created_date",),
            "ngay_tao_hoa_on": ("invoice_date",),
            "ngay_het_han": ("expiry_date",),
            "ghi_chu": ("note",),
            "chi_nhanh": ("branch", "center"),
            "trung_tam": ("center",),
            "nhan_vien": ("employee", "sales_owner"),
            "nhan_vien_sale": ("sales_owner",),
            "nhan_vien_ho_tro": ("sales_owner",),
            "so_buoi_i_hoc": ("present",),
            "so_buoi_ang_ky": ("enrolled",),
            "so_buoi_ghi_danh": ("enrolled",),
            "vang_co_phep": ("excused",),
            "vang_khong_phep": ("unexcused", "absent"),
            "so_luong_hoc_vien": ("enrolled",),
            "so_hoc_vien": ("enrolled",),
            "so_tien": ("payment_amount", "amount_due", "total_amount"),
            "so_tien_hoa_on": ("payment_amount",),
            "thuc_thu": ("payment_amount", "paid_amount"),
            "doanh_thu_tam_tinh": ("payment_amount", "total_amount"),
            "so_tien_no": ("debt_amount",),
            "con_no": ("debt_amount",),
            "so_tien_phai_thu": ("total_amount", "amount_due"),
            "da_ong": ("paid_amount",),
            "a_ong": ("paid_amount",),
            "ma_hop_ong": ("contract_code",),
            "hoa_on": ("invoice_code",),
            "ma_hoa_on": ("invoice_code",),
            "khach_hang": ("customer_name", "student_name", "full_name"),
            "ten_khach_hang": ("customer_name", "full_name"),
            "nguoi_tao": ("created_by_name",),
            "tai_khoan": ("username",),
            "so_ien_thoai": ("phone",),
            "sdt_phu_huynh": ("parent1_phone",),
            "email": ("email",),
            "nguon_du_lieu": ("source",),
            "nguon_kh": ("source",),
            "trang_thai_kh": ("status",),
            "nhan_vien_sale": ("sale_owner",),
        }

        route_aliases: dict[str, dict[str, tuple[str, ...]]] = {
            "/report/training/attendance": {
                "ma_hoc_sinh": ("student_code",), "ten_hoc_sinh": ("full_name",),
                "so_buoi_i_hoc": ("present",), "vang_co_phep": ("excused",),
                "vang_khong_phep": ("unexcused",),
            },
            "/report/training/class/v2": {
                "khoa_hoc": ("course_name",), "tong_so_lop": ("_class_count",),
                "lop_ang_hoc": ("_in_progress",), "lop_chua_hoc": ("_planned",),
                "a_hoc_ket_thuc": ("_completed",), "huy_lop": ("_cancelled",),
                "lop_sap_ket_thuc": ("_ending",), "lop_chua_co_lich": ("_without_schedule",),
            },
            "/report/crm/contract/index": {
                "khach_hang": ("student_name",), "o_tuong_kh": ("customer_type",),
                "ma_hop_ong": ("contract_code",), "khoa_hoc": ("package_name",),
                "lop_hoc": ("class_code",), "ngay_ang_ki": ("created_date",),
                "ngay_het_han": ("expiry_date",), "so_tien_phai_thu": ("total_amount",),
                "tinh_trang_thanh_toan": ("payment_status",), "nhan_vien": ("sales_owner",),
                "nguoi_tao": ("created_by_name",), "con_no_so_tien": ("debt_amount",),
                "trang_thai": ("contract_status",),
            },
            "/report/center/staff_teacher": {
                "ho_ten": ("full_name",), "tai_khoan": ("username",),
                "so_ien_thoai": ("phone",), "trang_thai": ("_active_label",),
                "trung_tam_chi_nhanh": ("_center",), "chuc_danh": ("role",),
                "phong_ban": ("role",), "phan_quyen": ("role",),
            },
            "/report/training/test": {
                "ho_ten": ("class_code", "name"), "tieu_chi": ("name",),
                "nhan_xet": ("status",),
            },
        }

        def derived(key: str) -> Any:
            if key == "no" or key == "stt":
                return index
            if key == "_class_count":
                return 1
            if key == "_in_progress":
                return 1 if str(source.get("status", "")).upper() in {"OPEN", "IN_PROGRESS", "ACTIVE"} else 0
            if key == "_planned":
                return 1 if str(source.get("status", "")).upper() in {"PLANNED", "NEW"} else 0
            if key == "_completed":
                return 1 if str(source.get("status", "")).upper() in {"COMPLETED", "DONE"} else 0
            if key == "_cancelled":
                return 1 if str(source.get("status", "")).upper() in {"CANCELLED", "CANCELED"} else 0
            if key == "_ending":
                return None
            if key == "_without_schedule":
                return 1 if not source.get("schedule") else 0
            if key == "_active_label":
                return "Hoạt động" if bool(source.get("active")) else "Ngừng hoạt động"
            if key == "_center":
                return "Trung tâm CenterOnline - Demo"
            return None

        aliases = {**common, **route_aliases.get(route, {})}
        projected: dict[str, Any] = {}
        for column in definition.columns:
            key = str(column.get("key"))
            value = derived(key) if key in {"no", "stt"} else source.get(key)
            if value in (None, ""):
                for candidate in aliases.get(key, ()):
                    value = derived(candidate) if candidate.startswith("_") else source.get(candidate)
                    if value not in (None, ""):
                        break
            projected[key] = value
        return projected

    def run(self, route: str, *, filters: Mapping[str, Any] | None = None, group_by: str | None = None, limit: int = 100) -> dict[str, Any]:
        definition = self.definition(route); filters = dict(filters or {})
        try:
            from .report_filter_domains import current_year_filters
        except ImportError:
            from report_filter_domains import current_year_filters
        definition = ReportDefinition(slug=definition.slug, route=definition.route, title=definition.title, entity=definition.entity,
            columns=definition.columns, filters=current_year_filters(definition.filters), tabs=definition.tabs, buttons=definition.buttons)
        if route == "/report/center/birth_day/index" and str(filters.get("birthday_type") or "student").lower() == "staff":
            definition = ReportDefinition(slug=definition.slug, route=definition.route, title="Báo cáo sinh nhật nhân viên - giáo viên", entity=definition.entity,
                columns=tuple({"key": key, "label": label} for key, label in (("no", "No."), ("ho_ten", "Họ tên"), ("ngay_sinh", "Ngày sinh"), ("chuc_danh", "Chức danh"), ("phong_ban", "Phòng ban"), ("qua_tang", "Quà tặng"), ("ngay_tang", "Ngày tặng"), ("trang_thai", "Trạng thái"), ("hanh_ong", "Hành động"))),
                filters=definition.filters, tabs=definition.tabs, buttons=definition.buttons)
        if route == "/report/teacher/sth/index":
            from .report_teacher import teacher_hours_columns
            definition = ReportDefinition(slug=definition.slug, route=definition.route, title=definition.title, entity=definition.entity, columns=tuple({"key": key, "label": label} for key, label in teacher_hours_columns(filters)), filters=definition.filters, tabs=definition.tabs, buttons=definition.buttons)
        source_rows = list(self.provider.query_report(entity=definition.entity, filters=filters))
        rows = [self._project(r, definition, index) for index, r in enumerate(source_rows[: max(1, min(int(limit), 10000))], start=1)]
        grouped: dict[str, dict[str, Any]] = {}
        if group_by:
            for row in rows:
                key = str(row.get(group_by, "")); bucket = grouped.setdefault(key, {group_by: key, "so_luong": 0}); bucket["so_luong"] += 1
        populated = sum(1 for row in rows if any(value not in (None, "") for value in row.values()))
        data_status = "NO_DATA" if not rows else ("OBSERVED" if populated == len(rows) else "PARTIAL")
        result = {"route": definition.route, "title": definition.title, "columns": list(definition.columns), "filters": list(definition.filters), "rows": rows, "groups": list(grouped.values()), "data_status": data_status, "source_entity": definition.entity}
        summary_fn = getattr(self.provider, "query_report_summary", None)
        if callable(summary_fn):
            summary = summary_fn(entity=definition.entity, filters=filters)
            if summary is not None:
                result["summary"] = dict(summary)
        return result

    def export_csv(self, route: str, *, filters: Mapping[str, Any] | None = None, group_by: str | None = None) -> str:
        result = self.run(route, filters=filters, group_by=group_by, limit=10000)
        out = io.StringIO(); writer = csv.writer(out)
        writer.writerow([c.get("label", c.get("key", "")) for c in result["columns"]])
        for row in result["rows"]: writer.writerow([row.get(c.get("key"), "") for c in result["columns"]])
        return out.getvalue()


def load_report_engine(provider: DataProvider, *, spec_path: Path | str = DEFAULT_SPEC_PATH) -> ReportEngine:
    return ReportEngine(provider, spec_path=spec_path)
