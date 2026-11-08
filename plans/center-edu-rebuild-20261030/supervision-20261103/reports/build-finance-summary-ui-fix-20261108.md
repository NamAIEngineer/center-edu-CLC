# Finance summary UI mapping fix — 2026-11-08

Status: COMPLETE (route-owned, bounded)

Run: `run_bf152f4f7779`
Branch: `center-edu-rebuild-verified`
HEAD before commit: `670a209d8024276e40240d62d9934f6570b94120`

## Change

`static/modules/report_finance.js` now reads backend `payload.summary` keys `total_amount`, `paid_amount`, `debt_amount`, and `student_count` before falling back to row aggregation. Existing label-key summaries remain supported. Missing `bad_debt`, refund, and unused-wallet values remain `null`, rendering as `—` (UNKNOWN). HTML escaping and existing route ownership remain unchanged.

`tests/report-finance-summary-ui-fix.mjs` covers numeric/string backend summary values, student count, UNKNOWN absent optional summaries, and backend-summary precedence over row values.

## File pins

Before:

- `static/modules/report_finance.js`: `cbf839be382c4b9b89d413f59f824ceefd11c7cd3bb531f9ebb798c20b03cf68`
- Existing `tests/test_report_finance_crm_controls.mjs`: `3ce2077e61e9c05b7186da71e3855d579c87ad92dbab5e6fe9f9091e62f947d1`

After:

- `static/modules/report_finance.js`: `970838fff5a4d13d35a6efd004eb6d1110a0da0dbc40188f29265d6dd1fb49a3`
- `tests/report-finance-summary-ui-fix.mjs`: `54f8a18ae0433a891133fee182ad6e1c2681556ca0d7eade9539e6bb3f89c9ac`

## Verification

- `PATH="/usr/local/bin:$PATH" node tests/report-finance-summary-ui-fix.mjs` — PASS (`Finance report summary backend-key mapping PASS`)
- `PATH="/usr/local/bin:$PATH" node tests/test_report_finance_crm_controls.mjs` — PASS (`Report finance/CRM control contracts PASS`)
- `PATH="/usr/local/bin:$PATH" node --check static/modules/report_finance.js` — PASS
- `python3 -m unittest tests.test_finance_contract_supervision tests.evidence.test_W2_finance_lane` — PASS (10 tests)
- `python3 -m py_compile modules/finance*.py modules/report_engine.py` — PASS
- `git diff --check` — PASS

Note: `python3 -m pytest ...` was unavailable because this environment has no `pytest` module; equivalent requested finance tests passed via `unittest` (10 tests).
