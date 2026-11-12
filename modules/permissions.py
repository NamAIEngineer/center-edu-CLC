"""Single route/action policy shared by the HTTP shell and the SPA.

The policy is intentionally explicit.  Empty data, failed APIs, or renderer
errors never grant or deny a route.  The browser receives this sanitized
projection from ``/api/auth/me`` and uses it for navigation only; server
checks remain authoritative for every mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from typing import Any


@dataclass(frozen=True)
class RolePolicy:
    routes: tuple[str, ...]
    actions: tuple[str, ...]


_READ_COMMON = (
    "/", "/dashboard/training", "/change_profile",
    "/training/*", "/crm/*", "/sale/*", "/report/training/*", "/report/teacher/*",
)

_POLICIES = {
    "ADMIN": RolePolicy(("*",), ("read", "create", "update", "delete", "import", "export")),
    "STAFF": RolePolicy(("*",), ("read", "create", "update", "delete", "import", "export")),
    "TEACHER": RolePolicy(_READ_COMMON, ("read",)),
    "STUDENT": RolePolicy(("/", "/dashboard/training", "/change_profile", "/training/*"), ("read",)),
    # Branch managers receive only the screens whose backend scope is proven.
    # In particular, do not expose call-center, finance, setup, teacher, report,
    # or generic generated-screen routes until their row scope is implemented.
    "BRANCH_MANAGER": RolePolicy(
        ("/", "/dashboard/training", "/change_profile", "/center/student/index", "/training/class"),
        ("read", "create", "update", "import", "export"),
    ),
}


def policy_for_role(role: str | None) -> dict[str, list[str]]:
    normalized = str(role or "").upper()
    policy = _POLICIES.get(normalized, RolePolicy((), ()))
    return {"allowed_routes": list(policy.routes), "allowed_actions": list(policy.actions)}


def route_allowed(role: str | None, route: str) -> bool:
    normalized = str(role or "").upper()
    route = str(route or "/").split("?", 1)[0] or "/"
    for pattern in _POLICIES.get(normalized, RolePolicy((), ())).routes:
        if pattern == "*" or fnmatch(route, pattern):
            return True
    return False


def action_allowed(role: str | None, action: str) -> bool:
    normalized = str(role or "").upper()
    return str(action or "read").lower() in set(_POLICIES.get(normalized, RolePolicy((), ())).actions)


def sanitized_policy(role: str | None) -> dict[str, Any]:
    return policy_for_role(role)


__all__ = ["RolePolicy", "policy_for_role", "route_allowed", "action_allowed", "sanitized_policy"]
