# Independent verifier: final post-push 2026-11-08

Reviewer: independent read-only verifier (`/root/report_verifier`), different from the builders/editors.
Run: `run_bf152f4f7779`.

## Pinned source and remote

- Repository: `/Users/nam/Documents/System-Agentic_AI/products/center-edu-rebuild`
- Branch: `center-edu-rebuild-verified`
- HEAD: `5a28f3524c526c5770d67b4594e0dfaef48f8765`
- `git ls-remote origin refs/heads/center-edu-rebuild-verified`: same SHA.
- Working tree has many pre-existing untracked `plans/` and `tests/` evidence files. No source files were edited by this verification.

SHA-256 at verification time:

| file | SHA-256 |
|---|---|
| `app.py` | `2ac26abff2b2d7a856d509137f156f942675f9b93132f65d218a5e8902802030` |
| `static/modules/report_finance.js` | `eb10872a1c31c547c4d27954e1c0c4f6b88e150e8880a0a98bf4fc927f535b46` |
| `static/modules/report_crm_center.js` | `8c0e704dfd02c54d2731b8f621be0519534402fb6ecfd14f5b2d8b2df1552dd2` |
| `static/modules/training_routes.js` | `bacf787b8a7f57881d2f85d676a9162cffaf3c58bc9cc877a40905b0a4a88349` |

## Checks executed

- `node --check static/modules/report_finance.js static/modules/report_crm_center.js static/modules/training_routes.js static/app.js`: PASS.
- `python3 -m unittest tests/test_training_backlog_regressions.py tests/test_training_projection_correction.py tests/test_training_supervision.py tests/test_training_timetable_lane.py`: **31 tests PASS**.
- `node tests/test_report_table.mjs`: **8 tests PASS**.
- `node tests/test_report_finance_crm_controls.mjs`: PASS.
- `node tests/report-finance-summary-ui-fix.mjs`: PASS.
- `node tests/report-pagination-contracts.mjs`: PASS.
- `node tests/test_report_crm_bill_route.mjs`: PASS.
- `node tests/test_center_student_filters.mjs`: **2 tests PASS**.
- `git diff --check`: PASS.
- `tests/report-filters-followup/check.mjs` was not runnable because the checkout lacks the `playwright` package (`MODULE_NOT_FOUND`).

## Acceptance review

**A1 — DONE_WITH_CONCERNS (source and focused test scope).** `training_seed_value` is module scoped and shared by initial seed and rich-demo backfill. `/training/absent-v2` and `/training/event` route columns/actions remain present in `training_routes.js`; 31 focused Python tests pass. The retained seed report states disposable SQLite backfill produced 12 rows per route with Vietnamese values. No fresh browser replay was run here.

**A2 — DONE_WITH_CONCERNS (source and focused test scope).** `report_crm_center.js` contains the CRM bill route, filter/action placement, Excel export, and pagination integration. CRM bill regression passes. Fresh DOM and visual parity are unavailable in this verifier.

**A3 — DONE_WITH_CONCERNS (source and focused test scope).** Center-student filter contract test passes; no fresh browser screenshot or live interaction was run.

**A4 — DONE_WITH_CONCERNS.** Finance/training report pagination, summary mapping, and control tests pass. Source inspection confirms debt/student-finance route controls and summary rendering. Totals depend on API `payload.summary`; this verifier did not establish live API values or reference parity. Exact reference-vs-local DOM remains UNKNOWN.

**A6 — UNKNOWN for this verifier.** Existing retained visual artifacts were not regenerated or treated as fresh proof after this push. No claim that every builder inspected every assigned screenshot is made here.

**A7 — DONE_WITH_CONCERNS.** This is an independent source/hash/test review after the final remote SHA. The required fresh browser/reference replay could not run because Playwright is unavailable; visual, mobile, private/reference, and full 134-screen parity remain UNKNOWN.

## Source ownership and risk notes

- `app.py` changes are the route-owned seed/backfill helper and training data repair commits; source inspection found no credential or reference mutation logic in the helper.
- Finance and CRM modules contain route-scoped controls. Reference inventory has blank or inconsistent control names on some report selectors; request-name parity is therefore not proven by static tests.
- The reference inventory records English `From date`/`To date` on CRM contract while current product instructions require Vietnamese labels. Current source follows the newer instruction; this evidence conflict remains documented, not silently resolved.
- No fabricated browser receipt, screenshot, or 134/134 claim is made.

## Verdict

`DONE_WITH_CONCERNS` for bounded source, test, and remote-tip verification. Product acceptance remains `PARTIAL / NOT_ACCEPTED` pending a supported fresh browser run with paired desktop/mobile DOM, action, screenshot, reference, and visual checks.
