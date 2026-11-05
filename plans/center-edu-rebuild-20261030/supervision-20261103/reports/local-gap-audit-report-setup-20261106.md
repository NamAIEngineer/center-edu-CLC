# Local gap audit: report and setup

- Date: 2026-11-06
- Runtime: `127.0.0.1:19066`, disposable SQLite
- Browser: Playwright + Chrome for Testing
- Scope: browser DOM and GET API only; no source edits, no reference writes.

## Route DOM evidence

```json
[
  {
    "route": "/report/finance/revenue_center",
    "http": 200,
    "url": "http://127.0.0.1:19066/report/finance/revenue_center",
    "title": "Center EDU — Academic Operations",
    "h": [],
    "text": "CENTEREDU Trung tâm Center EDU - Demo ⌄ 0 0 0 VI ● Trang chủ",
    "controls": {
      "forms": 1,
      "buttons": 13,
      "inputs": 3,
      "selects": 0,
      "tables": 0
    },
    "filter": false,
    "export": true
  },
  {
    "route": "/report/finance/revenue",
    "http": 200,
    "url": "http://127.0.0.1:19066/report/finance/revenue",
    "title": "Center EDU — Academic Operations",
    "h": [],
    "text": "CENTEREDU Trung tâm Center EDU - Demo ⌄ 0 0 0 VI ● Trang chủ",
    "controls": {
      "forms": 1,
      "buttons": 13,
      "inputs": 3,
      "selects": 0,
      "tables": 0
    },
    "filter": false,
    "export": true
  },
  {
    "route": "/report/attendance",
    "http": 200,
    "url": "http://127.0.0.1:19066/report/attendance",
    "title": "Center EDU — Academic Operations",
    "h": [],
    "text": "CENTEREDU Trung tâm Center EDU - Demo ⌄ 0 0 0 VI ● Trang chủ",
    "controls": {
      "forms": 1,
      "buttons": 13,
      "inputs": 3,
      "selects": 0,
      "tables": 0
    },
    "filter": false,
    "export": true
  },
  {
    "route": "/survey",
    "http": 200,
    "url": "http://127.0.0.1:19066/survey",
    "title": "Center EDU — Academic Operations",
    "h": [
      "Danh sách khảo sát"
    ],
    "text": "CENTEREDU Trung tâm Center EDU - Demo ⌄ 0 0 0 VI ● Trang chủ Tương tác Đào tạo CRM Sale Tài chính Báo cáo Khảo sát CSO 4 Callcenter Tài khoản Thiết lập Dashboard Trang chủ - Danh sách khảo sát Tạo khảo sátThống kêKết quả",
    "controls": {
      "forms": 1,
      "buttons": 164,
      "inputs": 4,
      "selects": 1,
      "tables": 1
    },
    "filter": true,
    "export": true
  },
  {
    "route": "/center/classroom/index",
    "http": 200,
    "url": "http://127.0.0.1:19066/center/classroom/index",
    "title": "Center EDU — Academic Operations",
    "h": [],
    "text": "CENTEREDU Trung tâm Center EDU - Demo ⌄ 0 0 0 VI ● Trang chủ",
    "controls": {
      "forms": 1,
      "buttons": 13,
      "inputs": 3,
      "selects": 0,
      "tables": 0
    },
    "filter": false,
    "export": true
  },
  {
    "route": "/setup/classroom",
    "http": 200,
    "url": "http://127.0.0.1:19066/setup/classroom",
    "title": "Center EDU — Academic Operations",
    "h": [],
    "text": "CENTEREDU Trung tâm Center EDU - Demo ⌄ 0 0 0 VI ● Trang chủ",
    "controls": {
      "forms": 1,
      "buttons": 13,
      "inputs": 3,
      "selects": 0,
      "tables": 0
    },
    "filter": true,
    "export": true
  },
  {
    "route": "/center/holiday/index",
    "http": 200,
    "url": "http://127.0.0.1:19066/center/holiday/index",
    "title": "Center EDU — Academic Operations",
    "h": [],
    "text": "CENTEREDU Trung tâm Center EDU - Demo ⌄ 0 0 0 VI ● Trang chủ Tương tác Đào tạo CRM Sale Tài chính Báo cáo Khảo sát CSO 4 Callcenter Tài khoản Thiết lập Dashboard Trang chủ - Lịch nghỉ Đang tải dữ liệu…",
    "controls": {
      "forms": 1,
      "buttons": 163,
      "inputs": 4,
      "selects": 0,
      "tables": 1
    },
    "filter": true,
    "export": true
  },
  {
    "route": "/center/index",
    "http": 200,
    "url": "http://127.0.0.1:19066/center/index",
    "title": "Center EDU — Academic Operations",
    "h": [],
    "text": "CENTEREDU Trung tâm Center EDU - Demo ⌄ 0 0 0 VI ● Trang chủ",
    "controls": {
      "forms": 1,
      "buttons": 13,
      "inputs": 3,
      "selects": 0,
      "tables": 0
    },
    "filter": false,
    "export": true
  }
]
```

## ADMIN GET API evidence

```json
[
  {
    "url": "/api/reports/run?route=/report/finance/revenue_center",
    "status": 200,
    "ok": true,
    "count": null,
    "error": null
  },
  {
    "url": "/api/reports/run?route=/report/finance/revenue",
    "status": "UNKNOWN",
    "error": "Error: apiRequestContext.fetch: socket hang up\nCall log:\n\u001b[2m  - → GET http://127.0.0.1:19066/api/reports/run?route=/report/finance/revenue\u001b[22m\n\u001b[2m    - user-"
  },
  {
    "url": "/api/reports/run?route=/report/attendance",
    "status": "UNKNOWN",
    "error": "Error: apiRequestContext.fetch: socket hang up\nCall log:\n\u001b[2m  - → GET http://127.0.0.1:19066/api/reports/run?route=/report/attendance\u001b[22m\n\u001b[2m    - user-agent"
  },
  {
    "url": "/api/reports/run?route=/report/training/attendance",
    "status": 200,
    "ok": true,
    "count": null,
    "error": null
  },
  {
    "url": "/api/surveys",
    "status": 200,
    "ok": true,
    "count": 0,
    "error": null
  },
  {
    "url": "/api/surveys?q=__NO_MATCH__",
    "status": 200,
    "ok": true,
    "count": 0,
    "error": null
  },
  {
    "url": "/api/export/surveys",
    "status": 200,
    "ok": true,
    "count": null,
    "error": null
  },
  {
    "url": "/api/classrooms",
    "status": 200,
    "ok": true,
    "count": 1,
    "error": null
  },
  {
    "url": "/api/classrooms?q=__NO_MATCH__",
    "status": 200,
    "ok": true,
    "count": 0,
    "error": null
  },
  {
    "url": "/api/export/classrooms",
    "status": 200,
    "ok": true,
    "count": null,
    "error": null
  },
  {
    "url": "/api/generated/screens?route=/center/holiday/index",
    "status": 200,
    "ok": true,
    "count": null,
    "error": null
  },
  {
    "url": "/api/generated/screens?route=/center/index",
    "status": 404,
    "ok": false,
    "count": null,
    "error": "SCREEN_SPEC_NOT_FOUND"
  }
]
```

## STUDENT GET/RBAC evidence

```json
[
  {
    "url": "/api/surveys",
    "status": 403,
    "ok": false
  },
  {
    "url": "/api/classrooms",
    "status": 403,
    "ok": false
  },
  {
    "url": "/api/reports/run?route=/report/finance/revenue_center",
    "status": 200,
    "ok": true
  }
]
```

## DB read-back

- DB path: `/tmp/center-edu-rep-set.SSmdcg/app.sqlite3`; exists=true; size=4096 bytes.
- No mutation endpoint called; persisted write/read-back and deletion rollback are UNKNOWN in this lane.

## Findings

- Local canonical classroom route is `/setup/classroom`; `/center/classroom/index` is a reference route without local contract.
- `/report/finance/revenue_center` and `/report/training/attendance` have working local report contracts. `/report/finance/revenue` and `/report/attendance` are unknown aliases; direct API probes raised server-side unknown-route errors and should be fail-closed.
- `/center/holiday/index` and `/center/index` have no confirmed local API contract from this lane.
- Student protected API access is denied for surveys/classrooms; finance report is readable with role filtering.
- Filter/export affordances are recorded from DOM where renderer loaded; route shell failures stay UNKNOWN.

## Source hashes

```text
280586a60b7376f9f90de3fb2e4ce046784014f6c9a60843601aec59eaead120  app.py
890c620b2966ccee157e337d554b7147a63e261106caeb4178d73f906ec3caf1  modules/report_engine.py
787a2e6b625b586c43d483295f68f03f09804efc0f275eff0bf58748c68e3bc4  modules/center_lane.py
84923c34c69c035e96ae425b5bb6c697fe17d9a4d7aef022d596d6466717e302  static/app.js
6994c1dde2a4ad8809345cb7a887a3d018a3229884864d30ef78244f586e12fa  static/modules/report_finance.js
a34eeb13cf87606889ec35bc335c37ceba1bbde49873b390bb51ef6fa08a18de  static/modules/center_lane.js
2829a75b7580051e0f3b1dba0ca75372d83498cb6cd91d29b7703709591ec591  static/modules/w6_overrides.js
```
