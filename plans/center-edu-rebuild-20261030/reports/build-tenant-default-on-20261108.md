# Build report: tenant default-on renderer

Date: 2026-11-08
Run: run_bf152f4f7779
Target: /Users/nam/Documents/System-Agentic_AI/products/center-edu-rebuild
Branch: center-edu-rebuild-verified
Base HEAD: d18332b8581a856dbd5138c5c3eb1c2584f73c5d
Selected provider: filesystem; native Bash/CLI transport, as recorded by ORCA hook enforcement.

## Producing boundary and scope

FACT: The row renderer previously passed missing `enabled` through `tenantEnabled`, which returned false. The renderer now derives checked state from record presence: unique missing records default on; persisted values still use the existing enabled parser. Duplicate-title rows remain disabled and unchecked. Persistence handlers are unchanged.

ASSUMPTION: The prior demo contract supplied in this task remains authoritative for default-on presentation. No fresh reference access occurred.

FACT: Only the owned renderer, focused test, and this report changed. Existing untracked evidence was preserved; no app.js, app.css, backend, DB, or reference writes occurred.

## SHA-256

| File | Before | After |
|---|---|---|
| static/modules/w6_screen_utils.js | 78ff47a78dea3b6fc88a20af7e33593701403b90c607320bfa98c7894ad9abfc | 4681c6248f7ee1b2d99b028786939d5d0a70fcc773bb5c9c2f8b58e3c25b4926 |
| tests/test_tenant_config_default_on.mjs | ABSENT | 3f2017c3ab4fb2ab1310b07f2086a7690dec3ec3295ace97653c5421fd588f6b |

## Acceptance

| ID | Builder result | Evidence |
|---|---|---|
| A1 | PASS, bounded source/unit | Unique missing record checked; persisted Không unchecked; existing Có parser preserved; duplicate-title rows disabled and unchecked. |
| A2 | PASS / UNKNOWN reference | Master Tất cả remains disabled, no handler or bulk operation added. Reference expectation for master behavior UNKNOWN. |
| A3 | PASS | Focused test in tests/; source renderer only; no shared app/backend/DB edits. |
| A4 | PASS | Node tests 2/2; syntax and diff checks pass; exact owned paths staged for Conventional Commit; no push. |

## Validation

- `node --test tests/test_tenant_config_default_on.mjs`: PASS, 2/2 (twice).
- `node --check static/modules/w6_screen_utils.js`: PASS.
- `git diff --check`: PASS.
- Node emits MODULE_TYPELESS_PACKAGE_JSON warning; no package change made.

UNKNOWN: Browser/visual/reference parity and real API persistence were not exercised. Independent verifier after final edit is required and remains for the coordinator to assign; builder reruns do not establish independent verification.

Status: DONE_WITH_CONCERNS
