# Independent verification — CRM bill report

- **Target:** `run_bf152f4f7779`; commit `5ebe25606f7b5ad2d13db3cb508c404336fa1829`; parent `5ebe256^`.
- **Scope:** read-only independent verification. Source, test, builder report, exact commit diff, and visual artifact paths inspected. No source, commit, push, or foreign-file changes.
- **Result:** **PASS (bounded) / DONE_WITH_CONCERNS**.

## Exact diff review

`git show --stat` reports 3 files, 20 insertions, 2 deletions:

- `static/modules/report_crm_center.js`: bill route actions changed from `['Excel', 'Chọn đối tượng', 'Chọn khóa học']` to `['Excel']`; bill route sets `activeTabIndex = 1`, selecting `Thống kê danh sách hóa đơn` while preserving the shared tab strip.
- `tests/test_report_crm_bill_route.mjs`: regression assertions added for Excel-only action, removal of unsupported actions, invoice tab selection, tab strip, filter strip, and page actions.
- `plans/.../build-report-crm-bill-20261108.md`: builder report added.

The commit diff is narrow and matches the builder report. No unrelated tracked files are in the commit.

## Contract assertions

- Invoice tab label present: `Thống kê danh sách hóa đơn`; selected index is `1` for `/report/crm/bill/index`.
- Excel-only action present for the bill route; `Chọn đối tượng` and `Chọn khóa học` absent from its action list.
- Filters render inside `<form class="filter-strip" data-report-form>`.
- No fabricated summary, totals, headers, or rows observed in the renderer; rows and columns come from the API payload, with an empty-state fallback.
- Pagination capacity remains **UNKNOWN**. The renderer consumes observed page-size metadata when supplied; this verification does not establish the reference pagination contract.

## Validation

- `node --check static/modules/report_crm_center.js` — PASS.
- `node tests/test_report_crm_bill_route.mjs` — PASS (`report crm bill route regression: PASS`).
- `git diff 5ebe256^ 5ebe256 --check` — PASS.

## Artifact integrity

| Artifact | SHA-256 | Bytes | Result |
|---|---|---:|---|
| `static/modules/report_crm_center.js` | `306e70362ca0de866161962387adbdec0702af4977632df73cf531f8632e6ebb` | 23814 | present |
| `tests/test_report_crm_bill_route.mjs` | `50c7b0b72f26d0b4e1424cf3a84bcf4035ac675c0a21a8d7cd975e8b92023655` | 664 | present |
| `build-report-crm-bill-20261108.md` | `978f9ebb039c70f96aee2514d65f9c779e986f59d1fca0e23b388cd9f679d679` | 864 | present |
| `before-reference.png` | `77018c679c16f6b3958a986102c70075c9a88ef6d367b7bf4d348acd1b75147e` | 286635 | present; PNG 2200x765 RGB |
| `after-local.png` | `3ec7d1afead631921a0ec314e91930b9469a9d8d89bb6e56c032e589007c4717` | 155060 | present; PNG 1440x900 RGB |

## Browser limitation / concerns

Fresh browser capture and live DOM/API/reference comparison were unavailable: builder reports Playwright credentials/runtime unavailable, and `after-local.png` is retained local evidence rather than a fresh authenticated capture. Therefore browser visual parity, live API behavior, RBAC, persistence, production state, and pagination semantics remain **UNKNOWN**; this report does not upgrade those claims.
