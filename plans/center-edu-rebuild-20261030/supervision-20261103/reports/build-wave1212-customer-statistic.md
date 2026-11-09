# Build wave1212 C — CRM customer statistic

Acceptance: A-wave1212-C / acceptance A6, A7; route `/report/crm/customer_statistic/index`.

## Evidence

Opened the assigned paired defect image before editing:
[claude-verify-1205 comparison](../evidence/visual/claude-verify-1205/cmp_report_crm_customer_statistic_index.png)

Fresh local capture at 1440x900:
[after screenshot](../evidence/visual/wave1212-customer-statistic-after/local_report_crm_customer_statistic_index.png)
[DOM/header evidence](../evidence/visual/wave1212-customer-statistic-after/dom.json)

The after DOM header has two rows:

```
No. | Nguồn dữ liệu | Tổng | Khách hàng chăm sóc | Khách hàng học thử | Khách hàng test/hẹn test | Khách hàng chăm sóc thành công
Số lượng | Tỉ lệ | Số lượng | Tỉ lệ | Số lượng | Tỉ lệ | Số lượng | Tỉ lệ
```

The after DOM action list contains no `Chạy báo cáo` or `Xóa lọc`. The screenshot was visually inspected after capture. Percentages render with a space before `%` and decimal points (`66.67 %`, `11.11 %` style), matching the reference convention.

SHA-256:

- source `static/modules/report_crm_center.js`: `552283a90aa63135245f73b48c45ead6b74a83754d8b42097e19f253726d8b1a`
- after screenshot: `428b23ff16c3def25276be7a6f89bbc6f0552656ec798795d4fcf1e11550660c`
- after DOM evidence: `e5b60b6f179a3d0822288a4580873d1d7e02e873c96e62c4f5fc2c0bfcd2775a`
- assigned comparison: `075a4b368ee32fa9d6aeab5c790ea2b8f83e7531399644d9a7b2aa809a485705`

Capture command:

```sh
NODE_PATH=/Users/nam/claude-center-audit/node_modules \
LOCAL_BASE=http://127.0.0.1:18990 \
node /tmp/capture_customer_stat.cjs plans/center-edu-rebuild-20261030/supervision-20261103/evidence/visual/wave1212-customer-statistic-after
```

## Changes

- Added route-owned two-tier grouped table markup with four observed groups, each containing `Số lượng` and `Tỉ lệ`.
- Preserved API-backed rows and values; no synthetic rows or labels were added to payload data.
- Rendered percentage values as `number %`, preserving numeric precision to two decimal places.
- Removed generic `Chạy báo cáo` and `Xóa lọc` nodes for this route after the shared render pass, without editing `app.js`.

## Validation

- `node --check static/modules/report_crm_center.js` PASS.
- `node tests/test_report_crm_bill_route.mjs` PASS.
- `node tests/test_report_finance_crm_controls.mjs` PASS.
- `git diff --check` PASS.

Status: DONE_WITH_CONCERNS

Concern: fresh paired reference replay uses the retained assigned reference image; this lane has fresh local DOM/screenshot proof. Reference live authentication and production verification remain outside this lane.
