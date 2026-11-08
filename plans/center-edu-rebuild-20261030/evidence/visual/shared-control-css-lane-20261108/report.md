# Shared control CSS lane evidence

Date: 2026-11-08
Base runtime commit: `bdbb7370e7b2224fd5c6c8aad34c6f15904e262d`
CSS SHA-256 before: `8c61b883f6a66c9f22b0fe977ef8666350422a4e1b2c2c80187bd13b8489b807`
CSS SHA-256 after: `a2f11f75723bb4ee2de36b89564338ea48472761dbe90520b858e6c4f3993bcf`

## Acceptance results

- **A1 textarea sizing:** PASS. `textarea` is border-box, bounded to its parent, and vertically resizable.
- **A2 filter sizing:** PASS. `.filter-strip` controls have bounded widths and remain within their grid cells at all tested viewports.
- **A3 scroll behavior:** PASS. `.ref-tabs` wrap with no inner horizontal scroll. `.table-wrap` keeps horizontal scrolling and hides vertical overflow; mobile center/student has no nested content scrollbar outside tables.

The regression receipt records 636/636 checks passing after the change. Baseline: 556/636 passed; 80 failures covered 36 filter sizing checks, 20 table-wrap vertical-overflow checks, 16 tab wrapping checks, four textarea sizing checks, and four tab overflow checks. The baseline also showed nested scroll findings on four mobile report routes. `ui_fine` and `ui_sweep` each reported 0/6 screens with issues before and after.

Routes: `/center/student/index`, `/center/upload_address`, `/report/crm/contract/index`, `/report/finance/student_finance`, `/report/center/birth_day/index`, `/setup/daily-evaluation`. Viewports: `1280x900`, `1440x900`, `1920x900`, `390x844`. Before and after receipts and screenshots are in their respective directories. Visual review covered mobile center/student, mobile CRM report filters/tabs, and mobile wide finance table. The wide table remains horizontally scrollable inside its table wrapper.

## Changed selectors

`textarea`; `.filter-strip`; `.filter-strip > *`; filter descendant inputs, selects, textareas, Select2 containers/selections, buttons, and checkbox/radio inputs; `.ref-tabs`; `.ref-tabs .ref-tab`; `.table-wrap`.

## Commands

Runtime servers were already running against disposable SQLite databases: port `19889` served `/private/tmp/cedu-css-before-20261108`, port `19888` served this worktree. `LOCAL_PASS` was supplied through the process environment; no password value is stored in the harnesses or receipts.

```sh
LOCAL_PASS="${LOCAL_PASS:?set locally outside evidence artifacts}" LOCAL_BASE=http://127.0.0.1:19889 CSS_STAGE=before CSS_EVIDENCE_DIR="$PWD/plans/center-edu-rebuild-20261030/evidence/visual/shared-control-css-lane-20261108" CSS_SOURCE_FILE=/private/tmp/cedu-css-before-20261108/static/app.css SOURCE_COMMIT=bdbb7370e7b2224fd5c6c8aad34c6f15904e262d node tests/evidence/test_shared_css_regressions.mjs
LOCAL_PASS="${LOCAL_PASS:?set locally outside evidence artifacts}" LOCAL_BASE=http://127.0.0.1:19888 CSS_STAGE=after CSS_EVIDENCE_DIR="$PWD/plans/center-edu-rebuild-20261030/evidence/visual/shared-control-css-lane-20261108" CSS_SOURCE_FILE="$PWD/static/app.css" SOURCE_COMMIT=bdbb7370e7b2224fd5c6c8aad34c6f15904e262d node tests/evidence/test_shared_css_regressions.mjs
LOCAL_PASS="${LOCAL_PASS:?set locally outside evidence artifacts}" LOCAL_BASE=http://127.0.0.1:19889 CSS_STAGE=before CSS_EVIDENCE_DIR="$PWD/plans/center-edu-rebuild-20261030/evidence/visual/shared-control-css-lane-20261108" node plans/center-edu-rebuild-20261030/evidence/visual/shared-control-css-lane-20261108/harness/ui_fine.js
LOCAL_PASS="${LOCAL_PASS:?set locally outside evidence artifacts}" LOCAL_BASE=http://127.0.0.1:19889 CSS_STAGE=before CSS_EVIDENCE_DIR="$PWD/plans/center-edu-rebuild-20261030/evidence/visual/shared-control-css-lane-20261108" node plans/center-edu-rebuild-20261030/evidence/visual/shared-control-css-lane-20261108/harness/ui_sweep.js
LOCAL_PASS="${LOCAL_PASS:?set locally outside evidence artifacts}" LOCAL_BASE=http://127.0.0.1:19888 CSS_STAGE=after CSS_EVIDENCE_DIR="$PWD/plans/center-edu-rebuild-20261030/evidence/visual/shared-control-css-lane-20261108" node plans/center-edu-rebuild-20261030/evidence/visual/shared-control-css-lane-20261108/harness/ui_fine.js
LOCAL_PASS="${LOCAL_PASS:?set locally outside evidence artifacts}" LOCAL_BASE=http://127.0.0.1:19888 CSS_STAGE=after CSS_EVIDENCE_DIR="$PWD/plans/center-edu-rebuild-20261030/evidence/visual/shared-control-css-lane-20261108" node plans/center-edu-rebuild-20261030/evidence/visual/shared-control-css-lane-20261108/harness/ui_sweep.js
node --check tests/evidence/test_shared_css_regressions.mjs
node --check plans/center-edu-rebuild-20261030/evidence/visual/shared-control-css-lane-20261108/harness/ui_fine.js
node --check plans/center-edu-rebuild-20261030/evidence/visual/shared-control-css-lane-20261108/harness/ui_sweep.js
git diff --check
```

CSS delimiter check: 256 matching brace pairs and 253 matching parenthesis pairs. Regression runs used isolated demo sessions and SQLite data only. They do not establish reference or live parity.
