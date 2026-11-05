# Finance semantic lane report — 2026-11-03

## FACT

- Reference inventory contract: `report_finance_debt` and `report_finance_student_finance` expose separate `Mã hóa đơn` and `Mã hợp đồng` columns (`/Users/nam/claude-center-audit/ref/reference-inventory.json`, slugs `report_finance_debt` and `report_finance_student_finance`).
- Before this lane, `_student_finance()` in `modules/finance_report_adapter.py` explicitly set `invoice_code` to `""` while sourcing rows from `finance_contracts`. This erased a persisted invoice relationship and made the invoice column a placeholder.
- Fix: `_contracts()` now selects the latest persisted `finance_bills.invoice_code` by `contract_code` (date/id descending). If `finance_bills` is absent, it emits `NULL`; `_student_finance()` no longer overwrites the value.
- Focused tests passed: `python3 -m py_compile modules/finance_report_adapter.py modules/tests/test_finance_report_semantic.py`; `python3 -m unittest -q modules.tests.test_finance_report_semantic tests.evidence.test_W5_report_finance_payment` -> `Ran 7 tests ... OK`.

## UNKNOWN

- No visual acceptance, production parity, authenticated reference API, or deployment claim. The reference inventory is structural/observational evidence only.
- No runtime route diff run; this lane stayed source/test bounded.

## Changed files

- `modules/finance_report_adapter.py`
- `modules/tests/test_finance_report_semantic.py`
- This report
