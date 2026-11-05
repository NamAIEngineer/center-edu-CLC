# Independent verifier: wave 2 / generated training projection

Date: 2026-11-05
Source: `/Users/nam/Documents/System-Agentic_AI/products/center-edu-rebuild`
Verified commit: `7d2534be527dd4cd1eddbe858d3c10c936ea21db`

## Results

- `git diff --check 7d2534b^ 7d2534b`: PASS.
- Focused projection/supervision tests: PASS (22 tests across `tests.test_training_projection_correction`, `tests.test_training_supervision`, and `tests.evidence.test_W1_training_routes`).
- Class-post tests: PASS, 5/5 when discovered from `modules` (`python3 -m unittest discover -s modules -p 'test_class_post.py' -v`). Direct dotted import from repository root fails because `modules/test_class_post.py` imports `report_crm_center` as a top-level module; this is a test invocation/import-path issue, not a source runtime failure.
- W5 class-post report tests: PASS, 5/5.
- Python compile and JavaScript syntax checks: PASS in prior QA run; no source edits in this verification.
- Full suite baseline from independent QA: 106 tests discovered, 105 PASS, 1 FAIL. Failure is stale assertion `test_health_and_public_shell` expecting literal `value="10"` in `static/app.js`; current page-size options are generated dynamically by `bindDataTable`.

## API / DB read-back

Disposable runtime used SQLite `/tmp/center-edu-verify-wave2c.sqlite3`, loopback port 18989, seeded with `CENTER_EDU_DEMO_PASSWORD=QA-only-20261105`; stopped after verification.

Authenticated `ADMIN` login returned HTTP 200. For each route, `GET /api/generated/screens?route=...` returned HTTP 200 and a valid route spec:

- `/training/announcement`: 0 records; empty state is truthful.
- `/training/event`: 0 records; empty state is truthful.
- `/training/post`: 0 records; empty state is truthful.

Search query `q=Center` also returned 0 records for all three routes. Persisted record projection was therefore not observable in this empty database, but source inspection confirms the additive `data` + `display_data` response shape at `app.py:2011-2018` and query matching against `display_data` at `app.py:2012`.

Exports for all three routes returned HTTP 403 `EXPORT_NOT_AVAILABLE`, matching their observed screen contracts rather than silently fabricating CSV output.

## Browser

No reference browser writes were performed. Existing sanitized reference survey is at `plans/ref-survey-20261105.json`. Local Playwright smoke was available in the earlier QA lane; this verifier did not alter or reuse a shared browser session.

## Verdict

`PASS_WITH_LIMITATIONS`: commit projection change is present and focused projection/report tests pass. Full suite remains blocked by one stale static assertion. Empty route DB read-back proves truthful no-data behavior; populated projection read-back and reference visual parity remain unverified in this lane.
