# CEDU-CRM-FIN-UI-002 — local independent QA (2026-11-06)

## Scope and runtime

Read-only browser QA against current HEAD `d12f375812b6b52493c35772c51419ba34fd0f7c`. Disposable runtime `127.0.0.1:19040`, SQLite `/tmp/cedu-crm-fin-20261106-a.sqlite3`, Playwright 1.63.0 with Chrome for Testing, viewport `1440x900`. No source edits, reference writes, or production data.

Source hashes: `static/app.js` `84923c34c69c035e96ae425b5bb6c697fe17d9a4d7aef022d596d6466717e302`; `app.py` `280586a60b7376f9f90de3fb2e4ce046784014f6c9a60843601aec59eaead120`.

## Route matrix

| ID | Route | DOM/API facts | Result |
|---|---|---|---|
| CRM-01 | `/crm/potential/index` | Title `Khách hàng tiềm năng`; search `#potential-query`; owner/assistant selects; filter/clear controls; table with 10 rendered rows and 46-item total; `/api/potential-customers` and `/api/screen-specs` HTTP 200. | PASS bounded shell/renderer |
| CRM-02 | `/crm/potential/appointment` | Title `Lịch hẹn khách hàng`; query/date/status/owner/action controls; export `#export-care-appointments`; empty state `0 mục` / `Chưa có dữ liệu`; `/api/care-appointments?scope=crm` and screen spec HTTP 200. | PASS empty-state/API |
| FIN-01 | `/finance/bill/index` | Title `Hóa đơn`; query, creator, date range, branch, employee, status controls; `#finance-bill-filter-clear`; summary `70` invoices; table 10 rows; `/api/finance/bills` and screen spec HTTP 200. | PASS bounded shell/renderer |
| FIN-02 | `/finance/revenue` | Revenue list with 4 rows; `#add-finance-revenue` create action; row action menus; `/api/finance/revenues` and screen spec HTTP 200. | PASS bounded shell/renderer |
| SALE-01 | `/sale/contract` | Title `Hợp đồng khóa học`; 20+ filter controls including text date inputs; table 10 rows / 86 items; `/api/finance/contracts`, summary, courses and screen spec HTTP 200. | PASS bounded shell/renderer |
| SUR-01 | `/survey` | Title `Danh sách khảo sát`; tabs/actions `#survey-create`, `#survey-statistics`, `#survey-results`; search and page-size select; one rendered survey row; `/api/surveys` and screen spec HTTP 200. | PASS bounded shell/renderer |

## FACT observations

- Authenticated local admin session established; `/api/auth/me` HTTP 200.
- All six target routes rendered without a route-level HTTP failure.
- Target APIs and route screen-spec APIs returned HTTP 200 in the captured run.
- CRM appointment truthfully rendered an empty state from an empty API array.
- Finance bill and sale contract rendered non-empty tables and summary values from local seeded SQLite data.
- Survey rendered a draft survey row and zero completion/sent/recipient counts.

## UNKNOWN / limits

- Search/filter/reset, modal focus/close, export/status mutation, and DB read-back were not promoted to VERIFIED in this run. The first interaction harness exceeded its bounded execution window while waiting on route action behavior; no mutation was performed and no source change was made.
- No conclusion about reference parity, visual pixel parity, or untested role permissions.
- No create/edit/delete, status change, export download, or external side effect executed.

## Evidence

Primary route capture was produced by an isolated Playwright run over all six routes. Screenshots were written under `/tmp/cedu-*.png` only for local inspection and are not treated as handoff evidence because they were not scrubbed or hashed into the repository evidence set.

Verdict: `PARTIAL / UNKNOWN_INTERACTION_COVERAGE`.
