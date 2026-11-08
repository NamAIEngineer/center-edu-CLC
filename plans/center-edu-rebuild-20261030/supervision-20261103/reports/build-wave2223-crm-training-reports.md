# BUILD — CRM bill and training report parity corrections

Run: `run_bf152f4f7779`  |  Role: BUILD  |  Status: DONE_WITH_CONCERNS

## PREDICT

Invoice reference requires Excel at the end of the filter row, observed invoice child headers, numeric payload-backed summary values, and no generic duplicate submit/reset controls. Training class pagination must remain source-backed without synthetic rows. Contract/customer-care controls must stay truthful when no observed page-size metadata exists.

## FACT

- `static/modules/report_crm_center.js`: CRM bill Excel now renders after filter fields; generic submit/reset controls are removed on observed auto-filter routes after shell normalization. Existing summary key resolution remains numeric-payload-first with `—` for absent values. Existing invoice child-header grouping and row aliases preserved.
- `static/modules/report_training.js`: existing observed pagination metadata and row-preserving empty behavior unchanged; no fake padding added.
- No shared CSS, app.py, database, training routes, finance module, or unrelated files changed.

## Validation

- `node --check static/modules/report_crm_center.js` PASS
- `node --check static/modules/report_training.js` PASS
- `node tests/test_report_crm_bill_route.mjs` PASS
- `node --test tests/test_report_table.mjs` PASS (8/8)
- `git diff --check` PASS

## Evidence boundaries

Assigned comparison image inspected. Fresh browser/DOM capture unavailable in this lane, so live visual, API, RBAC, persistence, and production evidence remain UNKNOWN. Source and focused tests establish renderer behavior only.

Acceptance: A2/A4/A6/A7/C2/C3/C4/C5/V1/V2 — source/test evidence PASS; browser/reference/live portions UNKNOWN.

Changed files: `static/modules/report_crm_center.js`, this report.
