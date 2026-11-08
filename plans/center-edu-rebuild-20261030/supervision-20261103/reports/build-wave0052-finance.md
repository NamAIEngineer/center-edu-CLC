# Wave 0052 finance report lane

Owner: finance report lane. Branch: `wave0052-finance`.

## Evidence reviewed

Reviewed `claude-compare-0052/INDEX.md` and both paired images:
- `cmp_report_finance_debt.png`
- `cmp_report_finance_student_finance.png`

The reference shows `Thanh toán` and status controls in the filter area. Current canonical policy already renders these as route filter controls and deliberately removed duplicate header actions; no unsupported header action was restored.

## Change

`summaryValue()` now derives `Tổng nợ xấu` only when rows carry an explicit overdue status and persisted debt amount (`debt_amount`, `amount_due`, or `debt`). Refund and unused-wallet values remain `—` unless the payload supplies explicit numeric fields. No zero defaults, synthetic rows, or guessed pagination were added.

Pagination remains `UNKNOWN`: debt and student-finance route metadata is `observed: false`; the retained 86-row comparison cannot authorize a page size or page count.

## Validation

- `node --check static/modules/report_finance.js` PASS
- `node tests/test_report_finance_crm_controls.mjs` PASS
- `node tests/report-pagination-contracts.mjs` PASS, 8/8
- `node tests/test_report_table.mjs` PASS, 8/8
- `git diff --check` PASS

## Browser attempt

One bounded attempt:
`NODE_PATH=/Users/nam/claude-center-audit/node_modules OUT_DIR=.../evidence/visual/wave0052-finance LOCAL_BASE=http://127.0.0.1:19246 node /Users/nam/claude-center-audit/shot_failing.js`

No route-specific debt/student-finance capture was produced. Fresh DOM/screenshot parity remains `UNKNOWN`; no retry.
