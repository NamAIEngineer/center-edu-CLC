# `/report/crm/bill/index` route lane

- Source/reference inspected: `report_crm_center.js`, comparison `INDEX.md`, `cmp_report_crm_bill_index.png`, reference-screen-specs route contract.
- Fixed observed defects: invoice tab selected with `Thống kê danh sách hóa đơn`; unsupported `Chọn đối tượng` and `Chọn khóa học` header actions removed; retained `Excel`; filters remain in `.filter-strip`.
- No totals/header/row fabrication. Pagination capacity remains UNKNOWN. Same viewport artifacts copied to `evidence/visual/report-crm-bill-20261108/` (`before-reference.png`, `after-local.png`); after screenshot is retained local evidence because Playwright credentials/runtime were unavailable for a fresh capture.
- Validation: `node --check static/modules/report_crm_center.js`; `node tests/test_report_crm_bill_route.mjs`; `git diff --check`.
