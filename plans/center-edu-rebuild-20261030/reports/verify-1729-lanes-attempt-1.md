# VERIFY report — three Center EDU 1729 repair lanes

Run: `run_bf152f4f7779`  
Role: VERIFY  
Workspace: `verify-1729-lanes`  
Date: 2026-11-08

## Limitations first

FACT: Verification used a fresh child checkout and `git fetch origin`; no product, test, evidence, database, credential, merge, cherry-pick, or push operation was performed.  
UNKNOWN: Browser host, reference screenshots, live API persistence, RBAC, and production parity. No browser claim is promoted from builder reports or checked-in visual artifacts.  
UNKNOWN: No authoritative capacity evidence was found for due-date 15, finance/CRM capacities, or any unproven route; these remain unchanged/UNKNOWN.

## Acceptance

| ID | Result | Evidence |
|---|---|---|
| A1 | PASS (source/hash bounded) | `efc1a5f97193d9026038e67245f91aa01ca04a3f` resolves exactly to `origin/NamAIEngineer/build-tenant-finance-1729`; parent `200ae1b886414f896b12a1be065801dd067d5511`. `report_finance.js` reads API `payload.summary` first, then only named numeric row aliases; absent/ambiguous values render `—`. Tenant lane report states catalog-backed, fail-closed behavior. |
| A2 | PASS (source/hash bounded) | `735a2d35b7a93fc682a06adb2b1f0d4489d6f1e1` and `2eea6d8f5f03344277814c2259572c2332018183` resolve exactly to `origin/NamAIEngineer/build-controls-1729`; ancestry is `200ae1b...` then `735a2d...`. `app.js` bypasses generic normalization for `/center/student/index`; class empty multi-select selects the source option with value `''` (Tất cả), while compact controls remain route-owned. |
| A3 | PASS (source/hash bounded) | `b89a3cbc5c19d0363dcb528e05f3c6448bca49e3` resolves exactly to `origin/NamAIEngineer/build-pagination-textarea-1729`, parent `56058e1a659a7abbc399d9467927d59cdffbe7b6`. Allocation student/hours page sizes are 20; other configured training pages remain 10; due-date/finance/CRM capacities remain untouched. `static/app.css` owns `textarea` rule with `resize: vertical`, width bounds, and `box-sizing: border-box`. |
| V1 | PASS | Exact diffs/parents/remote refs inspected. Node syntax, focused Node/Python tests, and per-commit `git diff --check` passed. |
| V2 | PASS (bounded) | Builder reports and source were reread. Visual/browser/reference/live claims remain UNKNOWN as required. |

## Exact refs and ancestry

- `origin/NamAIEngineer/build-tenant-finance-1729` = `efc1a5f97193d9026038e67245f91aa01ca04a3f`; parent `200ae1b886414f896b12a1be065801dd067d5511`.
- `origin/NamAIEngineer/build-controls-1729` = `2eea6d8f5f03344277814c2259572c2332018183`; lane commits: `735a2d35b7a93fc682a06adb2b1f0d4489d6f1e1` (parent `200ae1b...`) then `2eea6d8...` (parent `735a2d...`).
- `origin/NamAIEngineer/build-pagination-textarea-1729` = `b89a3cbc5c19d0363dcb528e05f3c6448bca49e3`; parent `56058e1a659a7abbc399d9467927d59cdffbe7b6`.

## Checks

- `node --check static/modules/report_finance.js` PASS
- `node --check static/app.js` PASS
- `node --check static/modules/training_routes.js` PASS
- `node --check static/modules/report_training.js` PASS
- `node --test tests/test_report_table.mjs tests/test_report_finance_crm_controls.mjs` PASS (8/8)
- `python3 -m unittest tests.test_app_normalizer_guard tests.test_training_projection_correction -v` PASS (7/7)
- `git diff --check efc1a5f^ efc1a5f` PASS
- `git diff --check 735a2d3^ 2eea6d8` PASS
- `git diff --check b89a3cb^ b89a3cb` PASS

## Concerns

INFERENCE: Finance row-alias fallback is bounded by explicit numeric aliases, but semantic equivalence of backend fields is not independently proven; only API summary or unambiguous loaded fields are accepted by source behavior.  
UNKNOWN: Browser DOM geometry/action behavior and reference parity. Builder-reported screenshots/DOM artifacts are not independent live proof.

Status: DONE_WITH_CONCERNS (A1 PASS, A2 PASS, A3 PASS; V1 PASS; V2 PASS bounded; browser/reference/live UNKNOWN)
