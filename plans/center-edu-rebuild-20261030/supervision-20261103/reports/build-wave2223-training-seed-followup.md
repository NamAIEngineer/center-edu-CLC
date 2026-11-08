# BUILD follow-up: training seed helper scope

## FACT

Moved route-owned `training_seed_value` to module scope in `app.py`. Initial screen seed and `CenterEduService._ensure_generated_demo_records()` now call the same helper; the prior nested helper no longer exists, so rich-demo backfill cannot raise `NameError`. Existing marker-only repair and user value preservation remain unchanged.

## CHECKS

- `node --check static/modules/training_routes.js` PASS.
- `python3 -m unittest tests.test_training_projection_correction tests.test_training_backlog_regressions` PASS (`10` tests).
- `git diff --check` PASS.
- Disposable `CENTER_EDU_RICH_DEMO=1` SQLite initialization/backfill PASS; both training routes produced 12 rows with natural Vietnamese values and exact statuses.

## INFERENCE

The scope defect was caused by `_training_seed_value` being defined inside the original seed function while referenced by the service backfill method. Shared module-level ownership removes that failure path while keeping route semantics bounded.

## UNKNOWN

Fresh browser screenshots/DOM hashes and private/live reference parity remain UNKNOWN in this worker lane. No credentials or reference writes used.

Commit: `140041ee240716fdbd7bb9ef9b099379e92b7bc4`
Remote SHA: UNKNOWN (push unavailable in worker lane).

Status: DONE_WITH_CONCERNS
Summary: Shared training seed helper scope fixed; initial seed and rich-demo backfill verified with focused checks and disposable SQLite initialization.
Concerns/Blockers: Browser evidence and remote push remain UNKNOWN.
