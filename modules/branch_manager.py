"""Tenant and branch scoped records for disposable integration tests.

The web app has several legacy domain tables with inconsistent scope columns.
This small repository is the bounded contract surface for the branch/manager
wave; callers must pass the authenticated actor, never a client supplied
tenant or branch identity.
"""

from __future__ import annotations

import csv
import io
import sqlite3
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


class ScopeDenied(PermissionError):
    """Raised when a row or branch is outside the actor's authenticated scope."""


@dataclass(frozen=True)
class Actor:
    user_id: int
    tenant_id: int
    role: str


SCHEMA = """
CREATE TABLE IF NOT EXISTS bm_tenants (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active'
);
CREATE TABLE IF NOT EXISTS bm_branches (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES bm_tenants(id),
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    UNIQUE(tenant_id, code)
);
CREATE TABLE IF NOT EXISTS bm_manager_assignments (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES bm_tenants(id),
    branch_id INTEGER NOT NULL REFERENCES bm_branches(id),
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    UNIQUE(tenant_id, branch_id, user_id, role)
);
CREATE TABLE IF NOT EXISTS bm_records (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES bm_tenants(id),
    branch_id INTEGER NOT NULL REFERENCES bm_branches(id),
    label TEXT NOT NULL,
    value TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS bm_audit (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    tenant_id INTEGER NOT NULL,
    branch_id INTEGER,
    action TEXT NOT NULL,
    record_id INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS bm_entity_scopes (
    entity TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    tenant_id INTEGER NOT NULL REFERENCES bm_tenants(id),
    branch_id INTEGER NOT NULL REFERENCES bm_branches(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(entity, entity_id)
);
CREATE INDEX IF NOT EXISTS idx_bm_entity_scope ON bm_entity_scopes(entity, tenant_id, branch_id);
CREATE TABLE IF NOT EXISTS bm_user_roles (
    user_id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES bm_tenants(id),
    role TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);
"""


class BranchManagerStore:
    """Scope-enforcing repository backed by a caller-owned SQLite connection."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.db.commit()

    def ensure_default_scope(self) -> None:
        """Create one disposable tenant/branch for local scope defaults."""
        self.db.execute("INSERT OR IGNORE INTO bm_tenants(id,name) VALUES(1,?)", ("Center EDU",))
        self.db.execute(
            "INSERT OR IGNORE INTO bm_branches(id,tenant_id,code,name) VALUES(1,1,?,?)",
            ("MAIN", "Trung tâm chính"),
        )
        self.db.commit()

    def user_scope(self, user_id: int) -> tuple[int, str] | None:
        row = self.db.execute(
            "SELECT tenant_id,role FROM bm_user_roles WHERE user_id=? AND active=1",
            (int(user_id),),
        ).fetchone()
        return (int(row["tenant_id"]), str(row["role"])) if row else None

    def branches(self, actor: Actor) -> list[dict[str, Any]]:
        allowed = self._branch_ids(actor)
        if not allowed:
            return []
        marks = ",".join("?" for _ in allowed)
        rows = self.db.execute(
            f"SELECT id,tenant_id,code,name,status FROM bm_branches WHERE id IN ({marks}) ORDER BY id",
            tuple(sorted(allowed)),
        ).fetchall()
        return [dict(row) for row in rows]

    def assignments(self, actor: Actor) -> list[dict[str, Any]]:
        """Return assignments visible to the authenticated actor.

        Managers only see their own active assignments.  Admin/staff may
        inspect assignments inside their tenant; a client supplied tenant ID
        is never used to widen this query.
        """
        if actor.role.upper() == "BRANCH_MANAGER":
            rows = self.db.execute(
                "SELECT id,tenant_id,branch_id,user_id,role,active FROM bm_manager_assignments "
                "WHERE tenant_id=? AND user_id=? AND active=1 ORDER BY id",
                (int(actor.tenant_id), int(actor.user_id)),
            ).fetchall()
        elif actor.role.upper() in {"ADMIN", "STAFF"}:
            rows = self.db.execute(
                "SELECT id,tenant_id,branch_id,user_id,role,active FROM bm_manager_assignments "
                "WHERE tenant_id=? ORDER BY id",
                (int(actor.tenant_id),),
            ).fetchall()
        else:
            return []
        return [dict(row) for row in rows]

    def assign_manager(self, actor: Actor, *, user_id: int, branch_id: int, role: str = "BRANCH_MANAGER") -> dict[str, Any]:
        """Create an assignment after checking tenant and branch ownership."""
        if actor.role.upper() not in {"ADMIN", "STAFF"}:
            raise ScopeDenied("manager assignment requires admin scope")
        self._check_branch(actor, int(branch_id))
        branch = self.db.execute(
            "SELECT tenant_id FROM bm_branches WHERE id=? AND status='active'",
            (int(branch_id),),
        ).fetchone()
        if branch is None or int(branch["tenant_id"]) != int(actor.tenant_id):
            raise ScopeDenied("branch outside tenant scope")
        normalized_role = str(role or "BRANCH_MANAGER").upper()
        if normalized_role != "BRANCH_MANAGER":
            raise ValueError("only BRANCH_MANAGER assignments are supported")
        self.db.execute(
            "INSERT INTO bm_manager_assignments(tenant_id,branch_id,user_id,role,active) VALUES(?,?,?,?,1) "
            "ON CONFLICT(tenant_id,branch_id,user_id,role) DO UPDATE SET active=1",
            (int(actor.tenant_id), int(branch_id), int(user_id), normalized_role),
        )
        self.db.commit()
        row = self.db.execute(
            "SELECT id,tenant_id,branch_id,user_id,role,active FROM bm_manager_assignments "
            "WHERE tenant_id=? AND branch_id=? AND user_id=? AND role=?",
            (int(actor.tenant_id), int(branch_id), int(user_id), normalized_role),
        ).fetchone()
        return dict(row)

    def scope_entity(self, actor: Actor, entity: str, entity_id: int) -> bool:
        row = self.db.execute(
            "SELECT tenant_id,branch_id FROM bm_entity_scopes WHERE entity=? AND entity_id=?",
            (str(entity), int(entity_id)),
        ).fetchone()
        if row is None:
            # Unmapped rows are visible only to same-tenant admin/staff. A
            # branch manager must fail closed until an explicit mapping exists.
            return actor.role.upper() in {"ADMIN", "STAFF"} and int(actor.tenant_id) == 1
        try:
            self._check_branch(actor, int(row["branch_id"]))
        except ScopeDenied:
            return False
        return int(row["tenant_id"]) == int(actor.tenant_id)

    def map_entity(self, *, entity: str, entity_id: int, tenant_id: int, branch_id: int, commit: bool = True) -> None:
        self.db.execute(
            "INSERT INTO bm_entity_scopes(entity,entity_id,tenant_id,branch_id) VALUES(?,?,?,?) "
            "ON CONFLICT(entity,entity_id) DO UPDATE SET tenant_id=excluded.tenant_id,branch_id=excluded.branch_id",
            (str(entity), int(entity_id), int(tenant_id), int(branch_id)),
        )
        if commit:
            self.db.commit()

    def entity_scope_ids(self, actor: Actor, entity: str, branch_id: int | None = None) -> set[int]:
        allowed = self._branch_ids(actor)
        if not allowed:
            return set()
        if branch_id is not None:
            self._check_branch(actor, int(branch_id))
            allowed = {int(branch_id)}
        marks = ",".join("?" for _ in allowed)
        rows = self.db.execute(
            f"SELECT entity_id FROM bm_entity_scopes WHERE entity=? AND tenant_id=? AND branch_id IN ({marks})",
            (str(entity), int(actor.tenant_id), *sorted(allowed)),
        ).fetchall()
        return {int(row[0]) for row in rows}

    def _branch_ids(self, actor: Actor) -> set[int] | None:
        role = actor.role.upper()
        if role in {"ADMIN", "STAFF"}:
            rows = self.db.execute(
                "SELECT id FROM bm_branches WHERE tenant_id=? AND status='active'",
                (actor.tenant_id,),
            ).fetchall()
            return {int(row["id"]) for row in rows}
        if role != "BRANCH_MANAGER":
            return set()
        rows = self.db.execute(
            "SELECT branch_id FROM bm_manager_assignments "
            "WHERE tenant_id=? AND user_id=? AND role='BRANCH_MANAGER' AND active=1",
            (actor.tenant_id, actor.user_id),
        ).fetchall()
        return {int(row["branch_id"]) for row in rows}

    def _check_branch(self, actor: Actor, branch_id: int) -> None:
        allowed = self._branch_ids(actor)
        if allowed is None or int(branch_id) not in allowed:
            raise ScopeDenied("branch outside authenticated scope")

    def _record(self, actor: Actor, record_id: int) -> sqlite3.Row:
        row = self.db.execute(
            "SELECT * FROM bm_records WHERE id=? AND tenant_id=?",
            (int(record_id), actor.tenant_id),
        ).fetchone()
        if row is None:
            raise ScopeDenied("record outside authenticated scope")
        self._check_branch(actor, int(row["branch_id"]))
        return row

    def _audit(self, actor: Actor, action: str, branch_id: int | None, record_id: int | None) -> None:
        self.db.execute(
            "INSERT INTO bm_audit(user_id,tenant_id,branch_id,action,record_id) VALUES(?,?,?,?,?)",
            (actor.user_id, actor.tenant_id, branch_id, action, record_id),
        )

    def list_records(self, actor: Actor, *, query: str = "", branch_id: int | None = None) -> list[dict[str, Any]]:
        allowed = self._branch_ids(actor)
        if not allowed:
            return []
        ids = sorted(allowed)
        marks = ",".join("?" for _ in ids)
        args: list[Any] = [actor.tenant_id, *ids]
        where = [f"tenant_id=? AND branch_id IN ({marks})"]
        if branch_id is not None:
            if int(branch_id) not in allowed:
                raise ScopeDenied("branch outside authenticated scope")
            where.append("branch_id=?")
            args.append(int(branch_id))
        if query:
            where.append("(label LIKE ? OR value LIKE ?)")
            needle = f"%{query}%"
            args.extend([needle, needle])
        rows = self.db.execute(
            "SELECT id,tenant_id,branch_id,label,value,updated_at FROM bm_records WHERE "
            + " AND ".join(where) + " ORDER BY id",
            args,
        ).fetchall()
        return [dict(row) for row in rows]

    def read(self, actor: Actor, record_id: int) -> dict[str, Any]:
        return dict(self._record(actor, record_id))

    def create(self, actor: Actor, *, branch_id: int, label: str, value: str = "") -> int:
        self._check_branch(actor, branch_id)
        if not str(label).strip():
            raise ValueError("label is required")
        cur = self.db.execute(
            "INSERT INTO bm_records(tenant_id,branch_id,label,value) VALUES(?,?,?,?)",
            (actor.tenant_id, int(branch_id), str(label).strip(), str(value)),
        )
        self._audit(actor, "create", int(branch_id), int(cur.lastrowid))
        self.db.commit()
        return int(cur.lastrowid)

    def update(self, actor: Actor, record_id: int, *, label: str | None = None, value: str | None = None) -> None:
        row = self._record(actor, record_id)
        next_label = row["label"] if label is None else str(label).strip()
        if not next_label:
            raise ValueError("label is required")
        next_value = row["value"] if value is None else str(value)
        self.db.execute(
            "UPDATE bm_records SET label=?,value=?,updated_at=CURRENT_TIMESTAMP WHERE id=? AND tenant_id=?",
            (next_label, next_value, int(record_id), actor.tenant_id),
        )
        self._audit(actor, "update", int(row["branch_id"]), int(record_id))
        self.db.commit()

    def delete(self, actor: Actor, record_id: int) -> None:
        row = self._record(actor, record_id)
        self.db.execute("DELETE FROM bm_records WHERE id=? AND tenant_id=?", (int(record_id), actor.tenant_id))
        self._audit(actor, "delete", int(row["branch_id"]), int(record_id))
        self.db.commit()

    def bulk_update(self, actor: Actor, record_ids: Iterable[int], *, value: str) -> None:
        ids = [int(record_id) for record_id in record_ids]
        try:
            self.db.execute("BEGIN")
            rows = [self._record(actor, record_id) for record_id in ids]
            for row in rows:
                self.db.execute(
                    "UPDATE bm_records SET value=?,updated_at=CURRENT_TIMESTAMP WHERE id=? AND tenant_id=?",
                    (str(value), int(row["id"]), actor.tenant_id),
                )
                self._audit(actor, "bulk_update", int(row["branch_id"]), int(row["id"]))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def export_csv(self, actor: Actor, *, branch_id: int | None = None) -> str:
        rows = self.list_records(actor, branch_id=branch_id)
        out = io.StringIO(newline="")
        writer = csv.DictWriter(out, fieldnames=("id", "tenant_id", "branch_id", "label", "value", "updated_at"))
        writer.writeheader()
        writer.writerows(rows)
        return out.getvalue()
