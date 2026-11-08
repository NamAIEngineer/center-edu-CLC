# Training absent/event visual follow-up — 2026-11-08 v2

Scope: `static/modules/training_routes.js` only.

Reference images reopened: `cmp_training_absent_v2.png`, `cmp_training_event.png` from `claude-compare-1957`. The local captures were also inspected; they were blank white captures, so no pixel parity claim is made.

Changes: route-owned compact geometry for `/training/absent-v2` and `/training/event`; fixed-height filters and comment controls; dense table column widths; compact status chips; absent status/progress summary; camera affordance retained in comment cell. No rows or API data fabricated.

Validation: `node --check static/modules/training_routes.js` PASS; `git diff --check` PASS. Fresh screenshot command was attempted with the installed harness at 1440x900 but ORCA pre-tool routing blocked the HTTP/browser transport for this EDIT_FILE worker (`http unavailable`), so fresh before/after screenshots remain UNKNOWN.

Limitations: browser/live/reference execution unavailable; visual parity remains `UNKNOWN`. Foreign worktree changes were preserved and are not included in this lane.
