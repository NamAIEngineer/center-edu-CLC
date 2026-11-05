# VERIFY-REPORT-ALIAS — independent QA (2026-11-06)

## Scope
Fresh disposable local runtime verification of report route aliases and exports against current working tree. No source edits, no reference writes.

- HEAD: `d12f375812b6b52493c35772c51419ba34fd0f7c`
- Runtime: `127.0.0.1:19041`; SQLite `/tmp/report-alias-20261106.sqlite3`; stopped cleanly after capture.
- Source hashes: `modules/report_engine.py` `dac25ba13d55c77b162f7adec9cdc86e66a46ef37f79edd16c9c4eb15c7074f0`; `test_app.py` `400a4052ec6f904b0ea4fdc17b427baad62dc1251bc6b6007dcabd09cb9462c9`.

## FACT results

| Request | Result |
|---|---|
| `GET /api/reports/run?route=/report/finance/revenue` | HTTP 200 JSON; canonical response route `/report/finance/revenue_center`. |
| `GET /api/reports/export?route=/report/finance/revenue` | HTTP 200 `text/csv`; UTF-8 BOM; revenue headers and data present. |
| `GET /api/reports/run?route=/report/attendance` | HTTP 200 JSON; canonical response route `/report/training/attendance`. |
| `GET /api/reports/export?route=/report/attendance` | HTTP 200 `text/csv`; attendance headers and rows present. |
| Canonical `/report/finance/revenue_center` run/export | HTTP 200 JSON / HTTP 200 CSV. |
| Canonical `/report/training/attendance` run/export | HTTP 200 JSON / HTTP 200 CSV. |
| `/report/training` (short route) | FAIL: remote connection closed; server traceback shows `KeyError: unknown report route: /report/training`. |
| Unknown `/report/unknown` | FAIL: remote connection closed; server traceback shows `KeyError: unknown report route: /report/unknown`. |

Captured response sizes: revenue run 2672 bytes, revenue CSV 233 bytes; attendance run 16150 bytes, attendance CSV 3954 bytes.

## Verdict
`PARTIAL / BLOCKED_ERROR_CONTRACT`.

The two requested aliases (`/report/finance/revenue`, `/report/attendance`) and their CSV exports work. Full canonical routes work. Unknown and unsupported short routes still escape the HTTP handler as uncaught `KeyError`, producing socket hangup instead of a structured 404/error response. This is a confirmed server error-contract defect; no repair was made because this task is independent QA only.

## UNKNOWN

Browser UI route checks were not required for API contract verification and were not used to promote any additional claim. No reference parity, role matrix, or mutation behavior was assessed.
