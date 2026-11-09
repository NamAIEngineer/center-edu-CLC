# Build wave1212 training + tenant

Acceptance: A-wave1212-T, acceptance A4/A5/A6; sole run `run_bf152f4f7779`.

## Render-path fixes

- `/report/training/register_learning`: repeated bounded post-render repair restores observed `From date` / `To date` values `01/11/2026` and `30/11/2026`, preserves `Tổng số học sinh`, formats ISO date cells as `dd/mm/yyyy`, removes generic submit/reset controls added by the shell normalizer.
- `/tenant/config_excel`: master state derives from actual rendered enabled row toggles after render. Master is checked when all enabled rendered rows are checked. Duplicate-title rows remain disabled fail-closed.

## Fresh evidence

- Local base `http://127.0.0.1:19012`, viewport `1440x900`, fresh Playwright capture.
- [register_learning screenshot](../evidence/visual/wave1212-training-tenant-after/local_report_training_register_learning.png) SHA-256 `2e02fa08dc368467fb6f04a8b168c6bdbb573600ac14c4579f97f9af41f27316`.
- [tenant screenshot](../evidence/visual/wave1212-training-tenant-after/local_tenant_config_excel.png) captured after final sync.
- [tenant DOM receipt](../evidence/visual/wave1212-training-tenant-after/dom-check.json): master `checked=true`, `disabled=true`; report toggles total 59, enabled 49, enabled checked 49, disabled 10 duplicate-title rows.
- Reference paired images retained in same artifact directory; no reference mutation.

## Validation

- `node --check static/modules/report_training.js`: PASS.
- `node --check static/modules/w6_screen_utils.js`: PASS.
- `node --test tests/test_tenant_config_default_on.mjs`: 2/2 PASS.
- Focused report/table/pagination/CRM tests: 13/13 PASS.
- `git diff --check`: PASS.

Status: DONE_WITH_CONCERNS
