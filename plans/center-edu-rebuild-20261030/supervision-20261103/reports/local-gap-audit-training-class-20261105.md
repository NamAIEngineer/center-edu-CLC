# CEDU-CLASS-01 — local `/training/class` gap audit

- Date: 2026-11-05 (Asia/Ho_Chi_Minh)
- Scope: read-only local disposable runtime; no source edits; no reference writes.
- Owner/next: training lane lead; compare against fresh authenticated reference DOM/API when browser host is available.

## Runtime and evidence

- Source root: `/Users/nam/Documents/System-Agentic_AI/products/center-edu-rebuild`
- Branch: `center-edu-rebuild-verified`; source was clean before/after audit.
- Runtime: `CENTER_EDU_RICH_DEMO=1`, `127.0.0.1:19105`, disposable SQLite `/tmp/cedu-class-audit-20261105-1793887770.sqlite3`.
- Login: local synthetic ADMIN fixture only. No reference credential or cookie persisted.
- Server started and stopped cleanly; log: `/tmp/cedu-class-audit.log`.
- Source hashes:
  - `app.py`: `280586a60b7376f9f90de3fb2e4ce046784014f6c9a60843601aec59eaead120`
  - `modules/training_routes.py`: `b3b5b23b2e47593e1b60202de9ea39cb1f9824eb53b1fac74d3d68ce742885c3`
  - `static/app.js`: `84923c34c69c035e96ae425b5bb6c697fe17d9a4d7aef022d596d6466717e302`
  - `static/modules/training_routes.js`: `849236f58565cf95c49d47eadd0f62615609be51f359ad26d7f996f9dccfa889`

## Observed local behavior (FACT)

1. `POST /api/auth/login` returned HTTP 200 with local ADMIN and CSRF token.
2. `GET /api/classes` returned HTTP 200 and 25 synthetic persisted class rows. Rows include `code`, `course_name`, `student_count`, `start_date`, `end_date`, `schedule`, `primary_manager`, `teacher`, `completed_sessions`, and `status`.
3. `GET /api/classes?q=ENG-FND` returned HTTP 200 with only matching `course_code` rows; no-match query `q=NO_SUCH_CLASS_9f5` returned HTTP 200 and `data: []`.
4. Invalid status `GET /api/classes?status=NOT_A_STATUS` returned HTTP 400 `VALIDATION_ERROR` (`class status is invalid`).
5. Reversed range `GET /api/classes?start_from=2026-12-01&start_to=2026-01-01` returned HTTP 400 `VALIDATION_ERROR` (`start_from must be before or equal to start_to`).
6. `GET /training/class` returned HTTP 200. Server-rendered response contained the route label `Lớp học` and two `Tìm kiếm` markers. A live browser DOM/action check was not possible in this lane; JS hydration, table row projection, pagination, and empty-state rendering remain unverified.
7. Direct SQLite read-back from the disposable DB showed persisted class rows, including `ENG-FND-01`, `start_date=2026-09-04`, `end_date=2026-12-03`, `status=OPEN`.

## Comparison boundary

- The reference survey evidence covers authenticated representative routes, but does not provide equal-state `/training/class` response semantics or a fresh browser DOM receipt for this run.
- Therefore local API/filter behavior is evidence for the independent implementation only. It does not establish reference parity, pixel parity, pagination parity, or role parity.

## Status

- Local API/search/validation/persistence: **OBSERVED PASS** for the cases above.
- Reference `/training/class` parity: **UNKNOWN**.
- Browser DOM/action/empty-state parity: **UNKNOWN** (browser host unavailable in this lane).
- No implementation change recommended from this audit. Next check: run authenticated reference and clone at matched viewport/data state; capture DOM/network evidence for class list columns, filter controls, pagination, and no-match empty state.

## Commands

```text
CENTER_EDU_RICH_DEMO=1 python3 app.py --host 127.0.0.1 --port 19105 --db /tmp/cedu-class-audit-20261105-1793887770.sqlite3
curl ... /api/auth/login
curl ... /api/classes
curl ... '/api/classes?q=ENG-FND'
curl ... '/api/classes?q=NO_SUCH_CLASS_9f5'
curl ... '/api/classes?status=NOT_A_STATUS'
curl ... '/api/classes?start_from=2026-12-01&start_to=2026-01-01'
```
