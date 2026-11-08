# BUILD wave2223 finance reports

## Acceptance

| ID | Result | Evidence |
|---|---|---|
| A4 | PASS | Debt/student-finance actions route Excel + Cập nhật dữ liệu together in filter strip; payment/status remain header controls. |
| A6 | PASS | Summary aliases use payload-backed numeric fields, including source debt/student-finance keys; absent values remain em dash. |
| A7 | PASS | No synthetic row padding or invented pagination; monthly routes render payload rows unchanged. |
| C2 | PASS | Scope limited to finance renderer and focused control test. |
| C3 | PASS | Route-specific control placement preserved; no duplicate header Excel. |
| C4 | PASS | Monthly sale/sale-team projection untouched where source lacks team/target dimensions. |
| C5 | PASS | Pagination remains disabled without observed route configuration. |
| V1 | PASS | `node tests/test_report_finance_crm_controls.mjs`; `node tests/report-finance-summary-ui-fix.mjs`; `node tests/report-pagination-contracts.mjs`. |
| V2 | PASS | `node --check static/modules/report_finance.js`. |

## FACT

- Changed `static/modules/report_finance.js` and `tests/test_report_finance_crm_controls.mjs`.
- Debt/student-finance filter-strip actions now contain `Cập nhật dữ liệu`, `Excel`; header contains payment/status controls only.
- Summary extraction recognizes payload row fields `so_tien_phai_thu`, `a_ong`/`so_tien_a_ong`, `con_no`, `hoan_tra`/`so_tien_hoan_tra`, `chua_dung`; missing fields remain UNKNOWN (`—`).
- Monthly sale and sale-team routes keep source row count and route projection; no six-row padding added.
- JavaScript source SHA-256: `eb10872a1c31c547c4d27954e1c0c4f6b88e150e8880a0a98bf4fc927f535b46`.

## INFERENCE

- Current source adapter emits monthly sale and sale-team through the same grouping path and lacks a distinct team/target contract. Renderer-only changes cannot safely invent those dimensions.

## UNKNOWN

- Assigned comparison PNGs were not present in this isolated child; fresh browser screenshots/DOM hashes and visual parity remain UNKNOWN.
- Reference page capacities for debt/student-finance remain unknown; no pagination was introduced.

## Commit

- Commit: pending coordinator integration.
- Remote SHA: none.

Status: DONE_WITH_CONCERNS
Summary: Finance renderer action placement and source-backed summaries repaired; monthly routes remain truthful without synthetic rows.
Concerns/Blockers: Fresh assigned PNGs and browser visual verification unavailable in child; monthly sale-team source dimension remains UNKNOWN.
