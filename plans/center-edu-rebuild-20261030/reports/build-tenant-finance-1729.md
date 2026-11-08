# BUILD tenant/finance 1729

Status: DONE_WITH_CONCERNS (local source/tests PASS; reference/live browser parity UNKNOWN)

FACT: `static/modules/w6_screen_utils.js` keeps tenant switches fail-closed: catalog rows are the source of report entries; duplicate titles, unreadable settings, read-only state, and the unsupported master bulk switch remain disabled. Existing persisted `enabled` values alone can produce the green `#2fbda5` state; no records are fabricated.

FACT: `static/modules/report_finance.js` now derives debt/student-finance summary values from API `summary` first, then only unambiguous numeric row fields (`total_amount`, `paid_amount`, `debt_amount`, refund/wallet aliases, student IDs/names). Missing values remain `—`; numeric values use `vi-VN` formatting. Existing payment/status filters, Excel, and green refresh button are retained.

FACT: pagination continues to use observed filter options only. No default page size was introduced for debt/student_finance because this checkout has no authoritative observed capacity metadata for those routes; unproven routes retain all rows. Payload pagination remains supported when supplied.

Validation: `node --check static/modules/report_finance.js`; `node --test tests/test_report_table.mjs tests/test_report_finance_crm_controls.mjs` (8 tests PASS). Tenant desktop/mobile DOM artifacts exist at `plans/center-edu-rebuild-20261030/evidence/visual/tenant-config-w-a-20261108/`, but they are source/runtime evidence, not reference/live parity.

UNKNOWN: browser host/reference screenshot, live API persistence, RBAC, and production parity. Backend and shared shell were outside allowed scope.
