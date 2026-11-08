# Finance/report pager and grouping counsel — 2026-11-08

Status: EVIDENCE-ONLY / NOT ACCEPTED FOR ROUTE PARITY

Scope: canonical checkout `center-edu-rebuild`, HEAD `188be041bfe77985b53c656430c35e1240e2be48`, continuing `run_bf152f4f7779`. Read-only review. No source, schema, data, credentials, browser, reference, or existing evidence writes. Reference inventory: `/Users/nam/claude-center-audit/ref/reference-inventory.json`, SHA-256 `b3adeadc39e50b777d687dd4a4744f0038b9819d403abf9d676925593eaf931e`; captured `2026-11-01T16:47:44.892Z`.

## FACT — reference contract

The retained reference inventory records these body-row counts and pager evidence:

| Route | Reference screenshot | Body rows | Pager/default evidence |
|---|---|---:|---|
| `/report/finance/revenue_center/by_month/sale/index` | `screens/082_report_finance_revenue_center_by_month_sale_index.png` | 6 (four retained tables) | no pager recorded |
| `/report/finance/revenue_center/by_month/sale_team/index` | `screens/081_report_finance_revenue_center_by_month_sale_team_index.png` | 6 (four retained tables) | no pager recorded |
| `/report/finance/debt` | `screens/084_report_finance_debt.png` | 18 (four retained tables) | `‹ 1 2 3 4 5 6 ›`; no page-size selector recorded |
| `/report/finance/student_finance` | `screens/085_report_finance_student_finance.png` | 20 (four retained tables) | `‹ 1 2 3 4 5 6 ›`; no page-size selector recorded |
| `/report/crm/bill/index` | `screens/091_report_crm_bill_index.png` | 17 | `‹ 1 2 3 4 ›`; no page-size selector recorded |
| `/report/crm/customer_care/index` | `screens/100_report_crm_customer_care_index.png` | 14 (four retained tables) | `‹ 1 2 3 4 5 ›`; no page-size selector recorded |
| `/report/training/due_date_student` | `screens/070_report_training_due_date_student.png` | 15 | selector `10 20 50`; pager `‹ 1 2 3 ›` |

The two monthly sale routes have materially different reference column contracts. Sale-team starts with `Nhóm sale/Thành viên`, then months and repeated KPI blocks. Sale starts with `Nhân viên sale`, `Tổng chỉ tiêu`, KPI totals, then months and repeated KPI blocks. Reference row counts are observations only; they do not authorize adding rows or copying reference data.

## FACT — current backend grouping and projection

`modules/finance_report_adapter.py:174-180` dispatches both monthly routes to `_monthly(f, "sales_owner")`. `:289-310` groups by the persisted `sales_owner` value, filters `year`, `start_month`, and `end_month` against `finance_bills.invoice_date`, and emits `thang_N`, `doanh_thu_moi`, `doanh_thu_tai_tuc`, `doanh_thu_tam_tinh`, `thuc_thu`, and `so_tien_no`. It does not emit a distinct sale-team dimension, target (`chi_tieu`), bad-debt (`no_xau`), refund (`hoan_tra`), or repeated per-period KPI blocks. The sale-team route therefore receives the same grouping and field set as sale; this is a concrete source-supported contract gap, not a demonstrated row-count bug.

`modules/report_engine.py:218-228` executes the provider, projects only fields declared by `screen_specs/reference-screen-specs.json`, preserves source row count up to the requested limit, and returns no pagination metadata or summary object. `modules/report_engine.py:207-216` leaves absent projected fields `None`; it does not invent KPI values. `modules/finance_report_adapter.py:257` caps bill reads at 500 and `:428` caps contract reads at 500. These caps are source limits; they do not prove reference pagination semantics.

## FACT — current frontend pager behavior

`static/modules/report_table.js:7-10` enables a page-size control only when a filter definition contains an observed length/page-size field. `:26-37` enables a pager without a selector only when API `payload.pagination` supplies `{enabled:true,pageSize}`. `static/modules/report_finance.js:281-302` passes `payload.pagination`, but no current backend path in `ReportEngine.run` produces it. Therefore debt/student-finance currently have no pager unless an unobserved API payload supplies metadata; CRM bill/customer-care renderers pass no route-specific pagination metadata (`static/modules/report_crm_center.js:311-333`), and training due-date uses `TRAINING_REPORT_PAGINATION` only for seven other routes (`static/modules/report_training.js:52-63`), excluding `/report/training/due_date_student`.

Concrete reproduced/source-supported defects:

1. `/report/finance/debt` and `/report/finance/student_finance`: reference shows pager, current route has no observed page-size selector and no backend `pagination` contract. **DEFECT: pager is absent from the source-supported current path.** Supported change: add an explicit route metadata contract only after preserving the observed default page capacity; reference does not establish that capacity, so exact size remains UNKNOWN.
2. `/report/crm/bill/index` and `/report/crm/customer_care/index`: reference shows pagers; current CRM renderer has no `pagination` argument and generic `reportPageSizes` sees no length control in the route filters. **DEFECT: pager is absent.** Supported change: route metadata with an evidence-backed default; exact capacity UNKNOWN.
3. `/report/training/due_date_student`: reference explicitly shows `10/20/50` selector and pager; current route’s filter spec includes `course_table_length` (`screen_specs/reference-screen-specs.json`, route entry) so selector discovery is possible, but `TRAINING_REPORT_PAGINATION` omits this route. If API filters are delivered unchanged, selector-driven paging can work; a deterministic current runtime DOM/API replay was not performed here. **INFERENCE: likely works through observed selector; live DOM proof UNKNOWN.**
4. Monthly sale/sale-team routes: reference has no pager, and current route filter specs contain only year/month/center or year/month/sale filters. No pagination defect is established. Grouping/column contract gap above is concrete.

## FACT — SUMMARY_KEYS audit (introduced by `efc1a5f97193d9026038e67245f91aa01ca04a3f`)

Current aliases are in `static/modules/report_finance.js:83-90`; hash `cbf839be382c4b9b89d413f59f824ceefd11c7cd3bb531f9ebb798c20b03cf68`.

| Summary label | Alias status against produced API fields | Counsel |
|---|---|---|
| `Tổng thu`: `total_revenue`, `total_amount`, `gross_amount`, `revenue`, `tong_thu` | `total_amount` is produced by class-revenue paths; monthly finance rows produce `doanh_thu_tam_tinh`, not these aliases. Others not observed in finance adapter output. | `total_amount` accepted only where that entity actually emits it; monthly mapping UNKNOWN. |
| `Tổng đã đóng`: `total_paid`, `paid_amount`, `paid`, `amount_paid`, `tong_da_dong` | `paid_amount` is produced by `_contracts` and mapped into student-finance rows (`:431-435`). Remaining aliases not observed. | `paid_amount` accepted for debt/student-finance; others UNKNOWN. |
| `Tổng còn nợ`: `total_debt`, `debt_amount`, `debt`, `amount_due`, `tong_con_no` | `debt_amount` is selected from contracts (`:425-429`); `amount_due` is produced for student-finance (`:434`). Remaining aliases not observed. | `debt_amount`/`amount_due` accepted only for those produced entities; others UNKNOWN. |
| `Tổng nợ xấu`: `bad_debt`, `total_bad_debt`, `bad_debt_amount`, `no_xau` | No corresponding produced field in finance adapter monthly/contracts/student-finance output. | UNKNOWN; must remain em dash. |
| `Số tiền hoàn trả`: `total_refund`, `refund_amount`, `refund`, `amount_refunded` | No produced field observed. | UNKNOWN; must remain em dash. |
| `Tiền chưa sử dụng`: `unused_amount`, `unused_balance`, `co_wallet`, `wallet_balance` | No produced field observed. | UNKNOWN; must remain em dash. |

`static/modules/report_finance.js:100-115` sums the first alias with any numeric row values. This is safe only where the alias is entity-produced and additive. It must not be extended to map monthly Vietnamese KPI fields or infer debt/bad-debt/refund semantics.

## INFERENCE / UNKNOWN boundaries

Reference body-row counts vary by retained tenant data and duplicated table captures; they cannot distinguish data variation from pagination or grouping defects. No source evidence proves that six monthly rows is a required current count, nor that debt’s six pages imply a default of 10, 18, or another capacity. Browser/login/reference re-execution was intentionally not performed; current DOM, API payload pagination, RBAC behavior, and post-restart persistence remain UNKNOWN.

## Supported next change

Implement only an evidence-backed pager metadata contract after obtaining a fresh reference/API observation of each default page capacity. For monthly reports, first obtain the real sale-team grouping dimension and KPI/target field contract; do not alias sale-team to `sales_owner` or fill missing KPI blocks from counts. Keep unsupported `SUMMARY_KEYS` aliases UNKNOWN.
