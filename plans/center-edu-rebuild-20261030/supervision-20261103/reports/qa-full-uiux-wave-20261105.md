# QA full UI/UX wave — 2026-11-05

Status: **PARTIAL / NOT_ACCEPTED**. Local synthetic desktop audit executed against current source; authenticated reference, mobile viewport, production runtime and global visual parity remain **UNKNOWN**.

## Evidence

- Disposable runtime: local SQLite under `/tmp/center-edu-qa-20261105-T5YZ` (no reference/customer data). Playwright harness `e2e_ui.js`, desktop `1440x900`; screenshots, downloads and logs copied to `../evidence/qa-full-uiux-wave-20261105/local-e2e-1440x900/`.
- Source hashes: [`source-hashes.sha256`](../evidence/qa-full-uiux-wave-20261105/source-hashes.sha256). Manifest: [`manifest.json`](../evidence/qa-full-uiux-wave-20261105/manifest.json).
- The run opened the ADMIN route inventory through the training, CRM, finance, reports, survey, call-center, student/setup and dashboard groups. It captured screenshots and exercised route navigation, filter/export affordances, modal/form visibility and console listeners. Full four-role completion is **UNKNOWN** because the long run was still progressing when the bounded QA window ended.
- Existing builder verification read-only: training/report lane 35 tests OK; CRM module syntax PASS and hash recorded in `builder-module-behavior-r1-20261105.md`; no source edits made by this worker.

## Findings

| ID | Route/surface | Repro | Expected | Actual | Severity | Owner | File | Evidence | Boundary |
|---|---|---|---|---|---|---|---|---|---|
| QA-UI-001 | All routes / authenticated reference | Open reference session and compare equal state | Same route, roles, data states and visuals | No authenticated reference/browser host available; public/reference parity cannot be exercised | P0 blocker | Coordinator/runtime | N/A | Existing ORCA capability receipts; no new reference capture | **FACT:** local-only run. **UNKNOWN:** reference behavior/parity |
| QA-UI-002 | All routes, mobile shell | Set viewport 390x844; open sidebar, flyouts, modals, tables | No overlap; keyboard/focus usable; horizontal overflow bounded | Mobile run not executed in this pass | P1 | QA/coordinator | `static/app.css`, `static/app.js` | Manifest `mobile: UNKNOWN` | **UNKNOWN**, no visual claim |
| QA-UI-003 | ADMIN route inventory | Navigate rail groups; hover flyout; Escape/backdrop close; open topbar actions | Flyout dismisses, topbar icons route or expose action, modal focus returns | Current shared-shell fixes are present in source; live acceptance after fix not independently completed before cutoff | P1 | Coordinator | `static/app.js` | [`source-hashes.sha256`](../evidence/qa-full-uiux-wave-20261105/source-hashes.sha256) | **FACT:** hash captured. **UNKNOWN:** live visual/keyboard acceptance |
| QA-UI-004 | `/training/timetable`, training reports | Open route; inspect filters/table/empty/error | Observed room headers only; explicit loading/empty/error; sentinel filters ignored | Builder report records these corrections and 35 focused tests pass; screenshot/equal-state reference acceptance remains unknown | P1 | Training builder | `static/modules/training_routes.js`, `report_training.js` | [`builder-training-reports-20261105.md`](builder-training-reports-20261105.md) | **FACT:** source/tests. **UNKNOWN:** private/reference parity |
| QA-UI-005 | `/crm/potential/index` delete/tabs/title | Open potential route; invoke delete; Escape/backdrop/Tab; inspect tabs/title | Accessible dialog, focus trap/restore, correct tablist and route title | Builder report records implementation; live DELETE/backend and visual acceptance not re-run | P1 | CRM builder | `static/modules/crm_routes.js` | [`builder-module-behavior-r1-20261105.md`](builder-module-behavior-r1-20261105.md) | **FACT:** source/hash. **UNKNOWN:** live action response |
| QA-UI-006 | ADMIN local route actions | Open route, filters, exports, forms; inspect console | No dead controls; expected API/status; no console errors | Captures/logs exist for opened ADMIN screens; per-route action completion for all 134 screens and all roles remains UNKNOWN due bounded run | P1 | QA/coordinator | `static/app.js`, module files | `local-e2e-1440x900/` | **FACT:** partial evidence only |
| QA-UI-007 | Loading/empty/error, pagination, headers | Force empty/filter/no-match and inspect table semantics | Explicit states, stable headers/pagination | Existing local contract/tests cover several routes; exhaustive route-by-route DOM/API assertion not completed | P1 | QA/coordinator | module-specific | E2E screenshots/log; prior receipts | **UNKNOWN** where no direct capture |

## Route coverage observed

ADMIN traversal reached dashboard, training routes (`announcement`, `absent-v2`, `event`, `post`, course/class/timetable/attendance/evaluation/tests/homework), CRM/sales/finance routes, reports, survey, call-center, student/setup and training dashboards. Exact per-screen outcome is in the copied E2E artifacts; routes without a direct screenshot/action receipt stay **UNKNOWN**.

## Safety and limitations

No source files edited. No submit/save/delete/import/renew or reference mutation performed. Synthetic local forms were opened read-only; any E2E action that would mutate was not treated as acceptance. HTTP/API/private-role semantics, authenticated reference equal-state, mobile 390x844, browser console in reference, deployment and persistence remain **UNKNOWN**. Do not claim global completion.
