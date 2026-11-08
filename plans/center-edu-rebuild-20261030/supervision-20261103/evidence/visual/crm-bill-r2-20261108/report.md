# CRM bill visual correction r2

Run: `run_bf152f4f7779`
Route: `/report/crm/bill/index`

Implemented in `static/modules/report_crm_center.js`:
- Restored observed `Người tạo` semantic label for the empty creator select.
- Kept only the observed `Excel` action; removed report/reset buttons for this route.
- Added observed summary block labels (`Đơn vị tiền tệ`, `Đã Đóng`, `Số lượng khách hàng`), displaying `—` until an API summary supplies concrete values.
- Added two-tier invoice header when payload columns include the observed child fields: `Đã Đóng`, `Thời gian đóng`, `Số hóa đơn`, `Hình thức thanh toán`.
- Pagination remains unconfigured/UNKNOWN; no capacity invented.

Evidence:
- Before comparison: `cmp_report_crm_bill_index.png` and `local_report_crm_bill_index.png` under this directory.
- After comparison: `../crm-bill-r2-20261108-after/cmp_report_crm_bill_index.png` and `local_report_crm_bill_index.png`.

Verification: `node --check static/modules/report_crm_center.js`; `node tests/test_report_crm_bill_route.mjs` PASS; local screenshot runner captured 25/25 routes at 1440x900.

Limitations: local API screenshot was authenticated only through disposable local admin flow; reference private API/RBAC and live values remain UNKNOWN. The local payload did not expose a concrete summary, so totals remain `—`; no rows/payment values fabricated.
