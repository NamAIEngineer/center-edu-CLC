"""Read-only persisted finance dashboard projection.

The projection aggregates existing finance tables.  It never inserts placeholder
rows or reports UNKNOWN as a value.  Router registration is intentionally left
for the coordinator because this worker cannot edit ``app.py``.
"""
from __future__ import annotations

import sqlite3
from typing import Any

from modules.finance import _attach_store, _register_metadata

ROUTE = "/dashboard/finance"
READ_ROLES = frozenset(("ADMIN", "STAFF", "TEACHER"))


class FinanceDashboard:
    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self.db.row_factory = sqlite3.Row

    @staticmethod
    def _check(role: str) -> None:
        if role not in READ_ROLES:
            raise PermissionError("Dashboard tài chính không dành cho vai trò này")

    def _count(self, table: str) -> int:
        exists = self.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
        return int(self.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]) if exists else 0

    def _sum(self, table: str, column: str) -> int:
        exists = self.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
        return int(self.db.execute(f"SELECT COALESCE(SUM({column}),0) FROM {table}").fetchone()[0] or 0) if exists else 0

    def summary(self, *, role: str = "ADMIN") -> dict[str, Any]:
        self._check(role)
        bills = self._sum("finance_bills", "payment_amount")
        spends = self._sum("finance_spends", "amount_vnd")
        contracts = self._count("finance_contracts")
        revenues = self._count("finance_revenues")
        return {
            "route": ROUTE,
            "source": "local-sqlite",
            "contract_count": contracts,
            "bill_count": self._count("finance_bills"),
            "revenue_count": revenues,
            "spend_count": self._count("finance_spends"),
            "reserve_count": self._count("finance_reserves"),
            "wallet_count": self._count("finance_wallets"),
            "appointment_count": self._count("finance_appointments"),
            "total_collected_vnd": bills,
            "total_spend_vnd": spends,
            "net_cash_vnd": bills - spends,
            "data_status": "OBSERVED" if any((bills, spends, contracts, revenues)) else "NO_DATA",
        }


def route_contract() -> dict[str, Any]:
    return {"route": ROUTE, "headings": ("Hợp đồng - Hóa đơn phát sinh hôm nay", "Hợp đồng", "Tiền hợp đồng", "Hóa đơn", "Quản lý kho ( vật phẩm )", "Thu - Nợ", "Các chương trình ưu đãi đang chạy", "Ưu đãi học phí đóng trước", "Ưu đãi nhập học kỳ thu 2026", "Ưu đãi Tung", "Ưu đãi nhập học kỳ thu"), "read_roles": sorted(READ_ROLES), "metrics": ("contract_count", "bill_count", "revenue_count", "spend_count", "reserve_count", "wallet_count", "appointment_count", "total_collected_vnd", "total_spend_vnd", "net_cash_vnd")}


def register(app_or_router: Any = None, service: Any = None) -> dict[str, Any]:
    target = service if service is not None else app_or_router
    _attach_store(target, "finance_dashboard_store", FinanceDashboard)
    return _register_metadata(app_or_router, service, name="finance_dashboard", routes=(ROUTE,), schema="finance_dashboard_projection")


__all__ = ["FinanceDashboard", "ROUTE", "READ_ROLES", "route_contract", "register"]
