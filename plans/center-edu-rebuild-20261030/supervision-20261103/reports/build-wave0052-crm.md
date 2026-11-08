# Wave 0052 CRM/report lane

Read reference comparison INDEX and CRM bill/contract/customer-care captures before editing.

Changes in `static/modules/report_crm_center.js`:
- Bill, contract, and customer-care routes keep Excel in the filter row; shared-shell normalization moves it to the row end.
- Excel uses the observed turquoise `#2bbbad` styling on these route-specific controls.
- Bill summary remains source-backed, deriving closed amount/customer count only from explicit payload row fields when complete.
- Existing invoice child columns/grouping and contract status selector preserved. No pagination or rows added without route metadata/source evidence.

Validation:
- `node --check static/modules/report_crm_center.js` PASS
- `node tests/test_report_crm_bill_route.mjs` PASS
- `PYTHONPATH=modules:. python3 -m unittest modules.test_report_crm_center tests.evidence.test_W5_report_crm_center` PASS (11 tests)
- `git diff --check` PASS
- Bounded shot command completed: 18/25 artifacts at `/tmp/wave0052-crm-shot-1794160801`; local bill screenshot copied to `evidence/visual/wave0052-crm-after/local_report_crm_bill_index.png`.

Hashes:
- screenshot SHA-256 `e25515189c9d819eee071ca115a406b386a93f467f618389da45c906784803fd`
- source SHA-256 `ed786ef58165a51b2f20bd019bf6645a6c77e834395796bd401cb9ede52208f8`

Reference/private/mobile/RBAC/production parity remains UNKNOWN. No row padding or fabricated statuses.
