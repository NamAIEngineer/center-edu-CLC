# Independent verification: call-center history alias (2026-11-05)

## Verdict

**PASS_WITH_LIMITATIONS** for the requested local disposable-runtime contract.

- `GET /api/callcenter/history` and `GET /api/call-history`: **PASS**. Both returned HTTP 200, identical records and filter behavior under an authenticated `ADMIN` session.
- Authentication: **PASS**. Unauthenticated history request returned HTTP 401 (`AUTH_REQUIRED`). Synthetic `ADMIN` and `STUDENT` logins returned HTTP 200.
- RBAC: **PASS**. Authenticated `STUDENT` request to either protected history API was rejected HTTP 403 (`FORBIDDEN`).
- CSRF: **PASS** for the mutating control used to seed disposable rows. `POST /api/call-history` without `X-CSRF-Token` returned HTTP 403; the same request with the login response token returned HTTP 201.
- Query filters: **PASS**. `status=OPEN`, `q=needle-x`, `date_from=2026-11-02`, and `staff_name=Alice` each returned the expected one synthetic row. Alias and canonical route returned the same two-row unfiltered result (reverse chronological order).
- Restart persistence: **PASS**. After clean process termination and restart against the same disposable SQLite file, the pre-restart session remained usable and both rows remained readable; a fresh login also returned both rows.
- Reference/private parity, production deployment, browser visual acceptance: **UNKNOWN**. This bounded check only proves the current local source and disposable SQLite runtime.

## Exact evidence

Runtime: `python3 app.py --host 127.0.0.1 --port 19827`, isolated `CENTER_EDU_DB` temporary file, `CENTER_EDU_RICH_DEMO=1`, synthetic password `VerifyPass!2026`; process stopped cleanly after probes. No product source or external state changed.

- `/api/health`: HTTP 200, `ok=true`, SQLite.
- Seeded rows with `ADMIN` + valid CSRF: `Alpha Verify` (`OPEN`, `CALL`, `Alice`, `2026-11-01 09:00`, note `needle-x`) and `Beta Verify` (`CLOSED`, `MESSAGE`, `Bob`, `2026-11-03 10:00`).
- `GET /api/callcenter/history`: HTTP 200, 2 rows (`Beta Verify`, `Alpha Verify`).
- `GET /api/call-history`: HTTP 200, 2 rows (`Beta Verify`, `Alpha Verify`); same JSON data as alias.
- `GET /api/callcenter/history?status=OPEN`: HTTP 200, 1 row (`Alpha Verify`).
- `GET /api/call-history?q=needle-x`: HTTP 200, 1 row (`Alpha Verify`).
- `GET /api/call-history?date_from=2026-11-02`: HTTP 200, 1 row (`Beta Verify`).
- `GET /api/call-history?staff_name=Alice`: HTTP 200, 1 row (`Alpha Verify`).
- Missing CSRF on both create attempts: HTTP 403; valid CSRF creates: HTTP 201.
- Student history read: HTTP 403.
- Restart old session read: HTTP 200, 2 rows; fresh admin login after restart: HTTP 200; alias read: HTTP 200, 2 rows.

## Source integrity

Current `products/center-edu-rebuild/app.py` SHA-256:

```
41f10f28823cfe2864f34440c701c4a0b9fe94671f4f1ecabafa169fd0dcf97c
```

The source dispatches both paths through the same handler branch:

```python
elif path in ("/api/call-history", "/api/callcenter/history"):
```

The read handler calls `call_history`, which enforces `ADMIN`/`STAFF` role and applies query, status, call type, party role, staff, and date filters. No source edits were made by this verifier.
