# Bounded report pagination follow-up

Run: `run_bf152f4f7779`  
Role: builder  
Branch baseline: `center-edu-rebuild-verified` @ `ae3526001774165ef11a7159b13ce7782288aa0f`

Implemented route-local pagination policy. `/report/training/due_date_student` keeps the retained selector values `10`, `20`, `50` from `course_table_length`; `/report/finance/debt`, `/report/finance/student_finance`, `/report/crm/bill/index`, and `/report/crm/customer_care/index` keep capacity UNKNOWN and render no inferred pager. Finance debt/student-finance now discard generic API pagination hints because retained inventory has no observed capacity selector; no row values, sale-team groups, summary values, shell, `app.py`, or `static/app.js` changed.

Focused regression: `node tests/report-pagination-contracts.mjs` PASS. Existing focused checks also pass: `node tests/test_report_table.mjs`, `node tests/test_report_finance_crm_controls.mjs`, `python3 -m unittest tests.evidence.test_W4_report_training_teacher tests.evidence.test_W5_report_crm_center`; node syntax checks pass for report modules; `git diff --check` PASS.

Source hashes (SHA-256):

| Path | SHA-256 |
|---|---|
| `static/modules/report_finance.js` | `9a9ff05f7d2749ddd6d957d472896d6150108554e35dff8733d4012c4b69ae89` |
| `static/modules/report_table.js` | `d7de95c55c048176e3b1c51d6d9ccbc088bed648727d2f29dfedca3317f23ac1` |
| `static/modules/report_training.js` | `6e36b7dbe53f69f66b0d3a77f6c81dea8f23b832496cf0d157c0aec452206496` |
| `static/modules/report_crm_center.js` | `5f021056a337db0c4d61ef64f298ed1cb29b15cbc7f4b73d7b00124c335fc221` |
| `tests/report-pagination-contracts.mjs` | `9d22907b707658e4d59b218557059d097def103ab8b45c16df11eca006dcc544` |
| `screen_specs/reference-screen-specs.json` | `c1fffd899488e2f1134890cd7d44f6c13104394b99e86da2964563909a0be9f6` |
| `MASTER_DEFECTS_claude_1729.md` | `70b688c7a83a2d07de5443ea3d09648bb0d88f8c0106395b9af83bba0dd181b1` |

Limitations: retained evidence proves controls and selector values only. Reference-private API semantics, role matrix, live parity, row capacity for routes without selectors, and exact finance summary metadata remain UNKNOWN. No commit or push performed; foreign dirty and untracked evidence preserved.
