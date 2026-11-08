# Wave2115 tenant config visual evidence

FACT: Fresh local Playwright capture at 1440x900 against disposable runtime `127.0.0.1:19421`, DB `/tmp/center-edu-wave2115-tenant-19421.sqlite3`.

FACT: Before and after captures are separate files and byte-identical (`cmp` PASS), proving the current source is a NO-OP visual correction. Both DOM snapshots report the catalog-backed table headers `No.`, `Báo cáo`, `Tắt/bật excel báo cáo`, 64 body rows, 49 checked toggles, and 11 disabled controls (including disabled `Tất cả` master).

FACT: Both PNGs are 1440x900. No reference file named `cmp_tenant_config_excel.png` was present in the workspace search; the retained verifier reference `tenant_config_excel.png` is outside this branch and was inspected visually. Local screenshot matches its visible table structure.

FACT: SHA-256:

- `before-1440x900.png`: `daec7e903ca6ef2eeb26eface02eeaca7df5565bfc9c32b60b3e3077b66224e4`
- `after-1440x900.png`: `daec7e903ca6ef2eeb26eface02eeaca7df5565bfc9c32b60b3e3077b66224e4`
- `before-dom.json`: generated fresh in this run
- `after-dom.json`: generated fresh in this run

UNKNOWN: Authenticated production/reference live parity, persistence mutation, and RBAC beyond disposable local ADMIN runtime.
