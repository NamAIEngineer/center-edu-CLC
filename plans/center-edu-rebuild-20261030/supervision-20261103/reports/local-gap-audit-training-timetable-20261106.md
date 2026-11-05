# CEDU-TRN-001 — local timetable and attendance gap audit

- Date: 2026-11-06 (Asia/Ho_Chi_Minh)
- Scope: read-only local `/training/timetable` and `/training/attendance`; synthetic disposable data only.
- No source, MATRIX, or reference data changed.

## Runtime

- Source: `/Users/nam/Documents/System-Agentic_AI/products/center-edu-rebuild`
- Branch: `center-edu-rebuild-verified`
- Runtime: `CENTER_EDU_RICH_DEMO=1`, `127.0.0.1:19108`
- SQLite: `/tmp/cedu-trn-audit-20261106-1793899290.sqlite3`
- Login: local synthetic ADMIN; credentials/cookies not persisted in repository.
- Server log: `/tmp/cedu-trn-audit2.log`; process stopped after probes.

## Source hashes

- `app.py`: `280586a60b7376f9f90de3fb2e4ce046784014f6c9a60843601aec59eaead120`
- `modules/training_routes.py`: `b3b5b23b2e47593e1b60202de9ea39cb1f9824eb53b1fac74d3d68ce742885c3`
- `static/app.js`: `84923c34c69c035e96ae425b5bb6c697fe17d9a4d7aef022d596d6466717e302`
- `static/modules/training_routes.js`: `849236f58565cf95c49d47eadd0f62615609be51f359ad26d7f996f9dccfa889`

## API and DB evidence (FACT)

1. `POST /api/auth/login` returned `200`.
2. `GET /api/timetable` returned `200`; SQLite `timetable_sessions` contained 364 rows. Sample persisted row: `2026-11-03`, `Room A1`, `SCHEDULED`.
3. `GET /api/timetable?room=Room%20A1` returned `200` with a filtered response (`Content-Length: 314`).
4. `GET /api/timetable/week?start=2026-11-02` returned `200` (`Content-Length: 6945`).
5. `GET /api/export/timetable?room=Room%20A1` returned `200`, `text/csv`, filename `timetable.csv`, content length 219.
6. `GET /api/timetable?date=not-a-date` returned `400 Bad Request` (`VALIDATION_ERROR` body; exact body not retained in this report).
7. `GET /api/attendance` returned `200`; SQLite `attendance` contained 864 rows. Sample rows: `2026-09-06` statuses `PRESENT`, `EXCUSED`, `ABSENT`.
8. `GET /api/attendance?status=ABSENT&date_from=2026-11-01&date_to=2026-11-30` returned `200` (`Content-Length: 6946`).
9. `GET /api/attendance?status=UNKNOWN` returned `400 Bad Request` (`VALIDATION_ERROR`).

## Renderer evidence

- `GET /training/timetable` and `/training/attendance` returned HTTP 200.
- Static response text contained two `Tìm kiếm` markers per route.
- Source markers show route-owned controls/actions: `attendance-status-filter`, `attendance-date-from`, `attendance-date-to`, `/api/attendance`; timetable `/api/timetable`, `/api/timetable/week`, `/api/export/timetable`, and `Ghi điểm danh` / timetable modal actions.
- Browser DOM hydration, interactive filter changes, table projection, pagination, mobile layout, and empty-state rendering were not executed. Browser host/harness unavailable in this lane: **UNKNOWN**.

## Boundary and status

- Local API/filter/export/error/persistence behavior: **OBSERVED PASS** for probes listed above.
- Reference authenticated parity, exact timetable matrix semantics, role-specific attendance visibility, DOM visual parity: **UNKNOWN**.
- No implementation change recommended from this audit. Next owner: training lane lead; run matched-state reference and clone browser checks when browser host is available.

## Commands

```text
CENTER_EDU_RICH_DEMO=1 python3 app.py --host 127.0.0.1 --port 19108 --db /tmp/cedu-trn-audit-20261106-1793899290.sqlite3
curl ... /api/auth/login
curl ... /api/timetable
curl ... '/api/timetable?room=Room%20A1'
curl ... '/api/timetable/week?start=2026-11-02'
curl ... '/api/export/timetable?room=Room%20A1'
curl ... /api/attendance
curl ... '/api/attendance?status=ABSENT&date_from=2026-11-01&date_to=2026-11-30'
curl ... '/api/attendance?status=UNKNOWN'
```
