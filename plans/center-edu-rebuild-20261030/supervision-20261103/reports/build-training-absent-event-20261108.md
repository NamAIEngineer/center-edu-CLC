# Training absent/event visual lane — 2026-11-08

Task: `run_bf152f4f7779`, dispatched task `task_ce158597da93`, dispatch `ctx_e84fc2fe48e0`.

FACT: Required reference images and `INDEX.md` were opened before editing. The owning renderer is `static/modules/training_routes.js`; no `app.py`, `static/app.js`, or shared CSS changes were made.

FACT: Removed attachment/textarea controls from the filter strip. Comment textarea, file input, and compact send icon now render inside each route table comment cell. Status cells render route-owned chips. Event rows expose route-owned action controls. Absent route status tabs were removed because source inventory identifies the status filter as the control and the reference capture has no action tab strip.

CHECKS: `node --check static/modules/training_routes.js` PASS. `python3 -m unittest tests.test_training_backlog_regressions tests.test_training_assessments_u06_u07` PASS (6 tests). `git diff --check` PASS.

VISUAL: Harness ran at same 1440x900 viewport against disposable port `18995`, output `plans/center-edu-rebuild-20261030/supervision-20261103/evidence/visual/training-absent-event-20261108/`. The harness produced blank REBUILD panes because the local runtime did not complete the login/navigation capture; therefore visual parity is UNKNOWN and no PASS claim is made. Existing harness output includes the requested route comparison files and hashes can be computed from the final workspace.

LIMITATIONS: Reference-private API semantics, authenticated reference parity, and live deployment remain UNKNOWN. Runtime log was empty; no preserved process was restarted.
