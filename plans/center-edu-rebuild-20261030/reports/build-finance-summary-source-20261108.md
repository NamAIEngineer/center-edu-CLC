# Build finance report summary source — 2026-11-08

Status: DONE_WITH_CONCERNS (source/tests; browser/reference/live UNKNOWN)

FACT: HEAD before edit `8cb16b4b7b4ba60614edd2bb06e3fba9f40cb7ae`.
FACT: Owned source hashes before edit: `modules/report_engine.py` `dac25ba13d55c77b162f7adec9cdc86e66a46ef37f79edd16c9c4eb15c7074f0`; `modules/finance_report_adapter.py` `c5dc1409f06293569a001b7f4bf07a724a1f866703850f76779a57408947a8c3`; `modules/tests/test_finance_report_semantic.py` `e0b83cf83014f8d485ec17bdf594fe1dc5509d0a5`.

## Acceptance

| ID | Result | Evidence |
|---|---|---|
| A1 | PASS | Optional provider summary; persisted `total_amount`, `paid_amount`, `debt_amount`; stable `student_id`/`student_code` count. |
| A2 | PASS | Summary emits no bad-debt/refund/unused-wallet aliases. |
| A3 | PASS (source) | Summary calls uncapped filtered contract relation; row projection limit unchanged. |
| A4 | PASS | Generic providers unchanged; finance fallback remains fail-closed. |
| A5 | PASS | 10 focused tests; compile and diff checks pass. |

INFERENCE: Frontend summary renderer consumes explicit summary keys already present in its contract.
UNKNOWN: Browser, reference, RBAC, live DB, and post-restart behavior were not exercised per constraints.

Commands:
- `python3 -m unittest modules.tests.test_finance_report_semantic modules.tests.test_finance_report_route_gap -v` (10 passed)
- `python3 -m py_compile modules/report_engine.py modules/finance_report_adapter.py`
- `git diff --check`

Changed: `modules/report_engine.py`, `modules/finance_report_adapter.py`, `modules/tests/test_finance_report_semantic.py`, this report.
