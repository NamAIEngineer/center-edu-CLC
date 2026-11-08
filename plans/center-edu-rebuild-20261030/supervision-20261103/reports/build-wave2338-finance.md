# Wave 2338 finance report lane

Owner: finance report lane. Branch: `wave2338-finance`.

## Changes

- Debt and student finance action order now matches the retained contract: `Excel`, then `Cập nhật dữ liệu`.
- Removed the stray page-header `Thanh toán` / status actions. Payment/status controls remain route filter controls; no duplicate header action is rendered.
- Existing summary mapping remains payload-backed. The adapter exposes persisted `total_amount`, `paid_amount`, `debt_amount`; unsupported refund, bad-debt, and wallet fields remain UNKNOWN (`—`) when absent. No synthetic zeros or rows added.
- Pagination remains UNKNOWN because these routes have no observed/source-backed page metadata; `FINANCE_REPORT_PAGINATION` remains `observed: false`.

## Validation

- `node --check static/modules/report_finance.js` PASS
- `node tests/test_report_finance_crm_controls.mjs` PASS
- `node tests/report-pagination-contracts.mjs` PASS (8/8)
- `node tests/test_report_table.mjs` PASS (8/8)
- `git diff --check` PASS

## Visual attempt

Attempted one bounded capture with `NODE_PATH=/Users/nam/claude-center-audit/node_modules`, `shot_failing.js`, and `LOCAL_BASE=http://127.0.0.1:19246`. The script produced a broad default capture set, but no debt/student-finance pair and no route-specific `claude-compare-2338` directory was available in this worktree. Fresh route-specific visual parity remains UNKNOWN; existing generated files are retained unmodified under `evidence/visual/wave2338-finance/` and are not claimed as debt proof.

Commit: `8d29c99293db68fd782f509f60ef737365eb7c69`
