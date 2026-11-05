# Handoff checkpoint

## Completed in this session

- Confirmed REA and application roots are separate.
- Preserved existing source; no reset, clean, branch deletion, deployment or production mutation.
- Captured source hash snapshot before new documentation.
- Logged into reference through Playwright/ORCA browser flow and observed authenticated dashboard/menu identity.
- Playwright inspected 18 representative reference routes; all were HTTP 200 and authenticated. Sanitized receipt: `plans/ref-survey-20261105.json`.
- Ran current local baseline and post-fix suite: 107 tests PASS; Python and JavaScript syntax PASS.
- Added `docs/parity/TAKEOVER.md`, `docs/parity/MATRIX.csv`, and this handoff.
- Fixed generic training projection: `/training/announcement`, `/training/event`, and `/training/post` now render persisted values through additive `display_data`; route headings match observed titles. Added focused regression.
- Fixed CRM appointment owner filtering: `/crm/potential/appointment` now builds the observed `Nhân viên` options from persisted appointment rows, keeps route-owned controls out of generic normalization, and filters/clears correctly in a real browser smoke.

## Active work

- Reference route survey complete for 18 representative routes; deeper mutation/API semantics remain bounded UNKNOWN.
- Generic training projection fix integrated and verified with local Playwright rich-demo smoke.
- CRM owner-filter fix is integrated in the working tree; browser smoke created only synthetic local rows in `/tmp/center-edu-care-owner-20261105.sqlite3` and stopped cleanly.
- Wave 2 projection verification completed 2026-11-05: `CenterEduService.generated_screen()` keeps persisted form payloads in `record.data` and exposes additive observed-column values in `record.display_data`; `static/app.js` and `static/modules/training_routes.js` consume the projection. Regression covers `/training/announcement`, `/training/event`, and `/training/post`.
- Exact local evidence: `python3 -m unittest discover -s . -p 'test_*.py' -v` -> **107/107 PASS**; focused projection test -> **PASS**; Python compile, JS syntax, and `git diff --check` -> **PASS**. Source hashes: `app.py` `280586a60b7376f9f90de3fb2e4ce046784014f6c9a60843601aec59eaead120`, `test_app.py` `69a8ca70eddad87c9f777a319042a95b5414f78a0009b5831dea7c6fcb768889`, `static/app.js` `6d0e3e011bfbe90c0943b39254a3b4ee1d5206f3ef7b8ba81bd601b7e9fc3ab5`, `static/modules/training_routes.js` `849236f58565cf95c49d47eadd0f62615609be51f359ad26d7f996f9dccfa889`.
- Ownership/runtime receipt: CENTER run `run_bf152f4f7779`, coordinator `term_73a214dd-0d3a-467a-8011-e1e78f4f7779`, generation 5. ORCA worker attempts were blocked at `agent-trust-workspace` after correct repo registration (`repo 671fb1a7-030f-4bef-86b8-d305e514f085`); failed dispatches `ctx_fcb8003079d5`, `ctx_2886849e5dd6`, `ctx_e3d9b2bca7b5` were released. Internal reviewer lanes: `/root/local_gap_audit` (CEDU-FIX-01), `/root/qa_reviewer` (CEDU-QA-03), `/root/reference_survey` (CEDU-REF-01).
- Integration receipts: commits `7d2534b` (projection implementation/regression) and `3da0fe0` (FIN-002 blocker/MATRIX), followed by `26921e4` and `463b9bb` handoff/verifier receipts, pushed to `NamAIEngineer/center-edu-CLC` branch `center-edu-rebuild-verified`; final remote SHA verified as `463b9bb5b944189cef4f7fa7be0bcc3a25115dfd`. No merge, deploy, or main-branch mutation.
- Independent verifier receipt: [`verifier-wave2-20261105.md`](../plans/center-edu-rebuild-20261030/supervision-20261103/reports/verifier-wave2-20261105.md), SHA-256 `cf3fc6953ee019506441cf92a642ef58bc54f601f0485bd58772ac76ac2bb948`, verdict `PASS_WITH_LIMITATIONS`. It independently ran 22 projection/supervision tests, class-post 5/5, W5 report 5/5, disposable ADMIN/API read-back (HTTP 200, truthful empty state, export 403). Its separate 106-test invocation recorded one stale pagination assertion; coordinator's current discovery run is 107/107 PASS. Populated projection read-back and reference visual parity remain unverified there.
- New independent populated proof: [`rich-demo-http-proof-20261105.md`](../plans/center-edu-rebuild-20261030/supervision-20261103/reports/rich-demo-http-proof-20261105.md), SHA-256 `a0307ffc3a9cef797d39b59d65b7c8a8fc01fd087f8c9ecf46f368be4b61121e`. Disposable process `127.0.0.1:19018` authenticated with HTTP 200; announcement/event/post each returned HTTP 200 with 12 persisted rows; `q=Demo 01` returned one match per route; raw `data`, projected `display_data`, and direct SQLite rows were read back. Runtime stopped cleanly.

## Known blockers / limits

- `SOURCE_ROOT` is not a Git repository; use file snapshots/hashes for integrity until an application worktree is identified.
- Reference private API, exact role matrix, formulas, and equal-state visual parity remain UNKNOWN until fresh direct evidence exists.
- Historical README receipts must not be treated as current runtime proof.
- Browser host is unavailable/disabled in this session; authenticated reference parity, equal-state screenshots, mobile `390x844`, and current finance duplicate-control/native-date reproduction remain **UNKNOWN**. Prior `113/134 rendered`, `21 UNKNOWN` route inventory remains the truthful coverage checkpoint.
- Current local browser capability proof: `require('playwright')` -> `NO_PLAYWRIGHT`; CUA inventory -> `browsers: []`, `Browsers: Error: The browser access host is unavailable`. No install, profile restart, settings bypass, or security change attempted.
- The prior QA lane reported one stale assertion against generated pagination markup; the current source suite is green after the projection regression update. This does not establish reference visual parity.

## Next step

Next: use an available local browser harness to reproduce the reported finance filter duplication and date-format behavior from current source; if browser remains unavailable, keep those findings `SUSPECT/UNKNOWN` and do not patch from screenshots alone. Independent verifier must run after the next source edit. Global status remains `PARTIAL / NOT_ACCEPTED`.

## Next bug ledger checkpoint

- `TRN-003` — **FIXED / VERIFIED locally** — owner: lead; evidence: `rich-demo-http-proof-20261105.md`, `MATRIX.csv`; populated HTTP/DB proof now exists for all three training routes.
- `FIN-002` — **VERIFIED LOCALLY WITH LIMITATIONS** — owner: lead; evidence: `finance-dom-wave-20261105.md`, DOM screenshots/hashes, current `MATRIX.csv`; paired select/search controls match the 23-filter observed contract, while the reproduced native date conversion was fixed route-owned with `data-date-text`. Post-fix DOM at `1440x900` and `390x844`: four date controls remain `type=text`; filter `HD-005` reduces rows `10→1`; clear restores `10`. Independent verifier report `verifier-finance-wave-20261105.md` confirms the bounded local behavior; reference/private parity remains UNKNOWN.
- `QA-UI-001/002` — **BLOCKED / UNKNOWN** — owner: runtime/host; evidence: CUA inventory and verifier reports; reference parity and mobile visual acceptance cannot be promoted from source/API evidence.

## Host notification checkpoint

Notifier: `/Users/nam/Documents/System-Agentic_AI/scripts/center-edu-notify`, fixed host thread, metadata-only and idempotent. Duplicate event/path/hash is suppressed; `QUEUED` means accepted by the notifier, not delivered/accepted by host.

- `report` `rich-demo-http-proof-20261105.md`: event `9345b83a2852e6b9`, state `QUEUED`, receipt `01a1abe8-b77f-7281-8d42-0d9c514c17d5`.
- `report` `verifier-wave2-20261105.md`: event `98a34d0d3ff5d910`, state `QUEUED`, receipt `01a1abe9-1ec9-7632-b7f7-17bbfbf746cc`.
- `report` `finance-dom-wave-20261105.md`: event `904470612374e67f`, state `QUEUED`, receipt `01a1abf3-a085-7002-b700-00b4f9c44c83`. Host delivery remains pending; do not resend duplicate event.
- `report` `verifier-finance-wave-20261105.md`: event `bdb47a20af590691`, state `QUEUED`, receipt `01a1abfd-7049-7fa3-b318-1dd3fe893a15`. Host delivery remains pending; do not resend duplicate event.

## FIN-002 independent verification checkpoint

- Target fix: `f152d7375633a7407dfdc0fc1ce25aaab35b089f`; verifier report SHA-256 `ccd52b8a3e6d254d539cb8404cc8fc1a741e0d301f6d080c4a26c8f66162a53f`.
- Independent verifier used isolated Chrome/Playwright-core at `1440x900` and `390x844`; 23 labels, 10 selects, 13 text inputs, four date filters `type=text` + `data-date-text=1`.
- Valid `05/11/2026` emitted `date_from=2026-11-05` and returned the filtered local row; clear reset restored the unfiltered table. Impossible `31/02/2026` returned HTTP 400 `date_from must be YYYY-MM-DD`; reversed range returned HTTP 400 `date_from must be before or equal to date_to`.
- Desktop table wrapper did not overflow (`1224=1224`); mobile preserved horizontal table scroll (`1165>338`). No reproducible 404 post-fix. Focused verifier suite: 12 PASS; JS syntax and diff-check PASS.
- Canonical PNGs and SHA-256: `desktop-1440x900.png` `920ed9643daedf7f61c8e29bf3027a001ca5d2fcec9c1a10e6987e3034ba93a9`; `mobile-390x844.png` `60e4d1df89a77e5111129bd81c3cb591a2c062bf886660e9ec07d18f122b5a5f`.
- Verdict `PASS_WITH_LIMITATIONS`: local FIN-002 behavior is verified; reference equal-state visual/private semantics and ordinary-date runtime remain UNKNOWN. Paired controls are retained because the observed screen spec contains all 23 controls; no duplicate-control bug is claimed.
- Continue invoking the notifier once per substantive report/done/failure artifact, exact canonical report path, no raw body/credentials/customer data. Do not treat queued as delivered; retain the 3-hour host fallback.

## FIN-003 localized date-filter error UX

- Current working-tree edit in `static/app.js` maps known finance date validation errors to Vietnamese UI text while preserving backend HTTP 400, `VALIDATION_ERROR`, and raw JSON messages. Source SHA-256: `84923c34c69c035e96ae425b5bb6c697fe17d9a4d7aef022d596d6466717e302`.
- Local disposable smoke at `127.0.0.1:19023` verified valid `05/11/2026` → ISO query and clear reset; impossible date and reversed range → Vietnamese toasts with backend 400/error-code/raw-message receipts. Summary stayed at prior totals in the invalid cases; the earlier zero-summary observation remains unconfirmed.
- Evidence: `plans/center-edu-rebuild-20261030/supervision-20261103/evidence/finance-error-ux-wave-20261105/` (`desktop-1440x900.png` SHA `b7f8f1becc5f51208c8634e2e6c1aa64e3f8c1e7560f8dfe9291d8ea31806f22`; `mobile-390x844.png` SHA `7cf2fab4a70a5bcbc14bfe425d432988d95e2ab22d99f391792b0d3855a3239d`; `network.json` SHA `980c72c32826c4f635539682caa1016e44e04d399b597459020a2ec9e87275d8`; independent receipt SHA `fbc83919b131a5a3b990b23be725aabc41f74376d98dcb74949ea43db1d549ee`).
- `FIN-003` is `VERIFIED WITH LIMITATIONS` after independent VERIFY-06 (`verifier-finance-error-ux-20261105.md`, SHA-256 `7fa095b5f3a6f72dd7bfd04a0dcaf2ef300104c0e54bcba963faf5785747cbfa`). Independent source hash matches `84923c34c69c035e96ae425b5bb6c697fe17d9a4d7aef022d596d6466717e302`; receipt `independent-network.json` SHA `fbc83919b131a5a3b990b23be725aabc41f74376d98dcb74949ea43db1d549ee`. Invalid and reversed filters preserve backend HTTP 400/raw errors while showing Vietnamese toasts; summary stays at 86 and clear restores 10 rows. Intermediate partial-date request can render before final validation; mobile table overflow remains UNKNOWN in this run. Reference parity, ordinary-date runtime, and the 21 route/action UNKNOWN cells remain UNKNOWN. Global status remains `PARTIAL / NOT_ACCEPTED`.
- `report` `finance-error-ux-wave-20261105.md`: notifier event `cc0221b2b4d7ab39`, state `FAILED`, receipt `Error: failed to queue session message: thread/queue/add failed: failed to read thread: invalid thread-store request: no rollout found for thread id 01a1a127-838d-7c91-a620-ad3b68b2c37d (code -32603)`. Do not blind-retry; host transport state is a bounded runtime blocker.

## CEDU-CLASS-01 local gap audit

- Read-only local audit report: `plans/center-edu-rebuild-20261030/supervision-20261103/reports/local-gap-audit-training-class-20261105.md`, SHA-256 `e28e0c2a815dd02bffc224267f79c918edfedb679a532b4664084eeade1a6e5d`.
- Disposable runtime `127.0.0.1:19105` + SQLite stopped cleanly. Login 200; `/api/classes` returned 25 persisted rows; `q=ENG-FND` matched; no-match returned `[]`; invalid status and reversed date range returned 400 `VALIDATION_ERROR`; SQLite read-back confirmed `ENG-FND-01`.
- `/training/class` HTTP 200 and route labels were observed. Live DOM hydration, pagination, empty-state interaction, and reference parity remain UNKNOWN because browser host is unavailable. No source change.
- Notifier event `e15a2ca56f95df71` state `FAILED`, same bounded thread-store error as FIN-003 (`no rollout found`); no blind retry.
- `report` `verifier-finance-error-ux-20261105.md`: notifier event `74a3ef51732ee694`, state `FAILED`, receipt same invalid thread-store/no rollout error; no blind retry.
- Integrated commit `9408c52` (`fix(center): localize finance date filter errors`) pushed fast-forward to `origin/center-edu-rebuild-verified`; no merge/deploy/main mutation. Final focused checks: JS syntax PASS, `test_health_and_public_shell` PASS, `test_finance_contract_filter_matrix_and_summary_are_scoped` PASS, diff-check PASS.
- Notifier `done` event `03f38bb75a8b8233` for FIN-003 also failed with the same invalid thread-store/no rollout receipt; host fallback remains required.


## 2026-11-06 priority UNKNOWN route wave

- `CEDU-TRN-001`: [local-gap-audit-training-timetable-20261106.md](../plans/center-edu-rebuild-20261030/supervision-20261103/reports/local-gap-audit-training-timetable-20261106.md), SHA `92efe449d29a2b034d1908473548b346f266c1e4105c553f393dd8e27542d613`. Local `/api/timetable` 200 with 364 persisted rows; room/week filters 200; CSV export 200; invalid date 400. Local `/api/attendance` 200 with 864 persisted rows; status/date filter 200; invalid status 400. Route HTML and renderer markers present. Browser DOM, pagination, mobile, empty-state, role/reference parity remain UNKNOWN.
- `CEDU-CRM-FIN-UI-002`: [local-gap-audit-crm-finance-20261106.md](../plans/center-edu-rebuild-20261030/supervision-20261103/reports/local-gap-audit-crm-finance-20261106.md), SHA `aeec4780ddf3eae7bcadafe84d91f47108bb28caf751262c7c540002d7ba2e50`. Independent QA rendered six priority routes: CRM potential/appointment, finance bill/revenue, sale contract, survey. APIs and screen specs 200; truthful empty/nonempty states observed. Search/reset/modal/export/status mutation and DB read-back remain UNKNOWN because the bounded interaction harness timed out. No source edits.
- Exact next route owners: training lane → `TRN-001/TRN-002/TRN-004/TRN-005`; CRM/finance lane → `CRM-001/CRM-003/FIN-001`; report/setup lane → `REP-001/SET-001`; coordinator owns integration and independent post-edit verification. No global 134/134 claim.
- Notifier diagnostics: nonsecret runtime values were `HOME=/Users/nam`, `CODEX_HOME=/Users/nam/.codex`, unset `CODEX_PROFILE`, `codex=/Users/nam/.local/bin/codex`, version `codex-cli 0.163.0`; expected target `CODEX_HOME=/Users/nam/.codex` matches. Receipt DB currently has `QUEUED=4`, `FAILED=4`; recent failures are recorded as `FAILED` with exact `no rollout found` receipts. No reset, account/provider/global-config change, proxy, or blind resend.
- New report events `14d5bc5a6ab56274` (training timetable) and `6bdc22e826c7faed` (CRM/finance) failed at the same bounded thread-store error; host fallback remains active. Do not re-notify already reviewed FIN-003 artifacts.


## CEDU-REP-SET-001 report/setup audit

- Report: `plans/center-edu-rebuild-20261030/supervision-20261103/reports/local-gap-audit-report-setup-20261106.md`, SHA `89b6c40fbe9e566ca3233033a779c73ddb29d2de962d1556a606c66f9abba561`.
- Disposable runtime `127.0.0.1:19066`, Playwright/Chrome, no source or reference writes. `/report/finance/revenue_center` API 200; `/survey` rendered with filter/export; `/setup/classroom` Admin list/no-match/export 200; Student `/api/surveys` and `/api/classrooms` 403; finance revenue report role-filtered 200.
- `/center/classroom/index` is not the local canonical route; `/setup/classroom` is implemented. `/center/index` has no local screen contract and returned `SCREEN_SPEC_NOT_FOUND`. `/center/holiday/index` generated route loaded; mutation persistence remains UNKNOWN.
- `/report/finance/revenue` and `/report/attendance` alias probes triggered server-side unknown-route socket hangup; classify as an implementation/runtime defect candidate, not a browser parity claim. The recorded `ReferenceError: Cannot access 'sp' before initialization` appeared in this harness capture but no `sp` declaration exists in tracked app source; classify tool/harness provenance UNKNOWN pending isolated reproduction.
- No implementation change yet. Owner: report/setup lane. Next: isolate alias handling and generic generated-screen render with a disposable local runtime; add regression only after source-level reproduction. Do not reset or bulk patch from this report.
- Notifier event state `FAILED` remains separate and recorded by its event ID; host fallback active.


## REP-002 report alias/error-boundary fix

- Source fix: `modules/report_engine.py` maps legacy aliases `/report/finance/revenue` → `/report/finance/revenue_center` and `/report/attendance` → `/report/training/attendance`. `app.py` converts unknown `KeyError` report definitions to structured HTTP 404 `NOT_FOUND`; `test_app.py` covers aliases, export, and unknown route.
- Focused test: `test_report_engine_v2_catalog_run_export_and_no_fake_rows` PASS; `py_compile` and diff-check PASS.
- Independent R2 report: `plans/center-edu-rebuild-20261030/supervision-20261103/reports/verifier-report-alias-r2-20261106.md`, SHA `1dedd36c4ba0ebece4870e721f5a9af225b1fed3c80721cd7f59a99caef5807b`, verdict `PASS_WITH_LIMITATIONS`. Alias run/export and canonical routes returned 200 JSON/CSV; `/report/training` and `/report/unknown` returned structured 404 JSON; no socket hangup.
- UI parity, role matrix, mutation semantics remain UNKNOWN. Notifier event `1163316d8674e96f` state `FAILED` with existing no-rollout thread-store receipt; no blind retry.
