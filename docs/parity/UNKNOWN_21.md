# Next 21 route/action audit cells

Historical checkpoint: `113/134` routes rendered, `21 UNKNOWN`. This ledger names the next concrete cells to audit. It is an action queue, not a claim that these are the only unresolved cells.

Evidence contract for every cell: local disposable SQLite; login/API status; DOM route render; filter/search/reset; empty/error; row action/modal/export where present; DB read-back after any synthetic write; source hash; separate reference parity `UNKNOWN` unless direct evidence. No reference writes. No shared source edits during QA.

| ID | Route | Focus | Owner | State |
|---|---|---|---|---|
| U01 | `/training/course` | list/search/empty/detail | training lane | UNKNOWN |
| U02 | `/training/class` | list/search/no-match/pagination | training lane | local API pass; DOM UNKNOWN |
| U03 | `/training/timetable` | room/week/filter/export | training lane | local API pass; DOM UNKNOWN |
| U04 | `/training/attendance` | status/date/filter/empty | training lane | local API pass; DOM UNKNOWN |
| U05 | `/training/daily-evaluation-v2` | list/filter/detail/error | training lane | UNKNOWN |
| U06 | `/training/test` | list/filter/export/detail | training lane | UNKNOWN |
| U07 | `/training/homework` | list/filter/action/error | training lane | UNKNOWN |
| U08 | `/training/confirm` | confirmation state/action | training lane | UNKNOWN |
| U09 | `/crm/potential/index` | search/owner/assistant/reset | CRM/finance lane | shell/API pass; interaction UNKNOWN |
| U10 | `/crm/potential/appointment` | empty/filter/export | CRM/finance lane | shell/API pass; interaction UNKNOWN |
| U11 | `/sale/potential/index` | search/filter/action | CRM/finance lane | UNKNOWN |
| U12 | `/sale/contract` | date/filter/summary/reset | CRM/finance lane | shell/API pass; interaction UNKNOWN |
| U13 | `/finance/bill/index` | filter/reset/confirm/edit | CRM/finance lane | shell/API pass; interaction UNKNOWN |
| U14 | `/finance/revenue` | list/create/edit/export | CRM/finance lane | shell/API pass; interaction UNKNOWN |
| U15 | `/finance/transfer/index` | filter/create/update/export | CRM/finance lane | UNKNOWN |
| U16 | `/finance/spend/index` | filter/create/update/export | CRM/finance lane | UNKNOWN |
| U17 | `/finance/assessment` | filter/create/update/export | CRM/finance lane | UNKNOWN |
| U18 | `/finance/reserve` | filter/create/update/export | CRM/finance lane | UNKNOWN |
| U19 | `/survey` | list/filter/create/builder/results | report/setup lane | shell/API pass; interaction UNKNOWN |
| U20 | `/report/finance/revenue_center` | filters/report/export/empty | report/setup lane | API 200; alias/error boundary verified; DOM/action/reference UNKNOWN |
| U21 | `/setup/classroom` | list/create/update/RBAC/reload | report/setup lane | Admin GET/no-match/export 200; writes/DOM parity UNKNOWN |

Current wave receipts:

- Training lane report `local-gap-audit-training-timetable-20261106.md`, SHA `92efe449d29a2b034d1908473548b346f266c1e4105c553f393dd8e27542d613`.
- CRM/finance lane report `local-gap-audit-crm-finance-20261106.md`, SHA `aeec4780ddf3eae7bcadafe84d91f47108bb28caf751262c7c540002d7ba2e50`.
- Report/setup lane remains pending.

Verification rule: `shell/API pass` never upgrades interaction or reference parity. A cell becomes `VERIFIED` only with direct implementation, data, interaction, and relevant UI evidence.

Report/setup receipt: `local-gap-audit-report-setup-20261106.md`, SHA `89b6c40fbe9e566ca3233033a779c73ddb29d2de962d1556a606c66f9abba561`; alias route socket-hangup and missing screen contract remain open.
