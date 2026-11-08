# Training report lane — 2026-11-08

Run: `run_bf152f4f7779`  
Scope: `static/modules/report_training.js` plus focused tests/report only.

## Source evidence

- Comparison inventory: `plans/center-edu-rebuild-20261030/supervision-20261103/evidence/visual/claude-compare-1843/INDEX.md`.
- Supplied comparison images opened: `cmp_report_training_class_v2.png`, `cmp_report_training_homework_ratio_index.png`, `cmp_report_training_allocation_student_index.png`, `cmp_report_training_due_date_student.png`.
- Route specs: `screen_specs/reference-screen-specs.json` confirms observed controls, including repeated `Chọn khóa học`, `Tháng 1`, and `10 20 50` selectors.
- Local API projection: `modules/report_training.py` has source-backed joins for class v2 and homework ratio; allocation/due-date use enrollment joins. Persisted row-count differences (demo/build 10/2, 7/10, and 15/10) remain UNKNOWN; no rows fabricated.

## Change

Exported `TRAINING_AUTO_FILTER_ROUTES` and applied it to the five observed update/change-driven training report screens. Homework ratio and due-date now retain observed auto-filter behavior, avoiding generic `Lọc`/`Xóa lọc` controls; duplicate labels/options remain unchanged.

## Verification

- `node --check static/modules/report_training.js` — PASS.
- `node --test tests/test_report_table.mjs` — PASS (8 tests).
- `node --test tests/report-pagination-contracts.mjs` — PASS.
- `git diff --check` — PASS.
- Browser host unavailable (`Browsers: Error: The browser access host is unavailable`); no before/after screenshots captured in this lane. Existing supplied comparison images are reference inputs only.

## Limits

Authenticated reference/private API, RBAC, production persistence, exact reference row values, and live DOM parity remain UNKNOWN. No app.py, static/app.js, shared CSS, finance modules, or foreign files changed.
