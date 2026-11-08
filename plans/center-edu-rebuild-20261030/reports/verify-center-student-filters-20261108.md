# Verification report: `/center/student/index` student filters

Status: DONE_WITH_CONCERNS

Scope: independent verification of `run_bf152f4f7779` against target HEAD `ae3526001774165ef11a7159b13ce7782288aa0f` and builder report `plans/center-edu-rebuild-20261030/reports/build-center-student-filters-20261108.md`.

## Findings

- `static/modules/center_lane.js` contains the route-owned exported `STUDENT_FILTERS` metadata and references it from `/center/student/index`.
- Independent import inspection passed: 11 filter entries; three `kind: "multi-select"` entries with exact placeholders `Chọn trạng thái`, `Chọn lớp học`, `Nguồn`; exact Vietnamese options match the builder contract; final page-size placeholder is `Hiển thị 10 25 50 100 bản ghi`.
- Metadata is frozen at the array level and contains no fabricated `api` or `rows` properties. No rows, API parameters, status mappings, or renderer behavior were added.
- Exact diff inspection against HEAD shows the target lane change only in `static/modules/center_lane.js` for this task. `app.py`, `static/app.js`, and shared CSS are unchanged versus HEAD. Existing foreign working-tree edits (`static/modules/report_finance.js` and unrelated untracked files) were left untouched.
- `tests/test_center_student_filters.mjs` is present as an untracked focused regression test; it asserts the compact multi-select metadata, exact options/placeholders, and page-size placeholder.

## Validation

- `node --check static/modules/center_lane.js`: PASS (Node emitted only the existing module-type warning).
- `node --test tests/test_center_student_filters.mjs`: PASS (1 test, 0 failures).
- Independent `node --input-type=module` import/assert inspection: PASS.
- `git diff --check`: PASS.
- No browser, DOM, reference replay, live API, or visual capture run; those remain UNKNOWN.

## Hashes

- Target HEAD: `ae3526001774165ef11a7159b13ce7782288aa0f`.
- `static/modules/center_lane.js`: `d3088b2de7769a2029270adf9ec1ee0076eb4c69411c3dd9deb453b3fe8d9cdc` (SHA-256).
- `tests/test_center_student_filters.mjs`: `128756815ba387dfa2c783421d83981e64c43c1db01676a63a67a72ce5eb8c74` (SHA-256).
- `plans/center-edu-rebuild-20261030/reports/build-center-student-filters-20261108.md`: `1c7f21fe7a67bf690b9b6db2e190be1e92295e3ea23db658f965f5df06779dcc` (SHA-256 at verification input).

## Concerns and limits

Status remains `DONE_WITH_CONCERNS`: browser/DOM and reference provenance are unverified; Node reports a module-type warning; the working tree contains unrelated foreign edits that were not modified.
