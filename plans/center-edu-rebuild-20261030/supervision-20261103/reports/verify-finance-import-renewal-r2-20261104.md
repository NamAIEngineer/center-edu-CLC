# Finance importer / renewal verifier R2 — 2026-11-04

Status: **PASS for local read-only contract; production/reference/private semantics UNKNOWN.** Scope limited to `/finance/contract` upload/import preview and renewal UI/API. Disposable SQLite runtime only. No reference mutation, credentials, tokens, external writes, or private CSV used.

## Evidence

- Runtime/API transcript: [http-verification.txt](../evidence/verify-finance-import-renewal-r2-20261104/http-verification.txt)
- UI source/DOM contract check: [ui-test.log](../evidence/verify-finance-import-renewal-r2-20261104/ui-test.log)
- Focused persistence/validation suite: [unit-tests.log](../evidence/verify-finance-import-renewal-r2-20261104/unit-tests.log)
- Inspected source hashes: [source-hashes.sha256](../evidence/verify-finance-import-renewal-r2-20261104/source-hashes.sha256)

## Findings

### Upload/import preview

`GET /api/finance/contract/upload/template` returns HTTP 200 and a UTF-8 CSV with 21 observed Vietnamese headings, heading-only. The private/reference download body remains UNKNOWN. The file control is rendered as `<input type="file" accept=".csv,text/csv">`; file selection calls preview only. Preview maps all 21 columns, displays rows, reports row errors, and returns `mutation:false`.

Validation rejects missing or unknown/duplicate headers, malformed UTF-8, oversized input (>2,000,000 bytes), surplus cells, duplicate contract code within a file, existing contract code, missing required contract/date values, invalid dates, negative/non-integer money, and negative/non-integer session counts. Focused tests: 6/6 pass. Malformed session count (`mười hai`) produced row 2 validation error. Preview left `finance_contracts`, `finance_contract_uploads`, and `finance_contract_upload_rows` unchanged (zero rows).

The save boundary is intentionally fail-closed. `can_commit:false`; UI save button remains disabled even after a valid preview. Direct commit returned HTTP 400 `VALIDATION_ERROR` with three explicit blockers: upload row schema lacks six observed fields, contract schema lacks gross aggregate/start/class persistence, and arithmetic/mapping to existing item/discount/debt fields is unverified. Therefore no hidden write, transaction, batch, or partial row was observed. Invalid commit also leaves zero batch/contract rows. Restart readback remains empty, proving preview does not persist.

### Auth / CSRF / role boundary

Authenticated ADMIN preview succeeded only with CSRF. Removing `X-CSRF-Token` returned HTTP 403 `CSRF_REQUIRED`. STUDENT preview returned HTTP 403 `FORBIDDEN`; STUDENT renewal read returned HTTP 403. TEACHER renewal read returned HTTP 200. Tenant isolation and cross-tenant semantics are UNKNOWN because the local model has no verified multi-tenant fixture or reference contract.

### Renewal panel/form

Static DOM check passed. Renewal route exposes four observed tab labels (including the observed duplicate), semantic `tablist`/`tab`/`tabpanel`, active-panel switching, and a class selector (`data-contract-extension-class`). API `GET /api/finance/contract/get_extension_contract` returns a local synthetic class list with `data_status=LOCAL_SYNTHETIC`. No downstream renewal form, amount calculation, submit action, or mutation is wired; `actions=[]`, `downstream=UNKNOWN_REFERENCE_RENEWAL_RULES`. This is correctly fail-closed. Production renewal rules, approval semantics, and tenant scope remain UNKNOWN.

### Browser/visual/network limits

Source-level DOM assertions and HTTP responses were captured. No installed browser/visual automation was available in this worker shell, so screenshot, live browser network waterfall, and production visual parity are UNKNOWN. HTTP status/JSON evidence is local synthetic runtime evidence only.

## Inspected files

`app.py`, `modules/finance_contract.py`, `static/modules/finance_contract.js`, `static/app.css`, `tests/test_finance_contract_supervision.py`, `tests/evidence/test_finance_contract_ui.mjs`.

## Verification commands

- `PYTHONPATH=. python3 -m unittest tests.test_finance_contract_supervision -v` → 6/6 passed.
- `node tests/evidence/test_finance_contract_ui.mjs` → `Finance contract UI mapping/tabs PASS`.
- Disposable HTTP script exercised template, preview, commit, renewal, CSRF, and role responses; transcript in evidence.

## Remaining UNKNOWN / not proven

Reference/private importer semantics, production persistence, tenant isolation, real browser screenshot/network capture, actual commit capability, renewal submission/accounting/approval behavior, and visual parity are UNKNOWN. Do not enable import commit or invent mappings until exact field persistence and reference approval evidence exists.
