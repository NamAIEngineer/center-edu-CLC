# BUILD report: wave2115 tenant config visual correction

## 1. Scope and diagnosis

FACT: Route owner is `static/modules/w6_screen_utils.js`; `static/modules/tenant_lane.js` is metadata-only. Current source already renders catalog-backed rows grouped by report group with `No.`, `Báo cáo`, and `Tắt/bật excel báo cáo` columns, plus a disabled master switch.

FACT: Current source preserves persisted `enabled` values, defaults uniquely identified missing records on, and disables duplicate-title rows/read-only/unreadable settings fail-closed. No synthetic 60-row data or unrelated files were added.

INFERENCE: The observed reference shape is already present in current source; no source correction is evidenced.

ASSUMPTION: The retained verifier reference `tenant_config_excel.png` represents the observed reference for this bounded local comparison. Exact `cmp_tenant_config_excel.png` was unavailable in the workspace search.

UNKNOWN: Production/reference authenticated API, RBAC, persistence, and live browser parity.

## 2. Fresh before/after evidence

FACT: Disposable local runtime used port `19421` and DB `/tmp/center-edu-wave2115-tenant-19421.sqlite3`; ADMIN login used the existing demo contract. Fresh Playwright captures at 1440x900 are in `evidence/visual/wave2115-tenant/`.

FACT: Before and after PNGs are byte-identical (`cmp` exit 0), both 1440x900, SHA-256 `daec7e903ca6ef2eeb26eface02eeaca7df5565bfc9c32b60b3e3077b66224e4`. DOM snapshots each report table headers `No.`, `Báo cáo`, `Tắt/bật excel báo cáo`, 64 rows, 49 checked toggles, and 11 disabled controls.

## 3. Verification

- `node --check static/modules/w6_screen_utils.js`: PASS
- `node --test tests/test_tenant_config_default_on.mjs`: PASS, 2/2
- `git diff --check`: PASS
- `git status --short`: only route-owned evidence/report additions; no source diff

## 4. Acceptance mapping

- A5: PASS, catalog-backed report/group rows only.
- A6: PASS, toggles/default state supported by source; duplicate titles and master fail-closed.
- A7: PASS, no fabricated rows or seed/data changes.
- C2-C5: PASS for local source/syntax/focused-test/visual evidence; live/reference persistence and RBAC remain UNKNOWN.
- V1: NO-OP PASS, fresh before/after visual captures identical; current source already matches observed shape.

## 5. Status

Status: DONE_WITH_CONCERNS (NO-OP; local source/tests/visual PASS; live/reference parity UNKNOWN)
