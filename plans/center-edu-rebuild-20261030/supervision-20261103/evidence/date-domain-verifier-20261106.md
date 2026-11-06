# Date-domain integration verifier

- Run: `run_bf152f4f7779`
- Scope: canonical `/Users/nam/Documents/System-Agentic_AI/products/center-edu-rebuild`; read-only source/test/helper verification.
- Expected/current SHA-256:
  - `static/app.js`: `ee40ccf00579622f9c7bef8d66d23855becdd4ebc550896460b094ec34ad75ac` (MATCH)
  - `static/modules/training_routes.js`: `7f95b7f50d58bb3936a8a0d602e7a0f148c4cfbdfe9f192a918cc220beb7f4de` (MATCH)
- `node --check static/app.js`: PASS
- `node --check static/modules/training_routes.js`: PASS
- Focused regression suite: `TZ=UTC python3 -m unittest tests.test_training_backlog_regressions`: 4/4 PASS; `TZ=Asia/Ho_Chi_Minh ...`: 4/4 PASS.

## Pure helper cases

Executed using `timetableWeekOptions` and `scopeTimetableRows`, with the same persisted synthetic rows under `TZ=UTC` and `TZ=Asia/Ho_Chi_Minh`; outputs identical.

- Monday `2026-09-07` populated: one Monday row.
- Wednesday no-match: zero rows.
- Clear reset: three rows in week `2026-09-07` through `2026-09-13`.
- Cross-year Monday `2026-12-28`: one row.
- Sunday `2027-01-03`: one row, same cross-year week.
- Clear cross-year: two rows (`2026-12-28`, `2027-01-03`).
- Week options: `Tuần 37 ♦ 2026 (07/09 - 13/09)` and `Tuần 53 ♦ 2026 (28/12 - 03/01)`.

## Boundary

This proves date-domain helper behavior and timezone stability only. It does not prove browser/UI acceptance, reference parity, visual parity, API persistence, or production behavior; no browser or DB write was performed.
