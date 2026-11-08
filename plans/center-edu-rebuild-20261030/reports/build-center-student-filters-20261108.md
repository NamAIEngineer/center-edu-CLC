# Build report: `/center/student/index` filter contract

Status: DONE_WITH_CONCERNS

Scope: run `run_bf152f4f7779`, builder lane. Target route only. Preserved route columns/actions, tenant/finance changes, `static/app.js`, shared CSS, and `app.py`.

FACT: `plans/center-edu-rebuild-20261030/supervision-20261103/MASTER_DEFECTS_claude_1729.md` records one observed defect for `/center/student/index`: filter control overflow (`CTRL_OVERFLOW=4`). Existing route-owned renderer in `static/app.js` already provides compact multi-select wrappers; this change makes the owning `static/modules/center_lane.js` metadata truthful and explicit by marking the three observed multi-select controls (`Chọn trạng thái`, `Chọn lớp học`, `Nguồn`) and preserving their observed Vietnamese options/placeholders.

FACT: Added exported immutable `STUDENT_FILTERS` contract. `/center/student/index` now references it. No rows, status mappings, API parameters, or renderer behavior were invented or changed.

FACT: Added `tests/test_center_student_filters.mjs`, asserting the three compact multi-select definitions, exact observed options/placeholders, and page-size placeholder.

Validation:

- `node --check static/modules/center_lane.js` PASS.
- `node --test tests/test_center_student_filters.mjs` PASS (1 test).
- `git diff --check` PASS.

Hashes:

- Target HEAD: `ae3526001774165ef11a7159b13ce7782288aa0f`.
- Current `static/modules/center_lane.js`: `d3088b2de7769a2029270adf9ec1ee0076eb4c69411c3dd9deb453b3fe8d9cdc` (SHA-256).
- Current `tests/test_center_student_filters.mjs`: `128756815ba387dfa2c783421d83981e64c43c1db01676a63a67a72ce5eb8c74` (SHA-256).

Limits: No browser/DOM capture run in this worker. Visual parity, responsive behavior, live API semantics, and reference option provenance remain UNKNOWN beyond the supplied reference inventory/screens and existing route-owned implementation. Working-tree foreign edits remain untouched; no commit/push.
