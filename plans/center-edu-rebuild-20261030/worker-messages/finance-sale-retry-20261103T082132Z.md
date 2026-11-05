# Finance/Sale retry worker report

## FACT

- Scope stayed inside `modules/finance*.py`, `modules/sale_domain.py`, and the new `test_finance_sale_gap.py`; no `app.py`, shared frontend, canonical reference, deployment, or visual evidence changed.
- Fixed appointment update validation: empty student/reference values now fail closed instead of overwriting a persisted record.
- Fixed transfer update validation: blank participants and same source/destination now fail closed, matching create invariants.
- Fixed point-rule read filtering: invalid status rejects; list/export now enforce the read-role boundary.
- Fixed inventory update: missing item ID now raises `KeyError` instead of reporting a successful no-op.
- Added focused Finance/Sale gap tests for truthful empty state, persistence, CRUD/filter/export/RBAC, validation, and Sale soft delete.

## INFERENCE

- Existing host API wiring already enforces HTTP role checks and reaches these stores; this retry keeps shared wiring untouched.
- The route facade in `modules/sale_domain.py` remains intentionally host-agnostic and delegates Sale persistence to the existing CRM stores.

## UNKNOWN

- Browser/visual parity and authenticated reference behavior remain UNKNOWN; no browser provider was used.
- No canonical `diff_local` or screenshot claim is made in this bounded retry.

## Verification

- `python3 -m unittest -q test_finance_sale_gap.py tests.evidence.test_W2_finance_lane test_w3_crm_vertical.py` -> `Ran 14 tests ... OK`.
- `python3 -m py_compile modules/finance*.py modules/sale_domain.py test_finance_sale_gap.py` -> PASS.
- `node --check static/modules/finance*.js static/modules/sale.js` -> PASS (`syntax_ok`).
- Isolated runtime `CENTER_EDU_DB=/tmp/center-edu-finance-sale-gap-20261103.sqlite3 CENTER_EDU_RICH_DEMO=1`, `127.0.0.1:19102`: `/api/health` returned `{"ok": true, "service": "center-edu-rebuild", "database": "sqlite"}`; process stopped after probe.

## Acceptance

- A3 PASS local focused Finance/Sale domain checks.
- A4 PASS persistent SQLite CRUD/filter/export paths exercised locally.
- A5 PASS status and validation invariants fail closed.
- A6 PASS RBAC checks exercised for read/write boundaries.
- A7 PASS truthful empty state returns zero persisted rows without filler.
- A8 UNKNOWN browser/visual/reference parity; deliberately unclaimed.
- C1 PASS scope and ownership constraints preserved.
- C4 PASS no shared app/frontend/canonical evidence edits.
- V1 PASS focused unit suite.
- V2 PASS Python and JavaScript syntax checks.
- V3 PASS isolated readiness probe; no deployment claim.

Status: DONE_WITH_LIMITATIONS
