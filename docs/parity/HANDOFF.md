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
- `FIN-002` — **FIXED LOCALLY / AWAITING INDEPENDENT VERIFIER** — owner: lead; evidence: `finance-dom-wave-20261105.md`, DOM screenshots/hashes, current `MATRIX.csv`; paired select/search controls match the 23-filter observed contract, while the reproduced native date conversion was fixed route-owned with `data-date-text`. Post-fix DOM at `1440x900` and `390x844`: four date controls remain `type=text`; filter `HD-005` reduces rows `10→1`; clear restores `10`. Independent verifier must still confirm the final commit before promotion to `VERIFIED`.
- `QA-UI-001/002` — **BLOCKED / UNKNOWN** — owner: runtime/host; evidence: CUA inventory and verifier reports; reference parity and mobile visual acceptance cannot be promoted from source/API evidence.

## Host notification checkpoint

Notifier: `/Users/nam/Documents/System-Agentic_AI/scripts/center-edu-notify`, fixed host thread, metadata-only and idempotent. Duplicate event/path/hash is suppressed; `QUEUED` means accepted by the notifier, not delivered/accepted by host.

- `report` `rich-demo-http-proof-20261105.md`: event `9345b83a2852e6b9`, state `QUEUED`, receipt `01a1abe8-b77f-7281-8d42-0d9c514c17d5`.
- `report` `verifier-wave2-20261105.md`: event `98a34d0d3ff5d910`, state `QUEUED`, receipt `01a1abe9-1ec9-7632-b7f7-17bbfbf746cc`.
- `report` `finance-dom-wave-20261105.md`: event `904470612374e67f`, state `QUEUED`, receipt `01a1abf3-a085-7002-b700-00b4f9c44c83`. Host delivery remains pending; do not resend duplicate event.
- Continue invoking the notifier once per substantive report/done/failure artifact, exact canonical report path, no raw body/credentials/customer data. Do not treat queued as delivered; retain the 3-hour host fallback.
