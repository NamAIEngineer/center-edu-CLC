# Independent verifier: wave2338 postintegration

Date: 2026-11-08. Reviewer: independent read-only verifier, separate from wave2338 builders. Run: `run_bf152f4f7779`.

## Pin and ownership

- Repository: `/Users/nam/Documents/System-Agentic_AI/products/center-edu-rebuild`
- Branch: `center-edu-rebuild-verified`
- HEAD and remote: `8dbf8de968d50dff15f373dccb3bc0ce85248742`
- Reviewed commits: `957a0a2` training, `f40664c` finance, `48ae99d` finance verification record, `8dbf8de` CRM bill.
- No source edits, commits, pushes, cleanup, or mutation were performed.

Current SHA-256:

| file | SHA-256 |
|---|---|
| `app.py` | `2ac26abff2b2d7a856d509137f156f942675f9b93132f65d218a5e8902802030` |
| `static/modules/report_finance.js` | `67eb3193ba8644253a1f8156459ea078b43a429aef158082f905233f9607a767` |
| `static/modules/report_crm_center.js` | `7492295c512562b11bd901993f8d19d8ff3987d8b96cc59fc20f63a5b586bedd` |
| `static/modules/training_routes.js` | `f074f02e1b2f9a210578f901dab7634b38407ad8225b83da4e6039fbfaee9a22` |
| `static/modules/report_table.js` | `d7de95c55c048176e3b1c51d6d9ccbc088bed648727d2f29dfedca3317f23ac1` |

## Checks

Executed successfully:

- `node --check static/modules/training_routes.js`
- `node --check static/modules/report_finance.js`
- `node --check static/modules/report_crm_center.js`
- `node tests/test_report_finance_crm_controls.mjs` — PASS
- `node tests/report-finance-summary-ui-fix.mjs` — PASS
- `node tests/test_report_crm_bill_route.mjs` — PASS
- `python3 -m unittest tests/test_training_backlog_regressions.py tests/test_training_projection_correction.py tests/test_training_supervision.py tests/test_training_timetable_lane.py` — **31 tests PASS**

Builder retained checks were also read: report table 8/8, report pagination 8/8, CRM/report focused tests PASS, `git diff --check` PASS. These are source/unit checks; they do not establish visual parity.

## Acceptance findings

**A1 — DONE_WITH_CONCERNS.** Training renderer now formats absent rows with student/code/birth date and session/class/date details, event rows with views/content/author/time, status chips, progress aliases, and event delete action. Source and 31 focused tests pass. Builder explicitly reports no screenshot/browser replay. The retained `claude-compare-2338` index still records unresolved row-count and duplicate-filter differences for `/training/absent-v2`, `/training/event`, `/training/class`, and training reports; current postintegration parity is therefore UNKNOWN.

**A2 — DONE_WITH_CONCERNS.** CRM bill summary derives totals only from explicit complete numeric row fields, and Excel is reappended after normalization. CRM bill regression and retained 11-test CRM suite pass. The retained screenshot is local smoke only. `claude-compare-2338` records CRM bill missing columns/actions and 17/70 row difference from its capture; no fresh paired reference replay was available.

**A3 — DONE_WITH_CONCERNS.** No new center-student source edit in this wave. Existing center-student focused evidence remains source/local smoke. Retained compare index still records missing filters and control overflow; no fresh postintegration DOM/reference replay.

**A4 — DONE_WITH_CONCERNS.** Finance action order is now `Excel`, then `Cập nhật dữ liệu`; header payment/status duplicates removed. Summary remains payload-backed and unsupported fields remain `—`; no fabricated totals/rows. Finance pagination remains explicitly UNKNOWN because no source-backed page metadata exists. Retained compare index still shows debt/student-finance row mismatches and other report row differences.

**A6 — UNKNOWN.** Builder reports were read. Training had no screenshot attempt due no running local instance; finance had one broad shot attempt without route-specific debt/student-finance proof; CRM local bill screenshot exists. Full per-screen 1440x900 before/after inspection cannot be verified here.

**A7 — DONE_WITH_CONCERNS.** This independent verifier checked final remote tip, source hashes, source ownership, focused checks, and retained artifact provenance after the latest edits. Fresh paired reference/local browser replay was not run. Visual, mobile, private/reference, RBAC, production, and full 134-screen acceptance remain UNKNOWN.

## Retained artifact evidence

Read `evidence/visual/claude-compare-2338/INDEX.md` and wave2338 builder reports. It explicitly lists unresolved differences, including control overflow on `/training/class` and `/center/student/index`, missing CRM bill columns/actions, duplicate training filters, missing contract action, and row-count mismatches across training, finance, and CRM reports. These artifacts are historical comparison evidence and were not overwritten or promoted to fresh proof.

No fabricated rows, credentials, reference writes, or synthetic parity receipts were observed in the reviewed wave commits. Training seed helper remains source-backed synthetic local fixture logic; it is not reference/customer data proof.

## Verdict

`DONE_WITH_CONCERNS` for bounded source, ownership, hash, and focused-test verification. Product acceptance remains `PARTIAL / NOT_ACCEPTED`. Do not claim 100%, `134/134`, `WITH_ISSUES=0`, or visual/reference parity until a supported fresh browser run verifies the affected routes at required viewports and the retained compare defects are rechecked.
