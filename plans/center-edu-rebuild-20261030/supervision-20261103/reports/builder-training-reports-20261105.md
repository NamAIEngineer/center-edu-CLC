# Training/report builder evidence — 2026-11-05

Scope: training/report lane files only. Private/reference semantics remain UNKNOWN; no synthetic rows added.

Changes:

- Timetable matrix now renders only observed/local room headers, preserving first-seen deduplication and preventing oversized empty grids. Existing week/day/date/time filters remain bounded and query-backed where verified.
- Training reports expose explicit loading, error, empty, scoped table headers, and submit focus behavior. Refresh failures stay visible with Vietnamese alert text; empty datasets remain empty.
- Report filters ignore observed sentinel choices (`Tất cả`, `All`, `Chọn ...`) instead of turning them into SQL predicates.
- W6 student helpers expose sentinel-safe filter normalization and deterministic pagination; student persistence remains coordinator-owned.

Verification:

- `node --check static/modules/training_routes.js`
- `node --check static/modules/report_training.js`
- `node --check static/modules/w6_overrides.js`
- `python3 -m unittest tests.test_training_supervision tests.test_training_timetable_lane tests.test_training_projection_correction tests.evidence.test_W1_training_routes tests.evidence.test_W4_report_training_teacher` — 35 tests, OK.
- Hash manifest: `builder-training-reports-20261105.hashes`.

Limitations: no visual/private reference acceptance; no app.js/app.css/shared DB changes; report routes with no local source stay empty/UNKNOWN by contract.
