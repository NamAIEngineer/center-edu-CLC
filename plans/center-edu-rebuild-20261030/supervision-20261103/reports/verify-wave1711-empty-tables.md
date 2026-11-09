# Wave 1711 empty-table route audit

Date: 2026-11-09
HEAD: `a6d9842` (`center-edu-rebuild-verified`)

## Scope

Routes audited:

- `/training/timetable`
- `/crm/target/index`
- `/callcenter/staff`
- `/report/finance/revenue_center/by_month/center/index`
- `/report/finance/revenue_center/by_month/sale_team/index`
- `/report/finance/revenue_center/by_month/sale/index`
- `/report/finance/class_revenue_tracking/index`
- `/report/finance/class_revenue_tracking_new/index`

No changes were made to `static/app.js`, `static/app.css`, `static/nav-config.js`, `index.html`, shared shell, or route source. No rows were invented.

## Findings

| Route | Classification | Evidence |
|---|---|---|
| `/training/timetable` | `DATA_ONLY` in default fixture; `MATCH` renderer contract | `app.py` `timetable()` reads `timetable_sessions` joined to classes/courses; renderer `renderTimetableRoute()` reads `/api/timetable` and renders persisted dates/rooms. Default service DB has 1 persisted session; rich demo has 364. Empty-table crawler result cannot establish a renderer defect. |
| `/crm/target/index` | `UNVERIFIED` / `DATA_ONLY` | Route is W6 generated-screen contract (`modules/center_lane.py`, `app.py::_w6_rows`). Default seed intentionally has no target row; rich demo seeding is route-contract dependent. The renderer preserves an empty state when `records=[]`; no source evidence supports adding target rows. |
| `/callcenter/staff` | `DATA_ONLY` | Route is W6 `callcenter_staff`; `center_lane.py` declares the contract and natural seed. Rich-demo `seed_w6_route()` is opt-in. Default production-shaped DB has no W6 seed rows, so an empty table is expected fixture state. |
| `/report/finance/revenue_center/by_month/center/index` | `DATA_ONLY` | `FinanceReportProvider._monthly(..., "center")` groups persisted `finance_bills`; no bills in default DB, 70 in rich demo. No renderer fallback or fabricated row. |
| `/report/finance/revenue_center/by_month/sale_team/index` | `DATA_ONLY` | Same `_monthly` adapter, grouped by persisted `sales_owner`; default DB has no bills, rich demo has 70 bills. |
| `/report/finance/revenue_center/by_month/sale/index` | `DATA_ONLY` | Same `_monthly` adapter, grouped by persisted `sales_owner`; default DB has no bills, rich demo has 70 bills. |
| `/report/finance/class_revenue_tracking/index` | `DATA_ONLY` | `FinanceReportProvider._class_revenue()` requires persisted `classes`, `courses`, `enrollments`, `finance_contracts`; default DB has one class and no contracts, rich demo has 25 classes and 86 contracts. Adapter returns persisted class aggregates only. |
| `/report/finance/class_revenue_tracking_new/index` | `DATA_ONLY` | Same persisted-source requirements and fail-closed behavior as the base class-revenue route. |

## Runtime source checks

Using an isolated temporary SQLite database:

```text
CENTER_EDU_RICH_DEMO=1:
  timetable_sessions=364
  classes=25
  finance_contracts=86
  finance_bills=70
  monthly center rows=1
  monthly sale_team rows=1
  monthly sale rows=1
  class_revenue rows=25
  timetable API rows=364

without CENTER_EDU_RICH_DEMO:
  timetable_sessions=1
  classes=1
  finance_contracts=0
  finance_bills=0
  monthly center/sale_team/sale rows=0
  class_revenue rows=1
  timetable API rows=1
```

The two datasets explain the crawler's empty states. The rich dataset contains persisted synthetic demo-domain rows; the default dataset is intentionally compact. Adding rows in the renderer or copying reference rows would violate the route ownership and no-fabrication constraints.

## Validation

- `python3` isolated `CenterEduService` source checks: passed.
- `FinanceReportProvider` route calls: passed; output counts above.
- `git diff --check`: not run because source tree was unchanged.
- Fresh browser paired screenshots: `UNKNOWN` in this lane; no browser port/runtime was provided in the worker context.

## Status

`PARTIAL / DATA_ONLY`: no evidenced source defect found. Empty-table flags require a fresh authenticated rich-demo capture to distinguish fixture selection from visual mismatch. No source patch is justified by current evidence.
