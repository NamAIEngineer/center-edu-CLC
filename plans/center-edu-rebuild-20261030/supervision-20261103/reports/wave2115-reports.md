# BUILD report — finance/training report pagination and semantic gaps

Run: `run_bf152f4f7779`  
Task: `task_b0423a858074`  
Branch: `NamAIEngineer/wave2115-reports`

## 1. Changes

- `static/modules/report_finance.js`: added route-owned header controls observed on `/report/finance/debt` (`Thanh toán`, `Excel`) and `/report/finance/student_finance` (`Thanh toán`, `Tất cả trạng thái học phí`, `Excel`); kept `Cập nhật dữ liệu` in the filter strip without duplicate header actions.
- Finance summaries now keep every value `—` when an empty `NO_DATA` payload contains generic zero defaults. Explicit backend summary fields and numeric row fields remain supported; missing optional fields stay UNKNOWN.
- `tests/test_report_finance_crm_controls.mjs` and `tests/report-finance-summary-ui-fix.mjs`: focused regressions for header controls and truthful empty summaries.
- `evidence/visual/wave2115-reports/`: fresh Playwright 1440x900 screenshots, DOM/payload readbacks, manifest, and SHA-256 receipt.

## 2. Direct evidence

- Fresh disposable runtime: `127.0.0.1:19115`, SQLite `/tmp/wave2115-reports-20261108.sqlite3`, ADMIN login using the local demo contract. No reference account or external write used.
- `manifest.json` records HTTP 200 report payloads and DOM for debt, student finance, training class-v2, due-date, class revenue, sale-team, CRM contract, and customer-care routes.
- Debt/student-finance readbacks expose the observed header controls; both payloads are `data_status: NO_DATA`, rows remain empty, pagination absent, and summary values render `—`.
- Due-date readback keeps the observed `10` selector and pager (`Hiển thị 1 đến 1 của 1 bản ghi`). Training class-v2, class revenue, sale-team, CRM contract, and customer-care rows remain provider-backed; no row padding or inferred capacity added.

## 3. Verification

- `node --check static/modules/report_finance.js` — PASS.
- `node tests/test_report_finance_crm_controls.mjs` — PASS.
- `node tests/report-finance-summary-ui-fix.mjs` — PASS.
- `node tests/report-pagination-contracts.mjs` — PASS.
- `node tests/test_report_table.mjs` — PASS (8/8).
- `git diff --check` — PASS.
- Foreign diff scan: only assigned finance module, focused tests, report artifact, and unique evidence directory changed; `report_training.js`, CRM module, app shell, shared CSS, route backends, and seed data unchanged.

## 4. Acceptance map

| ID | Result | Evidence |
|---|---|---|
| A4 | PASS (bounded) | Route-owned controls, backend payload readbacks, focused tests. |
| A6 | PASS (bounded) | Empty `NO_DATA` remains empty/UNKNOWN; no synthetic rows or totals. |
| A7 | PASS (bounded) | Fresh 1440x900 captures and DOM/payload manifest. |
| C2 | PASS | Observed debt/student-finance header controls. |
| C3 | PASS | Due-date selector/pager preserved; unsupported capacities omitted. |
| C4 | PASS | Sale/team/class-v2 and CRM rows are direct API projections only. |
| V1 | PASS | Syntax, focused regressions, table suite, diff check. |

## 5. Status / Summary / Concerns

**Status: DONE_WITH_CONCERNS (bounded local evidence).** Implemented the directly observed finance header and truthful empty-summary gaps; retained route-supported pagination and provider-backed projections. Reference-private semantics, authenticated production parity, RBAC, and row capacity for routes without observed selectors remain UNKNOWN; no commit/push has been performed by this worker yet.
