# BUILD report: training absent/event visual contract

Task: `run_bf152f4f7779` · branch `wave2115-training` · commit `ec0917e5`.

Acceptance scope: `A1, A6, A7 · C2, C3, C4 · V1`.

## FACT

Required reference images were opened before editing. The owning renderer is `static/modules/training_routes.js`; no `app.py`, `static/app.js`, shared CSS, seed data, credentials, or reference files changed.

Payload projection reads direct rows and generated-screen `{data, display_data}` wrappers. Absent fields resolve observed aliases (`hoc_vien`, `buoi_nghi`, `ly_do`); event fields resolve observed Vietnamese aliases and persisted values. Empty payloads remain `Chưa có dữ liệu` with no row insertion. Status chips map source status values. Absent `Thêm mới` remains a route-owned filter-row action. Event action controls use icon glyphs with titles and ARIA labels. Event rows include source-count footer and pager controls derived from `rows.length`; status progress bars expose ARIA values derived from payload rows.

## CHECKS

`node --check static/modules/training_routes.js`; `git diff --check`; `python3 -m unittest tests.test_training_backlog_regressions tests.test_training_assessments_u06_u07 tests.test_training_projection_correction` (`11` tests) PASS.

## VISUAL

Fresh Playwright captures ran at `1440x900` against disposable port `18996`; both routes returned HTTP `200`, console errors were empty. Artifacts and SHA-256 manifest: `evidence/visual/wave2115-training/`.

## INFERENCE

The source defect was renderer alias loss for generated-screen payloads plus missing route-owned event progress/footer geometry. Fresh local captures show persisted absent fields and event progress/footer structure.

## ASSUMPTION

Existing local rich-demo records are fixture data supplied by the runtime. The module does not create or filter those records.

## UNKNOWN

Private reference API semantics, reference authenticated DOM parity, RBAC behavior against private deployment, and production/live parity remain UNKNOWN.

## Status

Status: DONE_WITH_CONCERNS

Summary: Payload-backed absent/event rendering repaired; route controls, status/progress/footer geometry aligned; focused tests and fresh screenshots passed.

Concerns: Reference/private/live execution remains UNKNOWN; rich-demo fixture labels remain runtime-owned.
