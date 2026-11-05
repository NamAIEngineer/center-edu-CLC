# Builder report: call-center history API alias — 2026-11-05

## Outcome

Added the read-only compatibility alias `GET /api/callcenter/history` in `app.py`. It enters the existing `call_history` service contract through the same authenticated handler branch as `GET /api/call-history`, preserving all existing query parameters (`q`, `status`, `call_type`, `party_role`, `staff_name`, `date_from`, `date_to`), role checks, tenant/session behavior, CSRF boundary, and response shape. No mutation alias was added: the existing frontend and routing pattern use canonical `POST/PUT /api/call-history`, and adding an unrequested write path would duplicate the contract.

## Changed files and hashes

- `app.py` — `sha256: 41f10f28823cfe2864f34440c701c4a0b9fe94671f4f1ecabafa169fd0dcf97c`
- `tests/test_callcenter_api_alias.py` — `sha256: 8f1e23239257552ff5e7b46722df9f42370d739f3bd1b703a467cbfc80368474`

## Verification

Command:

```text
python3 -m py_compile app.py
python3 -m unittest tests.test_callcenter_api_alias -v
```

Result: `Ran 3 tests ... OK`.

FACT: unauthenticated alias request returns `401 AUTH_REQUIRED`.

FACT: `student` and `teacher` alias requests return `403 FORBIDDEN`; service role boundary remains active.

FACT: disposable SQLite test creates a call through the canonical endpoint, then alias and canonical filtered GET responses are byte-equivalent JSON payloads with one matching row.

FACT: after closing and recreating the server against the same disposable DB, alias GET returns the persisted `MISSED` row.

FACT: empty/list behavior is covered by the filtered list contract and returns HTTP 200 with `data` list.

FACT: canonical `GET /api/call-history` branch remains behaviorally unchanged; only its path condition now includes the compatibility alias.

## UNKNOWN / limits

UNKNOWN: private/reference tenant isolation semantics beyond this local service's existing session/database contract were not independently observable.

UNKNOWN: live production deployment, browser acceptance, and external call-center provider integration were not exercised.
