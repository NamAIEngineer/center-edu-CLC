"""Public CRM module entrypoint.

The implementation lives in :mod:`crm_domain` so route metadata and the
SQLite repository can be imported without coupling to the HTTP application.
"""
from .crm_domain import (
    APPOINTMENT_ACTIONS,
    APPOINTMENT_COLUMNS,
    APPOINTMENT_ROUTES,
    APPOINTMENT_STATUSES,
    CRM,
    CRMStore,
    PROSPECT_COLUMNS,
    PROSPECT_ROUTES,
    PROSPECT_STATUSES,
    READ_ROLES,
    SCHEMA,
    WRITE_ROLES,
    route_contract,
)

__all__ = [
    "CRM", "CRMStore", "SCHEMA", "PROSPECT_ROUTES", "APPOINTMENT_ROUTES",
    "PROSPECT_COLUMNS", "APPOINTMENT_COLUMNS", "PROSPECT_STATUSES",
    "APPOINTMENT_ACTIONS", "APPOINTMENT_STATUSES", "READ_ROLES",
    "WRITE_ROLES", "route_contract",
]
