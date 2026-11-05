"""Sale lane facade over the persistent CRM/Sale route store.

Sale routes share the prospect, appointment and route-record persistence
contracts, but retain a separate import surface for coordinator wiring and
future Sale-only policy.
"""
from .crm_domain import (
    APPOINTMENT_ACTIONS,
    APPOINTMENT_COLUMNS,
    APPOINTMENT_ROUTES,
    APPOINTMENT_STATUSES,
    CRMStore,
    PROSPECT_COLUMNS,
    PROSPECT_ROUTES,
    PROSPECT_STATUSES,
)
from .crm_routes import CRMRoutesStore, READ_ONLY_ROUTES, ROUTE_CONTRACTS, SALE_ROUTE_AUTHORITY, route_authority

SALE_ROUTES = tuple(route for route in ROUTE_CONTRACTS if route.startswith("/sale/") or route == "/dashboard/sale")
SaleCRMStore = CRMStore
SaleRoutesStore = CRMRoutesStore

__all__ = [
    "SaleCRMStore", "SaleRoutesStore", "SALE_ROUTES", "ROUTE_CONTRACTS", "READ_ONLY_ROUTES", "SALE_ROUTE_AUTHORITY", "route_authority",
    "PROSPECT_ROUTES", "APPOINTMENT_ROUTES", "PROSPECT_COLUMNS",
    "APPOINTMENT_COLUMNS", "PROSPECT_STATUSES", "APPOINTMENT_ACTIONS",
    "APPOINTMENT_STATUSES",
]
