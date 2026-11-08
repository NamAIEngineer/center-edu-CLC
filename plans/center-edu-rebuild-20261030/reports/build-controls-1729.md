# BUILD controls-1729

Status: DONE_WITH_CONCERNS

FACT: Commit `735a2d35b7a93fc682a06adb2b1f0d4489d6f1e1` pushed to `origin/NamAIEngineer/build-controls-1729`.
FACT: `static/app.js` now bypasses shared observed-control normalization for `/center/student/index`; route-owned compact multi-select wrappers remain intact. `static/app.js` and `static/modules/training_routes.js` compact trigger/menu controls now have bounded height, overflow, typography, and accessible remove affordance. `/training/class` empty status selection explicitly selects the observed `Tất cả` option while preserving scalar API semantics.
FACT: Focused checks passed: `node --check static/app.js`; `node --check static/modules/training_routes.js`; `python3 -m unittest tests.test_app_normalizer_guard tests.test_training_projection_correction -v` (7 tests OK); `git diff --check`.
FACT: Source hashes: `static/app.js` `a28ce428c3f32a1a6f322ba7e97e26fadff336424f370bb4523d783fac9ded41`; `static/modules/training_routes.js` `a1f389a502369ce2cbd15c2ebcc6c29eee1d4490f06c7a824c28c97df5a8095e`; `tests/test_app_normalizer_guard.py` `fb9d55eb856186c59c8b9ec0c11010e431a4cca309527c7fdd2f8d6d54762948`.
INFERENCE: The oversized student listbox regression came from the generic normalizer ignoring intentionally hidden native selects, then replacing compact route controls.
UNKNOWN: Browser route required for 1440x900 and 390x844 screenshots/DOM was unavailable in this isolated worker; no visual parity claim. `node --test tests/test_training_route_actions.mjs` has a pre-existing delayed async activity failure after its passing assertion (`TypeError: Cannot read properties of undefined (reading 'createElement')`); not caused by this diff.
