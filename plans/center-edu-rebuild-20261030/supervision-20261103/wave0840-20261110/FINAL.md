# Final eight-route handoff — 10 November 2026

Branch: `center-edu-rebuild-verified`. Source checkpoint: `ca62e02d994d77746241d171c25116109b01c5d4`. Local verification: `http://127.0.0.1:19369`, copied isolated fixture DB. Main server `18990` was not restarted or mutated.

Status: the eight requested functional repairs are verified against the latest explicit 08:40 brief. Archived screenshots contradict that brief's tab labels and table shapes. Every paired image preserves the contradiction. This is **not** archived-demo pixel acceptance or `134/134 DONE`.

| Route | Implementation commit | Verified behavior | Final paired image |
| --- | --- | --- | --- |
| `/crm/potential/index` | `b6edd42` | Five requested period/status tabs, seven requested columns; source-backed `/api/potential-customers`; pending selects NEW records | [CRM potential](final-8-route/cmp_crm_potential_index.png) |
| `/sale/potential/index` | `b6edd42` | Same five tabs with `scope=sale`; all nondefault clicks update period query state | [Sale potential](final-8-route/cmp_sale_potential_index.png) |
| `/report/finance/revenue_center` | `42f0981` | Four main tabs navigate to registered report routes; monthly detail has center/team/sale sub-tabs | [Revenue](final-8-route/cmp_report_finance_revenue_center.png) |
| `/report/crm/customer_care_result_by_center` | `f7c64aa` | Three in-place grouping views, five columns; center/sale group persisted customers; team uses explicit memberships only | [Customer care](final-8-route/cmp_report_crm_customer_care_result_by_center.png) |
| `/center/upload_address` | `9326293` | Import history/guide switch visible sections; CSV template download and one-row preview verified | [Upload](final-8-route/cmp_center_upload_address.png) |
| `/report/finance/class_revenue_tracking/index` | `42f0981` | Six requested columns; page one renders 10 of 25 persisted classes; pager retained | [Class revenue](final-8-route/cmp_report_finance_class_revenue_tracking_index.png) |
| `/report/finance/class_revenue_tracking_new/index` | `42f0981` | Same source-backed presentation using this report's actual producer fields | [Class revenue new](final-8-route/cmp_report_finance_class_revenue_tracking_new_index.png) |
| `/callcenter/staff` | `780485b`, `1167464` | One persisted staff row; inline staff filter; five requested statistics columns; counts derive from actual call-history relation | [Callcenter staff](final-8-route/cmp_callcenter_staff.png) |

Final focused browser probe: [independent-probe.json](final-8-route/independent-probe.json). Controller opened all eight final paired images. No console/page errors. All tested nondefault tabs changed URL or visible content. Potential today/week/month retain the same rows because this fixture's creation dates fall on the same day; behavioral tests independently cover date boundaries. The report overview's active “Theo tháng” also maps to monthly center detail.

Data limits: the fixture has no explicit sale-team memberships, so the team view displays `Chưa có dữ liệu nhóm sale.` Staff has no call-history rows, so known counts are zero; a missing ledger remains unknown. Class monetary cells preserve missing values and explicit zeroes; no reference numbers or extra records were fabricated.

## Validation

- Root Node suite: all 13 scripts exit zero; one opt-in normalizer test skipped. [Results](final-checks/node-tests.json).
- Python module suite: 25/25 pass. [Results](final-checks/module-tests.json).
- Application suite: 90 tests; only two existing failures: `test_finance_revenue_controls_keep_query_reset_export_contract`, `test_health_and_public_shell`. [Summary](final-checks/test_app-summary.json).
- Changed-module syntax and `git diff --check`: pass.
- Customer-care browser regression: pass, including active-state restoration, exact headers and truthful missing-team state.
- Eight-route `ui_sweep`: zero issues at [1280](final-checks/ui-sweep-1280/ui-sweep.json), [1440](final-checks/ui-sweep-1440/ui-sweep.json), [1920](final-checks/ui-sweep-1920/ui-sweep.json). [ui_fine](final-checks/ui-fine/ui-fine.json): zero issues.
- Protected `static/app.js`, `static/app.css`, `static/nav-config.js`, `static/index.html`, `app.py`: hashes unchanged from task pin. [Hashes](final-checks/protected-files.json).
- Full 134-route crawler plus focused rechecks: zero combined flags, zero console/page errors, zero `Demo NN` hits. [Combined artifact](final-checks/qa-report-134-combined-mixed-pins.json) explicitly records **mixed working-source pins**, not a same-HEAD full crawl. Its heuristic samples one nonactive tab; it does not establish all-interaction or pixel acceptance.

Extra crawler repair: `3aabdda` restores the export report's active tab and a working import-route click. Timetable repair `d317362` attaches seven persisted session rows to the DOM.

## Prior work remains partial

Checkpoint `ca62e02` preserves previously authorized packet/target/dashboard work. Fresh [paired review](prior-work-checkpoint/README.md) identifies remaining target-control visibility, chart/card structure, layout and metric-scope questions. These routes are **not** marked visually DONE. They remain separate from the eight functional fixes above.

No production deployment, real customer data, shared shell edits or branding copy.
