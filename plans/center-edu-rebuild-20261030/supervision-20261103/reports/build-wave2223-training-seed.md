# BUILD report: wave 2223 training seed correction

Task: `run_bf152f4f7779` · Acceptance: `A1,A6,A7,C2,C3,C4,C5,V1,V2`

## PREDICT

The generic generated-screen seed path in `app.py` emits `Demo NN` values for route records. Route-owned values must be generated at the seed/backfill boundary, then projected by the renderer without replacing persisted user values.

## FACT

- `app.py` now special-cases `/training/absent-v2` and `/training/event` seed values.
- Absent rows use natural Vietnamese learner names, session/date labels, reasons, and exact statuses: `Chưa phê duyệt`, `Đồng ý`, `Từ chối`, `Hủy`, `Nhận thông tin`.
- Event rows use durable numeric views, content labels, sent ratios, schedule fields, and exact statuses `Đã gửi` / `Chưa gửi`.
- Existing generated rows are repaired only when a generic `Demo NN` marker or generic status is present; non-marker persisted values remain unchanged.
- `training_routes.js` sent-field projection accepts durable count aliases.

## CHECKS

- `node --check static/modules/training_routes.js` PASS.
- `python3 -m unittest tests.test_training_projection_correction tests.test_training_backlog_regressions` PASS (`10` tests).
- `git diff --check` PASS.
- Disposable rich-demo SQLite inspection confirmed route rows contain Vietnamese synthetic values and no affected-row `Demo NN` markers.

## INFERENCE

Root defect was generic screen generator/backfill applying placeholder labels to the two training routes. Fix is at the producing seed/backfill boundary; renderer alias support preserves payload-backed values.

## UNKNOWN

Fresh Playwright 1440x900 screenshots, sanitized DOM hashes, and private reference/RBAC/live parity were not available in this worker lane. No credentials or reference data were accessed.

## CHANGED

- `app.py`
- `static/modules/training_routes.js`
- this report

Status: DONE_WITH_CONCERNS
Summary: Route-owned training seed/backfill now produces natural Vietnamese absent records and durable event metrics/statuses; renderer preserves aliases; focused checks pass.
Concerns/Blockers: Fresh browser PNG/DOM evidence and private/live parity remain UNKNOWN.
