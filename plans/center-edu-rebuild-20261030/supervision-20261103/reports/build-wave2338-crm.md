# CRM/report lane wave2338

Scope: `/report/crm/bill/index`, contract/customer-care metadata owned by `static/modules/report_crm_center.js`.

Changes:
- CRM bill summary accepts payload aggregates and derives closed amount/customer count only when every returned row has an explicit numeric payment field and explicit customer identity; otherwise preserves `—`.
- Reapplies Excel placement after shared-shell normalization so it remains at the end of the bill filter row.
- Existing source-backed invoice child-column grouping and observed contract status selector retained.

Evidence:
- Fresh bounded shot command: `NODE_PATH=/Users/nam/claude-center-audit/node_modules OUT_DIR=/tmp/wave2338-crm-shot LOCAL_BASE=http://127.0.0.1:18990 node /Users/nam/claude-center-audit/shot_failing.js` completed and produced local bill screenshot. It was a local smoke only; no authenticated reference replay.
- Screenshot: `evidence/visual/wave2338-crm-after/local_report_crm_bill_index.png`
- Screenshot SHA-256: `9075d0a1a97a08be71cdc779c62d84deedc2193472832678b61cd8061e50bd39`
- Source SHA-256: `7492295c512562b11bd901993f8d19d8ff3987d8b96cc59fc20f63a5b586bedd`

Validation:
- `node --check static/modules/report_crm_center.js` PASS
- `node tests/test_report_crm_bill_route.mjs` PASS
- `PYTHONPATH=modules:. python3 -m unittest modules.test_report_crm_center tests.evidence.test_W5_report_crm_center` PASS (11 tests)
- `git diff --check` PASS

Limitations: screenshot is local smoke; fresh reference/private/RBAC/mobile/production parity remains UNKNOWN. No rows or page sizes fabricated. Customer-care pagination unchanged because no source-backed observed page-size metadata exists.
