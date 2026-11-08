# Verification report: tenant default-on renderer

Date: 2026-11-08
Run: `run_bf152f4f7779`
Target: `/Users/nam/Documents/System-Agentic_AI/products/center-edu-rebuild`
Branch: `center-edu-rebuild-verified`
Current HEAD: `ae3526001774165ef11a7159b13ce7782288aa0f`
Comparison base: `d18332b8581a856dbd5138c5c3eb1c2584f73c5d`
Scope: read-only verification; no source, commit, push, DB, or reference mutation.

## V1 scope and ownership

FACT: `git diff --name-status d18332b..ae35260` contains exactly these three paths:

- `M static/modules/w6_screen_utils.js`
- `A tests/test_tenant_config_default_on.mjs`
- `A plans/center-edu-rebuild-20261030/reports/build-tenant-default-on-20261108.md`

FACT: Commit `ae3526001774165ef11a7159b13ce7782288aa0f` contains the same three paths. No backend, app, or DB path changed in the commit; a path scan found no `backend/`, `app/`, `db/`, `.sqlite`, or `.db` change. Existing foreign untracked/modified paths were preserved.

FACT: Builder report was inspected. Its claimed renderer behavior and bounded validation match the independent checks below.

## V2 checks

- `node --test tests/test_tenant_config_default_on.mjs`: PASS, 2/2.
- `node --check static/modules/w6_screen_utils.js`: PASS.
- `git diff --check`: PASS (no output).
- Independent ES-module import of `tenantConfigHtml`: PASS. A unique missing record emitted a checked toggle; persisted `enabled: "Không"` emitted an unchecked toggle; duplicate-title rows emitted disabled unchecked toggles; the `Tất cả` master emitted a disabled unchecked toggle.

Node emitted the existing `MODULE_TYPELESS_PACKAGE_JSON` warning; no package change was made.

## V3 hashes and limits

SHA-256 at verification:

| File | SHA-256 |
|---|---|
| `static/modules/w6_screen_utils.js` | `4681c6248f7ee1b2d99b028786939d5d0a70fcc773bb5c9c2f8b58e3c25b4926` |
| `tests/test_tenant_config_default_on.mjs` | `3f2017c3ab4fb2ab1310b07f2086a7690dec3ec3295ace97653c5421fd588f6b` |
| `plans/center-edu-rebuild-20261030/reports/build-tenant-default-on-20261108.md` | `b2671ad13f667e518acfa385b870b0177ce6107a7313d5460893b781974f94bd` |

Browser/visual parity: UNKNOWN. Reference behavior: UNKNOWN. Live API persistence: UNKNOWN. Screenshot not required for this source/unit lane.

Status: DONE_WITH_CONCERNS
